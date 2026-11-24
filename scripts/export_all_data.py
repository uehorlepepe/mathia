"""Export every digitised point into one flat CSV.

One row per tracked frame per clip, with the metre coordinates, the phase-window
flag and the clip's calibration constants attached, so the file stands alone
without the per-clip tracker CSVs or JSON calibrations.

Usage:  .venv/bin/python scripts/export_all_data.py
Output: outputs/all_data.csv
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "all_data.csv"

# clip stem -> (display name, pull-phase window used in the analysis)
CLIPS = {
    "a2": ("Yifan A2", (320, 328)),
    "a3": ("Yifan A3", (177, 194)),
    "dressel": ("Elite", (682, 778)),
}
TIME_BASE = {
    "a2": "real time",
    "a3": "real time",
    "dressel": "slowed (3.36 frames per picture)",
}


def main() -> None:
    rows = []
    for stem, (name, (lo, hi)) in CLIPS.items():
        cal = json.loads((ROOT / f"data/{stem}.calibration_body.json").read_text())
        d = pd.read_csv(ROOT / f"data/{stem}_hand_manual_bodycal.csv")
        for _, r in d.sort_values("frame").iterrows():
            rows.append(
                {
                    "swimmer": name,
                    "clip": stem,
                    "video": Path(cal["video"]).name,
                    "frame": int(r["frame"]),
                    "t_s": round(float(r["t"]), 4),
                    "x_px": round(float(r["x_px"]), 1),
                    "y_px": round(float(r["y_px"]), 1),
                    "x_m": round(float(r["x_m"]), 4),
                    "y_m": round(float(r["y_m"]), 4),
                    "in_pull_window": int(lo <= r["frame"] <= hi),
                    "m_per_px": round(float(cal["m_per_px"]), 6),
                    "scale_unc_pct": round(100 * float(cal["m_per_px_rel_unc"]), 1),
                    "fps": cal["fps"],
                    "image_w": cal["image_width"],
                    "image_h": cal["image_height"],
                    "time_base": TIME_BASE[stem],
                    "calibration": cal["method"],
                }
            )

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    print(f"wrote {OUT.relative_to(ROOT)}: {len(out)} rows, {out['clip'].nunique()} clips")
    print(out.groupby("swimmer").agg(points=("frame", "size"),
                                     pull_points=("in_pull_window", "sum")).to_string())


if __name__ == "__main__":
    main()
