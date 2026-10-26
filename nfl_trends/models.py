from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class EdgeResult:
    id: str
    summary: pd.DataFrame
    audit: pd.DataFrame
    secondary: dict[str, pd.DataFrame] = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
