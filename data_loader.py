"""Load raw pixel hand tracks, calibrate to metres, align to hand entry.

Raw digitised coordinates ``(t, x_pixel, y_pixel)`` from swimmer videos are:

1. cleaned (sorted, de-duplicated, NaN rows dropped, optional time trim),
2. converted to metres with a scale factor derived from a reference of known
   length (swimmer height, pool tile, lane rope, ...),
3. re-expressed so the moment the hand enters the water is the origin
   ``(t, x, y) = (0, 0, 0)``,

and exported as a pandas DataFrame with columns ``[t, x_meters, y_meters]``.

Typical use::

    from data_loader import build_dataframe, save

    df = build_dataframe(
        "data/cameron_hand.csv",
        calibration="data/cameron.calibration.json",  # from scripts/calibrate.py
        entry_time=4.0,                               # hand entry, seconds
    )
    save(df, "data/cameron_clean.csv")

Scale factor -- supply exactly one of:

* ``calibration=`` path/dict from ``scripts/calibrate.py`` (contains m_per_px)
* ``m_per_px=`` directly
* ``reference_m=`` + ``reference_px=``  (scale = reference_m / reference_px)

Hand entry -- supply exactly one of (default: first sample):

* ``entry_time=`` seconds; position is interpolated at that instant
* ``entry_index=`` row number of the entry sample (0-based, after cleaning)
* ``surface_y_px=`` water-surface row; entry = first downward crossing

Y axis: pixel y grows downward, so by default y is flipped to make "up"
positive, matching ``scripts/analyze.py``. Pass ``flip_y=False`` if you
prefer depth-positive-down.

Command line::

    python data_loader.py data/cameron_hand.csv \
        --calibration data/cameron.calibration.json \
        --entry-time 4.0 --out data/cameron_clean.csv

    python data_loader.py raw.csv --reference-m 1.9 --reference-px 380 \
        --surface-px 120 --out clean.csv
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

OUTPUT_COLUMNS = ["t", "x_meters", "y_meters"]
_PIXEL_COLUMNS = ["t", "x_px", "y_px"]

_ALIASES = {
    "t": "t", "time": "t", "t_s": "t", "seconds": "t",
    "x": "x_px", "x_px": "x_px", "x_pixel": "x_px", "x_pixels": "x_px",
    "y": "y_px", "y_px": "y_px", "y_pixel": "y_px", "y_pixels": "y_px",
    "frame": "frame",
}


# ---------------------------------------------------------------- loading

def load_track(source, fps=None):
    """Return a DataFrame with float columns [t, x_px, y_px].

    ``source`` may be a CSV path, a DataFrame, or any iterable of
    ``(t, x, y)`` rows.  If the input has a ``frame`` column but no ``t``,
    ``fps`` is required to convert frames to seconds.
    """
    if isinstance(source, pd.DataFrame):
        df = source.copy()
    elif isinstance(source, (str, Path)):
        df = pd.read_csv(source)
    else:
        df = pd.DataFrame(list(source), columns=_PIXEL_COLUMNS)

    rename = {}
    for col in df.columns:
        key = str(col).strip().lower()
        if key in _ALIASES and _ALIASES[key] not in rename.values():
            rename[col] = _ALIASES[key]
    df = df.rename(columns=rename)

    if "t" not in df.columns:
        if "frame" not in df.columns:
            raise ValueError(
                "input needs a time column (t/time) or a frame column + fps")
        if fps is None:
            raise ValueError("input has frames but no fps was supplied")
        df["t"] = pd.to_numeric(df["frame"], errors="coerce") / float(fps)

    missing = [c for c in _PIXEL_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"input is missing column(s): {missing}")

    for col in _PIXEL_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df[_PIXEL_COLUMNS].copy()


def clean_track(df, start=None, end=None):
    """Sort by t, drop NaN/duplicate samples, optionally trim to [start, end]."""
    df = df.dropna(subset=_PIXEL_COLUMNS).sort_values("t")
    df = df.drop_duplicates(subset="t", keep="first")
    if start is not None:
        df = df[df["t"] >= float(start)]
    if end is not None:
        df = df[df["t"] <= float(end)]
    df = df.reset_index(drop=True)
    if len(df) < 2:
        raise ValueError(f"only {len(df)} usable sample(s); need at least 2")
    return df


# ------------------------------------------------------------- calibration

def scale_from_reference(reference_m, reference_px):
    """Metres per pixel from a reference of known real length."""
    reference_m = float(reference_m)
    reference_px = float(reference_px)
    if reference_m <= 0 or reference_px <= 0:
        raise ValueError("reference length and pixel span must be positive")
    return reference_m / reference_px


def load_calibration(source):
    """Read a calibration produced by scripts/calibrate.py (path or dict)."""
    data = json.loads(Path(source).read_text()) if isinstance(
        source, (str, Path)) else dict(source)
    if "m_per_px" not in data:
        raise ValueError("calibration has no 'm_per_px' entry")
    return data


def resolve_scale(calibration=None, m_per_px=None,
                  reference_m=None, reference_px=None):
    """Turn any one of the calibration options into m_per_px."""
    if (reference_m is None) != (reference_px is None):
        raise ValueError("reference_m and reference_px must be given together")
    n_options = (calibration is not None) + (m_per_px is not None) + (
        reference_m is not None)
    if n_options != 1:
        raise ValueError(
            "supply exactly one of: calibration=, m_per_px=, "
            "reference_m=+reference_px=")
    if calibration is not None:
        return float(load_calibration(calibration)["m_per_px"])
    if m_per_px is not None:
        if float(m_per_px) <= 0:
            raise ValueError("m_per_px must be positive")
        return float(m_per_px)
    return scale_from_reference(reference_m, reference_px)


def apply_calibration(df, m_per_px, flip_y=True):
    """Add x_meters / y_meters columns to a pixel-track DataFrame."""
    out = df.copy()
    out["x_meters"] = out["x_px"] * m_per_px
    sign = -1.0 if flip_y else 1.0
    out["y_meters"] = sign * out["y_px"] * m_per_px
    return out


# ------------------------------------------------------------------ entry

def find_entry(df, entry_time=None, entry_index=None, surface_y_px=None):
    """Locate hand entry; return (t0, x0_px, y0_px) in pixel space.

    Exactly one of ``entry_time``, ``entry_index`` or ``surface_y_px`` may be
    given; if none, the first sample is used.
    """
    n_given = sum(v is not None for v in
                  (entry_time, entry_index, surface_y_px))
    if n_given > 1:
        raise ValueError("supply only one of entry_time/entry_index/"
                         "surface_y_px")

    t = df["t"].to_numpy(dtype=float)
    x = df["x_px"].to_numpy(dtype=float)
    y = df["y_px"].to_numpy(dtype=float)

    if entry_index is not None:
        i = int(entry_index)
        if not 0 <= i < len(df):
            raise ValueError(f"entry_index {i} out of range 0..{len(df) - 1}")
        return float(t[i]), float(x[i]), float(y[i])

    if entry_time is not None:
        t0 = float(entry_time)
        if not t[0] <= t0 <= t[-1]:
            raise ValueError(
                f"entry_time {t0} outside sampled range "
                f"[{t[0]}, {t[-1]}]")
        return float(t0), float(np.interp(t0, t, x)), float(np.interp(t0, t, y))

    if surface_y_px is not None:
        surf = float(surface_y_px)
        above = y < surf  # pixel y grows downward: above surface = smaller y
        cross = np.where(above[:-1] & ~above[1:])[0]
        if len(cross) == 0:
            raise ValueError(
                f"y_px never crosses surface_y_px={surf} going downward")
        i = cross[0]
        frac = (surf - y[i]) / (y[i + 1] - y[i])
        return (float(t[i] + frac * (t[i + 1] - t[i])),
                float(x[i] + frac * (x[i + 1] - x[i])),
                float(surf))

    return float(t[0]), float(x[0]), float(y[0])


def align_to_entry(df, t0, x0_px, y0_px, m_per_px, flip_y=True):
    """Translate a calibrated track so (t0, x0, y0) becomes (0, 0, 0)."""
    out = df.copy()
    sign = -1.0 if flip_y else 1.0
    out["t"] = out["t"] - t0
    out["x_meters"] = out["x_meters"] - x0_px * m_per_px
    out["y_meters"] = out["y_meters"] - sign * y0_px * m_per_px
    return out


# ------------------------------------------------------------------ main

def build_dataframe(source, *, calibration=None, m_per_px=None,
                    reference_m=None, reference_px=None, fps=None,
                    entry_time=None, entry_index=None, surface_y_px=None,
                    flip_y=True, start=None, end=None):
    """Full pipeline: raw pixels -> cleaned, calibrated, entry-aligned df.

    Returns a DataFrame with exactly the columns
    ``[t, x_meters, y_meters]`` where t=0, x=0, y=0 at hand entry.
    """
    scale = resolve_scale(calibration, m_per_px, reference_m, reference_px)
    raw = load_track(source, fps=fps)
    cleaned = clean_track(raw, start=start, end=end)
    t0, x0, y0 = find_entry(cleaned, entry_time, entry_index, surface_y_px)
    calibrated = apply_calibration(cleaned, scale, flip_y=flip_y)
    aligned = align_to_entry(calibrated, t0, x0, y0, scale, flip_y=flip_y)
    return aligned[OUTPUT_COLUMNS].reset_index(drop=True)


def save(df, path):
    """Validate column layout and write the cleaned track as CSV."""
    missing = [c for c in OUTPUT_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"DataFrame is missing column(s): {missing}")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df[OUTPUT_COLUMNS].to_csv(path, index=False)
    return path


def parse_args():
    p = argparse.ArgumentParser(
        description="Calibrate a raw pixel hand track to metres and align "
                    "it so hand entry is (0, 0, 0).")
    p.add_argument("input", help="CSV with t/x_px/y_px (track_hand.py output)")
    p.add_argument("--out", default=None, help="output CSV path")
    p.add_argument("--calibration", default=None,
                   help="JSON from scripts/calibrate.py")
    p.add_argument("--m-per-px", type=float, default=None)
    p.add_argument("--reference-m", type=float, default=None,
                   help="real length of the reference, e.g. 1.9 for height")
    p.add_argument("--reference-px", type=float, default=None,
                   help="its length in pixels")
    p.add_argument("--fps", type=float, default=None,
                   help="needed only if input has frames but no t column")
    p.add_argument("--entry-time", type=float, default=None,
                   help="seconds at which the hand enters the water")
    p.add_argument("--entry-index", type=int, default=None)
    p.add_argument("--surface-px", type=float, default=None,
                   help="y pixel row of the water surface")
    p.add_argument("--depth-positive", action="store_true",
                   help="keep pixel y direction (down = positive) instead "
                        "of flipping up to positive")
    p.add_argument("--start", type=float, default=None, help="trim: t >= start")
    p.add_argument("--end", type=float, default=None, help="trim: t <= end")
    return p.parse_args()


def main():
    args = parse_args()
    if args.out is None:
        args.out = str(Path(args.input).with_name(
            Path(args.input).stem + "_clean.csv"))
    df = build_dataframe(
        args.input,
        calibration=args.calibration,
        m_per_px=args.m_per_px,
        reference_m=args.reference_m,
        reference_px=args.reference_px,
        fps=args.fps,
        entry_time=args.entry_time,
        entry_index=args.entry_index,
        surface_y_px=args.surface_px,
        flip_y=not args.depth_positive,
        start=args.start,
        end=args.end,
    )
    out = save(df, args.out)
    print(f"Wrote {len(df)} samples to {out}")
    print(f"  t: [{df['t'].iloc[0]:.3f}, {df['t'].iloc[-1]:.3f}] s"
          f"   x: [{df['x_meters'].min():.3f}, {df['x_meters'].max():.3f}] m"
          f"   y: [{df['y_meters'].min():.3f}, {df['y_meters'].max():.3f}] m")
    print("  entry is at t=0, x=0, y=0")


if __name__ == "__main__":
    main()
