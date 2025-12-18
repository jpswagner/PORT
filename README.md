[![Nextflow](https://img.shields.io/badge/nextflow%20DSL2-%E2%89%A522.10.1-23aa62.svg)](https://www.nextflow.io/)
[![run with docker](https://img.shields.io/badge/run%20with-docker-0db7ed?labelColor=000000&logo=docker)](https://www.docker.com/)

# Plasmid Outbreak Reporting Tool (PORT)

<p align="center">
    <a href="https://creativecommons.org/licenses/by/4.0/">
        <img src="https://mirrors.creativecommons.org/presskit/buttons/88x31/png/by.png" alt="CC BY 4.0 License" height="31"/>
    </a>
</p>

# PORT

An automated pipeline for plasmid outbreak investigation.

<p align="center">
<img src="https://github.com/jqbeh/PORT/blob/main/docs/_figures/port_logo.png?raw=true" alt="alt text" width="500">
</p>

## Overview

PORT automates the analysis of Nanopore sequencing data for plasmid tracking. It performs:
1.  **Preprocessing**: Quality control and trimming (Porechop, NanoPlot).
2.  **Assembly**: Long-read assembly (Dragonflye or Autocycler).
3.  **Annotation**: Prokaryotic genome annotation (PGAP).
4.  **Characterization**:
    *   Antimicrobial Resistance (AMRFinderPlus).
    *   Plasmid Reconstruction (MOB-suite).
    *   Replicon Typing (PlasmidFinder).
5.  **Visualization**: Comparative gene synteny plots (Clinker) for whole plasmids and AMR gene flanking regions.

## Usage

### Prerequisites
*   [Nextflow](https://www.nextflow.io/docs/latest/getstarted.html) (>=22.10.1)
*   [Docker](https://docs.docker.com/engine/install/) or Singularity

### 1. Preparing PGAP Data
This pipeline uses PGAP for annotation, which requires a reference data library (~30GB).
You can either provide an existing directory or let the pipeline attempt to download it (requires internet and ~30GB space).

```bash
# Recommended: Set up data beforehand
python3 modules/pgap/pgap.py --update --data /path/to/pgap_data
```

### 2. Running the Pipeline

#### Standard Run (FASTQ Inputs)
Run the pipeline on a directory of raw Nanopore FASTQ files.

```bash
nextflow run main.nf \
    --input_dir ./data/fastq \
    --output_dir ./results \
    --pgap_data_dir /path/to/pgap_data \
    -profile standard
```

#### Run with Pre-assembled Genomes (FASTA Inputs)
Skip assembly and start directly with assessment and characterization.

```bash
nextflow run main.nf \
    --assemblies ./data/assemblies \
    --output_dir ./results \
    --pgap_data_dir /path/to/pgap_data \
    -profile standard
```

### Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--input_dir` | Directory containing input FASTQ files (`.fastq`, `.fastq.gz`) | `null` |
| `--assemblies` | Directory containing pre-assembled genomes (`.fasta`, `.fa`) | `null` |
| `--output_dir` | Directory where results will be saved | `./output` |
| `--pgap_data_dir` | Path to PGAP reference data directory. If not set, pipeline may try to download it. | `null` |
| `--assembler` | Assembler to use: `autocycler` (hybrid/circular) or `dragonflye` (long-read) | `autocycler` |
| `--read_type` | Read type for Autocycler (e.g., `ont_r10`, `ont_r9`) | `ont_r10` |
| `--medaka_model` | Medaka model for Dragonflye polishing | `r1041_e82_400bps_sup` |

## Outputs

Key results can be found in the output directory:
*   **`assemblies/`**: Final assembled genomes.
*   **`pgap_annotations/`**: Annotated GenBank (`.gbk`) and GFF files.
*   **`clinker_visualization/`**: Interactive HTML plots comparing plasmid structures and AMR gene contexts.
*   **`amrfinder_results/`**, **`mobsuite_results/`**, **`plasmidfinder/`**: Detailed typing reports.

## Documentation

Full documentation for PORT can be found [here](https://jqbeh.github.io/PORT/)

## Citation

If you use PORT in your research, please cite this repository.

## License

Distributed under the MIT License.
