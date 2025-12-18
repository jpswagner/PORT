#!/usr/bin/env nextflow

nextflow.enable.dsl=2

/*
========================================================================================
        IMPORT PLUGINS
========================================================================================
*/

include { validateParameters; paramsSummaryLog; samplesheetToList } from 'plugin/nf-schema'
include { startMessage } from './modules/messages'

include { PORECHOP          } from './modules/preprocess'
include { NANOPLOT          } from './modules/preprocess'
include { DRAGONFLYE        } from './modules/long_assemblers'
include { AUTOCYCLER        } from './modules/long_assemblers'
include { QUAST             } from './modules/assembly_assess'
include { AMRFINDERPLUS_RUN } from './modules/amrfinder'
include { MOBSUITE_RECON    } from './modules/mobsuite'
include { PLASMIDFINDER     } from './modules/plasmidfinder'
include { check_env         } from './modules/check_env'

// New Modules
include { PGAP_RUN; PGAP_DOWNLOAD } from './modules/pgap'
include { CLINKER_VISUALIZE; EXTRACT_INPUTS } from './modules/clinker'
include { CLINKER_VISUALIZE as CLINKER_VISUALIZE_PLASMIDS } from './modules/clinker'

workflow {

    println "       🚀 Starting main PORT pipeline..."
    startMessage(workflow.manifest.version)

     // Print summary of supplied parameters
    log.info paramsSummaryLog(workflow) 

    // Check output directory exists
    if( !file(params.output_dir).exists() ) {
        println "Creating output directory '${params.output_dir}'."
        file(params.output_dir).mkdirs()
    } else {
        println "--------------------------------------------------------------------------------"
        println "Overwriting results in existing output directory '${params.output_dir}'."
        println "--------------------------------------------------------------------------------"
    }


    // ─────────────────────────────
    // 🧬 Conditional Environment Check
    // ─────────────────────────────

    if (workflow.profile == 'conda') {
        check_env()
    }

    // ─────────────────────────────────────────────
    // 0️⃣  PGAP Data Preparation
    // ─────────────────────────────────────────────
    if (params.pgap_data_dir) {
        pgap_data_ch = Channel.value(file(params.pgap_data_dir))
    } else {
        PGAP_DOWNLOAD()
        pgap_data_ch = PGAP_DOWNLOAD.out.pgap_data_dir
    }

    // ─────────────────────────────────────────────
    // 1️⃣  Input handling
    // ─────────────────────────────────────────────
    if (params.assemblies) {
        channel
            .fromPath("${params.assemblies}/*.{fa,fasta}", checkIfExists: true)
            .ifEmpty { error "No FASTA files found in assemblies directory '${params.assemblies}'." }
            .map { file ->
                def sample_id = file.baseName.replaceFirst(/(\.fa|\.fasta)$/, '')
                tuple(sample_id, file)
            }
            .set { assemblies_ch }

    } else {
        channel
            .fromPath("${params.input_dir}/*.{fastq,fastq.gz}", checkIfExists: true)
            .ifEmpty { error "No FASTQ files found in input directory '${params.input_dir}'." }
            .map { file -> 
                def base = file.baseName
                def illumina = base ==~ /.*(_1|_2|_R1|_R2)(\.fastq(\.gz)?)?$/
                if (illumina) {
                    def sample_id = base.replaceFirst(/(\.fastq(\.gz)?)$/, '')
                    println "Ignoring Illumina-style file: ${file} (sample: ${sample_id})"
                    return null
                }
                def sample_id = base.replaceFirst(/(\.fastq(\.gz)?)$/, '')
                tuple(sample_id, file)
                }
            .filter { it != null }
            .set { fastq_files }

        // ─────────────────────────────────────────────
        // 2️⃣  Run assembly workflow
        // ─────────────────────────────────────────────
        PORECHOP(fastq_files)
        NANOPLOT(PORECHOP.out)

        if (params.assembler == 'autocycler') {
            AUTOCYCLER(PORECHOP.out, params.read_type)
            assemblies_ch = AUTOCYCLER.out.assembly
        } else {
            DRAGONFLYE(PORECHOP.out, params.medaka_model)
            assemblies_ch = DRAGONFLYE.out
        }
    }

    // ─────────────────────────────────────────────
    // 3️⃣  Common downstream step
    // ─────────────────────────────────────────────

    QUAST(assemblies_ch)

    // ─────────────────────────────────────────────
    // 4️⃣  Annotation with PGAP
    // ─────────────────────────────────────────────
    PGAP_RUN(assemblies_ch, pgap_data_ch)

    // ─────────────────────────────────────────────
    // 5️⃣  Characterization
    // ─────────────────────────────────────────────

    AMRFINDERPLUS_RUN(assemblies_ch)
    MOBSUITE_RECON(assemblies_ch)
    PLASMIDFINDER(assemblies_ch)

    // ─────────────────────────────────────────────
    // 6️⃣  Visualization with Clinker
    // ─────────────────────────────────────────────

    pgap_ch = PGAP_RUN.out.gbk
    amr_ch = AMRFINDERPLUS_RUN.out.report
    mob_ch = MOBSUITE_RECON.out.contig_report

    extract_input_ch = pgap_ch
        .join(amr_ch, remainder: false)
        .join(mob_ch, remainder: false)

    EXTRACT_INPUTS(extract_input_ch)

    // Visualize AMR Flanks (if any)
    EXTRACT_INPUTS.out.flanks
        .filter { it[1].size() > 0 }
        .set { flank_ch }
    CLINKER_VISUALIZE(flank_ch, 'amr_flank')

    // Visualize Plasmids (if any)
    EXTRACT_INPUTS.out.plasmids
        .filter { it[1].size() > 0 }
        .set { plasmid_ch }
    
    CLINKER_VISUALIZE_PLASMIDS(plasmid_ch, 'plasmid')
}
