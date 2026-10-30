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

- `Main.ipynb` — master trend notebook; run the setup cell first
- `scripts/` — source of truth for trend code; scripts read CSVs under `data/`
- `images/` — images used by the notebook
- `sbbreakers/` — SBBreakers dictionary notes (not scraper data)
- `trends/` — gone; do not commit generated figures, charts, or CSVs
- `nfl_trends/` — gone; trend code lives in `scripts/`, not a separate package

One `.py` file per trend, directly in `scripts/`. No subfolders in `scripts/` and no helper modules. No committed figures, charts, CSVs, or other generated output. The notebook regenerates them on every run.

## Adding trends to the notebook

Follow the current `Main.ipynb` sections as the format for new trends:

- Give each trend a concise, descriptive title in title case. Add a numbered
  entry with the same title and an anchor link to the “Explore the library”
  table of contents; use a short, stable anchor name.
- Put the anchor and a `##` title in the trend's Markdown title cell. Put the
  research question in a short subheading, followed by any original tweet URL
  the user supplies as a visible link in the same cell. Also put that URL in an
  `Original tweet` HTML comment before the anchor. Do not invent a source link
  when none is supplied.
- Put concise calculation rules and instructions for the season picker in
  italic text beneath the question and source. Keep the title cell focused;
  do not add a separate “Run or load the script” explanatory section.
- Keep the analysis in a descriptively named script under `scripts/`. In the
  notebook, follow the title cell with the interactive analysis, a `%run`
  example, a `%load` example, and the expandable view of the current script,
  matching the existing sections. The script is the source of truth; loaded
  code is only a copy.

One `.py` file per trend section, directly in `scripts/`. No subfolders in `scripts/` and no helper modules. Do not commit the figures, charts, or CSVs the notebook regenerates.

Current scripts: `opponent_stats_after_DET.py`; `broncos_after_big_loss.py`; `08_rested_after_scoring.py` DET 14-0-0 OVER (n=14, live 1); `09_home_underdog.py` PHI 0-9 SU / 2-7 ATS (n=9, live 1); `10_division_underdog.py` PHI 1-10 SU / 2-9 ATS (n=11, live 2); `11_after_under.py` DAL 6-1 SU / 6-1 ATS (n=7, live 1).
