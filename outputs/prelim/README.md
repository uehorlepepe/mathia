# Preliminary and final fits

This folder holds the result tables and the fitted curves. The headline comparison is the pull phase; the full-track fits are a check on the whole visible movement.

## The main tables

| File | What it contains |
|---|---|
| `summary_table.csv` | One row per clip per window, with R², RMSE, arc length, speed, scale, and uncertainty. |
| `comparisons.csv` | The pairwise RMSE table. |
| `pull_phase/pull_phase_own_fits.csv` | The pull-phase fit quality for each clip on its own points. |
| `pull_phase/pull_phase_cross_model.csv` | Each clip's model applied to the other clips, with the scale factor. |
| `pull_phase/pull_phase_summary.json` | The pull-phase results in a single JSON record. |

## The fitted curves

`pull_phase/a2_pull_phase.csv`, `a3_pull_phase.csv`, and `dressel_pull_phase.csv` each hold the fitted curve for one clip: time `t`, forward position `x_m`, and vertical position `y_m`. They are sampled on a fine grid, so the curve is smooth when plotted.

## The full-track fits

The folders `a2_vs_a3/`, `a2_vs_dressel/`, and `a3_vs_dressel/` hold the full-track fits from `scripts/analyze.py`. Each contains the fitted coefficients, the residuals, and a summary. These are a check on the whole movement, including recovery. They are not the headline comparison.

## The columns in `summary_table.csv`

| Column | Meaning |
|---|---|
| `track` | `A2`, `A3`, or `Dressel`. |
| `window` | `full_track` or `pull_phase`. |
| `frames`, `n_points`, `duration_s` | The window and its size. |
| `degree` | The polynomial degree used. |
| `r2_fit_own_track` | R² of the clip's own fit. |
| `r2_his_model_on_mine` | R² of the other clip's model on this clip, raw. |
| `r2_his_model_on_mine_scaled` | The same after one size factor. This is the shape score. |
| `size_factor_k` | The number that multiplies the other path to match this one. |
| `r2_his_model_on_mine_rotated`, `rotation_deg` | The rotation check. |
| `fit_rmse_mm` | The typical distance between the fit and the clicks, in millimetres. |
| `arc_length_m`, `arc_pm_m` | The path length and its calibration uncertainty. |
| `mean_speed_m_s`, `max_speed_m_s` | Hand speed. For Dressel these are nominal. |
| `cap_width_px`, `m_per_px`, `scale_unc_pct` | The calibration. |
| `time_base` | Whether the clip is real time or slowed. |

## How to rebuild these files

```bash
python scripts/analyze.py data/a2_hand_points_metres.csv data/a3_hand_points_metres.csv --labels A2 A3 --degree 3 --outdir outputs/prelim/a2_vs_a3
python scripts/pull_phase.py
python scripts/summary_table.py
```

The full command list is in the top-level README.
