"""Fit parametric hand trajectories, compute kinematics/arc length, and compare.

Examples:
    python scripts/analyze.py data/me_hand.csv --label Me
    python scripts/analyze.py data/me_hand.csv data/mcevoy_hand.csv \
        --labels Me McEvoy --compare

Input is the CSV written by track_hand.py. If x_m/y_m are empty, pass
--m-per-px (or re-run tracking with --calibration).

Outputs (in --outdir):
    fit.csv          fitted x(t), y(t), vx, vy, speed, cumulative arc length
    summary.json     polynomial degrees, R^2, RMSE, arc length, speed stats
    *_trajectory.png x-y path
    *_curves.png     x(t), y(t), speed(t)
    *_residuals.png  fit residuals
    comparison.png   normalised-time overlay (only with two files)
"""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.integrate import simpson


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("csv", nargs="+", help="one CSV, or two to compare")
    p.add_argument("--labels", nargs="+")
    p.add_argument("--outdir", default="outputs")
    p.add_argument("--m-per-px", type=float, default=None)
    p.add_argument("--flip-x", action="store_true",
                   help="make the swimming direction positive")
    p.add_argument("--degree", type=int, default=None,
                   help="polynomial degree (default: chosen by BIC, 2-5)")
    p.add_argument("--max-degree", type=int, default=5)
    p.add_argument("--sigma-clip", type=float, default=None,
                   help="iteratively drop residual outliers, e.g. 3.0")
    p.add_argument("--start", type=float, default=None, help="seconds")
    p.add_argument("--end", type=float, default=None, help="seconds")
    return p.parse_args()


def load_track(path, m_per_px, flip_x, start, end):
    df = pd.read_csv(path)
    df = df.sort_values("t").reset_index(drop=True)

    if m_per_px is not None:
        x = df["x_px"].to_numpy() * m_per_px
        y = -df["y_px"].to_numpy() * m_per_px
    elif "x_m" in df and df["x_m"].notna().all():
        x = df["x_m"].to_numpy()
        y = df["y_m"].to_numpy()
    else:
        print(f"WARNING: {path} has no metre columns; working in pixels")
        x = df["x_px"].to_numpy()
        y = -df["y_px"].to_numpy()

    if flip_x:
        x = -x

    t = df["t"].to_numpy()
    keep = np.ones(len(t), dtype=bool)
    if start is not None:
        keep &= t >= start
    if end is not None:
        keep &= t <= end
    t, x, y = t[keep], x[keep], y[keep]

    x = x - x[0]
    y = y - y[0]
    return t, x, y


def choose_degree(t, y, max_degree):
    best = None
    for d in range(2, max_degree + 1):
        if len(t) <= d + 1:
            break
        coef = np.polyfit(t, y, d)
        resid = y - np.polyval(coef, t)
        sse = float(np.sum(resid ** 2))
        n = len(t)
        bic = n * np.log(max(sse, 1e-12) / n) + (d + 1) * np.log(n)
        if best is None or bic < best[0]:
            best = (bic, d)
    return best[1] if best else min(2, len(t) - 1)


def robust_polyfit(t, y, degree, sigma_clip):
    mask = np.ones(len(t), dtype=bool)
    for _ in range(10):
        coef = np.polyfit(t[mask], y[mask], degree)
        resid = y - np.polyval(coef, t)
        if sigma_clip is None:
            break
        sd = np.std(resid[mask])
        new_mask = np.abs(resid) <= sigma_clip * sd
        if new_mask.sum() < degree + 2 or np.array_equal(new_mask, mask):
            break
        mask = new_mask
    return coef, mask


