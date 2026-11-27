# 8. Sources

This page records where the data came from, what software was used, and what was assumed. It is the honesty page: it states which numbers are measured, which are assumed, and which are borrowed.

## The video sources

### My footage

Two clips of my own 50 m freestyle, filmed from the pool deck.

| Clip | File | Resolution | Frame rate | Notes |
|---|---|---|---|---|
| A2 | `a2yifan.mov` | 1920 x 1080 | 29.97 fps | A wide shot, so the cap is small. |
| A3 | `a3yifan.mov` | 1920 x 1080 | 29.97 fps | The cap is larger and clearer. |

The videos are not included in the repository. The digitised coordinates are included, so the analysis can be checked without them.

### Elite footage

Caeleb Dressel, Tokyo 2020 Olympic 50 m freestyle. The race time in the clip is 21.07 s. The source is a YouTube technique clip published as `GyFwUUeNPkE`. The footage belongs to NBC Sports.

The clip is used for academic analysis only. It is not redistributed in this repository. The coordinates extracted from it are included for the same academic purpose, with the source recorded here.

The clip is **slowed**: its 60 fps container repeats each real picture about 3.36 times. The effective picture rate is about 17.9 per second. This is why the project compares shape and path length with Dressel, but not absolute time or speed.

## The calibration reference

The scale comes from the swim cap.

| Item | Value | Source |
|---|---|---|
| Assumed cap width | 0.19 m | An approximate adult head width. |
| Assumed uncertainty on cap width | 0.02 m | A conservative range around the assumed width. |
| A2 cap width in pixels | 41.3 px, sd 6.1 px, 6 frames | Measured in the A2 video. |
| A3 cap width in pixels | 148.0 px, sd 16.4 px, 7 frames | Measured in the A3 video. |
| Dressel cap width in pixels | 40.6 px, sd 3.8 px, 5 frames | Measured in the Dressel video. |

The cap width is an **assumption**, not a measurement of either swimmer. It is the largest single source of uncertainty in the lengths and speeds. The uncertainty is propagated through every length and speed.

The lane ropes are 2.5 m apart in the pool, but they are strongly foreshortened in these camera views. Using the rope would imply head widths of 0.39 m to 0.87 m, which is impossible. The rope is therefore used only as a cross-check, never as the working scale. The check is in `outputs/check/lane_rope_check.json`.

## The mathematics references

The project uses standard results from the IB Mathematics: Analysis and Approaches syllabus and from introductory calculus and statistics.

| Idea | Where it is used |
|---|---|
| Parametric curves | Writing the path as `r(t) = (x(t), y(t))`. |
| Polynomial regression | Fitting `x(t)` and `y(t)` with least squares. |
| Derivative as velocity | Computing hand speed from the fitted curve. |
| Arc length integral | Computing the length of the path. |
| Simpson's rule | Evaluating the arc-length integral numerically. |
| Root mean square error | Measuring the typical gap between two paths. |
| Coefficient of determination, R² | Measuring how much of the variation a model explains. |
| Bayesian Information Criterion | Checking the polynomial degree. |
| Propagation of uncertainty | Carrying the calibration error into every length and speed. |

These are textbook methods. The project does not claim to invent them. The contribution is applying them to a hand path in a sprint and reporting the result with an explicit uncertainty.

## The software

| Tool | What it was used for |
|---|---|
| Python 3 | Running the analysis. |
| NumPy | Polynomial fits, numerical differentiation, and integration. |
| pandas | Reading and writing the CSV files. |
| SciPy | Supporting numerical routines. |
| matplotlib | Drawing the figures. |
| OpenCV | Reading frames in the manual clicker and drawing the click checks. |
| yt-dlp | Downloading the source clip for academic analysis. |

The versions are not pinned. The results depend on the committed coordinates, not on the exact package version, so a rerun with a current install should reproduce the tables to the quoted precision.

## What was measured and what was assumed

| Quantity | Measured or assumed? | How |
|---|---|---|
| Hand position in each frame | Measured | Manual clicks in `track_hand.py`. |
| Frame number and time | Measured | Read from the video file. |
| Cap width in pixels | Measured | Several frames per clip, recorded in the calibration JSON. |
| Cap width in metres | Assumed | 0.19 m, an adult head width. |
| Scale in metres per pixel | Computed | 0.19 m divided by the cap width in pixels. |
| Path length and speed | Computed | From the fitted polynomials. |
| Gap between two paths | Computed | Normalised time, aligned starts, root mean square distance. |
| Shape score | Computed | R² after one overall size factor. |
| Size factor | Computed | Least-squares fit of one scale. |

No value in the result tables is typed in by hand. Every length, speed, R², and RMSE is computed from the digitised coordinates by the scripts in `scripts/`.

## What the sources do not support

The video sources support a comparison of **shape and path length** between these specific clips. They do not support:

- a claim about the swimmers in general, because there is one pull per clip;
- a claim about force, propulsion, or efficiency, because the project measures motion only;
- a comparison of absolute speed with Dressel, because the elite clip is slowed;
- a precise absolute length, because the cap calibration is uncertain by about 15%;
- a 3D path, because a single camera flattens the depth.

These limits are discussed in [05_limitations.md](05_limitations.md).

## Academic honesty

- The elite clip is cited by its public source, and the footage is not redistributed.
- The two clips of me are my own recordings.
- The calibration assumption is stated openly, with its uncertainty.
- The A2 result is labelled indicative because its pull window is short.
- The code and the digitised coordinates are included so that every number can be checked.
- No result is reported without the method that produced it.
