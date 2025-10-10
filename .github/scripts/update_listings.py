#!/usr/bin/env python3
"""
Script: update_listings.py
Scrapes internships with fixed skills/limits, deduplicates,
filters only tech internships, and merges into listing.json.
"""

import json
import subprocess
import sys
from pathlib import Path

LISTING_FILE = Path(".github/scripts/listings.json")
SCRAPER_SCRIPT = ".github/scripts/scrapper.py"  # actual file in the repo is 'scrapper.py'
DEDUPER_SCRIPT = ".github/scripts/remove_duplicates.py"


def load_json(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return []


def save_json(path, data):
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def normalize(s: str) -> str:
    return " ".join(str(s or "").strip().split()).lower()


# 🔑 Define tech-related keywords
TECH_KEYWORDS = [
    "software", "developer", "engineer", "engineering", "computer",
    "data", "machine learning", "artificial intelligence", "ai",
    "cyber", "security", "cloud", "full stack", "backend", "frontend",
    "mobile", "ios", "android", "web", "systems", "devops", "sre",
    "qa", "blockchain"
]


def is_tech_job(title: str, company: str = "") -> bool:
    t = normalize(title)
    for kw in TECH_KEYWORDS:
        if kw in t:
            return True
    return False


def main():
    # 1. Run scraper with fixed inputs
    print("Running scraper...")
    subprocess.run(
        [sys.executable, SCRAPER_SCRIPT],
        input=b"internship, intern, coop, co-op\n40\n",  # send input automatically
        check=True
    )

    # 2. Run deduper
    print("Running deduper...")
    subprocess.run(
        [sys.executable, DEDUPER_SCRIPT, "--input", "jobs.json", "--output", "jobs.dedup.json"],
        check=True
    )

    # 3. Load new + existing jobs
    new_jobs = load_json(Path("jobs.dedup.json"))
    existing_jobs = load_json(LISTING_FILE)

    seen = {(normalize(j.get("title")), normalize(j.get("company_name"))) for j in existing_jobs}
    merged = existing_jobs[:]

    added = 0
    skipped_nontech = 0
    for job in new_jobs:
        title = job.get("title") or job.get("job_name")
        company = job.get("company_name")

        # Skip if not a tech internship
        if not is_tech_job(title, company):
            skipped_nontech += 1
            continue

        key = (normalize(title), normalize(company))
        if key not in seen:
            merged.append(job)
            seen.add(key)
            added += 1

    save_json(LISTING_FILE, merged)
    print(f"✅ Merged {added} new tech jobs. Skipped {skipped_nontech} non-tech jobs. Total now = {len(merged)}")


if __name__ == "__main__":
    main()
