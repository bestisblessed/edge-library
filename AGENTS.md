# edge-library agent notes

## Data source

`data/` is the single source every current and future trend script reads from.
Do not point new scripts at Twin's nfl-ai tree, at `~/Code/nfl-ai`, or at any
other copy.

Refresh it with `./update_data.sh` from the repo root (Twin's Mac, about weekly):

```bash
cd ~/Code/edge-library && ./update_data.sh
```

`NFL_AI_DIR` overrides the default `~/Code/nfl-ai`. The script fails if that
path is missing. It replaces `data/` each run so removed upstream files do not
stay behind.

Copied masters (what nfl-ai's website and models actually read):

- `Scrapers/data/` → `data/`
- `Scrapers/final_data_pfr/` → `data/final_data_pfr/`

Not copied: `bak/`, `__pycache__/`, zips, `Scrapers/final_data/` (legacy),
`Scrapers/nfl.db`, model outputs, odds archives.

## Layout

- `Main.ipynb` — trend notebook; refresh cell points at `./update_data.sh`
- `scripts/` — trend scripts; they read CSVs under `data/`
- `sbbreakers/` — SBBreakers dictionary notes (not scraper data)
