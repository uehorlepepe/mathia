"""Click two points of known real-world distance to get metres per pixel.

Usage:
    python scripts/development/calibrate.py data/a2yifan.mov --time 11.0 --distance 2.5
    python scripts/development/calibrate.py data/dressel.mp4 --time 11.8 --distance 2.5

Example references: your body length (height), lane width (2.5 m), or the
distance between two pool tiles. Use a reference lying in the same plane as
the hand and perpendicular to the camera.
"""

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

WINDOW = "calibrate"


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("--time", type=float, default=0.0, help="seconds into video")
    p.add_argument("--distance", type=float, required=True,
                   help="real-world distance between the two clicked points (m)")
    p.add_argument("--out", default=None, help="output JSON path")
    p.add_argument("--width", type=int, default=1280)
    return p.parse_args()


def main():
    args = parse_args()
    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        raise SystemExit(f"Could not open {args.video}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_no = int(round(args.time * fps))
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
    ok, frame = cap.read()
    if not ok:
        raise SystemExit("Could not read frame")
    cap.release()

    h, w = frame.shape[:2]
    scale = args.width / w if w > args.width else 1.0
    disp = cv2.resize(frame, (int(w * scale), int(h * scale)))
    points = []

    def to_original(x, y):
        return x / scale, y / scale

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and len(points) < 2:
            points.append(to_original(x, y))

    cv2.namedWindow(WINDOW, cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback(WINDOW, on_mouse)
    print("Click the two endpoints of the known distance (R resets, Q quits).")

    while True:
        canvas = disp.copy()
        for i, (px, py) in enumerate(points):
            cv2.circle(canvas, (int(px * scale), int(py * scale)), 5,
                       (0, 0, 255), -1)
            cv2.putText(canvas, str(i + 1),
                        (int(px * scale) + 8, int(py * scale) - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        if len(points) == 2:
            p1 = tuple(int(v * scale) for v in points[0])
            p2 = tuple(int(v * scale) for v in points[1])
            cv2.line(canvas, p1, p2, (0, 255, 255), 2)
            px_dist = float(np.hypot(points[1][0] - points[0][0],
                                     points[1][1] - points[0][1]))
            cv2.putText(canvas, f"{px_dist:.1f} px",
                        (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                        (0, 255, 255), 2)

        cv2.imshow(WINDOW, canvas)
        key = cv2.waitKey(20) & 0xFF
        if key in (ord("q"), 27):
            break
        if key == ord("r"):
            points.clear()
        if len(points) == 2:
            px_dist = float(np.hypot(points[1][0] - points[0][0],
                                     points[1][1] - points[0][1]))
            m_per_px = args.distance / px_dist
            out = args.out or str(Path(args.video).with_suffix(".calibration.json"))
            data = {
                "video": str(Path(args.video)),
                "frame": frame_no,
                "fps": fps,
                "image_width": w,
                "image_height": h,
                "p1_px": list(points[0]),
                "p2_px": list(points[1]),
                "distance_m": args.distance,
                "pixel_distance": px_dist,
                "m_per_px": m_per_px,
            }
            Path(out).write_text(json.dumps(data, indent=2))
            print(f"Saved {out}\n1 px = {m_per_px:.6f} m")
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
