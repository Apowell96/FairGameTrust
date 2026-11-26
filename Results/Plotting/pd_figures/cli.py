"""Command-line entry point: validate game files, export tables and draw eight PDFs."""

import argparse
import json
from pathlib import Path
import platform
import zipfile
import io

import matplotlib
import numpy as np
import pandas as pd
import scipy

from . import __version__
from .data import load_dataset
from .io import atomic_write, sha256
from .plotting import FONT_FAMILY, check_font, make_cost_figure, make_rounds_figure, save_figure
from .settings import COSTS, DATASETS, GAMES_PER_CELL, MODELS, ROUNDS
from .statistics import build_plot_data

PACKAGE_ROOT = Path(__file__).resolve().parent.parent


def parser():
    command = argparse.ArgumentParser(description="Generate the study's cooperation, LOOK and penalty PDFs.")
    command.add_argument("--data-root", type=Path, default=PACKAGE_ROOT.parent,
                         help="Results directory containing English/, French/ and Chinese/ (default: ..)")
    command.add_argument("--output-root", type=Path, default=PACKAGE_ROOT/"output")
    command.add_argument("--datasets", nargs="+", choices=list(DATASETS), default=list(DATASETS))
    command.add_argument("--font-family", default=FONT_FAMILY)
    command.add_argument("--font-directory", type=Path, help="Optional folder containing locally installed font files")
    command.add_argument("--no-png", action="store_true", help="Export PDFs without PNG previews")
    command.add_argument("--validate-only", action="store_true", help="Validate raw games without writing outputs")
    command.add_argument("--allow-input-changes", action="store_true",
                         help="Permit raw-file hashes to differ from the publication input manifest")
    return command


def generate(data_root, output_root, keys, family=FONT_FAMILY, font_directory=None,
             png=True, validate_only=False, allow_input_changes=False):
    data_root, output_root = Path(data_root).resolve(), Path(output_root).resolve()
    keys = list(dict.fromkeys(keys))
    unknown = set(keys)-set(DATASETS)
    if not keys or unknown:
        raise ValueError(f"Unsupported dataset selection: {unknown}")
    for key in keys:
        raw_path = DATASETS[key].input_path(data_root).resolve()
        if output_root == raw_path or output_root.is_relative_to(raw_path):
            raise ValueError("The output folder must be separate from raw game data")
    expected = json.loads((PACKAGE_ROOT/"input_manifest.json").read_text())["files"]
    loaded, input_hashes = {}, {}
    for key in keys:
        item = load_dataset(data_root, DATASETS[key])
        if not allow_input_changes:
            for name, checksum in item.input_hashes.items():
                if expected.get(name) != checksum:
                    raise ValueError(f"Input differs from publication manifest: {name}. "
                                     "Use --allow-input-changes only for intentionally replaced data.")
        loaded[key] = item
        input_hashes.update(item.input_hashes)
        print(f"Validated {DATASETS[key].label}: 120 independent games", flush=True)
    if validate_only:
        return dict(validated_games=120*len(keys), datasets=keys)
    fonts = check_font(family, font_directory)
    audits, figures = [], []
    for key in keys:
        dataset, item = DATASETS[key], loaded[key]
        data = build_plot_data(item.rounds)
        tables = dict(round_level=item.rounds, game_level=data.games, game_rounds=data.game_rounds,
                      cost_summary=data.cost_summary, round_summary=data.round_summary)
        for name, frame in tables.items():
            atomic_write(output_root/"tables"/key/f"{name}.csv", frame.to_csv(index=False, float_format="%.17g"))
        for kind, make_figure in (("rounds", make_rounds_figure), ("cost", make_cost_figure)):
            figure = make_figure(data, dataset, family)
            try:
                audit = save_figure(figure, output_root/"figures", dataset, kind, family, png)
                audits.append(audit)
                figures.append(output_root/"figures"/audit["pdf"])
            finally:
                figure.clear()
        print(f"Exported {dataset.label}: two PDFs"+(" and PNG previews" if png else ""), flush=True)
    for name, checksum in input_hashes.items():
        if sha256(data_root/name) != checksum:
            raise ValueError(f"Raw input changed during export: {name}")
    code_paths = [PACKAGE_ROOT/"plot_figures.py", PACKAGE_ROOT/"requirements.txt", *sorted((PACKAGE_ROOT/"pd_figures").glob("*.py"))]
    manifest = dict(version=__version__, datasets={key: DATASETS[key].label for key in keys},
        games_per_dataset=120, games_per_model_cost=GAMES_PER_CELL, independent_games=120*len(keys),
        models=list(MODELS), monitoring_costs=COSTS, rounds=ROUNDS, round_1_included=True,
        cooperation="OptionB / 选项B", rate_denominator_per_game=20,
        sampling_unit="independent game; both agents combined before means and CIs",
        penalty="mean of both agents' total recorded penalties over rounds 1–10, including monitoring charges",
        confidence_intervals="pointwise two-sided 95% Student t, sample SD with ddof=1; n=10, df=9",
        font_family=family, font_files=fonts, input_sha256=input_hashes,
        code_sha256={p.relative_to(PACKAGE_ROOT).as_posix(): sha256(p) for p in code_paths},
        input_manifest_sha256=sha256(PACKAGE_ROOT/"input_manifest.json"), figures=audits,
        software=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__,
                      scipy=scipy.__version__, matplotlib=matplotlib.__version__))
    atomic_write(output_root/"manifest.json", json.dumps(manifest, indent=2)+"\n")
    lines = ["# Publication figures", "", "Each dataset has two PDFs: the 3 × 4 rounds/penalty figure "
        "and the vertically stacked cooperation/LOOK cost figure. Individual dots show independent games; "
        "error bars are pointwise 95% Student's t confidence intervals.", ""]
    for key in keys:
        lines += [f"## {DATASETS[key].label}", ""]
        for audit in (a for a in audits if a["dataset"] == key):
            label = "Cooperation, LOOK and penalty" if audit["kind"] == "rounds" else "Cooperation and LOOK by monitoring cost"
            lines.append(f"- [{label}](figures/{audit['pdf']})")
        lines.append("")
    atomic_write(output_root/"README.md", "\n".join(lines))
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in figures+[output_root/"README.md", output_root/"manifest.json"]:
            # Stable archive timestamps make repeated exports reproducible.
            info = zipfile.ZipInfo(path.relative_to(output_root).as_posix(), (2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(info, path.read_bytes())
    atomic_write(output_root/"publication_figures.zip", archive.getvalue())
    print(f"Saved {len(figures)} PDFs to {output_root/'figures'}", flush=True)
    return manifest


def main(argv=None):
    command = parser()
    args = command.parse_args(argv)
    try:
        generate(args.data_root, args.output_root, args.datasets, args.font_family,
                 args.font_directory, not args.no_png, args.validate_only, args.allow_input_changes)
    except (ValueError, FileNotFoundError) as error:
        command.error(str(error))
    return 0
