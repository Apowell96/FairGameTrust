"""Validate real game semantics and reject inconsistent input files."""

from pathlib import Path
import tempfile
import unittest

import pandas as pd

from support import PACKAGE
from pd_figures.data import decode_game, load_dataset, normalize_strategy, parse_bool, parse_list
from pd_figures.settings import COSTS, DATASETS, MODELS


def game_row(cost=.25, model=MODELS[0]):
    row = dict(language="en", n_rounds_is_known=True, played_rounds=10, max_rounds=10,
               agents_communicate=False, agent1_llm=model, agent2_llm=model)
    for agent, looked in ((1, True), (2, False)):
        charge = cost if looked else 0
        row.update({f"agent{agent}_personality": "none", f"agent{agent}_knows_opponent_with_prob": 0,
            f"agent{agent}_strategies": repr(["OptionB"]*10), f"agent{agent}_scores": repr([2+charge]*10),
            f"agent{agent}_trust_actions": repr(["LOOK" if looked else "NO_LOOK"]*10),
            f"agent{agent}_trust_costs": repr([charge]*10), f"agent{agent}_total_trust_cost": 10*charge,
            f"agent{agent}_look_count": 10 if looked else 0, f"agent{agent}_no_look_count": 0 if looked else 10,
            f"agent{agent}_look_ratio": 1 if looked else 0})
    return row


class DataTests(unittest.TestCase):
    def decode(self, row, cost=.25):
        return decode_game(row, cost, 0, DATASETS["english_horizon_known"], "sample.csv")

    def test_scores_and_actions_are_decoded(self):
        rows = pd.DataFrame(self.decode(game_row()))
        self.assertEqual(len(rows), 20)
        self.assertEqual(rows.cooperated.sum(), 20)
        self.assertEqual(rows.looked.sum(), 10)
        self.assertEqual(rows.groupby("agent").recorded_penalty.sum().to_dict(),
                         {"agent1": 22.5, "agent2": 20.0})

    def test_free_look_is_counted(self):
        rows = pd.DataFrame(self.decode(game_row(0), cost=0))
        self.assertEqual(rows.looked.sum(), 10)
        self.assertEqual(rows.monitoring_charge.sum(), 0)

    def test_translated_and_spaced_options(self):
        for text in ("OptionB", "Option B", "选项 B", "选项Ｂ", "ＯｐｔｉｏｎＢ"):
            self.assertEqual(normalize_strategy(text), "OptionB")
        self.assertEqual(normalize_strategy("选项 A"), "OptionA")
        with self.assertRaises(ValueError):
            normalize_strategy("invalid")

    def test_boolean_and_list_validation(self):
        self.assertTrue(parse_bool("TRUE"))
        self.assertFalse(parse_bool(False))
        for value in ("perhaps", 1):
            with self.assertRaises(ValueError):
                parse_bool(value)
        for value in ("[]", "not a list", "(1, 2)"):
            with self.assertRaises(ValueError):
                parse_list(value, "actions")

    def test_inconsistent_games_are_rejected(self):
        changes = [
            {"n_rounds_is_known": False}, {"language": "fr"}, {"played_rounds": 9},
            {"agent1_personality": "selfish"}, {"agent2_llm": "gpt-4o"},
            {"agents_communicate": True}, {"agent1_knows_opponent_with_prob": .5},
            {"agent1_scores": repr([2.5]*10)}, {"agent2_trust_costs": repr([.25]*10)},
            {"agent1_look_count": 9}, {"agent1_trust_actions": repr(["invalid"]*10)},
            {"agent1_strategies": repr(["OptionB"]*9)}, {"look_cost": .5},
        ]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                row = game_row(); row.update(change); self.decode(row)

    def test_duplicate_games_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)/"English/horizon_known/0"
            for folder in ("first", "duplicate"):
                path = directory/folder/"results_Prisoner_dilemma_trust_0.csv"
                path.parent.mkdir(parents=True)
                pd.DataFrame([game_row(0)]).to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, "Duplicate independent game"):
                load_dataset(temporary, DATASETS["english_horizon_known"])

    def test_incomplete_model_cost_cells_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            for cost in COSTS:
                path = Path(temporary)/f"English/horizon_known/{cost:g}/claude/results_Prisoner_dilemma_trust_0.csv"
                path.parent.mkdir(parents=True)
                pd.DataFrame([game_row(cost)]).to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, "ten independent games"):
                load_dataset(temporary, DATASETS["english_horizon_known"])

    def test_cost_point_75_is_excluded(self):
        with tempfile.TemporaryDirectory() as temporary:
            for cost in COSTS:
                for model in MODELS:
                    folder = Path(temporary)/f"English/horizon_known/{cost:g}/{model}"
                    folder.mkdir(parents=True)
                    for iteration in range(10):
                        pd.DataFrame([game_row(cost, model)]).to_csv(
                            folder/f"results_Prisoner_dilemma_trust_{iteration}.csv", index=False)
            excluded = Path(temporary)/"English/horizon_known/0.75/model"
            excluded.mkdir(parents=True)
            (excluded/"results_Prisoner_dilemma_trust_0.csv").write_text("not a game")
            actual = load_dataset(temporary, DATASETS["english_horizon_known"])
            self.assertEqual(actual.rounds.game_id.nunique(), 120)
            self.assertNotIn(.75, set(actual.rounds.cost))


if __name__ == "__main__":
    unittest.main()
