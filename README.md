# edge-library

Master notebook and scripts for NFL trend work. Every current and future trend
script reads from `data/`.

## Refresh `data/`

About weekly, on Twin's Mac, copy the latest nfl-ai scraper masters:

```bash
cd ~/Code/edge-library && ./update_data.sh
```

Override the nfl-ai checkout if it is not at `~/Code/nfl-ai`:

```bash
NFL_AI_DIR=/other/path/nfl-ai ./update_data.sh
```

The script replaces `data/` (so stale files cannot linger), copies
`Scrapers/data/` and `Scrapers/final_data_pfr/`, skips junk (`bak/`,
`__pycache__/`, zips), and prints the nfl-ai git SHA when available.

Then commit the refreshed snapshot in this repo if you want it saved.

## Layout

- `Main.ipynb` — NFL Edge Dictionary notebook
- `scripts/` — trend scripts (read `data/`)
- `data/` — committed snapshot of nfl-ai scraper masters
- `sbbreakers/` — SBBreakers trend dictionary notes
- `update_data.sh` — local refresh from Twin's nfl-ai checkout
