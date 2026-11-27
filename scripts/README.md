# Scripts

This folder contains the Python code that produced every number and figure. You do not need to read it to follow the project. It is included so the work can be checked and reproduced.

## The main scripts

| Script | What it does |
|---|---|
| `track_hand.py` | The manual clicker. Opens a video and records the hand one frame at a time. Needs the source videos. |
| `analyze.py` | Fits the polynomials, computes derivatives, arc length, and RMSE for one or more tracks. |
| `pull_phase.py` | Restricts each clip to the pull window and refits it. |
| `summary_table.py` | Builds `outputs/prelim/summary_table.csv` and `outputs/prelim/comparisons.csv`. |
| `export_all_data.py` | Builds `data/all_points.csv` from the individual point files. |
| `make_report_figures.py` | Builds the five figures in `figures/`. |
| `check_duplicate_frames.py` | Counts repeated frames in each clip. Needs the videos. |
| `lane_rope_check.py` | Measures the lane rope and compares it with the cap scale. Needs the videos. |
| `proposal_doc.py` | Builds the submitted proposal. It is a record of how the proposal was made. |

## The development scripts

These are kept for transparency, not as part of the final pipeline.

| Script | Why it is not used |
|---|---|
| `development/auto_track.py` | Automatic tracking drifted when the hand crossed the splash or the body. The final data are manual clicks. |
| `development/body_relative.py` | A body-relative extension that subtracts the swimmer's travel. The final results use the fixed camera frame. |
| `development/calibrate.py` | An early calibration helper, superseded by the cap calibration in `data/`. |

## The order to run them

```bash
# Full-track fits
python scripts/analyze.py data/a2_hand_points_metres.csv data/a3_hand_points_metres.csv --labels A2 A3 --degree 3 --outdir outputs/prelim/a2_vs_a3
python scripts/analyze.py data/a2_hand_points_metres.csv data/dressel_hand_points_metres.csv --labels A2 Dressel --degree 3 --outdir outputs/prelim/a2_vs_dressel
python scripts/analyze.py data/a3_hand_points_metres.csv data/dressel_hand_points_metres.csv --labels A3 Dressel --degree 3 --outdir outputs/prelim/a3_vs_dressel

# Pull-phase fits and tables
python scripts/pull_phase.py
python scripts/summary_table.py
python scripts/export_all_data.py

# Figures
python scripts/make_report_figures.py
```

## What you need

- Python 3.
- The packages in `../requirements.txt`: NumPy, pandas, SciPy, matplotlib, OpenCV, and yt-dlp.
- The source videos only for `track_hand.py`, `check_duplicate_frames.py`, `lane_rope_check.py`, and the click-check panel of `make_report_figures.py`.

The fits and the result tables need only the committed coordinates, not the videos.

## One convention to know

The script argument `--degree` is the polynomial degree for the fit. The full-track fits use degree 3. The pull-phase fits use degree 2 for A2, because 9 points cannot support a confident cubic, and degree 3 for A3 and Dressel.
