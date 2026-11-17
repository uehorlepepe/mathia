# Automatic tracking run — notes

`scripts/track_hand.py` is interactive (one mouse click per frame), so it cannot be
driven headlessly.  These tracks were produced with `scripts/auto_track.py`, which
follows one point with pyramidal Lucas–Kanade optical flow (forward–backward error
rejection + local template fallback), then median-filters the result.

This is a **best-effort approximation**, not equivalent to careful manual
digitisation.  Treat the numbers as exploratory.

## Clips and phases used

| Label | File | Frames | Time | Phase |
|-------|------|--------|------|-------|
| Me | `~/Downloads/Yifanwang50m.mov` (the file is named **50m**, not 40m) | 760–830 | 25.33–27.66 s | reach → entry, lane 3, approaching the wall |
| McEvoy | `data/mcevoy.mp4` | 228–276 | 8.26–10.00 s | one full right-arm cycle (recovery → entry → pull → recovery) |

## Calibration

* **McEvoy:** lane width 2.5 m spans ≈333 px at the swimmer's depth in frame 228
  → **0.0075 m/px** (isotropic).
* **Me:** the side-on camera foreshortens the two axes differently.
  Horizontal scale from the swimmer's body (≈85 px per ~1.3 m) → **0.015 m/px**;
  vertical scale from the lane-rope spacing (2.5 m ≈ 81 px) → **0.031 m/px**.
  These are rough; the oblique angle makes the horizontal scale the least certain.

## What is actually tracked

* **McEvoy:** the point stays on the swimmer's raised arm during recovery, but when
  the hand is underwater and in front of the torso the flow latches onto the body.
  The hidden part of the pull is therefore a proxy, not a measured wrist.
* **Me:** the swimmer is only ~120 px long and the camera pans, so the tracked point
  is the leading hand/forearm and drifts ahead by roughly one hand-length in the
  splash.  The path is dominated by the swimmer's translation along the lane, not
  by the arm's motion relative to the torso.

The clips are also shot from incompatible geometries (McEvoy: head-on underwater;
Me: distant elevated side view), so the two trajectories are not directly
comparable.  A valid IA comparison needs the same camera set-up and manual
digitisation of one anatomical point (e.g. wrist centre) on both clips.

## Outputs

* `data/me_hand.csv`, `data/mcevoy_hand.csv` — raw tracks (same schema as
  `track_hand.py`) plus `*.meta.json`.
* `outputs/me/`, `outputs/mcevoy/` — fits, plots, summaries.
* `outputs/comparison/` — overlay, comparison RMSE.
* `outputs/combined_hand_tracks.csv` — both raw tracks in one table
  (`swimmer,frame,t,x_px,y_px,x_m,y_m`).
* `outputs/combined_fit.csv` — both fitted curves in one table.
