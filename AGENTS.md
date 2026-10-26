# edge-library agent notes

## Data source

`data/` is the single source every current and future trend script reads from.
Do not point new scripts at Twin's nfl-ai tree or at any other copy.

Refresh it from the repo root (Twin's Mac, about weekly):

```bash
cd ~/Code/edge-library && ./update_data.sh
```

`update_data.sh` is the same three commands as the old notebook cell:
`rm -rf data`, `mkdir data`, `cp -r ~/Code/nfl-ai/Scrapers/data/* data/`.

## Layout

- `Main.ipynb` — trend notebook
- `scripts/` — trend scripts; they read CSVs under `data/`
- `sbbreakers/` — SBBreakers dictionary notes (not scraper data)
