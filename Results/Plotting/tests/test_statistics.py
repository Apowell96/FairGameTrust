"""Check independent-game aggregation, full-game penalties and t intervals."""

import unittest

import numpy as np
import pandas as pd
from scipy.stats import t

from support import PACKAGE
from pd_figures.statistics import build_plot_data, ci95_half_width


class StatisticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rows = []
        for game in (0, 1):
            for agent in (1, 2):
                for round_number in range(1, 11):
                    rows.append(dict(dataset="example", model="example", cost=.25,
                        game_id=str(game), iteration=game, agent=f"agent{agent}", round=round_number,
                        looked=int(game == 0 and agent == 1), cooperated=int(game == 1 or agent == 1),
                        recorded_penalty=(1 if agent == 1 else 3) if game == 0 else 5))
        cls.rounds = pd.DataFrame(rows)
        cls.data = build_plot_data(cls.rounds)

    def test_both_agents_combined_within_game(self):
        self.assertEqual(self.data.games.look_rate.tolist(), [.5, 0.])
        self.assertEqual(self.data.cost_summary.games.iloc[0], 2)
        self.assertEqual(self.data.cost_summary.look_rate.iloc[0], .25)
        self.assertEqual(len(self.data.game_rounds), 20)

    def test_penalty_is_full_game_total_per_agent(self):
        self.assertEqual(self.data.games.mean_total_penalty.tolist(), [20., 50.])
        self.assertEqual(self.data.cost_summary.mean_total_penalty.iloc[0], 35.)

    def test_ci_uses_game_sd_and_df(self):
        expected = t.ppf(.975, 1)*.25
        self.assertAlmostEqual(self.data.cost_summary.ci95_half_width_look_rate.iloc[0], expected)
        self.assertTrue(np.allclose(self.data.round_summary.ci95_half_width_look_rate, expected))
        # A t interval for two discrete game rates can extend outside [0, 1].
        self.assertGreater(expected, 1)

    def test_ci_zero_sd_and_invalid_inputs(self):
        self.assertEqual(ci95_half_width(0, 10), 0)
        self.assertAlmostEqual(ci95_half_width(1, 10), 2.2621571627409915/np.sqrt(10))
        for sd, n in ((1, 1), (-1, 10), (np.nan, 10), (1, np.nan)):
            with self.assertRaises(ValueError):
                ci95_half_width(sd, n)

    def test_duplicate_decisions_are_rejected(self):
        with self.assertRaises(ValueError):
            build_plot_data(pd.concat([self.rounds, self.rounds.iloc[:1]]))


if __name__ == "__main__":
    unittest.main()
