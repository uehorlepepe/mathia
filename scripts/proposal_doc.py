"""Build the completed Exploration Proposal as a single submission PDF.

Renders an HTML form matching the St. Robert CHS / MCV4U7 proposal template,
fills it with the results already computed in outputs/prelim/summary_table.csv,
draws one feasibility figure from the tracked pull-phase data, then prints the
page to PDF with headless Chrome.

Usage:  .venv/bin/python scripts/proposal_doc.py
Output: outputs/submission/IA_Exploration_Proposal_Yifan_Wang.pdf
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "submission"
FIG = OUT_DIR / "proposal_feasibility.png"
HTML = OUT_DIR / "proposal.html"
PDF = OUT_DIR / "IA_Exploration_Proposal_Yifan_Wang.pdf"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Pull-phase windows fixed in scripts/pull_phase.py.
WINDOWS = {"a2": (320, 328, 2), "a3": (177, 194, 3), "dressel": (682, 778, 3)}
LABELS = {"a2": "Yifan A2", "a3": "Yifan A3", "dressel": "Elite"}
COLOURS = {"a2": "#1f6f8b", "a3": "#c0504d", "dressel": "#3f3f3f"}


def feasibility_figure() -> None:
    fig, ax = plt.subplots(figsize=(6.4, 4.3), dpi=220)
    for stem, (lo, hi, deg) in WINDOWS.items():
        d = pd.read_csv(ROOT / f"data/{stem}_hand_points_metres.csv")
        d = d[(d.frame >= lo) & (d.frame <= hi)].sort_values("frame")
        t = d.t.to_numpy()
        u = (t - t.min()) / max(t.max() - t.min(), 1e-9)
        px = np.polyfit(u, d.x_m.to_numpy(), deg)
        py = np.polyfit(u, d.y_m.to_numpy(), deg)
        uu = np.linspace(0, 1, 200)
        ax.plot(np.polyval(px, uu), np.polyval(py, uu), "-", color=COLOURS[stem], lw=2)
        ax.plot(
            d.x_m,
            d.y_m,
            "o",
            color=COLOURS[stem],
            ms=4.5,
            mfc="white",
            mew=1.2,
            label=f"{LABELS[stem]} ({len(d)} pts)",
        )

    ax.set_xlabel("Horizontal hand displacement  x  / m", fontsize=9)
    ax.set_ylabel("Vertical hand displacement  y  / m", fontsize=9)
    ax.set_title(
        "Digitised pull-phase trajectories in a common frame\n(cap-calibrated, no rescaling applied)",
        fontsize=9.5,
    )
    ax.invert_yaxis()
    ax.set_aspect("equal", adjustable="datalim")
    ax.grid(alpha=0.25, lw=0.6)
    ax.tick_params(labelsize=8)
    ax.legend(fontsize=8, frameon=False, loc="best")
    fig.tight_layout()
    fig.savefig(FIG, bbox_inches="tight")
    plt.close(fig)


def build_html() -> str:
    table = pd.read_csv(ROOT / "outputs/prelim/summary_table.csv")
    row = {}
    for _, r in table.iterrows():
        row[(r["track"], r["window"])] = r

    def g(track, window, col, fmt="{:.2f}"):
        return fmt.format(row[(track, window)][col])

    data_rows = [
        (
            "Yifan A2",
            "317-340",
            "24 (9 in pull)",
            "3 / 2",
            f"{g('A2','full_track','r2_fit_own_track','{:.3f}')} / {g('A2','pull_phase','r2_fit_own_track','{:.3f}')}",
            f"{g('A2','full_track','arc_length_m')} / {g('A2','pull_phase','arc_length_m')}",
            f"{g('A2','full_track','mean_speed_m_s')} / {g('A2','pull_phase','mean_speed_m_s')}",
        ),
        (
            "Yifan A3",
            "171-194",
            "24 (18 in pull)",
            "3 / 3",
            f"{g('A3','full_track','r2_fit_own_track','{:.3f}')} / {g('A3','pull_phase','r2_fit_own_track','{:.3f}')}",
            f"{g('A3','full_track','arc_length_m')} / {g('A3','pull_phase','arc_length_m')}",
            f"{g('A3','full_track','mean_speed_m_s')} / {g('A3','pull_phase','mean_speed_m_s')}",
        ),
        (
            "Elite sprinter",
            "642-778",
            "18 (13 in pull)",
            "3 / 3",
            f"{g('Dressel','full_track','r2_fit_own_track','{:.3f}')} / {g('Dressel','pull_phase','r2_fit_own_track','{:.3f}')}",
            f"{g('Dressel','full_track','arc_length_m')} / {g('Dressel','pull_phase','arc_length_m')}",
            "not available (slowed footage)",
        ),
    ]
    data_html = "\n".join(
        "<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in data_rows
    )

    math_rows = [
        (
            "Parametric and polynomial function modelling",
            "Fitting cubic (or, where the sample is short, quadratic) parametric functions "
            "x(t) and y(t) to coordinate data extracted frame by frame from video, and judging "
            "the fit by its coefficient of determination and residual plot.",
            "2.11, 2.12",
        ),
        (
            "Vector concepts and kinematics",
            "Expressing hand position as a 2D vector function r(t) = (x(t), y(t)) and resolving "
            "the velocity vector v(t) = r′(t) into forward and vertical components, so the two "
            "strokes can be compared component by component.",
            "3.12, 3.14",
        ),
        (
            "Calculus: differentiation and arc length",
            "Differentiating the parametric position functions to obtain instantaneous velocity "
            "and speed, and evaluating the definite integral ∫‖r′(t)‖dt to compute the total "
            "length of the hand path for each swimmer.",
            "5.5, 5.8, 5.9",
        ),
        (
            "Statistics: residuals and coefficient of determination",
            "Using residuals, RMSE and R² to quantify, on a common scale, how far my trajectory "
            "departs from the motion predicted by the elite swimmer's model, with uncertainty "
            "propagated from the pixel-to-metre calibration.",
            "4.4, 4.14",
        ),
    ]
    math_html = "\n".join(
        f"<tr><td class='c1'>{a}</td><td>{b}</td><td class='c3'>{c}</td></tr>"
        for a, b, c in math_rows
    )

    return f"""<!doctype html>
