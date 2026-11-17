# Math IA: underwater hand-trajectory analysis

Pipeline for the exploration comparing a high-school sprinter with Cameron
McEvoy using parametric models, derivatives, arc length, and RMSE.

## 1. Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Install `ffmpeg` if you need to trim or convert video: `brew install ffmpeg`.

## 2. Get the videos onto this computer

For the McEvoy clip (use only for academic analysis; keep the source URL in your
bibliography):

```bash
yt-dlp -f "bv*[height<=1080]+ba/b[height<=1080]" \
  -o "data/mcevoy.%(ext)s" "YOUTUBE_URL"
```

Trim both videos to the same phase of the race (e.g. one full underwater pull
from hand entry to exit) with:

```bash
ffmpeg -i data/mcevoy.mp4 -ss 00:00:04 -to 00:00:06 -c copy data/mcevoy_clip.mp4
ffmpeg -i data/me.mov       -ss 00:00:02 -to 00:00:04 -c copy data/me_clip.mp4
```

Keep the full files too; trimming is just for faster tracking.

## 3. Filming protocol for your own swim

The comparison is only valid if the camera geometry is similar:

- Fixed camera, perpendicular to the lane, at the same height and distance as
  the McEvoy footage (as close as possible).
- Lock focus, exposure and white balance; never zoom while filming.
- 60 fps or higher if available (30 fps is workable, but 60 gives better
  derivatives).
- Keep your hand in one plane parallel to the image sensor; a hand moving
  toward/away from the camera introduces parallax error.
- Include a known length in the shot for calibration, at the same depth as the
  hand: pool tile spacing, lane-rope spacing (2.5 m), or your body length.
- Record the full stroke, then digitise **one** representative pull phase.

## 4. Calibrate pixels to metres

Pick two points of known distance on a frame:

```bash
python scripts/calibrate.py data/mcevoy_clip.mp4 --time 0 --distance 1.9
python scripts/calibrate.py data/me_clip.mp4 --time 0 --distance 1.9
```

This writes `data/<video>.calibration.json`. If you use body length, measure it
yourself (height is a decent proxy for the McEvoy clip) and use the *same
reference type* for both videos where possible. State the reference and its
uncertainty in the IA.

## 5. Digitise the hand

Click the same anatomical point (e.g. the wrist centre, not the fingertips) on
every frame:

```bash
python scripts/track_hand.py data/me_clip.mp4 \
  --out data/me_hand.csv --calibration data/me_clip.calibration.json \
  --start 2.0 --end 4.0 --point wrist

python scripts/track_hand.py data/mcevoy_clip.mp4 \
  --out data/mcevoy_hand.csv --calibration data/mcevoy_clip.calibration.json \
  --start 4.0 --end 6.0 --point wrist
```

Controls: click to record and advance, `a`/`d` to step, `u` to undo, `q` to
save and quit. The CSV is saved after every click, so you can stop and resume.
Record a wrist trajectory and, if you want, a second CSV for the fingertip.

## 6. Fit and compare

```bash
python scripts/analyze.py data/me_hand.csv --label Me --outdir outputs/me
python scripts/analyze.py data/me_hand.csv data/mcevoy_hand.csv \
  --labels Me McEvoy --compare --outdir outputs/comparison
```

Each run produces:

- `<label>_fit.csv` – fitted `x(t)`, `y(t)`, `vx`, `vy`, speed and cumulative
  arc length.
- `*_trajectory.png` – path in the x-y plane.
- `*_curves.png` – position and speed against time.
- `*_residuals.png` – residuals, useful for discussing model quality.
- `summary.json` – coefficients, degrees, R², RMSE, arc length, speed stats.
- `comparison.png` – normalised-time overlay plus RMSE when two files are given.

## 7. Mathematical choices

For each swimmer, fit

```
x(t) = a0 + a1 t + ... + an t^n
y(t) = b0 + b1 t + ... + bm t^m
```

on one pull phase. The script chooses the degree (2–5) by BIC, then robustly
refits with optional sigma clipping (`--sigma-clip 3`). Use `--degree` to force
a degree, which is useful for a sensitivity analysis.

Velocity and speed:

```
vx = dx/dt,  vy = dy/dt,  speed = sqrt(vx^2 + vy^2)
```

Arc length:

```
L = integral from t0 to t1 of sqrt((dx/dt)^2 + (dy/dt)^2) dt
```

Comparison: resample both tracks to normalised time `[0, 1]`, align the starting
point, then compute the Euclidean position RMSE. Report both the absolute arc
lengths and the normalised error.

## 8. Things worth mentioning in the IA

- Digitisation uncertainty: human clicks are accurate to roughly ±2–5 px;
  convert this to metres and propagate it.
- Frame timing uncertainty: half a frame at 30 fps is about 0.017 s.
- Polynomial fits are local: do not fit several stroke cycles with one high
  degree polynomial, and check the residuals.
- Fixed camera and same point of hand are essential for a fair comparison.
- The McEvoy video is secondary data; cite the URL and date accessed.
