process CLINKER_VISUALIZE {
    tag "$sample_id"
    label 'process_medium'
    label 'clinker_container'

    publishDir "${params.output_dir}/clinker_visualization", mode: 'copy'

    input:
    tuple val(sample_id), path(gbk_files)
    val(type) // 'plasmid' or 'amr_flank'

    output:
    path "${sample_id}_${type}_clinker.html", emit: html_plot

    script:
    """
    # If no GBK files, skip
    # Check if any file matching the pattern exists or if the input is a list
    if [ -n "$gbk_files" ] && [ -e "\$(ls -1 *.gbk 2>/dev/null | head -1)" ]; then
        clinker *.gbk -p "${sample_id}_${type}_clinker.html"
    else
        touch "${sample_id}_${type}_clinker.html"
        echo "No input files for clinker" > "${sample_id}_${type}_clinker.html"
    fi
    """
}

process EXTRACT_INPUTS {
    tag "$sample_id"
    label 'process_single'
    // Needs biopython. Using a standard image or relying on environment.
    container 'quay.io/biocontainers/biopython:1.78'

    input:
    tuple val(sample_id), path(gbk), path(amr_tsv), path(mob_report)

    output:
    tuple val(sample_id), path("amr_flank_*.gbk"), emit: flanks, optional: true
    tuple val(sample_id), path("plasmid_*.gbk"), emit: plasmids, optional: true

    script:
    """
    extract_clinker_inputs.py --gbk $gbk --amr_tsv $amr_tsv --mob_report $mob_report
    """
}
