# tagscrape

Data retrieval pipeline that builds an MTG card database annotated with Scryfall's functional tags, then prepares the data for machine learning.

## Pipeline

```
scrape_functional_tags.py          Scrape tag taxonomy from Scryfall docs
        |
        v
  data/functional_tags.json
        |
        v
mtg_tag_scraper.py                 Query Scryfall API for every tag, build card DB
        |
        v
  data/mtg_cards_database.csv
        |
        +---> tag_frequency_analysis.py    Analyze tag distribution
        |
        +---> sample_cards_for_ml.py       Sample & export ML-ready dataset
```

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

Run the full pipeline end-to-end:

```bash
python run_pipeline.py
```

Or run individual steps:

```bash
python scrape_functional_tags.py                                 # 1. Scrape tag taxonomy
python mtg_tag_scraper.py data/functional_tags.json              # 2. Build card database
python tag_frequency_analysis.py data/mtg_cards_database.csv     # 3. Analyze tag distribution
python sample_cards_for_ml.py data/mtg_cards_database.csv        # 4. Sample for ML
```

All scripts support `--help` for full option details.

## Output

| File | Description |
|------|-------------|
| `data/functional_tags.json` | Tag taxonomy organized alphabetically |
| `data/mtg_cards_database.csv` | Full card database with functional tags |
| `data/mtg_ml_sample.csv` | Sampled subset with ML-relevant fields only |
| `data/*_tag_frequency.txt` | Tag distribution report |

## Requirements

- Python 3.12+
- requests, beautifulsoup4, lxml (see `requirements.txt`)
