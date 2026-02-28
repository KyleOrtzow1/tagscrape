#!/usr/bin/env python3
"""
MTG Tag Frequency Analyzer

Analyzes the distribution of functional tags across the card database and
writes a detailed frequency report.
"""

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path


def analyze_tag_frequency(csv_file: str, top_n: int = 100):
    """
    Count tag occurrences across all cards and print/save a frequency report.

    Args:
        csv_file: Path to the card database CSV.
        top_n:    Number of top tags to display in the console report.
    """
    print(f"Analyzing tag frequencies from: {csv_file}\n")

    tag_counter: Counter[str] = Counter()
    total_cards = 0
    cards_with_tags = 0

    with open(csv_file, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            total_cards += 1
            tags_str = row.get("tags", "")
            if tags_str:
                cards_with_tags += 1
                tags = [t.strip() for t in tags_str.split(",") if t.strip()]
                tag_counter.update(tags)

    total_occurrences = sum(tag_counter.values())
    unique_tags = len(tag_counter)
    avg_tags = total_occurrences / cards_with_tags if cards_with_tags else 0

    # ---- Console report ----
    print("=" * 80)
    print(f"{'TAG FREQUENCY ANALYSIS':^80}")
    print("=" * 80)
    print(f"\nOverall statistics:")
    print(f"  Total cards:         {total_cards:,}")
    print(f"  Cards with tags:     {cards_with_tags:,}")
    print(f"  Cards without tags:  {total_cards - cards_with_tags:,}")
    print(f"  Tag occurrences:     {total_occurrences:,}")
    print(f"  Unique tags:         {unique_tags:,}")
    print(f"  Avg tags per card:   {avg_tags:.2f}")

    print(f"\n{'=' * 80}")
    print(f"{'TOP ' + str(top_n) + ' MOST COMMON TAGS':^80}")
    print("=" * 80)
    print(f"\n{'Rank':<6} {'Tag':<40} {'Count':<10} {'% of Cards':<12} {'Bar'}")
    print("-" * 80)

    for rank, (tag, count) in enumerate(tag_counter.most_common(top_n), 1):
        pct = (count / cards_with_tags) * 100
        bar = "\u2588" * int(pct / 2)
        print(f"{rank:<6} {tag:<40} {count:<10,} {pct:>6.2f}%      {bar}")

    # ---- Distribution insights ----
    common_threshold = cards_with_tags * 0.10
    rare_threshold = cards_with_tags * 0.01
    sorted_counts = sorted(tag_counter.values(), reverse=True)
    median_count = sorted_counts[len(sorted_counts) // 2] if sorted_counts else 0
    singletons = sum(1 for c in tag_counter.values() if c == 1)

    print(f"\n{'=' * 80}")
    print("Distribution insights:")
    print("=" * 80)
    print(f"  Tags on >10% of cards:       {sum(1 for _, c in tag_counter.items() if c > common_threshold)}")
    print(f"  Tags on <1% of cards:        {sum(1 for _, c in tag_counter.items() if c < rare_threshold)}")
    print(f"  Median tag frequency:        {median_count}")
    print(f"  Tags on only 1 card:         {singletons}")
    print("=" * 80)

    # ---- Save full report ----
    output_file = Path(csv_file).with_name(Path(csv_file).stem + "_tag_frequency.txt")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("MTG TAG FREQUENCY ANALYSIS\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total cards: {total_cards:,}\n")
        f.write(f"Cards with tags: {cards_with_tags:,}\n")
        f.write(f"Unique tags: {unique_tags:,}\n")
        f.write(f"Average tags per card: {avg_tags:.2f}\n\n")
        f.write("Rank\tTag\tCount\t% of Cards\n")
        for rank, (tag, count) in enumerate(tag_counter.most_common(), 1):
            pct = (count / cards_with_tags) * 100
            f.write(f"{rank}\t{tag}\t{count}\t{pct:.2f}%\n")

    print(f"\nFull frequency list saved to: {output_file}\n")

    return tag_counter


def parse_args():
    parser = argparse.ArgumentParser(
        description="Analyze functional tag frequency in the MTG card database.",
    )
    parser.add_argument(
        "csv_file",
        help="path to the card database CSV",
    )
    parser.add_argument(
        "-n", "--top-n",
        type=int,
        default=100,
        help="number of top tags to display (default: 100)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if not Path(args.csv_file).exists():
        print(f"Error: file '{args.csv_file}' not found!")
        sys.exit(1)

    try:
        analyze_tag_frequency(args.csv_file, args.top_n)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
