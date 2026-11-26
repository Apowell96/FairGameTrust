"""The two publication layouts, with explicit styles and no runtime patches."""

import hashlib
import io
import json
import math
from pathlib import Path

import matplotlib as mpl
from matplotlib import font_manager
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.text import Text
from matplotlib.ticker import FuncFormatter, MultipleLocator
from matplotlib.transforms import Bbox
import numpy as np

from .io import atomic_write, sha256
from .settings import COLOURS, COSTS, MODELS, ROUNDS

FONT_FAMILY = "Times New Roman"
ROUND_DOT_AREA = 28.0
COST_DOT_AREA = 24.0
ROUND_FIGSIZE = (20.0, 13.2)
COST_FIGSIZE = (10.0, 13.0)
ROUND_LABEL_SIZE = 20*10/7.2
ROUND_TICK_SIZE = 20*8.5/7.2
ROUND_TITLE_SIZE = 20*11/7.2
ROUND_BOUNDS = (-0.5464322916666666, -0.16384548611111127, 20.36544409232853, 13.25384548611111)
# Fixed paper rectangles retain panel dimensions and surrounding whitespace.
COST_BOUNDS = {
    "english_horizon_known": (-0.19669270833333352, 0.2227951388888886, 10.292235243055556, 12.64620486111111),
    "english_horizon_unknown": (-0.4156380208333328, 0.2227951388888886, 10.831276041666666, 12.64620486111111),
    "french": (-0.19669270833333352, 0.2227951388888886, 10.225286458333334, 12.64620486111111),
    "chinese": (-0.19669270833333352, 0.2227951388888886, 10.37068576388889, 12.64620486111111),
}


def check_font(family=FONT_FAMILY, font_directory=None):
    """Require the requested typeface; never silently substitute another font."""
    if font_directory is not None:
        for path in font_manager.findSystemFonts(fontpaths=[str(font_directory)]):
            font_manager.fontManager.addfont(path)
    result = {}
    for weight in ("normal", "bold"):
        try:
            path = font_manager.findfont(font_manager.FontProperties(family=family, weight=weight),
                                         fallback_to_default=False)
        except ValueError as error:
            raise ValueError(f"Font {family!r} is unavailable. Install it, use --font-directory, "
                             "or explicitly select --font-family.") from error
        result[weight] = {"file": Path(path).name, "sha256": sha256(path)}
    return result


def nice_upper(value):
    if value <= 0:
        return 1.0
    raw_step = value/5
    magnitude = 10**math.floor(math.log10(raw_step))
    normalized = raw_step/magnitude
    step = next(candidate for candidate in (1, 2, 5, 10) if normalized <= candidate)*magnitude
    return math.ceil(value/step)*step


def game_dots(axis, x, values, colour, width, area, alpha):
    values = np.asarray(values, dtype=float)
    offsets = np.linspace(-width, width, len(values)) if len(values) > 1 else np.zeros(len(values))
    return axis.scatter(x+offsets, values, color=colour, alpha=alpha, s=area,
                        edgecolors="none", clip_on=False, zorder=3, label="_nolegend_")


def legend(figure, dataset, fontsize, anchor, linewidth):
    handles = [Line2D([], [], color=COLOURS[model], marker="o", linewidth=linewidth,
                      markersize=5, label=dataset.model_label(model).replace("Claude Sonnet ", "Claude Sonnet\n")
                      .replace("Mistral Small ", "Mistral Small\n")) for model in MODELS]
    figure.legend(handles=handles, loc="upper center", bbox_to_anchor=(.5, anchor),
                  ncol=3, frameon=False, fontsize=fontsize, columnspacing=1.2,
                  handlelength=2., handletextpad=.5)


def axis_style(axis, tick_size, grid_width):
    axis.set_axisbelow(True)
    axis.grid(axis="y", color="#d5d8dc", linewidth=grid_width)
    axis.spines[["top", "right"]].set_visible(False)
    for spine in axis.spines.values():
        spine.set_linewidth(1.3)
    axis.tick_params(axis="both", labelsize=tick_size, width=1.5, length=6, pad=8)


def finish_lines(figure):
    for axis in figure.axes:
        for line in axis.lines:
            line.set_linewidth(line.get_linewidth()*1.15)
            line.set_markersize(line.get_markersize()*1.10)


def rate_limits(summary, metrics):
    lower = min(0., *(float((summary[m]-summary[f"ci95_half_width_{m}"]).min()) for m in metrics))
    upper = max(1., *(float((summary[m]+summary[f"ci95_half_width_{m}"]).max()) for m in metrics))
    return lower, upper


