"""Convert absolute hand tracks into body-relative hand tracks.

A raw hand track mixes the arm stroke with the swimmer's translation across the
pool (and any camera pan).  Subtracting a body-fixed landmark leaves the stroke
itself, which is what can be compared between swimmers.

The body landmark is the most stable dark region near the swimmer:

* trunks (McEvoy) -- the dark swimsuit separates cleanly from the water;
* cap (Yifan)     -- the dark cap above the lane rope.

Output keeps the ``track_hand.py`` schema (frame,t,x_px,y_px,x_m,y_m) but the
coordinates are now relative to the body landmark.

Usage:
    python scripts/body_relative.py data/me_hand.csv --video me.mov \
        --roi 350,195,800,248 --init 465,228 --scale-x 0.015 --scale-y 0.031 \
        --out data/me_hand_rel.csv
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np
import pandas as pd


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("hand_csv")
    p.add_argument("--video", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--roi", required=True, help="x0,y0,x1,y1 search window")
    p.add_argument("--init", required=True, help="body landmark x,y at first frame")
    p.add_argument("--method", choices=["dark", "skin"], default="dark",
                   help="dark = swimsuit/cap; skin = torso/arm skin blob")
    p.add_argument("--dark-threshold", type=float, default=115.0,
                   help="Lab L below which a pixel counts as swimsuit/cap")
    p.add_argument("--local-window", default="70,35",
                   help="follow window half-size around the previous point: "
                        "dx,dy (skin method)")
    p.add_argument("--min-area", type=int, default=25)
    p.add_argument("--max-area", type=int, default=4000)
    p.add_argument("--max-jump", type=float, default=35.0)
    p.add_argument("--m-per-px", type=float, default=None)
    p.add_argument("--scale-x", type=float, default=None)
    p.add_argument("--scale-y", type=float, default=None)
    return p.parse_args()


def body_point(frame, prev, roi, thr, min_area, max_area, method="dark"):
    x0, y0, x1, y1 = roi
    sub = frame[y0:y1, x0:x1]
    lab = cv2.cvtColor(sub, cv2.COLOR_BGR2LAB)
    L = lab[:, :, 0]
    if method == "skin":
        a = lab[:, :, 1].astype(np.int16)
        b = lab[:, :, 2].astype(np.int16)
        mask = ((a > 128) & (a < 158) & (b < 150) & (L > 90)).astype(np.uint8)
    else:
        mask = (L < thr).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, labels, stats, cent = cv2.connectedComponentsWithStats(mask)
    best = None
    for k in range(1, n):
        area = stats[k, cv2.CC_STAT_AREA]
        if not (min_area <= area <= max_area):
            continue
        cx, cy = cent[k]
        gx, gy = cx + x0, cy + y0
        d = float(np.hypot(gx - prev[0], gy - prev[1]))
        if best is None or d < best[0]:
            best = (d, gx, gy, area)
    if best is None or best[0] > 45.0:
        return prev, "hold"
    return (float(best[1]), float(best[2])), method


def main():
    args = parse_args()
    hand = pd.read_csv(args.hand_csv)
    video = str(Path(args.video).expanduser())
    cap = cv2.VideoCapture(video)

    roi = tuple(float(v) for v in args.roi.split(","))
    roi = tuple(int(v) for v in roi)
    prev = tuple(float(v) for v in args.init.split(","))
    frames = hand["frame"].astype(int).to_list()
    wdx, wdy = (int(v) for v in args.local_window.split(","))
    found = np.zeros((len(frames), 2), float)
    good = np.zeros(len(frames), bool)
    for i, frame in enumerate(frames):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(frame))
        ok, f = cap.read()
        if not ok:
            continue
        use_roi = roi
        if args.method == "skin":
            use_roi = (max(0, int(prev[0]) - wdx), max(0, int(prev[1]) - wdy),
                       min(f.shape[1], int(prev[0]) + wdx),
                       min(f.shape[0], int(prev[1]) + wdy))
        prev, m = body_point(f, prev, use_roi, args.dark_threshold,
                             args.min_area, args.max_area, args.method)
        found[i] = prev
        good[i] = m == "dark" or m == "skin"
    cap.release()

    # interpolate frames where the landmark was occluded, then smooth
    idx = np.arange(len(frames))
    if good.sum() >= 2:
        for k in range(2):
            found[:, k] = np.interp(idx, idx[good], found[good, k])
    found = np.column_stack([
        pd.Series(found[:, k]).rolling(5, center=True, min_periods=1)
        .median().to_numpy() for k in range(2)])
    body = {int(f): tuple(map(float, p)) for f, p in zip(frames, found)}
    methods = {"detected": int(good.sum()),
               "interpolated": int((~good).sum())}

    sx = args.scale_x if args.scale_x is not None else args.m_per_px
    sy = args.scale_y if args.scale_y is not None else args.m_per_px

    hand_xy = hand[["x_px", "y_px"]].to_numpy(float)
    body_xy = np.array([body[int(f)] for f in hand["frame"]])
    rel_px = hand_xy - body_xy
    rel_px -= rel_px[0]

    out = pd.DataFrame({
        "frame": hand["frame"].astype(int),
        "t": hand["t"],
        "x_px": rel_px[:, 0],
        "y_px": rel_px[:, 1],
        "x_m": "" if sx is None else rel_px[:, 0] * sx,
        "y_m": "" if sy is None else -rel_px[:, 1] * sy,
        "hand_x_px": hand_xy[:, 0],
        "hand_y_px": hand_xy[:, 1],
        "body_x_px": body_xy[:, 0],
        "body_y_px": body_xy[:, 1],
    })
    out.to_csv(args.out, index=False)
    Path(str(args.out) + ".meta.json").write_text(json.dumps({
        "hand_csv": args.hand_csv,
        "video": video,
        "body_roi": roi,
        "body_method": methods,
        "scale_x_m_per_px": sx,
        "scale_y_m_per_px": sy,
        "note": "x_px/y_px are hand minus body landmark, zeroed at first frame",
    }, indent=2))
    print(f"Wrote {len(out)} body-relative samples to {args.out}")
    print(f"  body detection: {methods}")
    print(f"  rel x: [{rel_px[:,0].min():.1f}, {rel_px[:,0].max():.1f}] px  "
          f"y: [{rel_px[:,1].min():.1f}, {rel_px[:,1].max():.1f}] px")


if __name__ == "__main__":
    main()
