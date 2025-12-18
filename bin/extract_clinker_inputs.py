#!/usr/bin/env python3
import argparse
import os
import csv
from Bio import SeqIO

def parse_amr_finder(tsv_file):
    """Parses AMRFinderPlus output to get contig IDs and positions of AMR genes."""
    amr_hits = []
    if not os.path.exists(tsv_file):
        return amr_hits

    with open(tsv_file, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            amr_hits.append({
                'contig_id': row['Contig id'],
                'start': int(row['Start']),
                'end': int(row['Stop']),
                'gene': row['Gene symbol'],
                'strand': row['Strand']
            })
    return amr_hits

def parse_mob_suite(txt_file):
    """Parses MOB-suite contig_report.txt to identify plasmid contigs."""
    plasmid_contigs = set()
    if not os.path.exists(txt_file):
        return plasmid_contigs

    try:
        with open(txt_file, 'r') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                # MOB-suite 3.x report usually has 'sample_id' which is actually the contig ID
                # OR 'contig_id'. It depends on the header.
                # Standard headers: sample_id, molecule_type, primary_cluster_id, ...
                # If the input was a multifasta, 'sample_id' in the report usually corresponds to the FASTA header.

                # Check for molecule_type == 'plasmid'
                is_plasmid = False
                if 'molecule_type' in row and row['molecule_type'] == 'plasmid':
                    is_plasmid = True

                if is_plasmid:
                    # Try to find the contig identifier
                    if 'sample_id' in row:
                        plasmid_contigs.add(row['sample_id'])
                    elif 'contig_id' in row:
                        plasmid_contigs.add(row['contig_id'])

    except Exception as e:
        print(f"Warning: Could not parse MOB-suite report: {e}")
    return plasmid_contigs

def extract_flanks(records, amr_hits, flank_bp=5000, output_dir="."):
    """Extracts flanking regions around AMR genes."""
    extracted_count = 0
    # Create map for fast access
    record_map = {rec.id: rec for rec in records}

    for i, hit in enumerate(amr_hits):
        contig_id = hit['contig_id']
        if contig_id not in record_map:
            continue

        rec = record_map[contig_id]

        # Define range (BioPython 0-based)
        # hit['start'] is 1-based start, hit['end'] is 1-based inclusive end
        # 0-based index: start-1
        gene_start = hit['start'] - 1
        gene_end = hit['end']

        start_pos = max(0, gene_start - flank_bp)
        end_pos = min(len(rec), gene_end + flank_bp)

        sub_rec = rec[start_pos:end_pos]
        # Make ID unique and safe
        safe_gene = hit['gene'].replace("'", "").replace(" ", "_")
        sub_rec.id = f"{safe_gene}_{i}"
        sub_rec.description = f"Flank {flank_bp}bp around {hit['gene']} on {contig_id}"

        # Clean annotations to ensure valid GBK (simple approach: let BioPython handle it,
        # but sometimes partial features cause issues. BioPython usually truncates them).

        out_name = os.path.join(output_dir, f"amr_flank_{safe_gene}_{i}.gbk")
        SeqIO.write(sub_rec, out_name, "genbank")
        extracted_count += 1

    return extracted_count

def extract_plasmids(records, plasmid_contig_ids, output_dir="."):
    """Extracts whole plasmid records."""
    count = 0
    for rec in records:
        # Check if ID matches known plasmids
        # MOB-suite might truncate IDs. We check exact match or if ID starts with it.
        # But exact match is safer.
        if rec.id in plasmid_contig_ids:
             out_name = os.path.join(output_dir, f"plasmid_{rec.id}.gbk")
             SeqIO.write(rec, out_name, "genbank")
             count += 1
    return count

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gbk", required=True, help="PGAP annotated GenBank file")
    parser.add_argument("--amr_tsv", required=True, help="AMRFinderPlus TSV output")
    parser.add_argument("--mob_report", required=True, help="MOB-suite contig report")
    parser.add_argument("--flank_size", type=int, default=5000, help="Flanking region size in bp")
    args = parser.parse_args()

    # Read GBK once
    if not os.path.exists(args.gbk):
        print("Error: GBK file not found")
        return

    records = list(SeqIO.parse(args.gbk, "genbank"))

    # 1. Extract AMR Flanks
    amr_hits = parse_amr_finder(args.amr_tsv)
    extract_flanks(records, amr_hits, args.flank_size)

    # 2. Extract Plasmids
    plasmid_ids = parse_mob_suite(args.mob_report)
    extract_plasmids(records, plasmid_ids)

if __name__ == "__main__":
    main()
