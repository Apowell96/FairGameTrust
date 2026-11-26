"""Shared paths and cached study data for the integration tests."""

from functools import lru_cache
import os
from pathlib import Path
import sys

PACKAGE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PACKAGE))
DATA_ROOT = Path(os.environ.get("FAIRGAME_RESULTS_DATA_ROOT", PACKAGE.parent)).resolve()

from pd_figures.data import load_dataset
from pd_figures.settings import DATASETS
from pd_figures.statistics import build_plot_data


@lru_cache(maxsize=4)
def study_data(key):
    loaded = load_dataset(DATA_ROOT, DATASETS[key])
    return loaded, build_plot_data(loaded.rounds)
