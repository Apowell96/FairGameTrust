"""Hand-check aggregation, effect direction, test tails and Holm families."""

import unittest

import numpy as np
import pandas as pd
from scipy.stats import t

from support import study
from pd_statistics.analyses import game_values, holm_adjust, mann_whitney, paired_early_late


class MethodTests(unittest.TestCase):
    def test_holm_step_down_unsorted(self):
        np.testing.assert_allclose(holm_adjust([.04, .001, .03, .2]), [.09, .004, .09, .2])

    def test_holm_keeps_undefined_planned_slots(self):
        actual = holm_adjust([.001, np.nan, .02, np.nan])
        np.testing.assert_allclose(actual[[0, 2]], [.004, .06])
        self.assertTrue(np.isnan(actual[[1, 3]]).all())

    def test_holm_rejects_invalid_p_values(self):
        for sample in [[-.01], [1.1], [np.inf], [[.1]]]:
            with self.subTest(sample=sample), self.assertRaises(ValueError):
                holm_adjust(sample)

    def test_mann_whitney_counts_ties_and_effect_direction(self):
        # Pairwise wins = 0; ties = 1; U_first = wins + ties/2 = 0.5.
        fit = mann_whitney([1., 2.], [2., 3.])
        self.assertEqual(fit["u_first"], .5)
        self.assertEqual(fit["u_second"], 3.5)
        self.assertEqual(fit["rank_biserial"], -.75)
        reversed_fit = mann_whitney([2., 3.], [1., 2.])
        self.assertEqual(reversed_fit["rank_biserial"], .75)
        self.assertEqual(fit["p_value"], reversed_fit["p_value"])
        self.assertEqual(fit["alternative"], "two-sided")
        self.assertTrue(fit["use_continuity"])
        self.assertFalse(fit["paired"])

    def test_all_identical_rank_samples(self):
        fit = mann_whitney([0]*10, [0]*10)
        self.assertEqual(fit["u_first"], 50.)
        self.assertEqual(fit["p_value"], 1.)
        self.assertEqual(fit["rank_biserial"], 0.)

    def test_invalid_rank_samples(self):
        for x, y in [([], [1]), ([np.nan], [1]), ([[1]], [2]), ([1], [np.inf])]:
            with self.subTest(x=x, y=y), self.assertRaises(ValueError):
                mann_whitney(x, y)

    def test_paired_t_statistic_one_sided_tail_and_ci(self):
        early = np.array([.75, .5, .875, .625])
        late = np.array([.1, .4, .3, .4])
        difference = late-early
        se = difference.std(ddof=1)/2
        statistic = difference.mean()/se
        fit = paired_early_late(early, late)
        self.assertAlmostEqual(fit["t_statistic"], statistic)
        self.assertAlmostEqual(fit["p_value"], t.cdf(statistic, df=3))
        self.assertAlmostEqual(fit["ci95_lower"], difference.mean()-t.ppf(.975, 3)*se)
        self.assertAlmostEqual(fit["ci95_upper"], difference.mean()+t.ppf(.975, 3)*se)
        self.assertEqual(fit["negative_games"], 4)
        self.assertLess(fit["p_value"], paired_early_late(late, early)["p_value"])

    def test_undefined_constant_differences_are_not_zero_tests(self):
        for early, late in [([0]*10, [0]*10), ([.5]*10, [0]*10)]:
            fit = paired_early_late(early, late)
            self.assertTrue(np.isnan(fit["t_statistic"]))
            self.assertTrue(np.isnan(fit["p_value"]))
            self.assertEqual(fit["ci95_lower"], fit["ci95_upper"])
            self.assertEqual(fit["test_status"], "constant_differences")

    def test_invalid_paired_samples(self):
        for early, late in [([0], [0]), ([0, 1], [0]), ([0, np.nan], [0, 1])]:
            with self.subTest(early=early), self.assertRaises(ValueError):
                paired_early_late(early, late)

    def test_game_windows_and_denominators(self):
        # Set round 1 LOOK=1, early LOOK=0, late LOOK=1 for both agents.
        source = study()[1]
        raw = source.loc[source.game_id.eq(source.game_id.iloc[0])].copy()
        raw["looked"] = raw["round"].isin([1, 6, 7, 8, 9, 10]).astype(int)
        raw["cooperated"] = raw.agent.eq("agent1").astype(int)
        raw["recorded_penalty"] = np.where(raw.agent.eq("agent1"), 2., 6.)
        game = game_values(raw).iloc[0]
        self.assertEqual(game.look_rate, .6)
        self.assertEqual(game.early_look_rate, 0.)
        self.assertEqual(game.late_look_rate, 1.)
        self.assertEqual(game.cooperation_rate, .5)
        self.assertEqual(game.mean_total_penalty, 40.)  # mean(20, 60), not sum(20, 60)
        self.assertEqual(game.early_decisions, 8)
        self.assertEqual(game.late_decisions, 10)

    def test_duplicate_and_incomplete_games_rejected(self):
        source = study()[1]
        game = source.loc[source.game_id.eq(source.game_id.iloc[0])]
        for bad in [game.iloc[:-1], pd.concat([game, game.iloc[:1]])]:
            with self.assertRaises(ValueError):
                game_values(bad)


if __name__ == "__main__":
    unittest.main()
