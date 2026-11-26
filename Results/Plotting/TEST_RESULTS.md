# Plotting validation

Validated on 26 November 2026 using the raw files in the repository's
`Results/` directory.

**28 tests passed.** All 480 input games were validated: 120 each for
English - horizon known, English - horizon unknown, French and Chinese.
Each dataset has three models, four monitoring costs and ten independent
games per model/cost cell.

## Reproduce

From the repository root:

```sh
python3 -m unittest discover -s Results/Plotting/tests -v
python3 Results/Plotting/plot_figures.py
```

## Checks completed

- All 480 game-level cooperation rates, LOOK rates and total penalties
  reproduce the saved reference values within floating-point tolerance.
- Every cost-level and round-level mean, sample SD and 95% t interval
  reproduces the reference calculations.
- CIs use ten independent games after combining both agents, with
  `ddof=1` and nine degrees of freedom. First-round decisions are included.
- Plotted curves, CI endpoints and penalty bars match their exported tables.
- All eight layouts retain the reference geometry, font sizes, Times New
  Roman, individual-game dot sizes and opacity, and axis labels.
- All eight PNG previews match the reference figures. Six are pixel-identical;
  the other two differ at fewer than 0.001% of pixels, by negligible rounding
  in error-bar rendering. The automated test allows less than 0.1% changed
  pixels and a mean absolute channel difference below 0.01 on a 0–255 scale.
- PDF output embeds TrueType Times New Roman. Exporting an unchanged figure
  twice produces the same PDF checksum; date metadata is omitted.
- Malformed inputs, inconsistent payoffs/charges, duplicate games and missing
  model/cost cells are rejected. Free LOOK decisions are counted correctly.
- Missing fonts fail explicitly. Validation alone needs no font and writes
  no output files.
- A relocated copy runs from its new parent `Results/` directory with no
  dependencies on other plotting or analysis scripts. Modified raw-file
  checksums are detected.
- Raw input SHA-256 checksums are checked again after figure generation.

## Environment

| Component | Version |
|---|---|
| Python | 3.9.6 |
| NumPy | 2.0.2 |
| pandas | 2.2.3 |
| SciPy | 1.13.1 |
| Matplotlib | 3.9.4 |
| Pillow | 11.2.1 |
| Font | Times New Roman, normal and bold |

The complete input, code, font and PDF checksums are in
[`output/manifest.json`](output/manifest.json). Figures and their underlying
tables are in `output/`. No statistical hypothesis tests are part of this
plotting package.
