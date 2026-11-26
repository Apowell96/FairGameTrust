#!/usr/bin/env python3
"""Generate the publication PDFs from the game files in Results/."""

import os
from pathlib import Path
import tempfile

# A writable cache also supports headless execution and synced macOS folders.
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir())/"fairgame-figure-font-cache"))

import matplotlib
matplotlib.use("Agg")

from pd_figures.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
