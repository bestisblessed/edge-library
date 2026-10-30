"""Load numeric-prefixed trend scripts by path.

The trend filenames start with digits, so they are not importable as modules.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib

matplotlib.use("Agg")

ROOT = Path(__file__).resolve().parents[1]
_CACHE: dict[str, object] = {}


def load_script(name: str):
    """Load ``scripts/<name>.py`` and cache the module."""
    if name in _CACHE:
        return _CACHE[name]
    path = ROOT / "scripts" / f"{name}.py"
    module_name = f"edge_scripts.{name}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    _CACHE[name] = module
    return module
