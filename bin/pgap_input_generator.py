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
    args = parser.parse_args()

    # Create the data structure
    data = {
        "fasta": {
            "class": "File",
            "location": os.path.basename(args.fasta)
        },
        "submol": {
            "class": "File",
            "location": "submol.yaml"
        }
    }

    # Write submol.yaml (required by PGAP)
    # PGAP accepts YAML or JSON. We will use JSON for portability if YAML lib missing.
    # However, 'submol.yaml' expects yaml extension, but content can be JSON (often compatible)
    # OR we just write a simple yaml manually since we don't have PyYAML.
    # Actually, JSON is valid YAML 1.2.

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
