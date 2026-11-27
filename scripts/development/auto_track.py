"""Automatic hand tracker (non-interactive stand-in for track_hand.py).

Tracks one hand with pyramidal Lucas-Kanade optical flow, using the
forward-backward error to reject bad matches and a local template match to
recover when the flow is ambiguous.  Writes the same CSV schema as
``track_hand.py`` so the rest of the pipeline is unchanged:

    frame,t,x_px,y_px,x_m,y_m

Example:
    python scripts/development/auto_track.py data/dressel.mp4 \
        --out data/dressel_hand_auto.csv --start-frame 642 --end-frame 778 \
        --init 760,335 --m-per-px 0.00468

This tracker was used during development. The final data were digitised by
hand with track_hand.py, so this script is not needed to reproduce the results.
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
    p.add_argument("video")
    p.add_argument("--out", required=True)
    p.add_argument("--start-frame", type=int, required=True)
    p.add_argument("--end-frame", type=int, required=True)
    p.add_argument("--init", default=None,
                   help="initial hand position in pixels: x,y")
    p.add_argument("--anchors", default=None,
                   help="semi-automatic: re-anchor the hand at key frames. "
                        "Format 'frame:x,y;frame:x,y;...' covering the window")
    p.add_argument("--m-per-px", type=float, default=None,
                   help="isotropic scale (metres per pixel)")
    p.add_argument("--scale-x", type=float, default=None,
                   help="horizontal scale, overrides --m-per-px for x")
    p.add_argument("--scale-y", type=float, default=None,
                   help="vertical scale, overrides --m-per-px for y")
    p.add_argument("--point", default="hand")
    p.add_argument("--overlay", default=None,
                   help="optional contact-sheet JPEG for checking the track")
    return p.parse_args()


def _lk(prev, cur, pts):
    nxt, st, _ = cv2.calcOpticalFlowPyrLK(
        prev, cur, pts, None, winSize=(21, 21), maxLevel=3,
        criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01))
    back, st2, _ = cv2.calcOpticalFlowPyrLK(
        cur, prev, nxt, None, winSize=(21, 21), maxLevel=3,
        criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01))
    fb = float(np.linalg.norm(back - pts))
    return nxt, bool(st.ravel()[0] and st2.ravel()[0]), fb


def _template(prev, cur, p, vel, patch=21, search=28):
    """Local normalised cross-correlation around the predicted position."""
    h, w = prev.shape
    pt = np.asarray(p).ravel()
    px, py = int(round(float(pt[0]))), int(round(float(pt[1])))
    r = patch // 2
    x0, y0 = px - r, py - r
    if x0 < 0 or y0 < 0 or x0 + patch > w or y0 + patch > h:
        return None, 0.0
    tpl = prev[y0:y0 + patch, x0:x0 + patch]
    if tpl.std() < 3:
        return None, 0.0
    cx = int(round(float(pt[0] + vel[0])))
    cy = int(round(float(pt[1] + vel[1])))
    sx0, sy0 = max(0, cx - search), max(0, cy - search)
    sx1 = min(w, cx + search + 1)
    sy1 = min(h, cy + search + 1)
    if sx1 - sx0 < patch + 2 or sy1 - sy0 < patch + 2:
        return None, 0.0
    res = cv2.matchTemplate(cur[sy0:sy1, sx0:sx1], tpl, cv2.TM_CCOEFF_NORMED)
    _, score, _, loc = cv2.minMaxLoc(res)
    if score < 0.55:
        return None, float(score)
    return np.array([[sx0 + loc[0] + r, sy0 + loc[1] + r]], np.float32), float(score)


def track(video, start, end, anchors):
    """Track between successive hand anchors; each anchor resets drift."""
    cap = cv2.VideoCapture(video)
    if not cap.isOpened():
        raise SystemExit(f"Could not open {video}")

    anchors = sorted(anchors, key=lambda a: a[0])
    pts = []
    for a_idx, (fa, (ax, ay)) in enumerate(anchors):
        fb = anchors[a_idx + 1][0] if a_idx + 1 < len(anchors) else end
        fb = min(fb, end)
        pts.extend(_track_segment(cap, fa, fb, (ax, ay)))
    cap.release()
    # de-duplicate frames, keep first
    seen = {}
    for f, xy, m in pts:
        seen.setdefault(f, (f, xy, m))
    return [seen[k] for k in sorted(seen)]


def _track_segment(cap, start, end, init):
    cap.set(cv2.CAP_PROP_POS_FRAMES, start)
    ok, frame = cap.read()
    if not ok:
        raise SystemExit("Could not read start frame")

    prev = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    p = np.array([[init]], np.float32)
    pts = [(start, p.ravel().copy(), "anchor")]
    vel = np.zeros(2, np.float32)
    hold = 0

    for i in range(start + 1, end + 1):
        ok, frame = cap.read()
        if not ok:
            break
        cur = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        q, good, fb = _lk(prev, cur, p)
        method = "lk"
        if not good or fb > 2.0:
            q2, score = _template(prev, cur, p, vel)
            method = "template" if q2 is not None else "hold"
            if q2 is not None:
                q = q2
            else:
                hold += 1
                q = p + vel
        else:
            hold = 0
        if method == "hold" and hold > 4:
            q = p  # do not let a guessed point run away
        d = (q - p).ravel()
        if np.linalg.norm(d) < 40:  # reject teleports
            vel = 0.5 * vel + 0.5 * d
            p = q
        pts.append((i, p.ravel().copy(), method))
        prev = cur

    return pts


def smooth(pts, kernel=5):
    frames = np.array([p[0] for p in pts])
    xy = np.array([p[1] for p in pts], float)
    # 1. suppress implausible single-frame jumps, interpolating across them
    if len(xy) > 4:
        step = np.linalg.norm(np.diff(xy, axis=0), axis=1)
        med = float(np.median(step)) or 1.0
        bad = step > max(8.0, 5.0 * med)
        if bad.any():
            idx = np.arange(len(xy))
            good = np.concatenate([[True], ~bad])
            for k in range(2):
                xy[:, k] = np.interp(idx, idx[good], xy[good, k])
    # 2. median filter removes residual single-frame spikes
    xy = np.column_stack([_med(xy[:, k], kernel) for k in range(2)])
    return frames, xy


def _med(x, k):
    if k < 3:
        return x
    return pd.Series(x).rolling(k, center=True, min_periods=1).median().to_numpy()


def overlay_sheet(video, pts, out, cols=8):
    cap = cv2.VideoCapture(video)
    thumbs = []
    for i, (x, y), _ in pts:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(i))
        ok, f = cap.read()
        if not ok:
            continue
        cv2.circle(f, (int(x), int(y)), 10, (0, 0, 255), 2)
        cv2.circle(f, (int(x), int(y)), 2, (0, 255, 0), -1)
        cv2.putText(f, str(i), (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (0, 255, 255), 2)
        f = cv2.resize(f, (300, int(300 * f.shape[0] / f.shape[1])))
        thumbs.append(f)
    cap.release()
    if not thumbs:
        return
    h = max(t.shape[0] for t in thumbs)
    w = max(t.shape[1] for t in thumbs)
    thumbs = [cv2.copyMakeBorder(t, 0, h - t.shape[0], 0, w - t.shape[1],
                                 cv2.BORDER_CONSTANT, value=(0, 0, 0))
              for t in thumbs]
    rows = []
    for i in range(0, len(thumbs), cols):
        row = thumbs[i:i + cols]
        while len(row) < cols:
            row.append(np.zeros_like(thumbs[0]))
        rows.append(np.hstack(row))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), np.vstack(rows))


def main():
    args = parse_args()
    video = str(Path(args.video).expanduser())
    if args.anchors:
        anchors = []
        for item in args.anchors.split(";"):
            f_str, xy_str = item.split(":")
            x_str, y_str = xy_str.split(",")
            anchors.append((int(f_str), (float(x_str), float(y_str))))
        if anchors[0][0] > args.start_frame:
            anchors.insert(0, (args.start_frame, anchors[0][1]))
    else:
        if not args.init:
            raise SystemExit("supply --init x,y or --anchors")
        init = tuple(float(v) for v in args.init.split(","))
        if len(init) != 2:
            raise SystemExit("--init must be x,y")
        anchors = [(args.start_frame, init)]

    pts = track(video, args.start_frame, args.end_frame, anchors)

    fps = cv2.VideoCapture(video).get(cv2.CAP_PROP_FPS)
    frames, xy = smooth(pts)

    sx = args.scale_x if args.scale_x is not None else args.m_per_px
    sy = args.scale_y if args.scale_y is not None else args.m_per_px
    origin = xy[0]

    rows = []
    for (frame, _, _), (x, y) in zip(pts, xy):
        x_px, y_px = float(x), float(y)
        x_m = "" if sx is None else f"{(x_px - origin[0]) * sx:.6f}"
        y_m = "" if sy is None else f"{-(y_px - origin[1]) * sy:.6f}"
        rows.append((int(frame), f"{frame / fps:.6f}",
                     f"{x_px:.3f}", f"{y_px:.3f}", x_m, y_m))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as f:
        f.write("frame,t,x_px,y_px,x_m,y_m\n")
        for r in rows:
            f.write(",".join(str(v) for v in r) + "\n")

    methods = {}
    for _, _, m in pts:
        methods[m] = methods.get(m, 0) + 1
    meta = {
        "video": video,
        "point": args.point,
        "method": "Lucas-Kanade + template fallback "
                  "(semi-automatic, re-anchored by hand)",
        "fps": fps,
        "start_frame": args.start_frame,
        "end_frame": args.end_frame,
        "anchors": [[f, list(xy)] for f, xy in anchors],
        "n_frames": len(pts),
        "methods": methods,
        "m_per_px": args.m_per_px,
        "scale_x_m_per_px": sx,
        "scale_y_m_per_px": sy,
        "origin_px": list(map(float, origin)),
    }
    Path(str(out) + ".meta.json").write_text(json.dumps(meta, indent=2))

    if args.overlay:
        overlay_sheet(video, pts, args.overlay)

    print(f"Wrote {len(pts)} samples to {out}")
    print(f"  methods: {methods}")
    print(f"  x: [{xy[:, 0].min():.1f}, {xy[:, 0].max():.1f}] px   "
          f"y: [{xy[:, 1].min():.1f}, {xy[:, 1].max():.1f}] px")


if __name__ == "__main__":
    main()
