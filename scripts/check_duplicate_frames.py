"""Detect repeated (duplicated) frames, i.e. slowed footage.

A slowed or non-native-frame-rate clip repeats whole frames. If consecutive
frames are identical, the video is showing fewer distinct pictures per second
than its nominal frame rate: the time axis is stretched and any duration read
off it is too long, so any speed computed from it is too small, by the repeat
factor.

    python scripts/check_duplicate_frames.py data/dressel.mp4
    python scripts/check_duplicate_frames.py data/dressel.mp4 --range 640 780
    python scripts/check_duplicate_frames.py data/a3yifan.mov --range 165 200

Prints the repeat factor and effective unique-picture rate for the whole clip
and for the requested frame range, and writes the result as JSON for citation:

    outputs/check/duplicate_frames_<name>.json
"""

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("--range", nargs=2, type=int, metavar=("LO", "HI"),
                   help="frame range to analyse separately (inclusive)")
    p.add_argument("--tol", type=float, default=0.05,
                   help="mean absolute difference below which two frames count "
                        "as the same picture (0-255 scale, default 0.05)")
    p.add_argument("--outdir", default="outputs/check")
    return p.parse_args()


def scan(path, tol):
    """Mean absolute grey-level difference between each pair of consecutive frames."""
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise SystemExit(f"cannot open {path}")
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    diffs, frames = [], []
    prev, i = None, 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        g = cv2.cvtColor(cv2.resize(frame, (320, 180)),
                         cv2.COLOR_BGR2GRAY).astype(np.float32)
        if prev is not None:
            diffs.append(float(np.abs(g - prev).mean()))
            frames.append(i)
        prev = g
        i += 1
    cap.release()
    return fps, i, np.array(frames), np.array(diffs)


def report(label, fps, frames, diffs, tol):
    if len(diffs) == 0:
        return None
    repeats = int((diffs < tol).sum())
    unique = len(diffs) - repeats
    factor = len(diffs) / unique if unique else float("inf")
    return {
        "scope": label,
        "frames_analysed": int(len(diffs) + 1),
        "transitions": int(len(diffs)),
        "identical_transitions": repeats,
        "distinct_pictures": int(unique + 1),
        "duplicate_fraction": round(repeats / len(diffs), 3),
        "mean_median_abs_diff": [round(float(diffs.mean()), 2),
                                 round(float(np.median(diffs)), 2)],
        "frames_per_unique_picture": round(factor, 2),
        "nominal_fps": round(fps, 2),
        "effective_unique_picture_hz": round(fps / factor, 2),
        "slowed": bool(factor > 1.15),
    }


def main():
    args = parse_args()
    path = Path(args.video)
    fps, n, frames, diffs = scan(path, args.tol)

    out = {
        "video": str(path),
        "nominal_fps": round(fps, 2),
        "total_frames": n,
        "tolerance": args.tol,
        "results": [],
    }
    whole = report("whole clip", fps, frames, diffs, args.tol)
    out["results"].append(whole)

    if args.range:
        lo, hi = args.range
        mask = (frames >= lo) & (frames <= hi)
        sub = report(f"frames {lo}-{hi}", fps, frames[mask], diffs[mask], args.tol)
        out["results"].append(sub)

    for r in out["results"]:
        if r is None:
            continue
        print(f"\n{r['scope']}: {r['frames_analysed']} frames at {r['nominal_fps']} fps")
        print(f"  identical transitions: {r['identical_transitions']}/{r['transitions']} "
              f"({100*r['duplicate_fraction']:.0f}%)")
        print(f"  frames per unique picture: {r['frames_per_unique_picture']}")
        print(f"  effective unique-picture rate: {r['effective_unique_picture_hz']} Hz")
        print(f"  slowed: {'yes' if r['slowed'] else 'no'}")

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    dest = outdir / f"duplicate_frames_{path.stem}.json"
    dest.write_text(json.dumps(out, indent=2))
    print(f"\nWrote {dest}")


if __name__ == "__main__":
    main()