<html><head><meta charset="utf-8">
<style>
  @page {{ size: A4; margin: 17mm 16mm 16mm 16mm; }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: "Times New Roman", Times, serif; font-size: 10.6pt;
         line-height: 1.38; color: #111; margin: 0; }}
  h1 {{ font-size: 15.5pt; text-align: center; margin: 0 0 2mm 0; letter-spacing: .2px; }}
  .sub {{ text-align: center; font-size: 10pt; margin: 0 0 5mm 0; color: #333; }}
  .meta {{ display: flex; justify-content: space-between; font-size: 10.4pt;
           border-top: 1.4px solid #111; border-bottom: 1.4px solid #111;
           padding: 2mm 0; margin-bottom: 5mm; }}
  h2 {{ font-size: 11pt; margin: 5.5mm 0 1.5mm 0; }}
  h2 .num {{ color: #555; font-weight: normal; }}
  .prompt {{ font-size: 9pt; color: #555; font-style: italic; margin: 0 0 2mm 0; }}
  p {{ margin: 0 0 2.2mm 0; text-align: justify; }}
  .topic {{ font-weight: bold; font-size: 11.2pt; margin: 1mm 0 1mm 0; }}
  ul {{ margin: 0 0 2.2mm 5mm; padding: 0; }}
  li {{ margin-bottom: 1.1mm; text-align: justify; }}
  table {{ border-collapse: collapse; table-layout: fixed; width: 100%; font-size: 8.8pt;
           margin: 1.5mm 0 2.5mm 0;
           page-break-inside: avoid; }}
  tr {{ page-break-inside: avoid; }}
  .fig {{ page-break-inside: avoid; }}
  h2 {{ page-break-after: avoid; }}
  th, td {{ border: .7px solid #999; padding: 1.6mm 2mm; vertical-align: top; text-align: left; }}
  th {{ background: #eee; font-size: 8.8pt; }}
  td.c1 {{ width: 27%; }} td.c3 {{ width: 12%; }}
  .fig {{ text-align: center; margin: 3mm 0 1mm 0; }}
  .fig img {{ width: 118mm; }}
  .cap {{ font-size: 8.6pt; color: #444; text-align: center; margin: 0 0 3mm 0; }}
  .note {{ font-size: 9.2pt; color: #333; }}
  .kv {{ font-size: 10pt; margin: 0 0 1.4mm 0; }}
  .kv b {{ display: inline-block; min-width: 26mm; }}
  hr {{ border: none; border-top: .7px solid #bbb; margin: 4mm 0 0 0; }}
</style></head>
<body>

<h1>IB Higher Level Mathematics: Analysis and Approaches</h1>
<div class="sub">St. Robert CHS (MCV4U7) &nbsp;·&nbsp; Mathematical Exploration Proposal</div>

<div class="meta"><span><b>Name:</b> Yifan Wang</span><span><b>Course:</b> MCV4U7</span>
<span><b>Due:</b> Monday, October 19, 2026</span></div>

<h2>1. Exploration Topic <span class="num">: sufficiently narrow, and plotted before committing</span></h2>
<div class="topic">A Comparative Parametric and Kinematic Analysis of Underwater Hand
Trajectories Between a High School Competitive Swimmer and an Elite Freestyle Sprinter</div>
<p class="note">The topic is deliberately narrow: it concerns one phase of one stroke, the
underwater hand pull of freestyle, for one hand, in two swimmers, rather than "modelling
swimming" or "parametric curves" in general.</p>

<h2>2. Specific Aim / Objective</h2>
<p class="prompt">What exactly are you trying to find out, and how will you know you have succeeded?</p>
<p>To model the 2D underwater hand-pull trajectories of my own competitive 50 m freestyle
sprint and of an elite world-class sprinter as parametric polynomial functions
x(t) and y(t), to compute the path length and instantaneous velocity of each hand using
calculus, and to quantify how far my motion departs from the elite model using vector
residuals, RMSE and the coefficient of determination R² of the elite model applied to my
own data. Success will be measured by four explicit criteria:</p>
<ul>
  <li><b>Convergent models:</b> a parametric fit to each trajectory with R² ≥ 0.95 in the
      pull window, whose residuals show no systematic trend.</li>
  <li><b>Computed kinematics:</b> an arc length and a mean and maximum hand speed for each
      of my two clips, each carrying an uncertainty propagated from the calibration.</li>
  <li><b>A quantified discrepancy:</b> an RMSE between my trajectory and the elite model in
      metres, and an R² of that model evaluated on my data.</li>
  <li><b>An honest account of scale:</b> the size difference between the two swimmers
      reported as an explicit scale factor rather than absorbed into a scale-invariant score.</li>
</ul>

<p><b>Feasibility check.</b> The template asks that data be plotted before a regression topic
is committed to. All three clips have therefore been digitised frame by frame already, and a
polynomial was fitted to each before this proposal was written. The pull-phase results are:</p>

<table>
  <colgroup><col style="width:15%"><col style="width:11%"><col style="width:14%"><col style="width:10%"><col style="width:12%"><col style="width:15%"><col style="width:23%"></colgroup>
  <tr><th>Track</th><th>Frames</th><th>Points</th><th>Degree<br>(full / pull)</th>
      <th>R²<br>(full / pull)</th><th>Arc length / m<br>(full / pull)</th>
      <th>Mean hand speed / m s⁻¹<br>(full / pull)</th></tr>
  {data_html}
</table>

<div class="fig"><img src="proposal_feasibility.png" alt="Digitised pull-phase hand trajectories"></div>
<div class="cap">Figure 1. The three digitised pull-phase hand paths in one common frame,
calibrated on the swim cap (0.19 m) and shown at true relative size.</div>

<p>Every fit exceeds the 0.95 threshold, residuals are of the order of a few centimetres, and
the three paths occupy overlapping regions of the frame, so a shared parametric comparison is
feasible. Two practical limits are already known and are stated here rather than discovered
later: the elite footage is slowed (about 3.4 frames per distinct picture), so it supports a
comparison of <i>shape</i> and path length but not of absolute time or speed; and one of my two
clips yields only 9 points in the pull window, so its pull-phase fit is quadratic and its
result will be reported as indicative.</p>

<h2>3. Strategies for Addressing Personal Engagement (Criterion C)</h2>
<p class="prompt">This criterion is about creative application of mathematics learned in this course.</p>
<p>As a competitive high school swimmer who placed 2nd in the B final at OFSAA and who has
coaching experience, I routinely analyse stroke mechanics and drag reduction from recordings.
The usual vocabulary for this is qualitative ("catch the water", "finish the pull"), and it is
not measurable. What interests me mathematically is that a hand moving through water traces a
curve, and that curve can be written as a vector function, differentiated, integrated and
compared. The creative step is to treat a coach's cue as a parametric curve and a disagreement
between two swimmers as a residual from a fitted model, which converts an argument about style
into a number with an uncertainty attached.</p>
<p>If the cubic model proves inadequate, the response will be mathematical rather than
ad hoc: raise the degree only where the point count supports it, restrict the window to the
phase where a single polynomial is justifiable, and report the change in R² and in arc length
so the effect of the modelling choice is visible.</p>

<h2>4. Mathematical Skills and Concepts</h2>
<table>
  <colgroup><col style="width:26%"><col style="width:62%"><col style="width:12%"></colgroup>
  <tr><th>Skill / concept</th><th>How it is used in the exploration</th><th>Syllabus</th></tr>
  {math_html}
</table>

<h2>5. Resources / Sources</h2>
<div class="kv"><b>My footage:</b> two clips of my own competitive 50 m freestyle sprint,
filmed from the pool deck at 1920 × 1080, 29.97 fps, and digitised by me one frame at a time
(24 points per clip over 0.77 s).</div>
<div class="kv"><b>Elite footage:</b> underwater 50 m freestyle race footage of an elite
sprinter, 1280 × 720, 60 fps, digitised in the same way (18 points).</div>
<div class="kv"><b>Calibration object:</b> a 0.19 m swim cap, measured in several frames of
each clip (5-7 frames) to obtain the pixel-to-metre scale and its uncertainty (±14-18%),
with the pool's lane markings checked as a cross-reference.</div>
<div class="kv"><b>Software:</b> Python with NumPy and pandas for the polynomial fits,
numerical differentiation and integration; results reproducible from the digitised coordinates.</div>

<hr>
<p class="cap" style="text-align:left; margin-top:2mm">All figures quoted above are computed
from my own digitised tracks; no value is estimated without a corresponding calculation.</p>

</body></html>
"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    feasibility_figure()
    html = build_html()
    HTML.write_text(html, encoding="utf-8")
    print(f"wrote {FIG.relative_to(ROOT)}")
    print(f"wrote {HTML.relative_to(ROOT)}")

    with tempfile.TemporaryDirectory() as profile:
        proc = subprocess.run(
            [
                CHROME,
                "--headless",
                "--disable-gpu",
                "--no-pdf-header-footer",
                f"--user-data-dir={profile}",
                f"--print-to-pdf={PDF}",
                HTML.as_uri(),
            ],
            capture_output=True,
            text=True,
        )
    if not PDF.exists():
        raise SystemExit(f"Chrome failed:\n{proc.stderr[-2000:]}")
    kb = PDF.stat().st_size / 1024
    print(f"wrote {PDF.relative_to(ROOT)} ({kb:.0f} kB)")


if __name__ == "__main__":
    main()
