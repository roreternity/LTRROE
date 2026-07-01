"""Centralized path configuration for the LTRROE package.

All generated artifacts live under ``outputs/`` at the repository root:
- ``outputs/files``   — generated CSV datasets and trained model pickles
- ``outputs/figures`` — generated figures (PNG)

Raw input data (if any) lives under ``data/``.
Importing this module ensures the output directories exist.
"""

from pathlib import Path

# ltrroe/paths.py -> parents[1] is the repository root
ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT / "data"
OUTPUTS = ROOT / "outputs"
FILES_DIR = OUTPUTS / "files"
FIG_DIR = OUTPUTS / "figures"

for _d in (DATA_DIR, FILES_DIR, FIG_DIR):
    _d.mkdir(parents=True, exist_ok=True)


def figures(subdir: str) -> Path:
    """Return (and create) a figures subdirectory, e.g. figures('rf_synth_project')."""
    path = FIG_DIR / subdir
    path.mkdir(parents=True, exist_ok=True)
    return path
