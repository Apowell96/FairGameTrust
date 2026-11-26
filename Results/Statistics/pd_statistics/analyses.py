"""Independent-game aggregation and only the tests used in Tables S1–S18."""

from itertools import combinations
import json

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, t, ttest_rel

from .settings import COSTS, MODELS


def holm_adjust(p_values):
    """Holm step-down adjustment; undefined tests retain their planned slots."""
    p = np.asarray(p_values, dtype=float)
    if p.ndim != 1 or np.isinf(p).any() or np.any((p < 0) | (p > 1)):
        raise ValueError("Expected a one-dimensional array of p-values in [0, 1] or NaN")
    valid = np.isfinite(p)
    working = np.where(valid, p, 1.)
    order = np.argsort(working, kind="stable")
    adjusted = np.empty_like(p)
    adjusted[order] = np.minimum(1., np.maximum.accumulate(working[order] * np.arange(len(p), 0, -1)))
    adjusted[~valid] = np.nan
    return adjusted


def game_values(rounds):
    """Combine both agents before inference; one row per independent game."""
    keys = ["dataset", "model", "cost", "game_id", "iteration"]
    if rounds.duplicated(["game_id", "agent", "round"]).any():
        raise ValueError("Duplicate agent/round observations")
    records = []
    for _, group in rounds.groupby(keys, sort=True):
        if len(group) != 20 or set(group["round"]) != set(range(1, 11)):
            raise ValueError("Expected twenty decisions per complete ten-round game")
        if set(group.agent) != {"agent1", "agent2"}:
            raise ValueError("Expected two agents per game")
        early = group.loc[group["round"].between(2, 5), "looked"]
        late = group.loc[group["round"].between(6, 10), "looked"]
        if len(early) != 8 or len(late) != 10:
            raise ValueError("Expected eight early and ten late decisions")
        row = group.iloc[0][keys].to_dict()
        records.append(dict(**row, source_file=group.source_file.iloc[0], decisions=20,
            cooperation_count=int(group.cooperated.sum()), look_count=int(group.looked.sum()),
            cooperation_rate=group.cooperated.mean(), look_rate=group.looked.mean(),
            mean_total_penalty=group.groupby("agent").recorded_penalty.sum().mean(),
            early_look_count=int(early.sum()), early_decisions=8, early_look_rate=early.mean(),
            late_look_count=int(late.sum()), late_decisions=10, late_look_rate=late.mean(),
            late_minus_early=late.mean()-early.mean()))
    return pd.DataFrame(records)


def mann_whitney(first, second):
    """Two-sided, tie-corrected normal approximation, continuity correction 0.5."""
    x, y = np.asarray(first, dtype=float), np.asarray(second, dtype=float)
    if x.ndim != 1 or y.ndim != 1 or not len(x) or not len(y) or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("Expected two nonempty finite one-dimensional samples")
    fit = mannwhitneyu(x, y, alternative="two-sided", method="asymptotic", use_continuity=True)
    u = float(fit.statistic)
    probability = u / (len(x)*len(y))
    return dict(n_first=len(x), n_second=len(y), mean_first=x.mean(), mean_second=y.mean(),
        mean_difference=x.mean()-y.mean(), median_first=float(np.median(x)), median_second=float(np.median(y)),
        u_first=u, u_second=len(x)*len(y)-u, rank_biserial=2*probability-1,
        probability_first_higher_half_ties=probability, p_value=float(fit.pvalue),
        method="asymptotic", alternative="two-sided", use_continuity=True, paired=False)


def paired_early_late(early, late):
    """One-sided paired t-test of late−early < 0; pointwise two-sided 95% CI."""
    early, late = np.asarray(early, dtype=float), np.asarray(late, dtype=float)
    if early.ndim != 1 or late.shape != early.shape or len(early) < 2 or not np.isfinite(early).all() or not np.isfinite(late).all():
        raise ValueError("Expected matching finite early/late samples with at least two games")
    differences = late-early
    differences[np.abs(differences) < 1e-12] = 0.
    n = len(differences)
    mean, sd = differences.mean(), differences.std(ddof=1)
    se = sd/np.sqrt(n)
    half = t.ppf(.975, n-1)*se
    if se > 1e-12:
        fit = ttest_rel(late, early, alternative="less")
        statistic, p_value, status = float(fit.statistic), float(fit.pvalue), "estimated"
    else:
        statistic, p_value, status = np.nan, np.nan, "constant_differences"
    return dict(n_games=n, df=n-1, mean_early=early.mean(), mean_late=late.mean(),
        mean_difference=mean, sd_difference=sd, se_difference=se,
        ci95_lower=mean-half, ci95_upper=mean+half,
        negative_games=int(np.sum(differences < 0)), zero_games=int(np.sum(differences == 0)),
        positive_games=int(np.sum(differences > 0)), t_statistic=statistic, p_value=p_value,
        test_status=status, alternative="less", paired=True,
        early_game_rates=json.dumps(early.tolist()), late_game_rates=json.dumps(late.tolist()),
        game_differences=json.dumps(differences.tolist()))


