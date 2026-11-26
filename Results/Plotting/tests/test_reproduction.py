"""Reproduce all four datasets and run the CLI in a relocated code/data folder."""

from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd

from support import DATA_ROOT, PACKAGE, study_data
from pd_figures.cli import generate
from pd_figures.settings import DATASETS


class ReproductionTests(unittest.TestCase):
    def compare_reference(self, filename, frames, keys):
        expected = pd.read_csv(PACKAGE/"tests/reference_data"/filename)
        actual = pd.concat(frames, ignore_index=True)
        merged = actual.merge(expected, on=keys, suffixes=("_actual", "_expected"), validate="one_to_one")
        self.assertEqual(len(merged), len(expected))
        self.assertEqual(len(actual), len(expected))
        for field in expected.columns.difference(keys):
            np.testing.assert_allclose(merged[f"{field}_actual"], merged[f"{field}_expected"],
                                       rtol=0, atol=1e-12, err_msg=field)

    def test_all_480_game_values(self):
        self.compare_reference("game_values.csv", [study_data(key)[1].games for key in DATASETS],
                               ["dataset", "model", "cost", "iteration"])

    def test_all_cost_means_sds_and_cis(self):
        self.compare_reference("cost_summaries.csv", [study_data(key)[1].cost_summary for key in DATASETS],
                               ["dataset", "model", "cost"])

    def test_all_round_means_sds_and_cis(self):
        self.compare_reference("round_summaries.csv", [study_data(key)[1].round_summary for key in DATASETS],
                               ["dataset", "model", "cost", "round"])

    def test_exact_input_file_set_and_hashes(self):
        expected = json.loads((PACKAGE/"input_manifest.json").read_text())["files"]
        actual = {name: value for key in DATASETS for name, value in study_data(key)[0].input_hashes.items()}
        self.assertEqual(len(actual), 480)
        self.assertEqual(actual, expected)

    def test_validation_only_writes_nothing_and_needs_no_font(self):
        with tempfile.TemporaryDirectory() as temporary, redirect_stdout(io.StringIO()):
            output = Path(temporary)/"not-created"
            result = generate(DATA_ROOT, output, ["chinese"], family="UnavailableFont12345", validate_only=True)
            self.assertEqual(result["validated_games"], 120)
            self.assertFalse(output.exists())

    def test_cli_relocated_without_old_scripts(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            results, code = directory/"Results", directory/"Results/Plotting"
            code.mkdir(parents=True)
            shutil.copytree(PACKAGE/"pd_figures", code/"pd_figures", ignore=shutil.ignore_patterns("__pycache__"))
            for name in ("plot_figures.py", "input_manifest.json", "requirements.txt"):
                shutil.copyfile(PACKAGE/name, code/name)
            for name in study_data("chinese")[0].input_hashes:
                target = results/name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(DATA_ROOT/name, target)
            environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
            command = [sys.executable, str(code/"plot_figures.py"), "--datasets", "chinese",
                       "--output-root", str(directory/"rendered"), "--no-png"]
            result = subprocess.run(command, cwd=directory, env=environment, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(list((directory/"rendered/figures").glob("*.pdf"))), 2)
            manifest = json.loads((directory/"rendered/manifest.json").read_text())
            self.assertEqual(manifest["independent_games"], 120)
            # Editing otherwise-valid input must be detected by its checksum.
            changed = next((results/"Chinese").glob("*/*/results_Prisoner_dilemma_trust_0.csv"))
            changed.write_bytes(changed.read_bytes()+b"\n")
            result = subprocess.run(command+["--validate-only"], cwd=directory,
                                    env=environment, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("Input differs from publication manifest", result.stderr)


if __name__ == "__main__":
    unittest.main()
