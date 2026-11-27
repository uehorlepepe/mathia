# Data

This folder contains every digitised hand position used in the project, plus the calibration that converts pixels to metres. The source videos are not included.

## Start here

Open `all_points.csv`. It is one flat table with all 66 points from all three clips, the swimmer label, the scale, and a flag for the pull window. It is the easiest file to open in Excel or Google Sheets.

## The files

| File | What it is |
|---|---|
| `all_points.csv` | All 66 points in one table, with the pull-window flag. |
| `a2_hand_manual.csv` | Raw A2 clicks: frame, time, and pixel coordinates. |
| `a3_hand_manual.csv` | Raw A3 clicks. |
| `dressel_hand_manual.csv` | Raw Dressel clicks. |
| `a2_hand_points_metres.csv` | A2 in metres, first point at the origin. |
| `a3_hand_points_metres.csv` | A3 in metres. |
| `dressel_hand_points_metres.csv` | Dressel in metres. |
| `a2.calibration_cap.json` | A2 cap width, scale, uncertainty, and lane-rope check. |
| `a3.calibration_cap.json` | A3 cap width, scale, uncertainty, and lane-rope check. |
| `dressel.calibration_cap.json` | Dressel cap width, scale, uncertainty, and lane-rope check. |
| `*.csv.meta.json` | A note recording where each raw click file came from. |

## The columns

The raw `*_hand_manual.csv` files contain only the clicks:

| Column | Meaning |
|---|---|
| `frame` | Video frame number. |
| `t` | Time in seconds. For Dressel this is nominal 60 fps time, not physical time. |
| `x_px`, `y_px` | The click in image coordinates, origin at the top left. |

The converted `*_hand_points_metres.csv` files add the metres:

| Column | Meaning |
|---|---|
| `x_m`, `y_m` | Position in metres, first click at the origin, upward positive. |

`all_points.csv` uses `t_s` for the time column. It also adds `swimmer`, `clip`, `video`, `m_per_px`, `scale_unc_pct`, `fps`, the image size, `time_base`, `calibration`, and `in_pull_window`.

## What the numbers mean

- **A2 and A3 are two clips of the same swimmer, me.** They are not two people.
- **Dressel is Caeleb Dressel**, Tokyo 2020 Olympic 50 m freestyle. The clip is slowed, so its time base is nominal.
- **The scale comes from the swim cap**, assumed 0.19 m wide. The uncertainty is 14% to 18%.
- **The lane rope is not the scale.** It is foreshortened in these camera views. See the calibration JSON files.

For the full explanation, read [../docs/02_data.md](../docs/02_data.md).
