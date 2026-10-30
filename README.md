# edge-library

The master notebook runs individual NFL trend scripts and displays their results.
Every current and future trend script reads from `data/`.

## Refresh `data/`

About weekly, on Twin's Mac:

```bash
cd ~/Code/edge-library && ./update_data.sh
```

That replaces `data/` with `~/Code/nfl-ai/Scrapers/data/` and
`~/Code/nfl-ai/Scrapers/final_data_pfr/`. Commit the snapshot when you want it
saved.

## Layout

- `Main.ipynb` — NFL Edge Dictionary notebook
- `scripts/` — trend scripts (read `data/`)
- `data/` — committed snapshot of nfl-ai scraper masters
- `sbbreakers/` — SBBreakers trend dictionary notes
- `update_data.sh` — local refresh from `~/Code/nfl-ai`

## Run a trend

Open `Main.ipynb` in Jupyter from the repository root and run a trend's cell.
The Detroit trend displays a summary, expandable game details, and charts; it
can also be run from the terminal with `python scripts/opponent_stats_after_DET.py`.
Notebook output requires IPython, Matplotlib, pandas, and ipywidgets. The bye
and home-underdog scripts are examples only, with no trend analysis yet.
Edit a trend's script rather than copying its code into the notebook.
