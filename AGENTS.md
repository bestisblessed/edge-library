# edge-library agent notes

## Data source

`data/` is the single source every current and future trend script reads from.
Do not point new scripts at Twin's nfl-ai tree or at any other copy.

Refresh it from the repo root (Twin's Mac, about weekly):

```bash
cd ~/Code/edge-library && ./update_data.sh
```

`update_data.sh` copies `~/Code/nfl-ai/Scrapers/data/` into `data/` and
`~/Code/nfl-ai/Scrapers/final_data_pfr/` into `data/final_data_pfr/`.

## Layout

One `.py` file per trend, directly in `scripts/`. No subfolders in `scripts/` and no helper modules. No committed figures, charts, CSVs, or other generated output. The notebook regenerates them on every run.

- `Main.ipynb` — master trend notebook; run the setup cell first
- `scripts/` — one `.py` file per trend, directly in this folder; each script reads CSVs under `data/`
- `images/` — images used by the notebook
- `trends/` — gone; do not commit generated figures, charts, or CSVs
- `nfl_trends/` — gone; trend code lives in `scripts/`, not a separate package
- `sbbreakers/` — SBBreakers dictionary notes (not scraper data)

Adding a trend means adding one real `.py` file directly in `scripts/` and a section in `Main.ipynb` that runs and browses it. Do not add a second file, a subfolder, a helper module, or a placeholder for that trend. Do not commit the tables or charts the notebook draws. Current scripts: `opponent_stats_after_DET.py`; `08_rested_after_scoring.py` DET 14-0-0 OVER (n=14, live 1); `09_home_underdog.py` PHI 0-9 SU / 2-7 ATS (n=9, live 1); `10_division_underdog.py` PHI 1-10 SU / 2-9 ATS (n=11, live 2); `11_after_under.py` DAL 6-1 SU / 6-1 ATS (n=7, live 1).