# One family per table: these are exactly the statistical tables in ESM.pdf.
TABLES = {
    "S1": ("penalty", "english_horizon_known", None, "mean_total_penalty"),
    "S2": ("cost", "english_horizon_known", None, "cooperation_rate"),
    "S3": ("cost", "english_horizon_known", None, "look_rate"),
    "S4": ("early_late", "english_horizon_known", None, "look_rate"),
    "S5": ("cost", "english_horizon_unknown", None, "cooperation_rate"),
    "S6": ("cost", "english_horizon_unknown", None, "look_rate"),
    "S7": ("horizon", "english_horizon_known", "english_horizon_unknown", "cooperation_rate"),
    "S8": ("early_late", "english_horizon_unknown", None, "look_rate"),
    "S9": ("cost", "french", None, "cooperation_rate"),
    "S10": ("language", "french", "english_horizon_known", "cooperation_rate"),
    "S11": ("cost", "french", None, "look_rate"),
    "S12": ("language", "french", "english_horizon_known", "look_rate"),
    "S13": ("early_late", "french", None, "look_rate"),
    "S14": ("cost", "chinese", None, "cooperation_rate"),
    "S15": ("language", "chinese", "english_horizon_known", "cooperation_rate"),
    "S16": ("cost", "chinese", None, "look_rate"),
    "S17": ("language", "chinese", "english_horizon_known", "look_rate"),
    "S18": ("early_late", "chinese", None, "look_rate"),
}


def row_identifier(table, model, cost, second_model=None, second_cost=None):
    result = f"{table}/{model}/{cost:g}"
    if second_model is not None:
        result += f"/{second_model}"
    if second_cost is not None:
        result += f"/{second_cost:g}"
    return result


def sample(games, dataset, model, cost):
    result = games.loc[games.dataset.eq(dataset) & games.model.eq(model) & games.cost.eq(cost)].sort_values("game_id")
    if len(result) != 10 or result.game_id.nunique() != 10:
        raise ValueError(f"Expected ten independent games: {dataset}, {model}, {cost:g}")
    return result


def compare_samples(table, games, first_dataset, second_dataset, first_model, second_model,
                    first_cost, second_cost, outcome, analysis):
    first = sample(games, first_dataset, first_model, first_cost)
    second = sample(games, second_dataset, second_model, second_cost)
    return dict(table_id=table, analysis=analysis, outcome=outcome,
        dataset_first=first_dataset, dataset_second=second_dataset,
        model=first_model, model_first=first_model, model_second=second_model,
        cost=first_cost, cost_first=first_cost, cost_second=second_cost,
        row_id=row_identifier(table, first_model, first_cost,
            second_model if analysis == "penalty" else None,
            second_cost if analysis == "cost" else None),
        first_game_ids=json.dumps(first.game_id.tolist()), second_game_ids=json.dumps(second.game_id.tolist()),
        first_game_values=json.dumps(first[outcome].tolist()), second_game_values=json.dumps(second[outcome].tolist()),
        **mann_whitney(first[outcome], second[outcome]))


def run_analyses(games):
    """Return 264 comparisons in 18 separate, planned Holm families."""
    all_tables = []
    for table, (analysis, first_dataset, second_dataset, outcome) in TABLES.items():
        rows = []
        if analysis == "penalty":
            for cost in COSTS:
                for first_model, second_model in combinations(MODELS, 2):
                    rows.append(compare_samples(table, games, first_dataset, first_dataset,
                        first_model, second_model, cost, cost, outcome, analysis))
        elif analysis == "cost":
            for model in MODELS:
                for lower, higher in combinations(COSTS, 2):
                    rows.append(compare_samples(table, games, first_dataset, first_dataset,
                        model, model, lower, higher, outcome, analysis))
        elif analysis in ("horizon", "language"):
            for model in MODELS:
                for cost in COSTS:
                    rows.append(compare_samples(table, games, first_dataset, second_dataset,
                        model, model, cost, cost, outcome, analysis))
        else:
            for model in MODELS:
                for cost in COSTS:
                    group = sample(games, first_dataset, model, cost)
                    rows.append(dict(table_id=table, analysis=analysis, outcome=outcome,
                        dataset_first=first_dataset, dataset_second=first_dataset, model=model,
                        model_first=model, model_second=model, cost=cost, cost_first=cost, cost_second=cost,
                        row_id=row_identifier(table, model, cost), game_ids=json.dumps(group.game_id.tolist()),
                        **paired_early_late(group.early_look_rate, group.late_look_rate)))
        frame = pd.DataFrame(rows)
        family_size = 18 if analysis == "cost" else 12
        if len(frame) != family_size:
            raise AssertionError("Unexpected Holm family size")
        frame["p_holm"] = holm_adjust(frame.p_value)
        frame["holm_family_size"] = family_size
        frame["significant"] = pd.array(
            [None if pd.isna(p) else p < .05 for p in frame.p_holm], dtype="boolean")
        frame["alpha"] = .05
        all_tables.append(frame)
    results = pd.concat(all_tables, ignore_index=True)
    if len(results) != 264 or not results.row_id.is_unique:
        raise AssertionError("Expected 264 unique ESM comparisons")
    return results
