"""Manually digitise the hand position, one click per frame.

Controls:
    left click  record hand at the current frame and advance
    d / space   next frame without recording
    a           previous frame
    u           undo the most recently recorded point
    x           delete the point on the current frame
    c           clear every point
    g           jump to a frame number (typed in the terminal)
    s           save now
    q / esc     save and quit

The CSV is auto-saved after every click, so a crash loses at most one point.

Usage:
    python scripts/track_hand.py data/me.mp4 --out data/me_hand.csv \
        --calibration data/me.calibration.json --start 2.0 --end 4.0
"""

import argparse
import json
import os
import tempfile
from pathlib import Path

import cv2
import numpy as np

WINDOW = "track hand"


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("--out", required=True)
    p.add_argument("--calibration", help="JSON produced by calibrate.py")
    p.add_argument("--start", type=float, default=0.0)
    p.add_argument("--end", type=float, default=None)
    p.add_argument("--step", type=int, default=1,
                   help="digitise every Nth frame")
    p.add_argument("--width", type=int, default=1280)
    p.add_argument("--point", default="hand",
                   help="label, e.g. wrist or fingertip")
    return p.parse_args()


def save_csv(path, records, fps, m_per_px, origin, meta):
    rows = []
    for frame in sorted(records):
        x_px, y_px = records[frame]
        if m_per_px is not None:
            x_m = (x_px - origin[0]) * m_per_px
            y_m = -(y_px - origin[1]) * m_per_px
        else:
            x_m, y_m = "", ""
        rows.append((frame, frame / fps, f"{x_px:.3f}", f"{y_px:.3f}",
                     x_m if x_m == "" else f"{x_m:.6f}",
                     y_m if y_m == "" else f"{y_m:.6f}"))

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".csv")
    with os.fdopen(fd, "w") as f:
        f.write("frame,t,x_px,y_px,x_m,y_m\n")
        for r in rows:
            f.write(",".join(str(v) for v in r) + "\n")
    os.replace(tmp, path)
    Path(str(path) + ".meta.json").write_text(json.dumps(meta, indent=2))


def main():
    args = parse_args()
    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        raise SystemExit(f"Could not open {args.video}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    ok, frame = cap.read()
    if not ok:
        raise SystemExit("Could not read first frame")
    h, w = frame.shape[:2]
    scale = args.width / w if w > args.width else 1.0
    disp_size = (int(w * scale), int(h * scale))

    m_per_px = None
    if args.calibration:
        cal = json.loads(Path(args.calibration).read_text())
        m_per_px = float(cal["m_per_px"])

    skip = max(1, args.step)
    start_frame = int(round(args.start * fps))
    end_frame = n_frames - 1 if args.end is None else int(round(args.end * fps))
    end_frame = min(end_frame, n_frames - 1)

    records = {}
    if Path(args.out).exists():
        import pandas as pd
        old = pd.read_csv(args.out)
        for _, r in old.iterrows():
            records[int(r["frame"])] = (float(r["x_px"]), float(r["y_px"]))
        print(f"Loaded {len(records)} existing points from {args.out}")

    origin = None
    current = start_frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, current)
    ok, frame = cap.read()
    if not ok:
        raise SystemExit("Could not read start frame")

    def to_original(x, y):
        return x / scale, y / scale

    def advance():
        nonlocal current, frame
        current = min(current + skip, end_frame)
        cap.set(cv2.CAP_PROP_POS_FRAMES, current)
        ok, frame = cap.read()
        return ok

    def go_back():
        nonlocal current, frame
        current = max(current - skip, start_frame)
        cap.set(cv2.CAP_PROP_POS_FRAMES, current)
        ok, frame = cap.read()
        return ok

    def commit():
        nonlocal origin
        if origin is None and records:
            origin = records[min(records)]
        meta = {
            "video": str(Path(args.video)),
            "fps": fps,
            "point": args.point,
            "step": skip,
            "calibration": args.calibration,
            "m_per_px": m_per_px,
            "origin_px": list(origin) if origin else None,
        }
        save_csv(args.out, records, fps, m_per_px,
                 origin or (0.0, 0.0), meta)

    def on_mouse(event, x, y, flags, param):
        nonlocal origin
        if event == cv2.EVENT_LBUTTONDOWN:
            records[current] = to_original(x, y)
            if origin is None:
                origin = records[current]
            commit()
            advance()

    cv2.namedWindow(WINDOW, cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback(WINDOW, on_mouse)
    print(__doc__)
    print(f"Video: {w}x{h} @ {fps:.3f} fps, {n_frames} frames")
    print(f"Digitising frames {start_frame} to {end_frame}")

    while True:
        canvas = cv2.resize(frame, disp_size)

        pts = sorted(records)
        for i in range(1, len(pts)):
            a = records[pts[i - 1]]
            b = records[pts[i]]
            cv2.line(canvas, (int(a[0] * scale), int(a[1] * scale)),
                     (int(b[0] * scale), int(b[1] * scale)),
                     (0, 200, 0), 1, cv2.LINE_AA)

        if current in records:
            p = records[current]
            cv2.drawMarker(canvas, (int(p[0] * scale), int(p[1] * scale)),
                           (0, 0, 255), cv2.MARKER_CROSS, 18, 2)
        elif records:
            p = records[max(records)]
            cv2.circle(canvas, (int(p[0] * scale), int(p[1] * scale)),
                       5, (0, 200, 0), -1)

        cv2.rectangle(canvas, (0, 0), (disp_size[0], 34), (0, 0, 0), -1)
        txt = (f"frame {current}/{end_frame}  t={current / fps:.3f}s  "
               f"points={len(records)}  "
               f"click=record+next  a/d=step  u=undo  q=save")
        cv2.putText(canvas, txt, (8, 23), cv2.FONT_HERSHEY_SIMPLEX,
                    0.55, (255, 255, 255), 1, cv2.LINE_AA)

        cv2.imshow(WINDOW, canvas)
        key = cv2.waitKey(20) & 0xFF
        if key in (ord("q"), 27):
            break
        if key in (ord("d"), ord(" "), 83):
            advance()
        elif key in (ord("a"), 81):
            go_back()
        elif key == ord("u") and records:
            records.pop(max(records))
            commit()
        elif key == ord("x") and current in records:
            records.pop(current)
            commit()
        elif key == ord("c"):
            records.clear()
            origin = None
            commit()
        elif key == ord("s"):
            commit()
            print(f"Saved {len(records)} points to {args.out}")
        elif key == ord("g"):
            try:
                target = int(input("Jump to frame: "))
            except ValueError:
                continue
            current = min(max(target, start_frame), end_frame)
            cap.set(cv2.CAP_PROP_POS_FRAMES, current)
            ok, frame = cap.read()
            if not ok:
                break

    commit()
    cap.release()
    cv2.destroyAllWindows()
    print(f"Saved {len(records)} points to {args.out}")


if __name__ == "__main__":
    main()
