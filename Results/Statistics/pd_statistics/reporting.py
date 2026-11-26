"""Readable supplementary tables; CSVs retain full numerical precision."""

import pandas as pd

from .analyses import TABLES
from .settings import DATASETS


def number(value, precision=9):
    return "NA" if pd.isna(value) else f"{value:.{precision}g}"


def decision(value):
    return "NA" if pd.isna(value) else "Yes" if value else "No"


def table_title(table):
    analysis, first, second, outcome = TABLES[table]
    metric = {"cooperation_rate": "cooperation rate", "look_rate": "LOOK rate",
              "mean_total_penalty": "mean total recorded penalty"}[outcome]
    label = DATASETS[first].label
    if analysis == "cost":
        return f"{label}: {metric} between monitoring costs"
    if analysis == "penalty":
        return f"{label}: {metric} between models"
    if analysis == "early_late":
        return f"{label}: early versus late LOOK rate"
    return f"{label} versus {DATASETS[second].label}: {metric}"


def table_report(table, frame):
    analysis, dataset_key, _, _ = TABLES[table]
    dataset = DATASETS[dataset_key]
    # Cross-language tables use the shared labels printed in the ESM.
    labels = DATASETS["english_horizon_known"] if analysis == "language" else dataset
    lines = [f"# Table {table}: {table_title(table)}", "",
        f"Holm family: {len(frame)} planned comparisons; significance uses adjusted p < 0.05.", ""]
    if analysis == "early_late":
        lines += ["One-sided paired t-tests of late−early < 0. Early = rounds 2–5; late = rounds 6–10. "
                  "Both agents are combined within each independent game. Confidence intervals are pointwise, "
                  "two-sided 95% t intervals for the mean game difference, in percentage points. "
                  "Undefined tests remain NA and retain their planned Holm slots.", "",
            "| Model | Monitoring cost | Early mean (%) | Late mean (%) | Late−early (pp) | Pointwise 95% CI (pp) | Negative games | t(9) | One-sided p | Holm p (12) | Significant |",
            "|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---|"]
        for row in frame.itertuples():
            lines.append(f"| {dataset.model_label(row.model)} | {row.cost:g} | {100*row.mean_early:.2f} | "
                f"{100*row.mean_late:.2f} | {100*row.mean_difference:+.2f} | "
                f"[{100*row.ci95_lower:.2f}, {100*row.ci95_upper:.2f}] | {row.negative_games:g}/{row.n_games:g} | "
                f"{number(row.t_statistic)} | {number(row.p_value)} | {number(row.p_holm)} | {decision(row.significant)} |")
    else:
        lines += ["Two-sided asymptotic Mann–Whitney U tests with tie correction and continuity correction 0.5. "
                  "Each sample has ten independent games. Means are descriptive; these tests assess ranks/distributions. "
                  "U and rank-biserial effects refer to the first sample. Positive rank-biserial means higher-ranked "
                  "values in that sample.", ""]
        if analysis == "penalty":
            headers = ["Monitoring cost", "First model", "Second model", "Mean penalty first", "Mean penalty second"]
        elif analysis == "cost":
            headers = ["Model", "Cost pair", "Mean rate lower (%)", "Mean rate higher (%)"]
        else:
            headers = ["Model", "Monitoring cost", "Mean rate first (%)", "Mean rate second (%)", "First−second (pp)"]
        headers += ["U first", "Rank-biserial", "Raw p", f"Holm p ({len(frame)})", "Significant"]
        lines += ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"]*len(headers)) + "|"]
        for row in frame.itertuples():
            if analysis == "penalty":
                cells = [f"{row.cost:g}", dataset.model_label(row.model_first), dataset.model_label(row.model_second),
                         f"{row.mean_first:.2f}", f"{row.mean_second:.2f}"]
            elif analysis == "cost":
                cells = [dataset.model_label(row.model), f"{row.cost_first:g} vs {row.cost_second:g}",
                         f"{100*row.mean_first:.2f}", f"{100*row.mean_second:.2f}"]
            else:
                cells = [labels.model_label(row.model), f"{row.cost:g}",
                         f"{100*row.mean_first:.2f}", f"{100*row.mean_second:.2f}", f"{100*row.mean_difference:+.2f}"]
            cells += [f"{row.u_first:g}", f"{row.rank_biserial:+.3f}", number(row.p_value), number(row.p_holm),
                      decision(row.significant)]
            lines.append("| " + " | ".join(cells) + " |")
    lines += ["", f"[Full-precision CSV]({table}.csv)", ""]
    return "\n".join(lines)


def overview(results):
    lines = ["# Supplementary statistical results", "",
        "These are the 264 comparisons in Tables S1–S18 of the electronic supplementary material. "
        "All rates combine both agents within independent games. Overall rates include rounds 1–10; "
        "early/late tests compare rounds 2–5 with rounds 6–10. No other analyses are run.", "",
        "| Table | Analysis | Comparisons | Significant after Holm | Undefined tests |",
        "|---|---|---:|---:|---:|"]
    for table in TABLES:
        frame = results.loc[results.table_id.eq(table)]
        lines.append(f"| [{table}](tables/{table}.md) | {table_title(table)} | {len(frame)} | "
                     f"{int(frame.significant.fillna(False).sum())} | {int(frame.p_value.isna().sum())} |")
    lines += ["", "[All comparisons](all_tests.csv) · [Independent-game values](game_values.csv)", ""]
    return "\n".join(lines)
