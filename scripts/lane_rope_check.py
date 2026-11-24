"""Can the yellow lane lines set the scale, and what happens if they do?

The idea is standard in principle: both swimmers are in an Olympic pool, so a
lane is 2.5 m wide and the lane ropes are a common absolute reference that needs
no assumption about the swimmer's body size. It works when the ropes and the
swimmer are at the same distance from the lens. A single camera cannot assume
that, so this script tests it instead:

  1. inventory -- is there a yellow line, how many separate ones, and is the
     near one pressed against the lens (clipped by the frame edge)?
  2. transfer test -- every calibration file also records a lane-width reading.
     Using it instead of the cap changes each clip's metres-per-pixel by a
     factor r. If the ropes were at the swimmer's distance, r would be 1 for all
     three clips and the same for each. The script reports r, the head length
     the rope scale would give the swimmer, the hand-pull length it would give,
     and the size ratio between my pull and his.

    python scripts/lane_rope_check.py
"""

import json
from pathlib import Path

import cv2
import numpy as np

CLIPS = {
    "a2": dict(video="data/a2yifan.mov", calib="data/a2.calibration_body.json", label="A2"),
    "a3": dict(video="data/a3yifan.mov", calib="data/a3.calibration_body.json", label="A3"),
    "dressel": dict(video="data/dressel.mp4", calib="data/dressel.calibration_body.json",
                    label="Dressel"),
}
HEAD_M = 0.19
OUT = Path("outputs/check")


def yellow_mask(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    return cv2.inRange(hsv, (18, 120, 120), (40, 255, 255))


def inventory(tag, cfg):
    calib = json.loads(Path(cfg["calib"]).read_text())
    cap = cv2.VideoCapture(cfg["video"])
    counts, best = [], (0, None, None, None, [])
    for idx in calib["cap_measurement"]["frames"]:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, fr = cap.read()
        if not ok:
            continue
        mask = yellow_mask(fr)
        n, _, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
        big = [s for s in stats[1:] if s[4] >= 2000]
        counts.append(len(big))
        if (mask > 0).sum() > best[0]:
            best = (int((mask > 0).sum()), idx, fr, mask, big)
    cap.release()

    n_yellow, idx, fr, mask, big = best
    edge = 0 if fr is None else fr.shape[0]
    clipped = bool(big) and any((s[1] <= 0 or s[1] + s[3] >= edge) for s in big)
    res = dict(
        clip=cfg["label"],
        yellow_px=int(n_yellow),
        separate_yellow_lines=int(round(np.median(counts))) if counts else 0,
        near_line_clipped_by_frame_edge=clipped,
    )
    if idx is not None:
        vis = fr.copy()
        vis[mask > 0] = (0, 0, 255)
        h, w = vis.shape[:2]
        cv2.imwrite(str(OUT / f"lanerope_{tag}.png"),
                    cv2.resize(vis, (900, int(h * 900 / w))),
                    [cv2.IMWRITE_PNG_COMPRESSION, 9])
        res["illustration_frame"] = idx
    return res


def transfer_test(cfg, arcs):
    calib = json.loads(Path(cfg["calib"]).read_text())
    body = calib["m_per_px"]
    rope = calib["rope_crosscheck"]["m_per_px_rope"]
    r = rope / body
    arc_body = arcs[cfg["label"]]
    return dict(
        clip=cfg["label"],
        m_per_px_cap=round(body, 6),
        m_per_px_lane=round(rope, 6),
        rope_over_cap=r,
        head_implied_m=round(HEAD_M * r, 2),
        pull_arc_body_m=round(arc_body, 3),
        pull_arc_lane_m=round(arc_body * r, 2),
    )


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    own = Path("outputs/prelim/pull_phase/pull_phase_own_fits.csv")
    arcs = {}
    if own.exists():
        import pandas as pd
        d = pd.read_csv(own)
        arcs = dict(zip(d.track, d.arc_length_m))

    inv = [inventory(tag, cfg) for tag, cfg in CLIPS.items()]
    print("Visible yellow lane lines in the digitised window")
    for r in inv:
        print(f"  {r['clip']:8s} {r['yellow_px']:>7d} yellow px   "
              f"lines: {r['separate_yellow_lines']}   "
              f"near line clipped by frame edge: {r['near_line_clipped_by_frame_edge']}")

    if arcs:
        tr = [transfer_test(cfg, arcs) for cfg in CLIPS.values()]
        print("\nWhat the lane-width reading would do (2.5 m between ropes)")
        for t in tr:
            print(f"  {t['clip']:8s} cap scale {t['m_per_px_cap']:.5f} m/px   "
                  f"lane scale {t['m_per_px_lane']:.5f} m/px   ratio {t['rope_over_cap']:.2f}")
            print(f"           head would be {t['head_implied_m']:.2f} m; "
                  f"pull would be {t['pull_arc_lane_m']:.1f} m "
                  f"(cap scale gives {t['pull_arc_body_m']:.2f} m)")
        ratios = {t["clip"]: t["rope_over_cap"] for t in tr}
        size_body = arcs["A3"] / arcs["Dressel"]
        size_lane = size_body * ratios["A3"] / ratios["Dressel"]
        print(f"\n  my pull / his pull, cap scale: {size_body:.2f}")
        print(f"  my pull / his pull, lane scale: {size_lane:.2f}")
        json.dump(dict(inventory=inv, transfer=tr,
                       size_ratio_cap=round(size_body, 3),
                       size_ratio_lane=round(size_lane, 3)),
                  open(OUT / "lane_rope_check.json", "w"), indent=2)
        print(f"\nWrote {OUT / 'lane_rope_check.json'}")
    else:
        json.dump(dict(inventory=inv), open(OUT / "lane_rope_check.json", "w"), indent=2)
        print(f"\nWrote {OUT / 'lane_rope_check.json'}")


if __name__ == "__main__":
    main()
