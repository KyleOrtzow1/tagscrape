#!/usr/bin/env python3
"""
Pipeline Orchestrator

Runs the full tagscrape pipeline end-to-end:
  1. Scrape functional tags from Scryfall docs
  2. Build card database using those tags
  3. Analyze tag frequency distribution
  4. Sample cards for ML training
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

STEPS = [
    {
        "name": "Scrape functional tags",
        "cmd": lambda a: [sys.executable, "scrape_functional_tags.py", "-o", a.tags_file],
    },
    {
        "name": "Build card database",
        "cmd": lambda a: [sys.executable, "mtg_tag_scraper.py", a.tags_file, "-o", a.database],
    },
    {
        "name": "Analyze tag frequency",
        "cmd": lambda a: [sys.executable, "tag_frequency_analysis.py", a.database],
    },
    {
        "name": "Sample cards for ML",
        "cmd": lambda a: [
            sys.executable, "sample_cards_for_ml.py", a.database,
            "-o", a.sample_output, "-n", str(a.sample_size),
        ],
    },
]


def run_step(name: str, cmd: list[str], step_num: int, total: int) -> bool:
    """Run a single pipeline step, returning True on success."""
    print(f"\n{'=' * 60}")
    print(f"[{step_num}/{total}] {name}")
    print(f"{'=' * 60}\n")

    start = time.time()
    result = subprocess.run(cmd)
    elapsed = time.time() - start

    if result.returncode != 0:
        print(f"\nStep failed with exit code {result.returncode} ({elapsed:.1f}s)")
        return False

    print(f"\nStep completed ({elapsed:.1f}s)")
    return True


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the full tagscrape pipeline end-to-end.",
    )
    parser.add_argument(
        "--tags-file",
        default="data/functional_tags.json",
        help="path for the scraped tags JSON (default: data/functional_tags.json)",
    )
    parser.add_argument(
        "--database",
        default="data/mtg_cards_database.csv",
        help="path for the card database CSV (default: data/mtg_cards_database.csv)",
    )
    parser.add_argument(
        "--sample-output",
        default="data/mtg_ml_sample.csv",
        help="path for the ML sample CSV (default: data/mtg_ml_sample.csv)",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=5000,
        help="number of cards to sample for ML (default: 5000)",
    )
    parser.add_argument(
        "--start-from",
        type=int,
        default=1,
        choices=range(1, len(STEPS) + 1),
        help="step number to start from (default: 1)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print("tagscrape pipeline")
    print(f"Running steps {args.start_from}-{len(STEPS)}\n")

    start = time.time()

    for i, step in enumerate(STEPS, 1):
        if i < args.start_from:
            continue

        cmd = step["cmd"](args)
        if not run_step(step["name"], cmd, i, len(STEPS)):
            print(f"\nPipeline aborted at step {i}.")
            sys.exit(1)

    elapsed = time.time() - start
    print(f"\n{'=' * 60}")
    print(f"Pipeline complete ({elapsed:.1f}s)")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
