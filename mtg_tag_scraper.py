#!/usr/bin/env python3
"""
MTG Card Database Builder with Functional Tags

Scrapes the Scryfall API to build a comprehensive database of Magic: The Gathering
cards annotated with their functional tags. Supports checkpoint/resume for the
long-running scrape process.
"""

import argparse
import csv
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set


import requests


class MTGDatabaseBuilder:
    """Builds a CSV database of MTG cards tagged with Scryfall functional tags."""

    BASE_URL = "https://api.scryfall.com"
    REQUEST_DELAY = 0.1  # seconds between API requests
    CHECKPOINT_INTERVAL = 500  # save checkpoint every N tags

    def __init__(self, tags_file: str, output_csv: str, checkpoint_file: str):
        self.output_csv = output_csv
        self.checkpoint_file = checkpoint_file
        self.cards_db: Dict[str, Dict[str, Any]] = {}
        self.processed_tags: Set[str] = set()
        self.request_count = 0
        self.start_time: datetime | None = None

        with open(tags_file, "r", encoding="utf-8") as f:
            tags_by_letter = json.load(f)

        self.all_tags: List[str] = []
        for _letter, tags in sorted(tags_by_letter.items()):
            self.all_tags.extend(tags)

        print(f"Loaded {len(self.all_tags)} functional tags from {tags_file}")

        self._load_checkpoint()

    # ------------------------------------------------------------------
    # Checkpoint persistence
    # ------------------------------------------------------------------

    def _load_checkpoint(self):
        """Resume previous progress from checkpoint file if available."""
        path = Path(self.checkpoint_file)
        if not path.exists():
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                checkpoint = json.load(f)
            self.processed_tags = set(checkpoint.get("processed_tags", []))
            self.cards_db = checkpoint.get("cards_db", {})
            print(
                f"Loaded checkpoint: {len(self.processed_tags)} tags processed, "
                f"{len(self.cards_db)} cards in database"
            )
        except Exception as e:
            print(f"Warning: could not load checkpoint: {e}")
            print("Starting fresh...")

    def _save_checkpoint(self):
        """Persist current progress so the scrape can be resumed later."""
        Path(self.checkpoint_file).parent.mkdir(parents=True, exist_ok=True)
        checkpoint = {
            "processed_tags": list(self.processed_tags),
            "cards_db": self.cards_db,
            "last_updated": datetime.now().isoformat(),
        }
        with open(self.checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(checkpoint, f, indent=2)

    # ------------------------------------------------------------------
    # Scryfall API interaction
    # ------------------------------------------------------------------

    def _make_request(self, url: str) -> Dict:
        """Make a rate-limited GET request to the Scryfall API."""
        headers = {
            "User-Agent": "MTGDatabaseBuilder/1.0",
            "Accept": "application/json",
        }

        time.sleep(self.REQUEST_DELAY)
        self.request_count += 1

        response = requests.get(url, headers=headers)

        if response.status_code == 429:
            print("Rate limited, waiting 1 second...")
            time.sleep(1)
            return self._make_request(url)

        response.raise_for_status()
        return response.json()

    def _search_tag(self, tag: str) -> List[Dict]:
        """Return all cards matching a given oracle tag, handling pagination."""
        all_cards: List[Dict] = []
        url: str | None = f"{self.BASE_URL}/cards/search?q=otag:{tag}"

        while url:
            try:
                data = self._make_request(url)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    break
                raise

            if "data" not in data:
                break

            all_cards.extend(data["data"])
            url = data.get("next_page") if data.get("has_more") else None

        return all_cards

    # ------------------------------------------------------------------
    # Card data helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _flatten_card_data(card: Dict) -> Dict:
        """Flatten a Scryfall card object into a single-level dict for CSV export."""
        flattened = {}

        if "card_faces" in card:
            for i, face in enumerate(card["card_faces"]):
                flattened[f"face_{i}_name"] = face.get("name", "")
                flattened[f"face_{i}_mana_cost"] = face.get("mana_cost", "")
                flattened[f"face_{i}_type_line"] = face.get("type_line", "")
                flattened[f"face_{i}_oracle_text"] = face.get("oracle_text", "")

        for key, value in card.items():
            if key == "card_faces":
                continue
            if isinstance(value, (list, dict)):
                flattened[key] = json.dumps(value)
            else:
                flattened[key] = value

        return flattened

    def _add_or_update_card(self, card: Dict, tag: str):
        """Insert a new card into the database, or append the tag to an existing one."""
        card_id = card["id"]

        if card_id not in self.cards_db:
            self.cards_db[card_id] = self._flatten_card_data(card)
            self.cards_db[card_id]["tags"] = [tag]
        else:
            tags = self.cards_db[card_id].setdefault("tags", [])
            if tag not in tags:
                tags.append(tag)

    # ------------------------------------------------------------------
    # Main pipeline
    # ------------------------------------------------------------------

    def _process_tag(self, tag: str, tag_index: int, total_tags: int) -> int:
        """Fetch all cards for a single tag and merge them into the database."""
        if tag in self.processed_tags:
            return 0

        print(f"\n[{tag_index + 1}/{total_tags}] Processing tag: '{tag}'")

        try:
            cards = self._search_tag(tag)
            print(f"   Found {len(cards)} cards")

            new_cards = 0
            for card in cards:
                if card["id"] not in self.cards_db:
                    new_cards += 1
                self._add_or_update_card(card, tag)

            print(f"   New: {new_cards} | Updated: {len(cards) - new_cards}")
            print(f"   Total cards in DB: {len(self.cards_db)}")

            self.processed_tags.add(tag)

            if len(self.processed_tags) % self.CHECKPOINT_INTERVAL == 0:
                print("   Saving checkpoint...")
                self._save_checkpoint()

            return len(cards)

        except Exception as e:
            print(f"   Error processing tag '{tag}': {e}")
            return 0

    def build_database(self):
        """Run the full scrape: iterate over every tag, build the card DB, export CSV."""
        self.start_time = datetime.now()
        remaining = len(self.all_tags) - len(self.processed_tags)

        print(f"\n{'=' * 70}")
        print("Starting MTG Card Database Build")
        print(f"{'=' * 70}")
        print(f"Start time:       {self.start_time:%Y-%m-%d %H:%M:%S}")
        print(f"Tags to process:  {len(self.all_tags)}")
        print(f"Already done:     {len(self.processed_tags)}")
        print(f"Remaining:        {remaining}")
        print(f"{'=' * 70}\n")

        for i, tag in enumerate(self.all_tags):
            if tag in self.processed_tags:
                continue

            self._process_tag(tag, i, len(self.all_tags))

            progress = ((i + 1) / len(self.all_tags)) * 100
            elapsed = datetime.now() - self.start_time
            print(f"   Progress: {progress:.1f}% | Elapsed: {elapsed}")

        print("\nSaving final checkpoint...")
        self._save_checkpoint()

        self.export_to_csv()

        duration = datetime.now() - self.start_time
        print(f"\n{'=' * 70}")
        print("Database Build Complete")
        print(f"{'=' * 70}")
        print(f"Unique cards:     {len(self.cards_db)}")
        print(f"Tags processed:   {len(self.processed_tags)}")
        print(f"API requests:     {self.request_count}")
        print(f"Duration:         {duration}")
        print(f"Output file:      {self.output_csv}")
        print(f"{'=' * 70}\n")

    # ------------------------------------------------------------------
    # CSV export
    # ------------------------------------------------------------------

    PRIORITY_FIELDS = [
        "id", "name", "tags", "mana_cost", "cmc",
        "type_line", "oracle_text", "colors", "set", "rarity",
    ]

    def export_to_csv(self):
        """Write the card database to a CSV file."""
        print(f"\nExporting to CSV: {self.output_csv}")

        if not self.cards_db:
            print("Warning: no cards to export!")
            return

        all_fields: set[str] = set()
        for card_data in self.cards_db.values():
            all_fields.update(card_data.keys())

        fieldnames = sorted(all_fields)
        for field in reversed(self.PRIORITY_FIELDS):
            if field in fieldnames:
                fieldnames.remove(field)
                fieldnames.insert(0, field)

        Path(self.output_csv).parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_csv, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()

            for card_data in self.cards_db.values():
                row = dict(card_data)
                if isinstance(row.get("tags"), list):
                    row["tags"] = ",".join(row["tags"])
                writer.writerow(row)

        print(f"Exported {len(self.cards_db)} cards to {self.output_csv}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build an MTG card database annotated with Scryfall functional tags.",
    )
    parser.add_argument(
        "tags_file",
        help="path to the functional_tags.json file",
    )
    parser.add_argument(
        "-o", "--output",
        default="data/mtg_cards_database.csv",
        help="output CSV file (default: data/mtg_cards_database.csv)",
    )
    parser.add_argument(
        "-c", "--checkpoint",
        default="data/scraper_checkpoint.json",
        help="checkpoint file for resume support (default: data/scraper_checkpoint.json)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if not Path(args.tags_file).exists():
        print(f"Error: tags file '{args.tags_file}' not found!")
        sys.exit(1)

    try:
        builder = MTGDatabaseBuilder(args.tags_file, args.output, args.checkpoint)
        builder.build_database()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user!")
        print("Progress has been saved to the checkpoint file.")
        print("Run the script again to resume from where you left off.")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