def make_rounds_figure(data, dataset, family=FONT_FAMILY):
    """Three rows: cooperation, LOOK, full-game total penalty; four cost columns."""
    with mpl.rc_context({"font.family": family, "pdf.fonttype": 42, "ps.fonttype": 42}):
        figure = Figure(figsize=ROUND_FIGSIZE, dpi=150, facecolor="white")
        FigureCanvasAgg(figure)
        axes = figure.subplots(3, 4, sharey="row")
        figure.subplots_adjust(left=.085, right=.975, bottom=.10, top=.7566500187055743,
                               wspace=.25, hspace=.65)
        legend(figure, dataset, ROUND_TICK_SIZE, .926, 2.)
        for axis in axes.ravel():
            axis_style(axis, ROUND_TICK_SIZE, .6)
            axis.xaxis.label.set_fontsize(ROUND_LABEL_SIZE)
            axis.yaxis.label.set_fontsize(ROUND_LABEL_SIZE)
            axis.title.set_fontsize(ROUND_TITLE_SIZE)
        for row, metric in enumerate(("cooperation_rate", "look_rate")):
            lower, upper = rate_limits(data.round_summary, [metric])
            axes[row, 0].set_ylim(lower-.03*(upper-lower), upper+.04*(upper-lower))
            for column, cost in enumerate(COSTS):
                axis = axes[row, column]
                for model_index, model in enumerate(MODELS):
                    series = data.round_summary.loc[data.round_summary.cost.eq(cost)
                        & data.round_summary.model.eq(model)].sort_values("round")
                    samples = data.game_rounds.loc[data.game_rounds.cost.eq(cost)
                        & data.game_rounds.model.eq(model)]
                    for round_number in ROUNDS:
                        values = samples.loc[samples["round"].eq(round_number)].sort_values("game_id")[metric]
                        game_dots(axis, round_number+(model_index-1)*.04, values,
                                  COLOURS[model], .15, ROUND_DOT_AREA, .30)
                    axis.errorbar(series["round"], series[metric], yerr=series[f"ci95_half_width_{metric}"],
                        color=COLOURS[model], marker="o", markersize=3.2, linewidth=1.7,
                        elinewidth=.8, capsize=2.2, zorder=4)
                axis.set_xticks(ROUNDS)
                axis.set_xlim(.72, 10.28)
                axis.set_xlabel("Round", fontsize=ROUND_LABEL_SIZE, labelpad=6)
                axis.yaxis.set_major_locator(MultipleLocator(.2))
                if row == 0:
                    axis.set_title(f"Monitoring cost\n= {cost:g}", fontsize=ROUND_TITLE_SIZE,
                                   fontweight="normal", pad=6)
        axes[0, 0].set_ylabel("Cooperation\nrate", fontsize=ROUND_LABEL_SIZE, labelpad=12)
        axes[1, 0].set_ylabel("LOOK\nrate", fontsize=ROUND_LABEL_SIZE, labelpad=12)
        metric = "mean_total_penalty"
        half = f"ci95_half_width_{metric}"
        upper = max(float(data.games[metric].max()), float((data.cost_summary[metric]+data.cost_summary[half]).max()))
        lower = min(0., float((data.cost_summary[metric]-data.cost_summary[half]).min()))
        ymax = nice_upper(upper*1.10)
        axes[2, 0].set_ylim(lower-.03*(ymax-lower) if lower < 0 else 0., ymax)
        positions = np.arange(len(MODELS))
        labels = ["Claude\nSonnet\n4.6", "GPT-\n4o",
                  "Mistral\nSmall\n2603" if dataset.key == "chinese" else "Mistral\nSmall 4"]
        for column, cost in enumerate(COSTS):
            axis = axes[2, column]
            series = data.cost_summary.loc[data.cost_summary.cost.eq(cost)].set_index("model").reindex(MODELS)
            axis.bar(positions, series[metric], width=.55, color=[COLOURS[m] for m in MODELS],
                yerr=series[half], capsize=4, error_kw={"ecolor": "#111111", "elinewidth": 1.1, "capthick": 1.1})
            for position, model in enumerate(MODELS):
                values = data.games.loc[data.games.cost.eq(cost) & data.games.model.eq(model)].sort_values("game_id")[metric]
                game_dots(axis, position, values, "#222222", .20, ROUND_DOT_AREA, .30)
            axis.set_xticks(positions, labels=labels)
            axis.set_xlim(-.6, len(MODELS)-.4)
        axes[2, 0].set_ylabel("Mean total\nrecorded penalty\nper agent", fontsize=ROUND_LABEL_SIZE, labelpad=12)
        finish_lines(figure)
        return figure


