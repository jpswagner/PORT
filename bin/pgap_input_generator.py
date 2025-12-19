#!/usr/bin/env python3
import argparse
import json
import os

def main():
    parser = argparse.ArgumentParser(description="Generate PGAP input.yaml (JSON format supported by cwltool)")
    parser.add_argument("--fasta", required=True, help="Input FASTA file")
    parser.add_argument("--output", required=True, help="Output YAML/JSON file")
    parser.add_argument("--genus", default="Staphylococcus", help="Genus")
    parser.add_argument("--species", default="aureus", help="Species")
    parser.add_argument("--strain", default="unknown", help="Strain")
    parser.add_argument("--pgap_data_dir", required=True, help="Path to PGAP data directory")
    args = parser.parse_args()

    # Create the data structure
    # According to PGAP CWL definition, 'supplemental_data' is a Directory object
    data = {
        "fasta": {
            "class": "File",
            "location": os.path.basename(args.fasta)
        },
        "submol": {
            "class": "File",
            "location": "submol.yaml"
        },
        "supplemental_data": {
            "class": "Directory",
            "location": args.pgap_data_dir
        }
    }

    submol_data = {
        "topology": "circular",
        "organism": {
            "genus_species": f"{args.genus} {args.species}",
            "strain": args.strain
        }
    }

    with open("submol.yaml", "w") as f:
        json.dump(submol_data, f)

    # Write input.yaml (as JSON)
    with open(args.output, "w") as f:
        json.dump(data, f)

if __name__ == "__main__":
    main()
