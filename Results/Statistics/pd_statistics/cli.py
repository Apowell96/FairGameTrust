"""Load Results/ games, run the 18 specified families and export tables."""

import argparse
import json
from pathlib import Path
import platform

import numpy as np
import pandas as pd
import scipy

from . import __version__
from .analyses import TABLES, game_values, run_analyses
from .data import load_dataset
from .io import atomic_write, sha256
from .reporting import overview, table_report
from .settings import DATASETS

PACKAGE_ROOT = Path(__file__).resolve().parent.parent


def generate(data_root, output_root, validate_only=False):
    data_root, output_root = Path(data_root).resolve(), Path(output_root).resolve()
    hashes, frames = {}, []
    for key, dataset in DATASETS.items():
        raw_path = dataset.input_path(data_root).resolve()
        if output_root == raw_path or output_root.is_relative_to(raw_path):
            raise ValueError("The output directory must be separate from raw game data")
        loaded = load_dataset(data_root, dataset)
        hashes.update(loaded.input_hashes)
        frames.append(game_values(loaded.rounds))
        print(f"Validated {dataset.label}: 120 independent games", flush=True)
    if len(hashes) != 480:
        raise ValueError("Expected 480 input game files")
    if validate_only:
        return dict(validated_games=480)
    games = pd.concat(frames, ignore_index=True)
    results = run_analyses(games)
    atomic_write(output_root/"game_values.csv", games.to_csv(index=False, float_format="%.17g"))
    atomic_write(output_root/"all_tests.csv", results.to_csv(index=False, float_format="%.17g"))
    for table in TABLES:
        frame = results.loc[results.table_id.eq(table)].dropna(axis=1, how="all")
        atomic_write(output_root/"tables"/f"{table}.csv", frame.to_csv(index=False, float_format="%.17g"))
        atomic_write(output_root/"tables"/f"{table}.md", table_report(table, frame))
    atomic_write(output_root/"REPORT.md", overview(results))
    for name, checksum in hashes.items():
        if sha256(data_root/name) != checksum:
            raise ValueError(f"Raw data changed during analysis: {name}")
    code = [PACKAGE_ROOT/"run_statistics.py", PACKAGE_ROOT/"requirements.txt",
            *sorted((PACKAGE_ROOT/"pd_statistics").glob("*.py"))]
    manifest = dict(version=__version__, input_sha256=hashes,
        code_sha256={p.relative_to(PACKAGE_ROOT).as_posix(): sha256(p) for p in code},
        datasets={key: dataset.label for key, dataset in DATASETS.items()}, independent_games=480,
        table_rows={table: int(results.table_id.eq(table).sum()) for table in TABLES},
        sampling_unit="independent game, both agents combined", monitoring_costs=[0, .25, .5, 1],
        cooperation="OptionB / 选项B", overall_rounds=list(range(1, 11)),
        early_rounds=[2, 3, 4, 5], late_rounds=[6, 7, 8, 9, 10],
        methods=dict(mann_whitney="two-sided asymptotic, ties corrected, continuity correction 0.5",
            early_late="one-sided paired t-test: mean(late−early) < 0",
            confidence_intervals="pointwise two-sided 95% Student t for mean paired difference, df=9",
            holm="18 per cost table; 12 per other table; undefined tests retain planned slots",
            significance="Holm-adjusted p < 0.05"),
        software=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__, scipy=scipy.__version__))
    atomic_write(output_root/"manifest.json", json.dumps(manifest, indent=2)+"\n")
    print(f"Saved 264 comparisons in 18 tables to {output_root}", flush=True)
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description="Calculate the statistics for supplementary Tables S1–S18")
    parser.add_argument("--data-root", type=Path, default=PACKAGE_ROOT.parent)
    parser.add_argument("--output-root", type=Path, default=PACKAGE_ROOT/"output")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        generate(args.data_root, args.output_root, args.validate_only)
    except (ValueError, FileNotFoundError) as error:
        parser.error(str(error))
    return 0