def make_cost_figure(data, dataset, family=FONT_FAMILY):
    """Cooperation above LOOK, with numeric monitoring cost on both x axes."""
    with mpl.rc_context({"font.family": family, "pdf.fonttype": 42, "ps.fonttype": 42}):
        figure = Figure(figsize=COST_FIGSIZE, dpi=150, facecolor="white")
        FigureCanvasAgg(figure)
        axes = figure.subplots(2, 1, sharex=True, sharey=True)
        figure.subplots_adjust(left=.105, right=.975, bottom=.10, top=.7853504273504274, hspace=.48)
        legend(figure, dataset, 20, .916, 2.3)
        lower, upper = rate_limits(data.cost_summary, ["cooperation_rate", "look_rate"])
        for axis, metric, title, ylabel in zip(axes, ("cooperation_rate", "look_rate"),
                ("(a) Cooperation", "(b) LOOK"), ("Cooperation rate", "LOOK rate")):
            axis_style(axis, 18, .8)
            axis.set_title(title, fontsize=28.8, fontweight="bold", pad=12)
            for model_index, model in enumerate(MODELS):
                series = data.cost_summary.loc[data.cost_summary.model.eq(model)].sort_values("cost")
                for cost in COSTS:
                    values = data.games.loc[data.games.model.eq(model) & data.games.cost.eq(cost)].sort_values("game_id")[metric]
                    game_dots(axis, cost+(model_index-1)*.01125, values, COLOURS[model], .03, COST_DOT_AREA, .32)
                axis.errorbar(series.cost, series[metric], yerr=series[f"ci95_half_width_{metric}"],
                    color=COLOURS[model], marker="o", markersize=5, linewidth=2.3, capsize=4,
                    elinewidth=1.2, zorder=4)
            span = upper-lower
            axis.set_ylim(lower-.03*span if lower < 0 else 0, upper+.04*span)
            axis.set_xlim(-.06, 1.06)
            axis.set_xticks(COSTS)
            axis.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
            axis.yaxis.set_major_locator(MultipleLocator(.2))
            axis.set_xlabel("Monitoring cost", fontsize=22, labelpad=9)
            axis.set_ylabel(ylabel, fontsize=22, labelpad=10)
            axis.tick_params(labelbottom=True)
        finish_lines(figure)
        return figure


def numerical_fingerprint(figure):
    """Stable across processes; object arrays are encoded as values, not addresses."""
    def numbers(values):
        return np.asarray(values, dtype=float).tolist()
    payload = []
    for axis in figure.axes:
        payload.append(dict(xlim=numbers(axis.get_xlim()), ylim=numbers(axis.get_ylim()),
            lines=[(numbers(line.get_xdata()), numbers(line.get_ydata())) for line in axis.lines],
            collections=[dict(offsets=numbers(c.get_offsets()),
                segments=[numbers(s) for s in c.get_segments()] if hasattr(c, "get_segments") else [])
                for c in axis.collections],
            bars=[numbers(p.get_bbox().bounds) for p in axis.patches if hasattr(p, "get_bbox")]))
    return hashlib.sha256(json.dumps(payload, sort_keys=True, allow_nan=False).encode()).hexdigest()


def save_figure(figure, output, dataset, kind, family=FONT_FAMILY, png=True):
    bounds = ROUND_BOUNDS if kind == "rounds" else COST_BOUNDS[dataset.key]
    path = Path(output)
    suffix = "rounds_and_penalty" if kind == "rounds" else "cooperation_and_look_by_cost"
    stem = f"{dataset.key}_{suffix}"
    fingerprint = numerical_fingerprint(figure)
    metadata = dict(Title=f"{dataset.label}: {suffix.replace('_', ' ')}",
        Subject="Neutral games; monitoring costs 0, 0.25, 0.5 and 1; independent-game 95% t confidence intervals",
        Creator="FairGameTrust publication plotting", CreationDate=None, ModDate=None)
    with mpl.rc_context({"font.family": family, "pdf.fonttype": 42, "ps.fonttype": 42}):
        for format_ in ("pdf", "png") if png else ("pdf",):
            buffer = io.BytesIO()
            options = {"metadata": metadata} if format_ == "pdf" else {"dpi": 120}
            figure.savefig(buffer, format=format_, bbox_inches=Bbox.from_bounds(*bounds), pad_inches=0, **options)
            atomic_write(path/f"{stem}.{format_}", buffer.getvalue())
    if numerical_fingerprint(figure) != fingerprint:
        raise AssertionError("Export changed numerical plot content")
    texts = [text for text in figure.findobj(match=Text) if text.get_visible() and text.get_text()]
    families = sorted({text.get_fontproperties().get_name() for text in texts})
    return dict(dataset=dataset.key, label=dataset.label, kind=kind, pdf=f"{stem}.pdf", axes=len(figure.axes),
        figure_inches=figure.get_size_inches().tolist(), export_bounds_inches=bounds,
        font_family=family, resolved_font_names=families, numerical_sha256=fingerprint,
        visible_text=[text.get_text() for text in texts],
        axes_positions=[list(axis.get_position().bounds) for axis in figure.axes],
        axis_label_sizes=[axis.xaxis.label.get_fontsize() for axis in figure.axes],
        tick_sizes=[axis.get_xticklabels()[0].get_fontsize() for axis in figure.axes],
        pdf_sha256=sha256(path/f"{stem}.pdf"))
