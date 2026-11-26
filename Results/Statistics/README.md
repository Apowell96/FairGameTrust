# Statistical analyses

Statistical analysis, using the raw game
CSVs in the parent `Results/` directory. 

The four datasets are **English - horizon known**, **English - horizon unknown**,
**French** and **Chinese**. French and Chinese games have known horizons.
Monitoring costs are **0, 0.25, 0.5 and 1**.

## Run

From the repository root:

```sh
python3 -m pip install -r Results/Statistics/requirements.txt
python3 Results/Statistics/run_statistics.py
python3 -m unittest discover -s Results/Statistics/tests -v
```

Or from this folder:

```sh
python3 run_statistics.py
python3 -m unittest discover -s tests -v
```

Python 3.9.6 and the pinned dependency versions were used for validation.
Input and output paths are resolved relative to this package, so commands
work from any working directory. No plotting libraries or fonts are required.

To select different paths:

```sh
python3 run_statistics.py --data-root /path/to/Results --output-root /path/to/output
python3 run_statistics.py --validate-only
```

Raw files are read only. Valid input updates are accepted; metadata, game
structure, actions, payoffs and monitoring charges are checked for consistency.

## Included tables and correction families

Each table is its own Holm family. Comparisons remain within one model and
monitoring cost unless those variables define the comparison itself.

| ESM table | Comparison | Holm family size |
|---|---|---:|
| S1 | English - horizon known: penalties between models at each cost | 12 |
| S2, S3 | English - horizon known: cooperation and LOOK between all cost pairs | 18 each |
| S4 | English - horizon known: early versus late LOOK | 12 |
| S5, S6 | English - horizon unknown: cooperation and LOOK between all cost pairs | 18 each |
| S7 | English: cooperation between known and unknown horizons at each model/cost | 12 |
| S8 | English - horizon unknown: early versus late LOOK | 12 |
| S9, S11 | French: cooperation and LOOK between all cost pairs | 18 each |
| S10, S12 | French versus English - horizon known: cooperation and LOOK | 12 each |
| S13 | French: early versus late LOOK | 12 |
| S14, S16 | Chinese: cooperation and LOOK between all cost pairs | 18 each |
| S15, S17 | Chinese versus English - horizon known: cooperation and LOOK | 12 each |
| S18 | Chinese: early versus late LOOK | 12 |


## Independent-game observations

Both agents are combined **within each game before inference**. Each
model/cost/dataset has ten independent games.

- **Overall cooperation:** OptionB count / 20 decisions, across both agents
  and rounds 1–10. Chinese `选项B` is the same cooperative action.
- **Overall LOOK:** recorded LOOK count / 20 decisions, including round 1
  and decisions made when monitoring is free.
- **Penalty:** sum each agent's ten recorded penalties, including actual
  monitoring charges, then average the two agent totals within the game.
  Lower penalties are better.
- **Early LOOK:** LOOK count across both agents in rounds 2–5 / 8 decisions.
- **Late LOOK:** LOOK count across both agents in rounds 6–10 / 10 decisions.
- **Paired difference:** late minus early within each game. A negative
  difference indicates reduced monitoring.

`pd_statistics/data.py` validates actions, neutral personalities, language and
horizon flags, complete games, model pairings, payoffs, monitoring charges,
unique game identities and ten games per model/cost cell. Model names are read
from CSV contents; model-folder spelling is not used to identify the LLM.
Raw identifiers are preserved. Chinese cost and early–late tables use
Mistral Small 2603; the other tables use Mistral Small 4.

## Statistical methods

**Mann–Whitney U:** `scipy.stats.mannwhitneyu(first, second,
alternative="two-sided", method="asymptotic", use_continuity=True)`.
This uses the tie-corrected normal approximation and continuity correction
0.5. Samples are unpaired, with ten independent games per sample. Matching
iteration numbers across conditions do not create pairs.

The tests assess ranks/distributions; reported means and their differences
are descriptive. The first sample is the lower monitoring cost, the first
listed model, the known English horizon, or French/Chinese respectively.
`U_first` refers to that sample. Rank-biserial effect is
`2 * U_first / (n_first * n_second) - 1`; positive means higher-ranked values
in the first sample. `U_first/(n_first*n_second)` gives half weight to ties.

**Early–late LOOK:** `scipy.stats.ttest_rel(late, early, alternative="less")`.
This is a one-sided paired t-test of a decrease, with ten independent
within-game differences and nine degrees of freedom:

```text
H0: population mean(late − early) ≥ 0
H1: population mean(late − early) < 0
```

The pointwise, two-sided 95% CI for the mean difference is:

```text
mean_difference ± t.ppf(0.975, 9) * sample_SD(differences) / sqrt(10)
```

Sample SD uses `ddof=1`. Intervals are not adjusted for multiplicity. Constant
paired differences have undefined tests and remain NA. Their observed CI bounds are descriptive and do not establish zero population uncertainty. Negative-game counts refer to **late−early differences**,
not round-by-round slopes.

**Holm correction:** the step-down adjustment is applied separately to each
table's planned family. Undefined p-values use internal p=1 placeholders to
retain their slots; outputs remain NA. Significance uses adjusted **p < 0.05**.
Each language comparison and outcome has its own 12-test family.

## Outputs

- `output/REPORT.md`: index and significant/undefined counts by ESM table.
- `output/tables/S1.csv` … `S18.csv`: full-precision results, sample values,
  game identifiers, test settings and Holm family sizes.
- `output/tables/S1.md` … `S18.md`: readable tables using ESM numbering.
- `output/all_tests.csv`: all 264 comparisons.
- `output/game_values.csv`: all 480 independent game observations, rates,
  penalties, early/late values, counts and raw-file provenance.
- `output/manifest.json`: input and code fingerprints for the current run,
  method settings and software versions.

## Code organisation and tests

`run_statistics.py` starts `pd_statistics/cli.py`. `data.py` reads and validates
raw games; `analyses.py` performs aggregation, the two test types and Holm;
`reporting.py` formats tables. All file writes use `io.py`.

Tests check aggregation and denominators, one-sided tails, tie handling,
effect direction, planned Holm families, undefined tests, input consistency
and command-line execution after relocation. Valid data updates are also
checked. See `TEST_RESULTS.md` for the test record.

This component is part of FairGameTrust; see `LICENSE`.
