"""Restrict all three clips to the pull phase (hand entry -> end of pull sweep)
and recompute the cross-model R^2 so window length stops confounding it.

Phase definition: entry is the frame of maximum forward hand extension (the
hand reaches furthest forward, i.e. just after entry); exit is the frame where
the hand reaches its rearmost point, the end of the backward sweep. Frames
after that are recovery and are dropped.

    python scripts/pull_phase.py
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OUT = Path("outputs/prelim/pull_phase")
TRACKS = {"a2": 2, "a3": 3, "dressel": 3}  # degree used per clip (a2: too few points for a cubic)


def load(tag):
    d = pd.read_csv(f"data/{tag}_hand_points_metres.csv").sort_values("t").reset_index(drop=True)
    t = d.t.to_numpy()
    return t - t.min(), d.x_m.to_numpy(), d.y_m.to_numpy(), d.frame.to_numpy()


def phase_window(x, search_end):
    entry = int(np.argmax(x[:search_end]))
    exit_ = entry + int(np.argmin(x[entry:]))
    return entry, exit_


def normalised(t):
    span = t.max() - t.min()
    return (t - t.min()) / span if span > 0 else np.zeros_like(t)


def fit(u, x, y, deg):
    return np.polyfit(u, x, deg), np.polyfit(u, y, deg)


def predict(cx, cy, u):
    return np.c_[np.polyval(cx, u), np.polyval(cy, u)]


def r2(pred, data, allow_scale=False):
    ss_tot = float(((data - data.mean(0)) ** 2).sum())
    if allow_scale:
        s = float((pred * data).sum() / (pred * pred).sum())
        pred = s * pred
    else:
        s = float("nan")
    ss_res = float(((data - pred) ** 2).sum())
    return 1 - ss_res / ss_tot, float(np.sqrt(ss_res / len(data))), s


def rotate_scale(pred, data):
    """Best rotation + scale only (no translation): is it the same shape, seen
    at a different angle? Diagnostic only."""
    U, S, Vt = np.linalg.svd(pred.T @ data)
    R = U @ Vt
    s = S.sum() / float((pred ** 2).sum())
    return r2(s * pred @ R, data)[0], float(np.degrees(np.arctan2(R[1, 0], R[0, 0]))), s


def arc_length(cx, cy, deg, n=2000):
    g = np.linspace(0, 1, n)
    vx = np.polyval(np.polyder(cx), g)
    vy = np.polyval(np.polyder(cy), g)
    return float(np.trapezoid(np.hypot(vx, vy), g))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    W = {}
    for tag in TRACKS:
        t, x, y, frame = load(tag)
        e, f = phase_window(x, len(x) if tag != "a2" else 16)
        sl = slice(e, f + 1)
        W[tag] = dict(
            t=t[sl] - t[e],
            x=x[sl] - x[e],
            y=y[sl] - y[e],
            frames=(int(frame[e]), int(frame[f])),
            entry=e,
            exit_=f,
        )
        # write the restricted points so the exploration can show them
        pd.DataFrame({
            "frame": frame[sl], "t": t[sl] - t[e],
            "x_m": x[sl] - x[e], "y_m": y[sl] - y[e],
        }).to_csv(OUT / f"{tag}_pull_phase.csv", index=False)

    rows = []
    for tag, deg in TRACKS.items():
        w = W[tag]
        u = normalised(w["t"])
        cx, cy = fit(u, w["x"], w["y"], deg)
        D = np.c_[w["x"], w["y"]]
        r2_own, rmse_own, _ = r2(predict(cx, cy, u), D)
        g = np.linspace(0, 1, 2000)
        # d/du is metres per unit normalised time; divide by the clip's own
        # duration to get m/s
        speed = np.hypot(np.polyval(np.polyder(cx), g), np.polyval(np.polyder(cy), g))
        dur = float(w["t"].max())
        arc = arc_length(cx, cy, deg)
        rows.append(dict(
            track=tag.upper() if tag != "dressel" else "Dressel",
            frames=f"{w['frames'][0]}-{w['frames'][1]}",
            n_points=int(len(w["t"])),
            duration_s=round(float(w["t"].max()), 3),
            degree=deg,
            forward_span_m=round(float(w["x"].max() - w["x"].min()), 3),
            vertical_span_m=round(float(w["y"].max() - w["y"].min()), 3),
            arc_length_m=round(arc, 3),
            mean_speed_m_s=round(arc / dur, 3),
            max_speed_m_s=round(float(speed.max()) / dur, 3),
            r2_own_fit=round(r2_own, 4),
            fit_rmse_mm=round(1000 * rmse_own, 1),
        ))
    own = pd.DataFrame(rows)
    own.to_csv(OUT / "pull_phase_own_fits.csv", index=False)
    print("Pull-phase fits (entry -> end of backward sweep)")
    print(own.to_string(index=False))

    cross = []
    for target in ["a3", "a2"]:
        for src in ["dressel"]:
            deg = TRACKS[src]
            ws, wt = W[src], W[target]
            cx, cy = fit(normalised(ws["t"]), ws["x"], ws["y"], deg)
            # target degree must match the source model's order for a like-for-like test
            r2_raw, rmse, _ = r2(predict(cx, cy, normalised(wt["t"])), np.c_[wt["x"], wt["y"]])
            r2_si, _, s = r2(predict(cx, cy, normalised(wt["t"])), np.c_[wt["x"], wt["y"]], allow_scale=True)
            r2_rot, angle, srot = rotate_scale(predict(cx, cy, normalised(wt["t"])), np.c_[wt["x"], wt["y"]])
            cross.append(dict(source=src.upper() if src != "dressel" else "Dressel",
                              target=target.upper(), degree=deg,
                              r2=round(r2_raw, 4), r2_scale_invariant=round(r2_si, 4),
                              r2_rotated=round(r2_rot, 4), angle_deg=round(angle, 1),
                              scale=round(s, 3), rotation_scale=round(srot, 3),
                              rmse_mm=round(1000 * rmse, 1)))
    # reverse direction, for completeness
    for src in ["a3", "a2"]:
        deg = TRACKS["dressel"]
        ws, wt = W[src], W["dressel"]
        cx, cy = np.polyfit(normalised(ws["t"]), ws["x"], deg), np.polyfit(normalised(ws["t"]), ws["y"], deg)
        r2_raw, rmse, _ = r2(predict(cx, cy, normalised(wt["t"])), np.c_[wt["x"], wt["y"]])
        r2_si, _, s = r2(predict(cx, cy, normalised(wt["t"])), np.c_[wt["x"], wt["y"]], allow_scale=True)
        cross.append(dict(source=src.upper(), target="Dressel", degree=deg,
                          r2=round(r2_raw, 4), r2_scale_invariant=round(r2_si, 4),
                          r2_rotated=round(rotate_scale(predict(cx, cy, normalised(wt["t"])), np.c_[wt["x"], wt["y"]])[0], 4),
                          angle_deg=round(rotate_scale(predict(cx, cy, normalised(wt["t"])), np.c_[wt["x"], wt["y"]])[1], 1),
                          scale=round(s, 3),
                          rotation_scale=round(rotate_scale(predict(cx, cy, normalised(wt["t"])), np.c_[wt["x"], wt["y"]])[2], 3),
                          rmse_mm=round(1000 * rmse, 1)))

    cross_df = pd.DataFrame(cross)
    cross_df.to_csv(OUT / "pull_phase_cross_model.csv", index=False)
    print("\nCross-model R^2 on the restricted pull phase")
    print(cross_df.to_string(index=False))

    his_own = float(own.loc[own.track == "Dressel", "r2_own_fit"].iloc[0])
    summary = {
        "phase_definition": "entry = max forward extension, exit = rearmost point of the backward sweep",
        "dressel_own_r2": his_own,
        "own_fits": own.to_dict(orient="records"),
        "cross_model": cross,
        "gap_to_his_own_r2": {
            c["target"]: round(his_own - c["r2_scale_invariant"], 4)
            for c in cross if c["target"] != "Dressel"
        },
    }
    (OUT / "pull_phase_summary.json").write_text(json.dumps(summary, indent=2))

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    for tag, label in [("dressel", "Dressel"), ("a3", "A3"), ("a2", "A2")]:
        w = W[tag]
        u = normalised(w["t"])
        cx, cy = fit(u, w["x"], w["y"], TRACKS[tag])
        g = np.linspace(0, 1, 400)
        axes[0].plot(np.polyval(cx, g), np.polyval(cy, g), lw=2,
                     label=f"{label} ({w['t'].max():.2f} s, n={len(u)})")
        axes[0].plot(w["x"], w["y"], ".", ms=5, alpha=0.6)
        axes[1].plot(g, np.hypot(np.polyval(np.polyder(cx), g),
                                 np.polyval(np.polyder(cy), g)) / float(w["t"].max()),
                     lw=2, label=label)
    axes[0].set_title("pull phase only (entry to end of sweep)")
    axes[0].set_xlabel("forward (m)")
    axes[0].set_ylabel("vertical (m)")
    axes[0].axis("equal")
    axes[0].grid(alpha=0.3)
    axes[0].legend(fontsize=8)
    axes[1].set_title("hand speed within the pull")
    axes[1].set_xlabel("normalised pull time")
    axes[1].set_ylabel("speed (m/s)")
    axes[1].grid(alpha=0.3)
    axes[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "pull_phase.png", dpi=170)
    plt.close(fig)
    print(f"\nDressel's own R^2 on the same phase: {his_own:.4f}")
    print(f"Wrote {OUT}/")


if __name__ == "__main__":
    main()
