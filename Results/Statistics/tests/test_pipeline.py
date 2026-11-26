"""Check analysis families, input structure and command-line execution."""

import ast
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd

from support import DATA_ROOT, PACKAGE, study
from pd_statistics.analyses import TABLES, holm_adjust
from pd_statistics.cli import generate
from pd_statistics.io import sha256


class PipelineTests(unittest.TestCase):
    def test_planned_analysis_families(self):
        results = study()[3]
        self.assertEqual(len(results), 264)
        self.assertEqual(set(results.table_id), {f"S{i}" for i in range(1, 19)})
        for table, group in results.groupby("table_id"):
            expected = 18 if TABLES[table][0] == "cost" else 12
            self.assertEqual(len(group), expected)
            self.assertTrue(group.holm_family_size.eq(expected).all())
            np.testing.assert_allclose(group.p_holm.to_numpy(dtype=float),
                                       holm_adjust(group.p_value), equal_nan=True)
        self.assertEqual(set(results.analysis), {"cost", "penalty", "language", "horizon", "early_late"})
        self.assertEqual(set(results.loc[results.analysis.eq("penalty"), "dataset_first"]),
                         {"english_horizon_known"})

    def test_loaded_game_structure(self):
        loaded, rounds, games, _ = study()
        self.assertEqual(len(loaded), 4)
        self.assertEqual(len(games), 480)
        self.assertEqual(len(rounds), 9600)
        self.assertTrue(games.game_id.is_unique)
        self.assertTrue(games.groupby(["dataset", "model", "cost"]).size().eq(10).all())
        self.assertTrue(games.cooperation_rate.between(0, 1).all())
        self.assertTrue(games.look_rate.between(0, 1).all())

    def test_validation_only_writes_nothing(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)/"output"
            result = generate(DATA_ROOT, output, validate_only=True)
            self.assertEqual(result["validated_games"], 480)
            self.assertFalse(output.exists())

    def test_cli_runs_after_relocation_and_accepts_valid_input_updates(self):
        with tempfile.TemporaryDirectory() as temporary:
            results = Path(temporary)/"Results"
            target = results/"Statistics"
            shutil.copytree(PACKAGE/"pd_statistics", target/"pd_statistics")
            for name in ["run_statistics.py", "requirements.txt"]:
                shutil.copyfile(PACKAGE/name, target/name)
            inputs = {name: checksum for item in study()[0].values()
                      for name, checksum in item.input_hashes.items()}
            for name in inputs:
                destination = results/name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(DATA_ROOT/name, destination)
            command = [sys.executable, "-B", str(target/"run_statistics.py")]
            completed = subprocess.run(command, cwd=temporary, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, text=True)
            self.assertEqual(completed.returncode, 0, completed.stdout)
            output = pd.read_csv(target/"output/all_tests.csv")
            manifest = json.loads((target/"output/manifest.json").read_text())
            self.assertEqual(len(output), 264)
            self.assertEqual(len(list((target/"output/tables").glob("*.csv"))), 18)
            self.assertEqual(manifest["independent_games"], 480)
            self.assertTrue(output.p_value.dropna().between(0, 1).all())
            for name, checksum in inputs.items():
                self.assertEqual(sha256(results/name), checksum)

            # A valid change in a free-monitoring game must be accepted.
            name = next(name for name in inputs if name.startswith("English/horizon_known/0/"))
            changed = results/name
            frame = pd.read_csv(changed)
            actions = ast.literal_eval(frame.loc[0, "agent1_trust_actions"])
            actions[0] = "NO_LOOK" if actions[0] == "LOOK" else "LOOK"
            frame.loc[0, "agent1_trust_actions"] = repr(actions)
            frame.loc[0, "agent1_look_count"] = actions.count("LOOK")
            frame.loc[0, "agent1_no_look_count"] = actions.count("NO_LOOK")
            frame.loc[0, "agent1_look_ratio"] = actions.count("LOOK")/10
            frame.to_csv(changed, index=False)
            accepted = subprocess.run(command+["--validate-only"], cwd=temporary,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            self.assertEqual(accepted.returncode, 0, accepted.stdout)


if __name__ == "__main__":
    unittest.main()
