# Publication plotting code

Generate the study's PDF figures from the game CSVs in `Results/`.
The code is standalone and uses the data alongside this folder.

| Dataset | Input directory, relative to `Results/` | Horizon |
|---|---|---|
| English - horizon known | `English/horizon_known` | Known |
| English - horizon unknown | `English/horizon_unknown` | Unknown |
| French | `French` | Known |
| Chinese | `Chinese` | Known |

Each dataset contains 120 neutral games: three LLMs × four monitoring costs ×
ten independent games. Included monitoring costs are **0, 0.25, 0.5 and 1**.

The raw model identifiers are preserved. Chinese retains the display label Mistral Small 2603; English and French use Mistral Small 4.

## Run

From the repository root:

```sh
python3 -m pip install -r Results/Plotting/requirements.txt
python3 Results/Plotting/plot_figures.py
```

Or, from this folder:

```sh
python3 plot_figures.py
```

The code uses Python 3.9 or later. Exact versions used for validation are
recorded in `TEST_RESULTS.md` and `output/manifest.json`. The dependency file
pins the tested numerical and rendering libraries.

**Times New Roman must be installed locally** to reproduce the figure typeface.
Font files are not distributed. The program reports an error if the font is
unavailable; it does not silently substitute another typeface. A locally
supplied font folder can be selected with `--font-directory`. An intentional
alternative can be selected explicitly, for example `--font-family "DejaVu Sans"`.

Examples:

```sh
python3 plot_figures.py --datasets french chinese
python3 plot_figures.py --datasets english_horizon_known
python3 plot_figures.py --data-root /path/to/Results --output-root /path/to/figures
python3 plot_figures.py --validate-only
python3 plot_figures.py --no-png
```

The default data root is the parent of this folder, so commands work from any
working directory. Game files are read only. The output folder must be separate
from the raw dataset directories.

## Figures and outputs

Each dataset produces two layouts:

1. **Cooperation, LOOK and penalty**: a 3 × 4 figure. The first row shows
   cooperation across rounds, the second LOOK across rounds, and the third
   mean total recorded penalty per agent over the full game. Columns are
   monitoring costs 0, 0.25, 0.5 and 1.
2. **Cooperation and LOOK by monitoring cost**: cooperation above LOOK in a
   vertically stacked figure, with one line per LLM.

`output/figures/` contains eight PDFs and their PNG previews. PDFs embed Times
New Roman and retain the established font sizes, colours, panel geometry and
individual-game dots. The rounds/penalty dots have area 28 pt² and opacity
0.30; cost-curve dots have area 24 pt² and opacity 0.32. Horizontal spreading
improves visibility without changing the vertical values. Axis labels use **rate** and
**Monitoring cost**.

`output/README.md` links to the generated PDFs. `output/publication_figures.zip`
contains the selected PDFs, their manifest and the figure index. PDF metadata
contains the dataset labels above; its dates are omitted for repeatable output.

`output/tables/<dataset>/` contains the exact plotted values:

- `round_level.csv`: the twenty agent/round decisions per game;
- `game_level.csv`: overall cooperation/LOOK rates and mean total penalties;
- `game_rounds.csv`: both agents combined within each game and round;
- `cost_summary.csv`: means, sample SDs and CI half-widths by model/cost;
- `round_summary.csv`: means, sample SDs and CI half-widths by model/cost/round.

`output/manifest.json` records the raw-file checksums, code checksums, resolved
font files, software versions, figure settings and PDF checksums. Input paths
are relative to `Results/`. The supplied `input_manifest.json` identifies the
480 files used for the publication figures. Hash mismatches stop normal export.
Use `--allow-input-changes` only when deliberately replacing the study data;
the numerical regression tests then need to be reviewed for that dataset.

## Definitions and confidence intervals

**Cooperation is OptionB**, including Chinese `选项B`; OptionA is defection.
LOOK rates use the recorded `LOOK`/`NO_LOOK` decisions, including when monitoring
cost is zero. All plots include **rounds 1–10**, including the first round.

One overall rate per game is the corresponding count over both agents divided
by **20 decisions**. Per-round rates first average the two agents within each
game. A game, rather than an agent or decision, is the independent sampling unit.

For penalties, sum each agent's ten recorded round penalties, then average the
two agent totals within the game. The bars average those game values. Recorded
penalties include the actual monitoring charges. Lower penalties are better.

Each error bar is a pointwise, two-sided **95% Student's t confidence interval**:

```text
mean ± t.ppf(0.975, n - 1) * sample_SD / sqrt(n)
```

Sample SD uses `ddof=1`; the data have **n=10 independent games** per model/cost
and **9 degrees of freedom**. Intervals are calculated from game-level values,
and are displayed without clipping to [0, 1]. They are not simultaneous or
adjusted for multiple comparisons. No hypothesis tests are performed.

## Input validation

The loader checks the language and horizon flags, neutral personalities,
complete ten-round games, model pairings, unique game identities, and ten games
in every model/cost cell. It reconciles every round's payoff and monitoring
charge with the recorded penalty. Saved LOOK counts, ratios and charge totals
are checked when supplied. Invalid actions, inconsistent scores, duplicate
games and missing model/cost cells raise explicit errors.

CSV files contain one game per row and are stored as:

```text
Results/
  English/
    horizon_known/<cost>/<model-folder>/results_Prisoner_dilemma_trust_<iteration>.csv
    horizon_unknown/<cost>/<model-folder>/results_Prisoner_dilemma_trust_<iteration>.csv
  French/<cost>/<model-folder>/results_Prisoner_dilemma_trust_<iteration>.csv
  Chinese/<cost>/<model-folder>/results_Prisoner_dilemma_trust_<iteration>.csv
  Plotting/
```

Model-folder spelling is not used to identify the LLM: the recorded model fields
are authoritative. Cost and iteration are read from the directory and filename.
The schema and calculations are implemented in `pd_figures/data.py` and
`pd_figures/statistics.py`; layouts and typography are in `pd_figures/plotting.py`.

## Tests

From the repository root:

```sh
python3 -m unittest discover -s Results/Plotting/tests -v
```

Or from this folder:

```sh
python3 -m unittest discover -s tests -v
```

The suite checks malformed data and payoff reconciliation, zero-cost LOOK,
independent-game aggregation, full-game penalty totals, t interval calculations,
all 480 publication game values, all model/cost and round summaries, plotted
means/error bars, fonts, layouts, individual-game dots and all eight preview
images against saved references. It also tests exact PDF repeatability and
runs a relocated copy with its own input files to ensure
there are no dependencies on other analysis scripts.

The checked reference tables and previews are in `tests/reference_data/` and
`tests/reference_figures/`. Integration tests use the raw files in the parent
`Results/` folder. For a different location, set `FAIRGAME_RESULTS_DATA_ROOT`.

This plotting component is part of FairGameTrust and uses the repository's
license; see `LICENSE`.
