"""Summary table, pairwise comparisons and the three-way figure.

Framing: the only R^2 that is a result is *his model applied to my track*.
Fitting his own track is how the model is obtained, not a competing score, so
his own R^2 is recorded as fit quality and never used as a benchmark.

Sizes: the fitted scale factor k says how much his pull-phase path must be
enlarged to sit on mine (k > 1 means my path is larger). The figure shows both
the enlarged comparison and the true-size comparison, because the two clips are
calibrated on the swimmer's own cap, the only length in these videos that is at
the swimmer's distance from the lens.

Two windows are reported, because they answer different questions:

  full_track  every digitised frame, entry through recovery
  pull_phase  entry (max forward extension) to the end of the backward sweep,
              i.e. the same physical phase in all three clips

    python scripts/summary_table.py
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OUT = Path("outputs/prelim")
PHASE = OUT / "pull_phase"
PAIRS = {
    "a2_vs_a3": OUT / "a2_vs_a3",
    "a2_vs_dressel": OUT / "a2_vs_dressel",
    "a3_vs_dressel": OUT / "a3_vs_dressel",
}
CALIBRATIONS = ["a2", "a3", "dressel"]
LABELS = {"a2": "A2", "a3": "A3", "dressel": "Dressel"}
PHASE_DEGREE = {"a2": 2, "a3": 3, "dressel": 3}
COLOURS = {"a2": "#2ca02c", "a3": "#ff7f0e", "dressel": "#1f77b4"}


def load_repeat_factor():
    path = Path("outputs/check/duplicate_frames_dressel.json")
    if not path.exists():
        return None
    for r in json.loads(path.read_text())["results"]:
        if r["scope"].startswith("frames"):
            return r["frames_per_unique_picture"]
    return None


def time_basis(tag, repeat):
    if tag != "dressel":
        return "real time (native 29.97 fps)"
    if repeat is None:
        return "slowed footage (run check_duplicate_frames.py)"
    return f"slowed footage ({repeat:g} frames per picture, not real time)"


def main():
    summaries = {k: json.loads((v / "summary.json").read_text()) for k, v in PAIRS.items()}
    cal = {t: json.loads(Path(f"data/{t}.calibration_cap.json").read_text()) for t in CALIBRATIONS}
    repeat = load_repeat_factor()

    def track(summary, label):
        return [x for x in summary if isinstance(x, dict) and x.get("label") == label][0]

    def cross_full(summary, source, target):
        block = [x for x in summary if isinstance(x, dict) and "cross_model_r2" in x][0]
        for c in block["cross_model_r2"]:
            if c["source"] == source and c["target"] == target:
                return c
        return None

    full = {
        "a2": track(summaries["a2_vs_a3"], "A2"),
        "a3": track(summaries["a2_vs_a3"], "A3"),
        "dressel": track(summaries["a2_vs_dressel"], "Dressel"),
    }
    full_cross = {
        "a2": cross_full(summaries["a2_vs_dressel"], "Dressel", "A2"),
        "a3": cross_full(summaries["a3_vs_dressel"], "Dressel", "A3"),
        "dressel": None,
    }

    phase_own = pd.read_csv(PHASE / "pull_phase_own_fits.csv")
    phase_cross = pd.read_csv(PHASE / "pull_phase_cross_model.csv")

    def phase_row(label):
        return phase_own[phase_own.track == label].iloc[0]

    def phase_cross_row(target):
        return phase_cross[(phase_cross.source == "Dressel") & (phase_cross.target == target)].iloc[0]

    rows = []
    for tag in ["a2", "a3", "dressel"]:
        label = LABELS[tag]
        c = cal[tag]
        cm = c["cap_measurement"]
        rel = c["m_per_px_rel_unc"]
        d = pd.read_csv(f"data/{tag}_hand_points_metres.csv")
        base = dict(
            track=label,
            time_base=time_basis(tag, repeat),
            cap_width_px=cm["width_px_mean"],
            cap_sd_px=cm["width_px_sd"],
            cap_frames=cm["n_frames"],
            m_per_px=round(c["m_per_px"], 6),
            scale_unc_pct=round(100 * rel, 1),
        )
        fc = full_cross[tag]
        rows.append(dict(
            base,
            window="full_track",
            frames=f"{int(d.frame.min())}-{int(d.frame.max())}",
            n_points=full[tag]["n_points"],
            duration_s=round(full[tag]["duration_s"], 3),
            degree=f"{full[tag]['degree_x']}/{full[tag]['degree_y']}",
            r2_fit_own_track=round(full[tag]["r2_2d"], 4),
            r2_his_model_on_mine=round(fc["r2"], 4) if fc else None,
            size_factor_k=round(fc["scale"], 4) if fc and "scale" in fc else None,
            r2_his_model_on_mine_scaled=round(fc["r2_scaled"], 4) if fc else None,
            r2_his_model_on_mine_rotated=None,
            rotation_deg=None,
            fit_rmse_mm=round(1000 * full[tag]["fit_rmse"], 1),
            forward_span_m=round(full[tag]["forward_range"], 3),
            vertical_span_m=round(full[tag]["vertical_range"], 3),
            arc_length_m=round(full[tag]["arc_length"], 3),
            arc_pm_m=round(full[tag]["arc_length"] * rel, 3),
            mean_speed_m_s=round(full[tag]["mean_speed"], 3),
            max_speed_m_s=round(full[tag]["max_speed"], 3),
        ))

        p = phase_row(label)
        pc = phase_cross_row(label) if tag != "dressel" else None
        rows.append(dict(
            base,
            window="pull_phase",
            frames=p.frames,
            n_points=int(p.n_points),
            duration_s=float(p.duration_s),
            degree=str(int(p.degree)),
            r2_fit_own_track=float(p.r2_own_fit),
            r2_his_model_on_mine=float(pc.r2) if pc is not None else None,
            size_factor_k=float(pc.scale) if pc is not None else None,
            r2_his_model_on_mine_scaled=float(pc.r2_scale_invariant) if pc is not None else None,
            r2_his_model_on_mine_rotated=float(pc.r2_rotated) if pc is not None else None,
            rotation_deg=float(pc.angle_deg) if pc is not None else None,
            fit_rmse_mm=float(p.fit_rmse_mm),
            forward_span_m=float(p.forward_span_m),
            vertical_span_m=float(p.vertical_span_m),
            arc_length_m=float(p.arc_length_m),
            arc_pm_m=round(float(p.arc_length_m) * rel, 3),
            mean_speed_m_s=float(p.mean_speed_m_s),
            max_speed_m_s=float(p.max_speed_m_s),
        ))

    table = pd.DataFrame(rows)
    order = ["track", "window", "frames", "n_points", "duration_s", "degree",
             "r2_fit_own_track", "r2_his_model_on_mine", "r2_his_model_on_mine_scaled",
             "size_factor_k", "r2_his_model_on_mine_rotated", "rotation_deg", "fit_rmse_mm",
             "forward_span_m", "vertical_span_m", "arc_length_m", "arc_pm_m",
             "mean_speed_m_s", "max_speed_m_s", "cap_width_px", "cap_sd_px", "cap_frames",
             "m_per_px", "scale_unc_pct", "time_base"]
    table = table[order]
    table.to_csv(OUT / "summary_table.csv", index=False)
    print(table.drop(columns=["time_base"]).to_string(index=False))

    def path_compare(a_tag, b_tag):
        curves = []
        for tag in (a_tag, b_tag):
            d = pd.read_csv(PHASE / f"{tag}_pull_phase.csv")
            u = (d.t - d.t.min()) / (d.t.max() - d.t.min())
            g = np.linspace(0, 1, 300)
            curves.append((np.interp(g, u, d.x_m), np.interp(g, u, d.y_m)))
        (xa, ya), (xb, yb) = curves
        dist = np.hypot((xa - xa[0]) - (xb - xb[0]), (ya - ya[0]) - (yb - yb[0]))
        return float(np.sqrt((dist ** 2).mean())), float(dist.mean()), float(dist.max())

    comp_rows = []
    for summary in summaries.values():
        comp = [x for x in summary if isinstance(x, dict) and "comparison" in x][0]["comparison"]
        comp_rows.append(dict(
            pair=" vs ".join(comp["labels"]),
            window="full_track",
            position_rmse_m=round(comp["position_rmse"], 4),
            mean_diff_m=round(comp["mean_position_difference"], 4),
            max_diff_m=round(comp["max_position_difference"], 4),
            arc_length_difference_m=round(comp["arc_length_difference"], 4),
        ))
    for target in ["A3", "A2"]:
        rmse, mean_d, max_d = path_compare("dressel", target.lower())
        comp_rows.append(dict(
            pair=f"Dressel vs {target}",
            window="pull_phase",
            position_rmse_m=round(rmse, 4),
            mean_diff_m=round(mean_d, 4),
            max_diff_m=round(max_d, 4),
            arc_length_difference_m=round(abs(
                float(phase_row(target).arc_length_m) -
                float(phase_row("Dressel").arc_length_m)), 4),
        ))
    comparisons = pd.DataFrame(comp_rows)
    comparisons.to_csv(OUT / "comparisons.csv", index=False)
    print()
    print(comparisons.to_string(index=False))

    # ---------------- figure: my path against his, enlarged and at true size
    def curves_for(tag):
        d = pd.read_csv(PHASE / f"{tag}_pull_phase.csv")
        u = (d.t - d.t.min()) / (d.t.max() - d.t.min())
        deg = PHASE_DEGREE[tag]
        cx, cy = np.polyfit(u, d.x_m, deg), np.polyfit(u, d.y_m, deg)
        g = np.linspace(0, 1, 400)
        return dict(d=d, cx=cx, cy=cy, g=g,
                    X=np.polyval(cx, g), Y=np.polyval(cy, g))

    his = curves_for("dressel")
    mine = {tag: curves_for(tag) for tag in ["a2", "a3"]}

    fig = plt.figure(figsize=(15.5, 8.4))
    gs = fig.add_gridspec(2, 3, width_ratios=[1, 1, 0.82], wspace=0.26, hspace=0.34)

    for col, tag in enumerate(["a2", "a3"]):
        label = LABELS[tag]
        pc = phase_cross_row(label)
        k = float(pc.scale)
        m = mine[tag]
        for row, scaled in [(0, True), (1, False)]:
            ax = fig.add_subplot(gs[row, col])
            factor = k if scaled else 1.0
            ax.plot(his["X"] * factor, his["Y"] * factor, "--", lw=2.2,
                    color=COLOURS["dressel"],
                    label=f"Dressel{' x ' + format(k, '.2f') if scaled else ' (true size)'}")
            ax.plot(m["X"], m["Y"], "-", lw=2.4, color=COLOURS[tag], label=f"{label} (mine)")
            ax.plot(m["d"].x_m, m["d"].y_m, ".", ms=4.5, alpha=0.5, color=COLOURS[tag])
            ax.set_aspect("equal", adjustable="datalim")
            ax.grid(alpha=0.3)
            ax.legend(fontsize=8, loc="best")
            if row == 0:
                ax.set_title(f"{label}: his path scaled x{k:.2f} onto mine", fontsize=11)
            else:
                ax.set_title(f"{label}: true size, no enlargement", fontsize=11)
            if col == 0:
                ax.set_ylabel("vertical displacement (m)")
            if row == 1:
                ax.set_xlabel("forward displacement (m)")

    ax = fig.add_subplot(gs[:, 2])
    tags = ["a2", "a3"]
    si = [float(phase_cross_row(LABELS[t]).r2_scale_invariant) for t in tags]
    raw = [float(phase_cross_row(LABELS[t]).r2) for t in tags]
    kk = [float(phase_cross_row(LABELS[t]).scale) for t in tags]
    x = np.arange(len(tags))
    bars = ax.bar(x, si, 0.55, color=[COLOURS[t] for t in tags])
    ax.axhline(0, color="gray", lw=0.8)
    ax.set_xticks(x, [LABELS[t] for t in tags])
    bottom = min(0, min(raw) - 0.1)
    ax.set_ylim(bottom, 1.05)
    ax.set_ylabel(r"$R^2$ of his model on my pull")
    ax.set_title("only my $R^2$ is a result\n(his own fit is not compared)", fontsize=11)
    ax.grid(alpha=0.3, axis="y")
    for xi, (s, r, k) in enumerate(zip(si, raw, kk)):
        ax.text(xi, s + 0.03, f"{s:.2f}", ha="center", fontsize=11, weight="bold")
        ax.text(xi, s + 0.10, f"his path x{k:.2f}", ha="center", fontsize=8, style="italic")
        ax.text(xi, bottom + 0.03, f"unscaled: {r:.2f}", ha="center", fontsize=8)

    fig.savefig(OUT / "three_way.png", dpi=165, bbox_inches="tight")
    plt.close(fig)
    print("\nwrote summary_table.csv, comparisons.csv, three_way.png")


if __name__ == "__main__":
    main()
