"""Check plotted means/CIs, typography, layouts, dot counts and PDF exports."""

import io
import json
from pathlib import Path
import re
import tempfile
import unittest

from matplotlib.collections import PathCollection
from matplotlib.container import ErrorbarContainer
from matplotlib.text import Text
from matplotlib.transforms import Bbox
import numpy as np
from PIL import Image

from support import PACKAGE, study_data
from pd_figures.plotting import (COST_BOUNDS, FONT_FAMILY, ROUND_BOUNDS, check_font,
    make_cost_figure, make_rounds_figure, numerical_fingerprint, save_figure)
from pd_figures.settings import COSTS, DATASETS, MODELS


class PlottingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        check_font()
        cls.reference = json.loads((PACKAGE/"tests/reference_data/geometry.json").read_text())
        cls.figures = {}
        for key, dataset in DATASETS.items():
            data = study_data(key)[1]
            cls.figures[key, "rounds"] = make_rounds_figure(data, dataset)
            cls.figures[key, "cost"] = make_cost_figure(data, dataset)

    @classmethod
    def tearDownClass(cls):
        for figure in cls.figures.values():
            figure.clear()

    def test_all_eight_layouts_and_font_sizes(self):
        for (key, kind), figure in self.figures.items():
            with self.subTest(dataset=key, figure=kind):
                expected = self.reference[key][kind]
                self.assertEqual(len(figure.axes), len(expected["axes"]))
                np.testing.assert_allclose(figure.get_size_inches(), expected["figsize"], rtol=0, atol=1e-12)
                bounds = ROUND_BOUNDS if kind == "rounds" else COST_BOUNDS[key]
                np.testing.assert_allclose(bounds, expected["save_bounds"], rtol=0, atol=1e-12)
                for axis, reference in zip(figure.axes, expected["axes"]):
                    np.testing.assert_allclose(axis.get_position().bounds, reference["bounds"], rtol=0, atol=1e-12)
                    np.testing.assert_allclose(axis.get_ylim(), reference["ylim"], rtol=0, atol=1e-12)
                    self.assertEqual(axis.get_xlabel(), reference["xlabel"])
                    self.assertEqual(axis.get_ylabel(), reference["ylabel"])
                    self.assertAlmostEqual(axis.xaxis.label.get_fontsize(), reference["xlabel_size"])
                    self.assertAlmostEqual(axis.yaxis.label.get_fontsize(), reference["ylabel_size"])
                    self.assertAlmostEqual(axis.title.get_fontsize(), reference["title_size"])
                    self.assertAlmostEqual(axis.get_xticklabels()[0].get_fontsize(), reference["tick_size"])

    def test_titles_captions_and_font_family(self):
        for figure in self.figures.values():
            figure.canvas.draw()
            self.assertIsNone(figure._suptitle)
            self.assertEqual(len(figure.texts), 0)
            texts = [t for t in figure.findobj(match=Text) if t.get_visible() and t.get_text()]
            self.assertEqual({t.get_fontproperties().get_name() for t in texts}, {FONT_FAMILY})
            self.assertFalse(any("frequency" in t.get_text().lower() or "LOOK cost" in t.get_text() for t in texts))

    def test_individual_game_dot_counts_and_sizes(self):
        for (_, kind), figure in self.figures.items():
            dots = [c for axis in figure.axes for c in axis.collections if isinstance(c, PathCollection)]
            self.assertEqual(len(dots), 252 if kind == "rounds" else 24)
            self.assertTrue(all(len(c.get_offsets()) == 10 for c in dots))
            self.assertTrue(all(np.array_equal(c.get_sizes(), [28 if kind == "rounds" else 24]) for c in dots))
            self.assertTrue(all(c.get_alpha() == (.30 if kind == "rounds" else .32) for c in dots))

    def check_curve(self, container, expected, x_field, metric):
        line, _, collections = container.lines
        np.testing.assert_allclose(np.asarray(line.get_xdata(), dtype=float), expected[x_field], rtol=0, atol=1e-12)
        np.testing.assert_allclose(np.asarray(line.get_ydata(), dtype=float), expected[metric], rtol=0, atol=1e-12)
        half = expected[f"ci95_half_width_{metric}"].to_numpy()
        for segment, x, y, error in zip(collections[0].get_segments(), expected[x_field], expected[metric], half):
            np.testing.assert_allclose(segment, [[x, y-error], [x, y+error]], rtol=0, atol=1e-12)

    def test_all_mean_curves_and_error_bar_endpoints(self):
        for key in DATASETS:
            data = study_data(key)[1]
            for row, metric in enumerate(("cooperation_rate", "look_rate")):
                for column, cost in enumerate(COSTS):
                    axis = self.figures[key, "rounds"].axes[row*4+column]
                    containers = [c for c in axis.containers if isinstance(c, ErrorbarContainer)]
                    self.assertEqual(len(containers), 3)
                    for model, container in zip(MODELS, containers):
                        sample = data.round_summary.loc[data.round_summary.cost.eq(cost)
                            & data.round_summary.model.eq(model)].sort_values("round")
                        self.check_curve(container, sample, "round", metric)
                axis = self.figures[key, "cost"].axes[row]
                containers = [c for c in axis.containers if isinstance(c, ErrorbarContainer)]
                self.assertEqual(len(containers), 3)
                for model, container in zip(MODELS, containers):
                    sample = data.cost_summary.loc[data.cost_summary.model.eq(model)].sort_values("cost")
                    self.check_curve(container, sample, "cost", metric)

    def test_penalty_bar_heights_match_full_game_totals(self):
        for key in DATASETS:
            for column, cost in enumerate(COSTS):
                axis = self.figures[key, "rounds"].axes[8+column]
                actual = [patch.get_height() for patch in axis.patches]
                sample = study_data(key)[1].cost_summary
                expected = sample.loc[sample.cost.eq(cost)].set_index("model").reindex(MODELS).mean_total_penalty
                np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-12)

    def test_fingerprint_is_stable_across_distinct_figure_objects(self):
        other = make_cost_figure(study_data("french")[1], DATASETS["french"])
        try:
            self.assertEqual(numerical_fingerprint(other), numerical_fingerprint(self.figures["french", "cost"]))
        finally:
            other.clear()

    def test_pdf_fonts_and_repeatability(self):
        figure = self.figures["english_horizon_known", "cost"]
        with tempfile.TemporaryDirectory() as temporary:
            first = save_figure(figure, Path(temporary)/"first", DATASETS["english_horizon_known"], "cost", png=False)
            second = save_figure(figure, Path(temporary)/"second", DATASETS["english_horizon_known"], "cost", png=False)
            contents = (Path(temporary)/"first"/first["pdf"]).read_bytes()
            fonts = re.findall(rb"/BaseFont\s*/([^\s/]+)", contents)
            self.assertTrue(fonts)
            self.assertTrue(all(b"TimesNewRoman" in name for name in fonts))
            self.assertIn(b"/FontFile2", contents)
            self.assertNotIn(b"/CreationDate", contents)
            self.assertEqual(first["pdf_sha256"], second["pdf_sha256"])

    def test_all_eight_previews_match_reference_figures(self):
        for (key, kind), figure in self.figures.items():
            with self.subTest(dataset=key, figure=kind):
                bounds = ROUND_BOUNDS if kind == "rounds" else COST_BOUNDS[key]
                buffer = io.BytesIO()
                figure.savefig(buffer, format="png", dpi=120,
                               bbox_inches=Bbox.from_bounds(*bounds), pad_inches=0)
                buffer.seek(0)
                actual = np.asarray(Image.open(buffer)).astype(float)
                reference = np.asarray(Image.open(PACKAGE/"tests/reference_figures"/
                                                 f"{key}_{kind}.png")).astype(float)
                self.assertEqual(actual.shape, reference.shape)
                # Permit sub-pixel rounding differences in otherwise identical plots.
                self.assertLess(np.mean(np.any(actual != reference, axis=2)), .001)
                self.assertLess(np.mean(np.abs(actual-reference)), .01)

    def test_missing_font_is_an_explicit_error(self):
        with self.assertRaisesRegex(ValueError, "unavailable"):
            check_font("UnavailableFont12345")


if __name__ == "__main__":
    unittest.main()
