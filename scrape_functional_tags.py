#!/usr/bin/env python3
"""
Scryfall Functional Tags Scraper

Scrapes functional tags from https://scryfall.com/docs/tagger-tags
and saves them to a JSON file. Functional tags are identified by headers
containing "(functional)" in the text.
"""

import argparse
import json
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup


def scrape_functional_tags():
    """
    Scrape functional tags from the Scryfall tagger tags page.

    Returns:
        dict: Tag categories mapped to their respective tag lists.
    """
    url = "https://scryfall.com/docs/tagger-tags"

    print("Fetching page content...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching page: {e}")
        return {}

    print("Parsing HTML content...")
    soup = BeautifulSoup(response.content, "html.parser")

    functional_tags = {}

    functional_headers = soup.find_all(
        "h2", string=re.compile(r".*\(functional\).*", re.IGNORECASE)
    )
    print(f"Found {len(functional_headers)} functional tag sections")

    for header in functional_headers:
        category = header.get_text().replace("(functional)", "").strip()
        print(f"Processing category: {category}")

        # Walk siblings until the next h2, looking for the paragraph with tag links
        tags_paragraph = None
        current = header.find_next_sibling()

        while current and current.name != "h2":
            if current.name == "p":
                links = current.find_all("a", href=re.compile(r"oracletag%3A"))
                if links:
                    tags_paragraph = current
                    break
            current = current.find_next_sibling()

        if not tags_paragraph:
            print(f"  No tags paragraph found for category '{category}'")
            continue

        tag_links = tags_paragraph.find_all("a", href=re.compile(r"oracletag%3A"))
        tags = []

        for link in tag_links:
            href = link.get("href", "")
            parsed_url = urlparse(href)
            query_params = parse_qs(parsed_url.query)

            if "q" not in query_params:
                continue

            query = query_params["q"][0]
            if "oracletag%3A" in query:
                tag_name = requests.utils.unquote(query.split("oracletag%3A")[1])
                tags.append(tag_name)
            elif "oracletag:" in query:
                tags.append(query.split("oracletag:")[1])

        if tags:
            functional_tags[category] = sorted(tags)
            print(f"  Found {len(tags)} tags in category '{category}'")
        else:
            print(f"  No tags found for category '{category}'")

    return functional_tags


def save_to_json(data, filename="functional_tags.json"):
    """Save the functional tags data to a JSON file."""
    try:
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)

        total_tags = sum(len(tags) for tags in data.values())
        print(f"Successfully saved {len(data)} categories ({total_tags} tags) to {filename}")
    except Exception as e:
        print(f"Error saving to JSON: {e}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Scrape functional tags from Scryfall's tagger documentation."
    )
    parser.add_argument(
        "-o", "--output",
        default="data/functional_tags.json",
        help="output JSON file path (default: data/functional_tags.json)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print("Scryfall Functional Tags Scraper")
    print("=" * 40)

    functional_tags = scrape_functional_tags()

    if functional_tags:
        save_to_json(functional_tags, args.output)

        print("\nSummary:")
        print("-" * 20)
        for category, tags in sorted(functional_tags.items()):
            print(f"{category}: {len(tags)} tags")
    else:
        print("No functional tags found!")


if __name__ == "__main__":
    main()