def fit_one(label, t, x, y, args):
    dt = np.median(np.diff(t))
    deg_x = args.degree or choose_degree(t, x, args.max_degree)
    deg_y = args.degree or choose_degree(t, y, args.max_degree)
    cx, mx = robust_polyfit(t, x, deg_x, args.sigma_clip)
    cy, my = robust_polyfit(t, y, deg_y, args.sigma_clip)
    use = mx & my

    dcx = np.polyder(cx)
    dcy = np.polyder(cy)

    tt = np.linspace(t.min(), t.max(), 1000)
    xx = np.polyval(cx, tt)
    yy = np.polyval(cy, tt)
    vx = np.polyval(dcx, tt)
    vy = np.polyval(dcy, tt)
    speed = np.hypot(vx, vy)

    ds = speed
    s = np.concatenate([[0.0], np.cumsum((ds[1:] + ds[:-1]) / 2 * np.diff(tt))])
    arc_length = float(simpson(speed, tt))

    rx = x - np.polyval(cx, t)
    ry = y - np.polyval(cy, t)
    ss_res = float(np.sum(rx[use] ** 2 + ry[use] ** 2))
    ss_tot = float(np.sum((x[use] - x[use].mean()) ** 2 +
                          (y[use] - y[use].mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    rmse_fit = float(np.sqrt(np.mean(rx[use] ** 2 + ry[use] ** 2)))

    summary = {
        "label": label,
        "n_points": int(len(t)),
        "n_used": int(use.sum()),
        "duration_s": float(t.max() - t.min()),
        "dt_s": float(dt),
        "degree_x": int(deg_x),
        "degree_y": int(deg_y),
        "coef_x_descending": cx.tolist(),
        "coef_y_descending": cy.tolist(),
        "r2_2d": float(r2),
        "fit_rmse": rmse_fit,
        "arc_length": arc_length,
        "mean_speed": float(np.mean(speed)),
        "max_speed": float(np.max(speed)),
        "forward_range": float(xx.max() - xx.min()),
        "vertical_range": float(yy.max() - yy.min()),
    }
    fit_df = pd.DataFrame({
        "t": tt, "x": xx, "y": yy, "vx": vx, "vy": vy,
        "speed": speed, "arc_length": s,
    })
    return summary, fit_df, (t, x, y, rx, ry, use)


def save_single_plots(label, summary, fit_df, raw, outdir):
    t, x, y, rx, ry, use = raw
    prefix = outdir / label.lower().replace(" ", "_")

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(fit_df["x"], fit_df["y"], "b-", lw=2, label="polynomial model")
    ax.plot(x[use], y[use], "k.", ms=6, alpha=0.6, label="digitised")
    ax.plot(x[~use], y[~use], "rx", ms=8, label="clipped outliers")
    ax.set_xlabel("forward displacement (m)")
    ax.set_ylabel("vertical displacement (m)")
    ax.set_title(f"{label}: hand trajectory")
    ax.axis("equal")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(f"{prefix}_trajectory.png", dpi=200)
    plt.close(fig)

    fig, axes = plt.subplots(3, 1, figsize=(8, 8), sharex=True)
    axes[0].plot(t, x, "k.", ms=4, alpha=0.6)
    axes[0].plot(fit_df["t"], fit_df["x"], "b-", lw=2)
    axes[0].set_ylabel("x (m)")
    axes[1].plot(t, y, "k.", ms=4, alpha=0.6)
    axes[1].plot(fit_df["t"], fit_df["y"], "b-", lw=2)
    axes[1].set_ylabel("y (m)")
    axes[2].plot(fit_df["t"], fit_df["speed"], "r-", lw=2)
    axes[2].set_ylabel("speed (m/s)")
    axes[2].set_xlabel("time (s)")
    for a in axes:
        a.grid(alpha=0.3)
    fig.suptitle(f"{label}: fitted position and speed")
    fig.tight_layout()
    fig.savefig(f"{prefix}_curves.png", dpi=200)
    plt.close(fig)

    fig, axes = plt.subplots(2, 1, figsize=(8, 5), sharex=True)
    axes[0].axhline(0, color="gray", lw=1)
    axes[0].plot(t, rx, "b.", ms=5)
    axes[0].set_ylabel("x residual (m)")
    axes[1].axhline(0, color="gray", lw=1)
    axes[1].plot(t, ry, "r.", ms=5)
    axes[1].set_ylabel("y residual (m)")
    axes[1].set_xlabel("time (s)")
    for a in axes:
        a.grid(alpha=0.3)
    fig.suptitle(f"{label}: fit residuals")
    fig.tight_layout()
    fig.savefig(f"{prefix}_residuals.png", dpi=200)
    plt.close(fig)


def normalise(t, x, y, n=300):
    tn = (t - t.min()) / (t.max() - t.min())
    grid = np.linspace(0, 1, n)
    return grid, np.interp(grid, tn, x), np.interp(grid, tn, y)


def compare(tracks, summaries, outdir):
    grid = None
    aligned = []
    for label, (t, x, y, *_rest) in tracks.items():
        g, xn, yn = normalise(t, x, y)
        aligned.append((label, xn - xn[0], yn - yn[0]))
        grid = g

    n = min(len(pair[1]) for pair in aligned)
    d = np.sqrt((aligned[0][1][:n] - aligned[1][1][:n]) ** 2 +
                (aligned[0][2][:n] - aligned[1][2][:n]) ** 2)
    rmse = float(np.sqrt(np.mean(d ** 2)))

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for label, xn, yn in aligned:
        axes[0].plot(xn, yn, lw=2, label=label)
        axes[1].plot(grid, np.hypot(np.gradient(xn, grid),
                                    np.gradient(yn, grid)) *
                     (tracks[label][0].max() - tracks[label][0].min()),
                     lw=2, label=label)
    axes[0].set_xlabel("forward displacement (m)")
    axes[0].set_ylabel("vertical displacement (m)")
    axes[0].set_title("normalised-time hand paths")
    axes[0].axis("equal")
    axes[0].legend()
    axes[0].grid(alpha=0.3)
    axes[1].set_xlabel("normalised time")
    axes[1].set_ylabel("speed (m/s)")
    axes[1].set_title("speed")
    axes[1].legend()
    axes[1].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(outdir / "comparison.png", dpi=200)
    plt.close(fig)

    return {
        "labels": [a[0] for a in aligned],
        "position_rmse": rmse,
        "mean_position_difference": float(np.mean(d)),
        "max_position_difference": float(np.max(d)),
        "arc_length_difference": abs(summaries[0]["arc_length"] -
                                     summaries[1]["arc_length"]),
    }


def main():
    args = parse_args()
    if len(args.csv) > 2:
        raise SystemExit("At most two CSVs can be compared")
    labels = args.labels or [Path(p).stem for p in args.csv]
    if len(labels) != len(args.csv):
        raise SystemExit("--labels must match the number of CSV files")

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    summaries, tracks = [], {}
    for path, label in zip(args.csv, labels):
        t, x, y = load_track(path, args.m_per_px, args.flip_x,
                             args.start, args.end)
        if len(t) < 5:
            raise SystemExit(f"{path}: need at least 5 digitised frames")
        summary, fit_df, raw = fit_one(label, t, x, y, args)
        prefix = label.lower().replace(" ", "_")
        fit_df.to_csv(outdir / f"{prefix}_fit.csv", index=False)
        save_single_plots(label, summary, fit_df, raw, outdir)
        summaries.append(summary)
        tracks[label] = (t, x, y) + raw[3:]
        print(f"\n{label}")
        print(f"  points: {summary['n_points']} (used {summary['n_used']})")
        print(f"  degree x/y: {summary['degree_x']}/{summary['degree_y']}")
        print(f"  R^2: {summary['r2_2d']:.4f}   fit RMSE: "
              f"{summary['fit_rmse']:.5f}")
        print(f"  arc length: {summary['arc_length']:.4f}")
        print(f"  mean/max speed: {summary['mean_speed']:.3f} / "
              f"{summary['max_speed']:.3f}")

    if len(args.csv) == 2:
        comp = compare(tracks, summaries, outdir)
        summaries.append({"comparison": comp})
        print("\nComparison")
        print(f"  normalised path RMSE: {comp['position_rmse']:.4f}")
        print(f"  arc length difference: "
              f"{comp['arc_length_difference']:.4f}")

    (outdir / "summary.json").write_text(json.dumps(summaries, indent=2))
    print(f"\nWrote results to {outdir}/")


if __name__ == "__main__":
    main()
