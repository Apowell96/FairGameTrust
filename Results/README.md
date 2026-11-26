# Results

Raw game data, figures and statistical analyses for the FAIRGAME-Trust
Prisoner's Dilemma experiments. The plotting and statistics packages read
the CSV files in this directory directly; no LLM API access is needed to
analyse these data.

- [PDF figures](Plotting/output/README.md)
- [Statistical results and tables](Statistics/output/REPORT.md)
- [Plotting documentation](Plotting/README.md)
- [Statistics documentation](Statistics/README.md)

## Experimental conditions

| Dataset | Data directory | Game horizon | Independent games |
|---|---|---|---:|
| English - horizon known | `English/horizon_known/` | Known | 120 |
| English - horizon unknown | `English/horizon_unknown/` | Unknown | 120 |
| French | `French/` | Known | 120 |
| Chinese | `Chinese/` | Known | 120 |

Each dataset contains three models × four monitoring costs × ten independent
games, giving **480 games** in total. Each game has two agents using the same
LLM and lasts ten rounds. Agents have no assigned personality and do not
communicate. In the unknown-horizon condition, agents are not told the total
number of rounds; the recorded games still contain ten rounds.

Monitoring costs are **0, 0.25, 0.5 and 1**.

| Model | Recorded model identifier |
|---|---|
| Claude Sonnet 4.6 | `claude-sonnet-4-6` |
| GPT-4o | `gpt-4o` |
| Mistral Small 4 | `mistral-small-2603` |

Some Chinese output labels use **Mistral Small 2603** for the same recorded
Mistral identifier. Model identity is read from the CSV fields, independently
of the spelling or capitalisation of model-folder names.

## Directory layout

```text
Results/
├── English/
│   ├── horizon_known/<cost>/<model>/
│   └── horizon_unknown/<cost>/<model>/
├── French/<cost>/<model>/
├── Chinese/<cost>/<model>/
├── Plotting/
│   ├── plot_figures.py
│   ├── pd_figures/
│   ├── tests/
│   └── output/
│       ├── figures/        # PDFs and PNG previews
│       └── tables/         # Values used in the plots
└── Statistics/
    ├── run_statistics.py
    ├── pd_statistics/
    ├── tests/
    └── output/
        ├── REPORT.md      # Index of statistical tables
        ├── all_tests.csv
        ├── game_values.csv
        └── tables/        # Tables S1–S18 as CSV and Markdown
```

## Raw CSV files

Each `<cost>/<model>/` directory contains ten files named
`results_Prisoner_dilemma_trust_0.csv` through
`results_Prisoner_dilemma_trust_9.csv`. Each file contains one game row.

| Fields | Contents |
|---|---|
| `language`, `n_rounds_is_known`, `max_rounds`, `played_rounds` | Language and game-horizon metadata |
| `agent1_llm`, `agent2_llm` | Model identifiers |
| `agent1_personality`, `agent2_personality` | Personality settings, recorded as `none` |
| `agent1_strategies`, `agent2_strategies` | Strategic actions in round order |
| `agent1_scores`, `agent2_scores` | Recorded penalties in round order, including monitoring charges |
| `agent1_trust_actions`, `agent2_trust_actions` | `LOOK` or `NO_LOOK` decisions in round order |
| `agent1_trust_costs`, `agent2_trust_costs` | Monitoring charges incurred in each round |

Sequence fields contain ten entries stored as list strings. The monitoring
cost is identified by the enclosing cost directory. Additional columns record
agent metadata and summaries of monitoring decisions.

## Rates, penalties and confidence intervals

**Cooperation is OptionB**, including Chinese `选项B`; OptionA is defection.
LOOK rates use recorded monitoring decisions, including when monitoring
cost is zero.

The independent sampling unit is a **game**. Both agents are combined within
each game before calculating group means, confidence intervals or tests.

- Overall cooperation and LOOK rates use both agents across **rounds 1–10**:
  the corresponding count divided by 20 decisions.
- Per-round rates average the two agents within each game before averaging
  across the ten games.
- Total penalty is calculated by summing each agent's ten recorded penalties,
  then averaging the two agent totals within the game. Lower penalties are
  better. Monitoring charges are included.
- Early LOOK uses **rounds 2–5**, with eight decisions per game; late LOOK
  uses **rounds 6–10**, with ten decisions per game. Their paired difference
  is **late minus early**; negative values indicate reduced monitoring.

Figure error bars are pointwise, two-sided **95% Student's t confidence
intervals across ten independent games**, using sample SD with `ddof=1`
and nine degrees of freedom. They are not adjusted for multiple comparisons.
Dots show individual games.

## Generate the figures and statistics

Run these commands from the **repository root** in a Python environment
with the dependencies installed:

```sh
python3 -m pip install -r Results/Plotting/requirements.txt -r Results/Statistics/requirements.txt
python3 Results/Plotting/plot_figures.py
python3 Results/Statistics/run_statistics.py
```

Dependency versions are pinned in the two requirements files. The packages
have been tested with Python 3.9.6. Their input paths are resolved relative
to the package location, so the scripts can also be called from another
working directory. Raw game files are read only.

The figures use **Times New Roman**, which must be installed locally.
Font files are not included. See the [plotting documentation](Plotting/README.md)
for font options, dataset selection and alternative input/output paths.
Statistics do not require plotting libraries or fonts.

### Figures

Each dataset produces two PDFs, for eight PDFs in total:

1. A **3 × 4 figure**: cooperation across rounds in the first row, LOOK across
   rounds in the second, and mean total recorded penalty per agent in the
   third. Columns represent the four monitoring costs.
2. A **vertically stacked figure**: cooperation rate above LOOK rate, both
   against monitoring cost, with one line per model.

PDFs and PNG previews are in [Plotting/output/figures](Plotting/output/figures/).
The [figure index](Plotting/output/README.md) links to each PDF. CSV files
under `Plotting/output/tables/` contain the plotted observations and summaries.

### Statistical analyses

The statistics package generates **264 comparisons in Tables S1–S18**:

- Cooperation and LOOK rates between all six monitoring-cost pairs within
  each model and dataset, with Holm correction across 18 comparisons per
  dataset and outcome.
- Total penalties between models at each monitoring cost for
  English - horizon known, with Holm correction across 12 comparisons.
- Cooperation rates between known and unknown English horizons at each
  model/cost, with Holm correction across 12 comparisons.
- French versus English and Chinese versus English, using known horizons,
  at each model/cost for cooperation and LOOK. Holm correction covers
  12 comparisons separately for each language pair and outcome.
- Early versus late LOOK rates within each model/cost, with Holm correction
  across 12 groups separately for each dataset.

Independent-sample comparisons use **two-sided asymptotic Mann–Whitney U
tests**, with tie correction and a continuity correction of 0.5. These assess
ranks/distributions; reported means are descriptive. Results include U,
rank-biserial effect sizes, raw p-values and Holm-adjusted p-values.

Early–late comparisons use **one-sided paired t-tests** of whether the mean
within-game late-minus-early difference is negative. They include pointwise,
two-sided 95% confidence intervals and counts of games with negative
differences. Undefined tests remain NA. Statistical significance uses
**Holm-adjusted p < 0.05**.

See the [statistics documentation](Statistics/README.md) for the table mapping
and calculation details, or open the [results report](Statistics/output/REPORT.md).

## Run the tests

From the repository root:

```sh
python3 -m unittest discover -s Results/Plotting/tests -v
python3 -m unittest discover -s Results/Statistics/tests -v
```

## License

See the repository's [Apache 2.0 license](../LICENSE).
