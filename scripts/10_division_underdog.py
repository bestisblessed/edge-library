#!/usr/bin/env python3
"""CLI: PHI 2+ point dog vs NFC East. Reads data/games.csv."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nfl_trends.division_underdog import main

if __name__ == "__main__":
    main()
