"""Parameterized NFL trend audits. All reads go through data/ at the repo root."""

from nfl_trends.after_under import analyze as analyze_after_under
from nfl_trends.division_underdog import analyze as analyze_division_underdog
from nfl_trends.home_underdog import analyze as analyze_home_underdog
from nfl_trends.rested_after_scoring import analyze as analyze_rested_after_scoring

__all__ = [
    "analyze_after_under",
    "analyze_division_underdog",
    "analyze_home_underdog",
    "analyze_rested_after_scoring",
]
