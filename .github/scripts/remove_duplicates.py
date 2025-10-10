#!/usr/bin/env python3
"""
Script: remove_duplicates.py
Reads listing.json (or jobs.json) and removes duplicate job objects using
(job title, company_name) as the dedupe key.

Usage:
    python remove_duplicates.py [--input listing.json] [--output listing.dedup.json] [--inplace]

If --inplace is passed the input file will be overwritten after deduplication.

This script treats title and company_name case-insensitively and ignores
extra whitespace when comparing.
"""

import json
import argparse
import sys
from pathlib import Path


def normalize(s: str) -> str:
    if s is None:
        return ""
    # collapse whitespace and lowercase
    return " ".join(str(s).strip().split()).lower()


def dedupe_jobs(jobs):
    seen = set()
    out = []
    removed = 0

    for job in jobs:
        title = normalize(job.get('title') or job.get('job_name'))
        company = normalize(job.get('company_name') or job.get('company'))
        key = (title, company)
        if key in seen:
            removed += 1
            continue
        seen.add(key)
        out.append(job)

    return out, removed


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', '-i', default='jobs.json', help='Input JSON file (default: jobs.json)')
    p.add_argument('--output', '-o', default='listing.dedup.json', help='Output JSON file')
    p.add_argument('--inplace', action='store_true', help='Overwrite the input file')

    args = p.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        alt = Path('jobs.json')
        if alt.exists():
            print(f"Input {in_path} not found, using {alt}")
            in_path = alt
        else:
            print(f"Error: input file {in_path} not found and jobs.json also missing.")
            sys.exit(1)

    with in_path.open('r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except Exception as e:
            print('Failed to parse JSON:', e)
            sys.exit(1)

    if not isinstance(data, list):
        print('Expected JSON array at top-level')
        sys.exit(1)

    out, removed = dedupe_jobs(data)
    kept = len(out)

    out_path = in_path if args.inplace else Path(args.output)
    with out_path.open('w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f'Results: kept={kept}, removed={removed}, written={out_path}')


if __name__ == '__main__':
    main()
