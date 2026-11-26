# Test results

Tested on **26 November 2026** using the raw game CSVs in `Results/`.

**23 tests passed.**

The suite covers:

- Valid actions and metadata, complete games, payoff and charge consistency,
  duplicate games, model/cost group sizes and exclusion of cost 0.75.
- Combining both agents within each independent game, rate denominators,
  early/late round windows and full-game penalty aggregation.
- U statistics, tied values and rank-biserial direction on small examples.
- The paired t statistic, lower one-sided tail and two-sided confidence interval.
- Holm step-down adjustment and retention of undefined planned slots.
- Undefined tests for constant paired differences.
- Planned analysis families and valid output structure.
- Validation-only execution without writing outputs.
- Command-line execution after relocation and acceptance of valid input updates.
- Raw input files remaining unchanged during analysis.

Environment: Python 3.9.6, NumPy 2.0.2, pandas 2.2.3 and SciPy 1.13.1.

From the repository root:

```sh
python3 Results/Statistics/run_statistics.py
python3 -m unittest discover -s Results/Statistics/tests -v
```
