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

One `.py` file per trend, directly in `scripts/`. No subfolders in `scripts/` and no helper modules. No committed figures, charts, CSVs, or other generated output. The notebook regenerates them on every run.

- `Main.ipynb` — NFL Edge Dictionary notebook
- `scripts/` — one `.py` file per trend, directly in this folder
- `images/` — notebook images
- `trends/` — gone; do not commit generated figures, charts, or CSVs
- `nfl_trends/` — gone; analyzers live in `scripts/`, not a separate package
- `data/` — committed snapshot of nfl-ai scraper masters
- `sbbreakers/` — SBBreakers trend dictionary notes
- `update_data.sh` — local refresh from `~/Code/nfl-ai`

## Run a trend

From a fresh checkout, run `pip install -r requirements.txt` before opening the notebook.

Open `Main.ipynb` in Jupyter from the repository root and run the first setup
cell. Run the Detroit trend cell, select seasons (use Command/Ctrl for multiple
selections), and click **Run trend**. Run a source-view cell and expand its
output to see the current script.

The Detroit trend displays a summary, expandable game details, and charts; it
can also be run from the terminal with `python scripts/opponent_stats_after_DET.py`.
Every notebook section runs a real script from `scripts/`.
Edit a trend's script rather than copying its code into the notebook.

A new trend is one real `.py` file directly in `scripts/` plus its own notebook section:
a header, a `%run scripts/<script>.py --notebook` cell, and a source-view cell.
Do not add a second file, a subfolder, a helper module, or a placeholder for that trend.
Do not commit the tables or charts the notebook draws.

Current trend scripts, re-run on the committed `data/` snapshot:

- `scripts/08_rested_after_scoring.py` — DET 14-0-0 OVER (n=14, live 1)
- `scripts/09_home_underdog.py` — PHI 0-9 SU / 2-7 ATS (n=9, live 1)
- `scripts/10_division_underdog.py` — PHI 1-10 SU / 2-9 ATS (n=11, live 2)
- `scripts/11_after_under.py` — DAL 6-1 SU / 6-1 ATS (n=7, live 1)
