#!/usr/bin/env python3
"""Fetch the public PDF surrogate pack for private research use.

Source metadata is duplicated minimally here so the script has no YAML dependency.
The human/machine source-of-record is ../../research/source-manifest.yaml.
Review each publisher's applicable terms before retaining or redistributing files.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.request import Request, urlopen

OUT = Path(__file__).resolve().parent / "documents"

SOURCES = {
    "chatham_cfal_bidding_plans_2026.pdf":
        "https://www.chatham-ma.gov/DocumentCenter/View/9876/CFAL-Bidding-Plans-February-2026-PDF",
    "northbrook_bid_manual_2020.pdf":
        "https://www.northbrook.info/sites/default/files/bids/01%20NPL%20Construction%20Manual%2009.18.2020%20FINAL.pdf",
    "bloomfield_dd_estimate_2022.pdf":
        "https://bloomfieldct.gov/DocumentCenter/View/995/Design-Development-Phase-Estimate-PDF",
    "masterpiece_sommet_blanc_budget_proposal_2023.pdf":
        "https://aspengroup.online/public/companyData/8/projects/1/images/1SkUb2W811tmEWK36uUCkPtBqjPXQKs5Q.pdf",
    "foundation_sample_job_costing_2024.pdf":
        "https://www.foundationsoft.com/wp-content/uploads/2024/04/2024-04_FOUNDATION-SampleJobCostingReportBook_.pdf",
    "bluebeam_takeoffs_estimation_course.pdf":
        "https://downloads.bluebeam.com/pdfs/TakeoffsandEstimation-CourseCurriculum-mech.pdf",
    "awi_practical_guide.pdf":
        "https://awiqcp.org/wp-content/uploads/2020/06/a-practical-guide-to-the-architectural-woodwork-standards.pdf",
}


def fetch(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "Adaptive-AI-Lab-research/0.1"})
    with urlopen(req, timeout=90) as response:
        return response.read()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    hashes: list[str] = []

    for filename, url in SOURCES.items():
        destination = OUT / filename
        print(f"fetch {filename}\n  {url}")
        data = fetch(url)
        destination.write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        hashes.append(f"{digest}  {filename}")
        print(f"  {len(data):,} bytes  sha256={digest}")

    (OUT / "SHA256SUMS").write_text("\n".join(hashes) + "\n", encoding="utf-8")
    print(f"wrote {OUT / 'SHA256SUMS'}")


if __name__ == "__main__":
    main()
