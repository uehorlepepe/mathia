"""Create the five teacher-facing figures in figures/.

Run from the repository root:

    python scripts/make_report_figures.py

The script uses only the digitised coordinates and the result tables that are
already committed, so the figures can be rebuilt without the source videos.
The video frame in figure 2 is optional: if data/a3yifan.mov is absent, that
panel is replaced by a plain note.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

LABELS = {"a2": "A2 (my clip 2)", "a3": "A3 (my clip 3)",
          "dressel": "Dressel (elite)"}
SHORT = {"a2": "A2", "a3": "A3", "dressel": "Dressel"}
COLOURS = {"a2": "#2ca02c", "a3": "#ff7f0e", "dressel": "#1f77b4"}
FULL_DEGREE = {"a2": 3, "a3": 3, "dressel": 3}
PULL_DEGREE = {"a2": 2, "a3": 3, "dressel": 3}

plt.rcParams.update({
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 9,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})


def load_full(tag: str) -> pd.DataFrame:
    return pd.read_csv(ROOT / f"data/{tag}_hand_points_metres.csv").sort_values("t")


def load_pull(tag: str) -> pd.DataFrame:
    path = ROOT / f"outputs/prelim/pull_phase/{tag}_pull_phase.csv"
    return pd.read_csv(path).sort_values("t")


def fit_curve(t: np.ndarray, x: np.ndarray, y: np.ndarray, degree: int):
    """Fit on normalised time u in [0, 1], so evaluation never extrapolates."""
    u = (t - t.min()) / (t.max() - t.min())
    cx = np.polyfit(u, x, degree)
    cy = np.polyfit(u, y, degree)
    return cx, cy


def save(fig, name: str) -> None:
    fig.savefig(FIG / name, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote figures/{name}")


def figure_workflow() -> None:
    """A plain-language map of the method."""
    fig, ax = plt.subplots(figsize=(12.6, 4.2))
    ax.set_xlim(0, 12.6)
    ax.set_ylim(0, 4.2)
    ax.axis("off")

    steps = [
        ("1. Film", "one arm pull\nfrom the side"),
        ("2. Click", "one point on the\nhand per frame"),
        ("3. Convert", "pixels to metres\nwith the swim cap"),
        ("4. Fit", "smooth curves\nx(t) and y(t)"),
        ("5. Calculate", "speed and\npath length"),
        ("6. Compare", "gap to the\nelite path"),
    ]
    w, h, gap = 1.72, 1.25, 0.28
    x0, y0 = 0.15, 2.05
    for i, (head, body) in enumerate(steps):
        x = x0 + i * (w + gap)
        box = FancyBboxPatch((x, y0), w, h, boxstyle="round,pad=0.04,rounding_size=0.12",
                             linewidth=1.2, edgecolor="#4a4a4a", facecolor="#f4f7fb")
        ax.add_patch(box)
        ax.text(x + w / 2, y0 + h - 0.26, head, ha="center", va="center",
                fontsize=11, weight="bold", color="#1f3f5f")
        ax.text(x + w / 2, y0 + 0.42, body, ha="center", va="center",
                fontsize=9.5, color="#222222")
        if i < len(steps) - 1:
            ax.add_patch(FancyArrowPatch((x + w + 0.02, y0 + h / 2),
                                         (x + w + gap - 0.02, y0 + h / 2),
                                         arrowstyle="-|>", mutation_scale=13,
                                         linewidth=1.2, color="#666666"))

    # Calibration note feeding step 3.
    cx = x0 + 2 * (w + gap) + w / 2
    ax.add_patch(FancyArrowPatch((cx, 1.45), (cx, y0 - 0.03),
                                 arrowstyle="-|>", mutation_scale=13,
                                 linewidth=1.2, color="#666666"))
    ax.text(cx, 1.18, "Calibration: the swim cap is about 0.19 m wide\n"
                      "in every clip, so its pixel width gives the scale.",
            ha="center", va="top", fontsize=9.5, color="#333333")

    ax.text(0.15, 0.28,
            "The same six steps are used for each clip. The result is a path in metres, "
            "not a set of subjective stroke comments.",
            ha="left", va="bottom", fontsize=9.5, color="#444444", style="italic")
    save(fig, "fig1_workflow.png")


def figure_video_to_path() -> None:
    """One clip shown as video, as x(t)/y(t), and as an x-y path."""
    tag = "a3"
    d = load_full(tag)
    cx, cy = fit_curve(d.t.to_numpy(), d.x_m.to_numpy(), d.y_m.to_numpy(),
                       FULL_DEGREE[tag])
    u = np.linspace(0, 1, 500)
    tt = d.t.min() + u * (d.t.max() - d.t.min())
    xx = np.polyval(cx, u)
    yy = np.polyval(cy, u)

    fig = plt.figure(figsize=(14.2, 5.4))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.55, 1.05, 1.05], wspace=0.28)

    # Panel A: one video frame with every clicked point drawn on it.
    ax = fig.add_subplot(gs[0, 0])
    video = ROOT / "data/a3yifan.mov"
    if video.exists():
        cap = cv2.VideoCapture(str(video))
        cap.set(cv2.CAP_PROP_POS_FRAMES, 180)
        ok, frame = cap.read()
        cap.release()
        if ok:
            crop = frame[350:1080, 250:1600]
            crop = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
            scale = 780 / crop.shape[1]
            crop = cv2.resize(crop, None, fx=scale, fy=scale)
            ax.imshow(crop)
            for _, r in d.iterrows():
                x = (r.x_px - 250) * scale
                y = (r.y_px - 350) * scale
                ax.plot(x, y, "o", ms=4.5, mfc="#ff2b2b", mec="white", mew=0.7)
            ax.set_title("A3: all 24 clicked hand positions", fontsize=13)
            ax.text(0.02, 0.03, "one dot = one frame; frame 180 is shown",
                    transform=ax.transAxes, fontsize=9, color="white",
                    bbox=dict(facecolor="black", alpha=0.45, pad=3, edgecolor="none"))
            ax.set_xticks([])
            ax.set_yticks([])
        else:
            ax.text(0.5, 0.5, "video frame not available", ha="center", va="center")
            ax.axis("off")
    else:
        ax.text(0.5, 0.5, "video frame not available\n(source video is not committed)",
                ha="center", va="center", fontsize=11)
        ax.axis("off")

    # Panel B: the two coordinate functions and their fits.
    ax = fig.add_subplot(gs[0, 1])
    t0 = d.t.min()
    ax.plot(d.t - t0, d.x_m, "o", ms=4.5, color="#1f77b4", alpha=0.75,
            label="x, clicked")
    ax.plot(d.t - t0, d.y_m, "o", ms=4.5, color="#d62728", alpha=0.75,
            label="y, clicked")
    ax.plot(tt - t0, xx, "-", lw=2.2, color="#1f77b4", label="x, fitted")
    ax.plot(tt - t0, yy, "-", lw=2.2, color="#d62728", label="y, fitted")
    ax.set_xlabel("time from first click (s)")
    ax.set_ylabel("position (m)")
    ax.set_title("Coordinates and smooth fits")
    ax.grid(alpha=0.25)
    ax.legend(loc="best", ncol=1)

    # Panel C: the path those coordinates trace.
    ax = fig.add_subplot(gs[0, 2])
    ax.plot(xx, yy, "-", lw=2.5, color=COLOURS[tag])
    ax.plot(d.x_m, d.y_m, "o", ms=4.5, mfc="white", mec=COLOURS[tag], mew=1.0)
    ax.set_xlabel("forward displacement (m)")
    ax.set_ylabel("vertical displacement (m)")
    ax.set_title("The hand path")
    ax.set_aspect("equal", adjustable="datalim")
    ax.grid(alpha=0.25)
    ax.annotate("start", xy=(d.x_m.iloc[0], d.y_m.iloc[0]),
                xytext=(8, 8), textcoords="offset points", fontsize=9)
    ax.annotate("end", xy=(d.x_m.iloc[-1], d.y_m.iloc[-1]),
                xytext=(-22, -14), textcoords="offset points", fontsize=9)
    ax.text(0.03, 0.04, "path length = 2.07 m\nR² = 0.991",
            transform=ax.transAxes, fontsize=10,
            bbox=dict(facecolor="white", alpha=0.85, edgecolor="#cccccc"))

    fig.suptitle("From video to a mathematical path (A3, full tracked movement)",
                 fontsize=14, y=1.02)
    save(fig, "fig2_video_to_path.png")


def figure_three_pulls() -> None:
    """The pull phase of each clip at the same physical scale."""
    pulls = {tag: load_pull(tag) for tag in ("a2", "a3", "dressel")}
    fits = {}
    for tag, d in pulls.items():
        cx, cy = fit_curve(d.t.to_numpy(), d.x_m.to_numpy(), d.y_m.to_numpy(),
                           PULL_DEGREE[tag])
        g = np.linspace(0, 1, 300)
        fits[tag] = (np.polyval(cx, g), np.polyval(cy, g))

    all_x = np.concatenate([v[0] for v in fits.values()])
    all_y = np.concatenate([v[1] for v in fits.values()])
    xlim = (all_x.min() - 0.08, all_x.max() + 0.08)
    ylim = (all_y.min() - 0.08, all_y.max() + 0.08)

    fig, axes = plt.subplots(2, 2, figsize=(12.0, 6.8))
    axes = axes.ravel()
    arcs = {"a2": 0.762, "a3": 1.764, "dressel": 1.418}
    r2s = {"a2": 0.9891, "a3": 0.9945, "dressel": 0.9939}

    for ax, tag in zip(axes[:3], ("a2", "a3", "dressel")):
        d = pulls[tag]
        X, Y = fits[tag]
        ax.plot(X, Y, "-", lw=2.6, color=COLOURS[tag], label="fitted path")
        ax.plot(d.x_m, d.y_m, "o", ms=5, mfc="white", mec=COLOURS[tag],
                mew=1.0, label="clicked points")
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        ax.set_aspect("equal", adjustable="box")
        ax.grid(alpha=0.25)
        ax.set_title(f"{LABELS[tag]}: pull phase")
        ax.set_xlabel("forward displacement (m)")
        ax.set_ylabel("vertical displacement (m)")
        ax.text(0.04, 0.05,
                f"length = {arcs[tag]:.2f} m\nR² = {r2s[tag]:.3f}",
                transform=ax.transAxes, fontsize=10,
                bbox=dict(facecolor="white", alpha=0.85, edgecolor="#cccccc"))
        ax.legend(loc="upper right")

    ax = axes[3]
    for tag in ("a2", "a3", "dressel"):
        X, Y = fits[tag]
        ax.plot(X, Y, "-", lw=2.6, color=COLOURS[tag], label=SHORT[tag])
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.25)
    ax.set_title("All three, same scale")
    ax.set_xlabel("forward displacement (m)")
    ax.set_ylabel("vertical displacement (m)")
    ax.legend(loc="upper right")
    ax.text(0.04, 0.05,
            "Dressel's clip is slowed,\nso only shape and length\nare compared.",
            transform=ax.transAxes, fontsize=9,
            bbox=dict(facecolor="white", alpha=0.85, edgecolor="#cccccc"))

    fig.suptitle("One pull, three swimmers, one scale", fontsize=15, y=0.99)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    save(fig, "fig3_three_pulls.png")


def figure_click_checks() -> None:
    """One frame per clip with every clicked point drawn on it."""
    specs = {
        "a2": dict(video="data/a2yifan.mov", frame=329,
                   crop=(300, 700, 950, 1400), label="A2"),
        "a3": dict(video="data/a3yifan.mov", frame=180,
                   crop=(350, 1080, 250, 1600), label="A3"),
        "dressel": dict(video="data/dressel.mp4", frame=706,
                        crop=(280, 620, 520, 980), label="Dressel"),
    }
    fig, axes = plt.subplots(1, 3, figsize=(15.0, 5.2))
    for ax, (tag, spec) in zip(axes, specs.items()):
        d = pd.read_csv(ROOT / f"data/{tag}_hand_manual.csv").sort_values("frame")
        video = ROOT / spec["video"]
        y0, y1, x0, x1 = spec["crop"]
        if video.exists():
            cap = cv2.VideoCapture(str(video))
            cap.set(cv2.CAP_PROP_POS_FRAMES, spec["frame"])
            ok, frame = cap.read()
            cap.release()
            if ok:
                crop = frame[y0:y1, x0:x1]
                crop = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
                ax.imshow(crop)
                ax.plot(d.x_px - x0, d.y_px - y0, "-", lw=1.0,
                        color="white", alpha=0.7)
                ax.plot(d.x_px - x0, d.y_px - y0, "o", ms=5.0,
                        mfc="#ff2b2b", mec="white", mew=0.8)
                ax.set_title(f"{spec['label']}: {len(d)} clicked points")
                ax.set_xticks([])
                ax.set_yticks([])
                continue
        ax.text(0.5, 0.5, "video frame not available\n(source video is not committed)",
                ha="center", va="center", fontsize=10)
        ax.axis("off")
    fig.text(0.5, 0.01,
             "Each dot is one clicked frame, drawn on one frame of the clip. "
             "The clicks sit on the hand, not on the body or the lane rope.",
             ha="center", fontsize=10, color="#333333")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    save(fig, "fig5_click_checks.png")


def figure_comparison() -> None:
    """The two headline comparison scores."""
    comp = pd.read_csv(ROOT / "outputs/prelim/comparisons.csv")
    rmse = {
        "a2": float(comp.loc[(comp.pair == "Dressel vs A2") &
                             (comp.window == "pull_phase"), "position_rmse_m"].iloc[0]),
        "a3": float(comp.loc[(comp.pair == "Dressel vs A3") &
                             (comp.window == "pull_phase"), "position_rmse_m"].iloc[0]),
    }
    table = pd.read_csv(ROOT / "outputs/prelim/summary_table.csv")
    r2 = {}
    for tag in ("a2", "a3"):
        row = table[(table.track == tag.upper()) & (table.window == "pull_phase")].iloc[0]
        r2[tag] = float(row.r2_his_model_on_mine_scaled)

    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.6))
    tags = ["a2", "a3"]
    colours = [COLOURS[t] for t in tags]
    names = [SHORT[t] for t in tags]

    ax = axes[0]
    vals = [100 * rmse[t] for t in tags]
    bars = ax.bar(names, vals, color=colours, width=0.55)
    ax.set_ylabel("typical gap (cm)")
    ax.set_title("Distance from Dressel's path\n(lower is better)")
    ax.set_ylim(0, max(vals) * 1.28)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 1.2, f"{v:.0f} cm",
                ha="center", va="bottom", fontsize=12, weight="bold")
    ax.grid(alpha=0.25, axis="y")

    ax = axes[1]
    vals = [r2[t] for t in tags]
    bars = ax.bar(names, vals, color=colours, width=0.55)
    ax.set_ylabel("R² after one size adjustment")
    ax.set_title("Shape agreement with Dressel\n(higher is better)")
    ax.set_ylim(0, 1.0)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.02, f"{v:.2f}",
                ha="center", va="bottom", fontsize=12, weight="bold")
    ax.grid(alpha=0.25, axis="y")

    fig.text(0.5, -0.02,
             "The R² score removes overall size, so it compares shape. "
             "The distance in centimetres also includes scale error, which is about 15%.",
             ha="center", fontsize=9.5, color="#444444")
    fig.tight_layout()
    save(fig, "fig4_comparison.png")


def main() -> None:
    figure_workflow()
    figure_video_to_path()
    figure_three_pulls()
    figure_comparison()
    figure_click_checks()


if __name__ == "__main__":
    main()
