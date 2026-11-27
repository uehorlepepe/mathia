# Outputs

This folder contains the fitted curves, the result tables, the checks, and the submitted proposal. The numeric files are committed. The generated plots are not, because they are large and can be rebuilt.

## Start here

- `prelim/summary_table.csv`: every fit result for every clip and both windows. This is the main table.
- `prelim/comparisons.csv`: the pairwise RMSE table.

## What is in each folder

| Path | What it contains |
|---|---|
| `prelim/summary_table.csv` | R², RMSE, arc length, speed, scale, and uncertainty for every fit. |
| `prelim/comparisons.csv` | The pairwise RMSE table. |
| `prelim/pull_phase/` | The pull-phase fits, the cross-model table, and the own-fit table. |
| `prelim/a2_vs_a3/` | The full-track fits and summary for A2 against A3. |
| `prelim/a2_vs_dressel/` | The full-track fits and summary for A2 against Dressel. |
| `prelim/a3_vs_dressel/` | The full-track fits and summary for A3 against Dressel. |
| `check/` | The repeated-frame counts and the lane-rope cross-check. |
| `submission/` | The proposal I submitted, plus the HTML that produced it. |

## The CSV files

| File | What it holds |
|---|---|
| `summary_table.csv` | One row per clip per window. Columns include `r2_fit_own_track`, `r2_his_model_on_mine_scaled`, `size_factor_k`, `arc_length_m`, `arc_pm_m`, `mean_speed_m_s`, and `max_speed_m_s`. |
| `comparisons.csv` | One row per pair. Columns are `position_rmse_m`, `mean_diff_m`, `max_diff_m`, and `arc_length_difference_m`. |
| `pull_phase/*_pull_phase.csv` | The fitted pull-phase curve for one clip: time `t`, forward `x_m`, and vertical `y_m`. |

## What is not committed

The plots inside `prelim/` and `check/` are generated images. They are ignored by git because they are large and can be rebuilt with `scripts/make_report_figures.py` or the analysis scripts. The numeric results are the record.

## The submitted proposal

`submission/IA_Exploration_Proposal_Yifan_Wang.pdf` is the proposal I submitted. It is kept as a historical record of the planning stage. The final results in the README supersede the early numbers in the proposal where they differ.

The five main figures are in the top-level `figures/` folder, not here, so they display on the repository front page.
