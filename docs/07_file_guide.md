# 7. File guide

This page explains what every file in the repository is for. You can read the project without opening any of them, but this page is here in case you want to check a number or reuse a file.

## The top level

| Path | What it is |
|---|---|
| `README.md` | The front door. Question, short answer, data, method, results, limits, and links. |
| `data/` | The digitised points, the calibration, and the combined spreadsheet. |
| `docs/` | The long version, one page per topic, from question to sources. |
| `figures/` | The five figures used in the README and the results. |
| `outputs/` | The fitted curves, the result tables, the checks, and the submitted proposal. |
| `scripts/` | The Python code that produced every number. Not needed to read the project. |
| `requirements.txt` | The Python packages needed to rerun the analysis. |

## `data/`

The data folder contains the hand positions. The videos themselves are **not** included, because they are large and because the elite footage is not mine to redistribute.

| File | What it contains |
|---|---|
| `a2_hand_manual.csv` | The raw A2 clicks: frame number, time, and pixel coordinates. |
| `a3_hand_manual.csv` | The raw A3 clicks. |
| `dressel_hand_manual.csv` | The raw Dressel clicks. |
| `a2_hand_points_metres.csv` | A2 converted to metres, with the first point at the origin. |
| `a3_hand_points_metres.csv` | A3 converted to metres. |
| `dressel_hand_points_metres.csv` | Dressel converted to metres. |
| `a2.calibration_cap.json` | A2 cap width, scale, uncertainty, and the lane-rope cross-check. |
| `a3.calibration_cap.json` | A3 cap width, scale, uncertainty, and the lane-rope cross-check. |
| `dressel.calibration_cap.json` | Dressel cap width, scale, uncertainty, and the lane-rope cross-check. |
| `all_points.csv` | All 66 points in one flat table, with a label, the video name, the scale, and a pull-window flag. This is the easiest file to open in Excel. |
| `*.csv.meta.json` | A short note recording where each raw click file came from and how it was produced. |

### The columns in the CSV files

The raw `*_hand_manual.csv` files contain `frame`, `t`, `x_px`, and `y_px`. The converted `*_hand_points_metres.csv` files add `x_m` and `y_m`.

| Column | Meaning |
|---|---|
| `frame` | The video frame number. |
| `t` | The time stamp in seconds. For Dressel this is the nominal 60 fps time, not physical time. |
| `x_px`, `y_px` | The click in image coordinates. The origin is the top left of the frame. |
| `x_m`, `y_m` | The position in metres, with the first click at the origin and upward positive. |

`all_points.csv` adds:

| Column | Meaning |
|---|---|
| `swimmer` | `Yifan A2`, `Yifan A3`, or `Caeleb Dressel`. |
| `clip` | `a2`, `a3`, or `dressel`. |
| `video` | The source file name. |
| `t_s` | The time in seconds. This is the name used in `all_points.csv` instead of `t`. |
| `m_per_px` | The scale used to convert pixels to metres. |
| `scale_unc_pct` | The calibration uncertainty in percent. |
| `time_base` | `real time` or the slowed-footage note. |
| `in_pull_window` | `1` if the point is inside the pull, `0` if it is recovery. |

## `docs/`

| File | What it covers |
|---|---|
| `01_question.md` | The question, the aim, what success looks like, and why the topic matters to me. |
| `02_data.md` | The three clips, the manual clicks, repeated frames, calibration, and the lane-rope check. |
| `03_method.md` | The full mathematics: parametric curves, polynomial fits, derivatives, arc length, RMSE, scale factor, and uncertainty. |
| `04_results.md` | Every result table, including the full-track fits, the pull-phase fits, the pairwise comparisons, and the rotation check. |
| `05_limitations.md` | The ten main limits and what each one means for the conclusion. |
| `06_glossary.md` | Plain-language definitions of every technical term. |
| `07_file_guide.md` | This page. |
| `08_sources.md` | The video sources, the calibration reference, the software, and the honesty notes. |

## `figures/`

