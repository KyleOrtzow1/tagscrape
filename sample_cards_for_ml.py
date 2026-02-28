#!/usr/bin/env python3
"""
MTG Card Sampler for ML

Randomly samples N cards from the full database and exports only the
ML-relevant fields, producing a smaller CSV ready for model training.
"""

import argparse
import csv
import random
import sys
from pathlib import Path

ML_FIELDS = [
    "id",
    "name",
    "mana_cost",
    "cmc",
    "type_line",
    "oracle_text",
    "colors",
    "color_identity",
    "keywords",
    "power",
    "toughness",
    "loyalty",
    "tags",
]


def sample_cards(input_csv: str, output_csv: str, sample_size: int, seed: int | None):
    """
    Randomly sample cards from the database and export ML-relevant fields.

    Args:
        input_csv:    Path to the full card database CSV.
        output_csv:   Path to write the sampled CSV.
        sample_size:  Number of cards to sample.
        seed:         Random seed for reproducibility (None for non-deterministic).
    """
    if seed is not None:
        random.seed(seed)
        print(f"Using random seed: {seed}")

    print(f"Reading cards from: {input_csv}\n")

    all_cards: list[dict] = []
    tagged_count = 0

    with open(input_csv, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ml_row = {field: row.get(field, "") for field in ML_FIELDS}
            all_cards.append(ml_row)
            if ml_row.get("tags", "").strip():
                tagged_count += 1

    total = len(all_cards)
    print("Database statistics:")
    print(f"  Total cards:      {total:,}")
    print(f"  Cards with tags:  {tagged_count:,}")
    print(f"  Cards without:    {total - tagged_count:,}")
    print(f"  Tag coverage:     {tagged_count / total * 100:.2f}%\n")

    if sample_size > total:
        print(f"Warning: requested {sample_size:,} but only {total:,} cards available.")
        sample_size = total

    print(f"Sampling {sample_size:,} cards...")
    sampled = random.sample(all_cards, sample_size)

    sampled_tagged = sum(1 for c in sampled if c.get("tags", "").strip())
    print(f"\nSample statistics:")
    print(f"  Size:           {sample_size:,}")
    print(f"  With tags:      {sampled_tagged:,} ({sampled_tagged / sample_size * 100:.2f}%)")
    print(f"  Without tags:   {sample_size - sampled_tagged:,}")

    print(f"\nWriting to: {output_csv}")
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ML_FIELDS)
        writer.writeheader()
        writer.writerows(sampled)

    print(f"Wrote {sample_size:,} cards to {output_csv}")

    # Quick preview
    print(f"\nPreview (first 3 cards):")
    print("-" * 80)
    for i, card in enumerate(sampled[:3], 1):
        tags = card["tags"]
        print(f"  {i}. {card['name']}  |  {card['type_line']}  |  CMC {card['cmc']}")
        print(f"     Tags: {tags[:80]}{'...' if len(tags) > 80 else ''}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Sample cards from the MTG database for ML training.",
    )
    parser.add_argument(
        "input_csv",
        help="path to the full card database CSV",
    )
    parser.add_argument(
        "-o", "--output",
        default="mtg_ml_sample.csv",
        help="output CSV file (default: mtg_ml_sample.csv)",
    )
    parser.add_argument(
        "-n", "--sample-size",
        type=int,
        default=5000,
        help="number of cards to sample (default: 5000)",
    )
    parser.add_argument(
        "-s", "--seed",
        type=int,
        default=None,
        help="random seed for reproducibility",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if not Path(args.input_csv).exists():
        print(f"Error: input file '{args.input_csv}' not found!")
        sys.exit(1)

    try:
        sample_cards(args.input_csv, args.output, args.sample_size, args.seed)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
