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

Frames that are visually identical are skipped automatically (some clips
repeat each real frame several times), so every click shows a new image.

The CSV is auto-saved after every click, so a crash loses at most one point.

Usage:
    python scripts/track_hand.py data/a3yifan.mov \
        --out data/a3_hand_manual.csv --start 5.7 --end 6.5 \
        --point wrist --enhance --loupe 5
"""

import argparse
import json
import os
import tempfile
from pathlib import Path

import cv2
import numpy as np

def enhance(im):
    """Local-contrast + unsharp mask, for washed-out underwater footage."""
    lab = cv2.cvtColor(im, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(l)
    im = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)
    blur = cv2.GaussianBlur(im, (0, 0), 1.2)
    return cv2.addWeighted(im, 1.6, blur, -0.6, 0)


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
    p.add_argument("--enhance", action="store_true",
                   help="CLAHE + unsharp mask to make a dim hand easier to see")
    p.add_argument("--loupe", type=int, default=4,
                   help="magnification of the cursor loupe (0 disables)")
    p.add_argument("--min-change", type=float, default=1.0,
                   help="skip repeated/near-identical frames while advancing "
                        "(mean abs pixel difference; 0 disables)")
    p.add_argument("--max-skip", type=int, default=40,
                   help="maximum frames to skip while looking for a new image")
    p.add_argument("--title", default=None,
                   help="window title (default: video file name)")
    p.add_argument("--at", type=float, default=None,
                   help="start at this time in seconds instead of resuming "
                        "after the last recorded point")
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
    # Always scale to --width: upscaling small clips makes precise clicking
    # easier, and to_original() divides the click coordinates back out.
    scale = args.width / w
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

    origin = records[min(records)] if records else None
    # Resume at the first frame after the last recorded one, so a crash or an
    # accidental close doesn't make you re-click points you already have.
    done = [f for f in records if start_frame <= f <= end_frame]
    if args.at is not None:
        current = int(round(args.at * fps))
        current = min(max(current, start_frame), end_frame)
        done = [f for f in done if f < current]
    else:
        current = min(max(done) + 1, end_frame) if done else start_frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, current)
    ok, frame = cap.read()
    if not ok:
        raise SystemExit("Could not read start frame")

    def to_original(x, y):
        return x / scale, y / scale

    history = [current]

    def same_image(a, b):
        return (args.min_change > 0
                and float(cv2.absdiff(a, b).mean()) < args.min_change)

    def advance():
        """Step forward, skipping frames that are visually identical.

        Some source clips are stored at 30/60 fps but repeat each real frame
        several times.  Without this, a click appears not to advance because
        the next frame is the same picture.
        """
        nonlocal current, frame
        if current >= end_frame:
            return False
        base = frame
        steps = 0
        new = frame
        while current < end_frame and steps < args.max_skip:
            ok, new = cap.read()
            if not ok:
                return False
            current += 1
            steps += 1
            if steps >= skip and not same_image(new, base):
                break
        frame = new
        history.append(current)
        return True

    def go_back():
        nonlocal current, frame
        if len(history) > 1:
            history.pop()
        target = history[-1] if history else max(current - skip, start_frame)
        current = target
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
            "min_change": args.min_change,
            "calibration": args.calibration,
            "m_per_px": m_per_px,
            "origin_px": list(origin) if origin else None,
        }
        save_csv(args.out, records, fps, m_per_px,
                 origin or (0.0, 0.0), meta)

    win = args.title or f"track hand - {Path(args.video).stem}"
    mouse = {"pos": None}

    def on_mouse(event, x, y, flags, param):
        nonlocal origin
        if event == cv2.EVENT_MOUSEMOVE:
            mouse["pos"] = (x, y)
        elif event == cv2.EVENT_LBUTTONDOWN:
            records[current] = to_original(x, y)
            if origin is None:
                origin = records[current]
            commit()
            px, py = records[current]
            print(f"point frame={current} t={current / fps:.3f}s "
                  f"({px:.1f},{py:.1f})  total={len(records)}", flush=True)
            advance()

    cv2.namedWindow(win, cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback(win, on_mouse)
    print(__doc__)
    print(f"Video: {w}x{h} @ {fps:.3f} fps, {n_frames} frames")
    print(f"Digitising frames {start_frame} to {end_frame}")

    while True:
        view = enhance(frame) if args.enhance else frame
        canvas = cv2.resize(view, disp_size)

        pts = sorted(records)
        for i in range(1, len(pts)):
            a = records[pts[i - 1]]
            b = records[pts[i]]
            cv2.line(canvas, (int(a[0] * scale), int(a[1] * scale)),
                     (int(b[0] * scale), int(b[1] * scale)),
                     (0, 200, 0), 1, cv2.LINE_AA)
        for p in records.values():
            cv2.circle(canvas, (int(p[0] * scale), int(p[1] * scale)),
                       3, (0, 220, 0), -1)

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

        # Magnified inset around the cursor, so small/low-res hands are clickable.
        if args.loupe > 0 and mouse["pos"] is not None:
            mx, my = mouse["pos"]
            ox, oy = int(mx / scale), int(my / scale)
            half = 28
            x0, x1 = max(0, ox - half), min(w, ox + half)
            y0, y1 = max(0, oy - half), min(h, oy + half)
            crop = view[y0:y1, x0:x1]
            if crop.size:
                size = min(320, int(2 * half * args.loupe))
                loupe = cv2.resize(crop, (size, size),
                                   interpolation=cv2.INTER_CUBIC)
                lx = 8 if mx > disp_size[0] // 2 else disp_size[0] - size - 8
                ly = 42
                canvas[ly:ly + size, lx:lx + size] = loupe
                cv2.rectangle(canvas, (lx, ly), (lx + size, ly + size),
                              (255, 255, 255), 1)
                c = (lx + size // 2, ly + size // 2)
                cv2.drawMarker(canvas, c, (0, 0, 255),
                               cv2.MARKER_CROSS, 16, 1)
                cv2.putText(canvas, f"{args.loupe}x", (lx + 4, ly + 16),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            (255, 255, 255), 1, cv2.LINE_AA)

        cv2.imshow(win, canvas)
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
            history.clear()
            history.append(current)

    commit()
    cap.release()
    cv2.destroyAllWindows()
    print(f"Saved {len(records)} points to {args.out}")


if __name__ == "__main__":
    main()