| File | What it shows |
|---|---|
| `fig1_workflow.png` | The six steps from video to comparison. |
| `fig2_video_to_path.png` | One clip turned into a parametric path, step by step. |
| `fig3_three_pulls.png` | The three pull paths at the same physical scale. This is the headline figure. |
| `fig4_comparison.png` | The typical gap and the shape score for A2 and A3 against Dressel. |
| `fig5_click_checks.png` | The clicked points drawn on one frame of each clip, as a check that the clicks landed on the hand. |

## `outputs/`

| Path | What it contains |
|---|---|
| `prelim/summary_table.csv` | Every fit result for every clip and both windows: R², RMSE, arc length, speed, scale, and uncertainty. |
| `prelim/comparisons.csv` | The pairwise RMSE table. |
| `prelim/pull_phase/` | The pull-phase fits, the cross-model table, and the own-fit table. |
| `prelim/a2_vs_a3/`, `a2_vs_dressel/`, `a3_vs_dressel/` | The full-track fits and summaries for each pair. |
| `check/duplicate_frames_*.json` | How many frames repeat in each clip and what the effective picture rate is. |
| `check/lane_rope_check.json` | The lane-rope cross-check that shows why the rope is not the scale. |
| `submission/IA_Exploration_Proposal_Yifan_Wang.pdf` | The proposal I submitted. It is kept as a historical record. |

The plots inside `outputs/` are generated images. They are not committed to git, because they are large and can be rebuilt. The numeric files (`.csv`, `.json`) are committed so the results can be checked without the videos.

## `scripts/`

| File | What it does | Needed to reproduce the results? |
|---|---|---|
| `track_hand.py` | The manual clicker. Opens a video and records the hand position one frame at a time. | Only if you have the source videos. |
| `analyze.py` | Fits the polynomials, computes derivatives, arc length, and RMSE for one or more tracks. | Yes, for the full-track fits. |
| `pull_phase.py` | Restricts each clip to the pull window and refits it. | Yes. |
| `summary_table.py` | Builds `summary_table.csv` and `comparisons.csv` from the fits. | Yes. |
| `export_all_data.py` | Builds `data/all_points.csv` from the individual point files. | Yes. |
| `make_report_figures.py` | Builds the five figures in `figures/`. | Yes, if you want to regenerate the figures. |
| `check_duplicate_frames.py` | Counts repeated frames in each clip. | Only with the videos. |
| `lane_rope_check.py` | Measures the lane rope and compares it with the cap scale. | Only with the videos. |
| `proposal_doc.py` | Builds the submitted proposal. | No. It is a record of how the proposal was made. |
| `development/auto_track.py` | The automatic tracker tried before the manual clicks. It drifted, so it is not used. | No. |
| `development/body_relative.py` | A body-relative extension that subtracts the swimmer's travel. | No. It is a possible extension. |
| `development/calibrate.py` | An early calibration helper. | No. |

### How the scripts connect

```
raw clicks (data/*_hand_manual.csv)
        |
        v
calibration + pixels to metres (data/*_hand_points_metres.csv)
        |
        v
analyze.py  ->  full-track fits (outputs/prelim/*_vs_*)
        |
pull_phase.py  ->  pull-phase fits (outputs/prelim/pull_phase)
        |
summary_table.py  ->  summary_table.csv + comparisons.csv
        |
export_all_data.py  ->  data/all_points.csv
        |
make_report_figures.py  ->  figures/*.png
```

The commands needed to rebuild the result tables and figures are listed in the README. They need only the committed coordinates, not the videos.

## What is not in the repository

| Missing item | Why |
|---|---|
| The three source videos | Large files, and the Dressel footage belongs to its original broadcaster. |
| The generated plots inside `outputs/` | Large, and reproducible from the committed numbers. |
| The virtual environment `.venv/` | It is a local install of the Python packages. |
| The submitted PDF's editable source | The PDF is kept as a record; the HTML that produced it is also included. |

## The shortest path for a reader

1. Read `README.md`.
2. Look at `figures/fig3_three_pulls.png` and `figures/fig4_comparison.png`.
3. If you want the mathematics, read `docs/03_method.md`.
4. If you want every number, read `docs/04_results.md`.
5. If you want to check a value, open `data/all_points.csv` or `outputs/prelim/summary_table.csv`.
