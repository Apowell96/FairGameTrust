"""Aggregate agents within independent games before means and confidence intervals."""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import t


@dataclass
class PlotData:
    games: pd.DataFrame
    game_rounds: pd.DataFrame
    cost_summary: pd.DataFrame
    round_summary: pd.DataFrame


def ci95_half_width(sample_sd, n):
    sample_sd, n = np.asarray(sample_sd, dtype=float), np.asarray(n, dtype=float)
    if not np.isfinite(sample_sd).all() or not np.isfinite(n).all() or np.any(sample_sd < 0) or np.any(n < 2):
        raise ValueError("95% t intervals require finite nonnegative sample SDs and at least two independent games")
    return t.ppf(.975, n-1)*sample_sd/np.sqrt(n)


def summarize(frame, keys, metrics):
    grouped = frame.groupby(keys, sort=True)
    result = grouped.size().to_frame("games")
    for metric in metrics:
        result[metric] = grouped[metric].mean()
        result[f"sd_game_{metric}"] = grouped[metric].std(ddof=1)
        result[f"ci95_half_width_{metric}"] = ci95_half_width(result[f"sd_game_{metric}"], result.games)
    return result.reset_index()


def build_plot_data(rounds):
    keys = ["dataset", "model", "cost", "game_id", "iteration"]
    if rounds.duplicated(["game_id", "agent", "round"]).any():
        raise ValueError("Duplicate agent/round observations")
    counts = rounds.groupby("game_id").size()
    if not counts.eq(20).all():
        raise ValueError("Each independent game must contain twenty decisions")
    rates = rounds.groupby(keys, as_index=False).agg(cooperation_rate=("cooperated", "mean"),
                                                    look_rate=("looked", "mean"))
    agent_totals = rounds.groupby(keys+["agent"], as_index=False).recorded_penalty.sum()
    totals = agent_totals.groupby(keys, as_index=False).recorded_penalty.mean().rename(
        columns={"recorded_penalty": "mean_total_penalty"})
    games = rates.merge(totals, on=keys, validate="one_to_one")
    game_rounds = rounds.groupby(keys+["round"], as_index=False).agg(
        cooperation_rate=("cooperated", "mean"), look_rate=("looked", "mean"))
    cost_summary = summarize(games, ["dataset", "model", "cost"],
                             ["cooperation_rate", "look_rate", "mean_total_penalty"])
    round_summary = summarize(game_rounds, ["dataset", "model", "cost", "round"],
                              ["cooperation_rate", "look_rate"])
    return PlotData(games, game_rounds, cost_summary, round_summary)
