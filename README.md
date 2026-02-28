# tagscrape

Data retrieval pipeline that builds an MTG card database annotated with Scryfall's functional tags, then prepares the data for machine learning.

## Pipeline

```
scrape_functional_tags.py          Scrape tag taxonomy from Scryfall docs
        |
        v
  functional_tags.json
        |
        v
mtg_tag_scraper.py                 Query Scryfall API for every tag, build card DB
        |
        v
  mtg_cards_database.csv
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

Or use the provided setup scripts (`setup_and_run.bat` / `setup_and_run.ps1`).

## Usage

```bash
# 1. Scrape the functional tag taxonomy
python scrape_functional_tags.py

# 2. Build the card database (long-running, supports resume via checkpoint)
python mtg_tag_scraper.py functional_tags.json

# 3. Analyze tag distribution
python tag_frequency_analysis.py mtg_cards_database.csv

# 4. Sample cards for ML training
python sample_cards_for_ml.py mtg_cards_database.csv -n 5000 -s 42
```

All scripts support `--help` for full option details.

## Output

| File | Description |
|------|-------------|
| `functional_tags.json` | Tag taxonomy organized alphabetically |
| `mtg_cards_database.csv` | Full card database with functional tags |
| `mtg_ml_sample.csv` | Sampled subset with ML-relevant fields only |
| `*_tag_frequency.txt` | Tag distribution report |

## Requirements

- Python 3.12+
- requests, beautifulsoup4, lxml (see `requirements.txt`)
