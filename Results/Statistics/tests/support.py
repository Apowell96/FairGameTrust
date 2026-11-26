"""Shared integration fixtures; raw games are read directly from Results/."""

from functools import lru_cache
import os
from pathlib import Path
import sys

import pandas as pd

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE))
DATA_ROOT = Path(os.environ.get("FAIRGAME_RESULTS_DATA_ROOT", PACKAGE.parent))

from pd_statistics.analyses import game_values, run_analyses
from pd_statistics.data import load_dataset
from pd_statistics.settings import DATASETS


@lru_cache(maxsize=1)
def study():
    loaded = {key: load_dataset(DATA_ROOT, dataset) for key, dataset in DATASETS.items()}
    rounds = pd.concat([item.rounds for item in loaded.values()], ignore_index=True)
    games = game_values(rounds)
    return loaded, rounds, games, run_analyses(games)
