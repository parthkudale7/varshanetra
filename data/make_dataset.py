"""
Builds a synthetic but physically-motivated monsoon dataset for the
15 Pune wards in wards.py: 3-hourly rainfall over three monsoon
seasons (June-Sept), plus terrain-driven flood risk labels.

This is NOT real IMD/MOSDAC data. It exists so the modeling pipeline
can be built and tested end to end before real historical data is
available. Swap load_or_build() for a real loader once you have one -
everything downstream (features.py, train_*.py) only cares about the
columns, not where they came from.

Run directly to regenerate data/dataset.csv:
    python data/make_dataset.py
"""

import numpy as np
import pandas as pd
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent))
from wards import load_wards

RNG_SEED = 7
STEPS_PER_DAY = 8            # 3-hour resolution
SEASON_DAYS = 122             # roughly June 1 - Sept 30
SEASONS = 3

# a handful of deliberate multi-day storm windows, so there's real
# extreme-event structure to hold out for testing later instead of
# everything being close to average
STORM_WINDOWS = [
    (35, 3),   # (day offset into season, duration in days)
    (61, 2),
    (98, 4),
]


def _season_rain_prob(day_of_season: int) -> float:
    # rises through June, peaks in July/Aug, tapers in Sept
    x = day_of_season / SEASON_DAYS
    return 0.15 + 0.45 * np.sin(np.pi * x) ** 1.3


def _base_rainfall_series(rng: np.random.Generator) -> np.ndarray:
    n = SEASON_DAYS * SEASONS * STEPS_PER_DAY
    rain = np.zeros(n)
    wet = False
    for season in range(SEASONS):
        for day in range(SEASON_DAYS):
            idx0 = (season * SEASON_DAYS + day) * STEPS_PER_DAY
            in_storm = any(d0 <= day < d0 + dur for d0, dur in STORM_WINDOWS)
            p_wet = _season_rain_prob(day)
            if in_storm:
                p_wet = min(0.95, p_wet + 0.5)
            for step in range(STEPS_PER_DAY):
                i = idx0 + step
                # light autocorrelation: raining now raises odds of raining next step
                p = p_wet + (0.25 if wet else 0.0)
                wet = rng.random() < p
                if not wet:
                    rain[i] = 0.0
                    continue
                shape, scale = (2.2, 9.0) if not in_storm else (3.0, 22.0)
                rain[i] = rng.gamma(shape, scale)
    return rain


def build_dataset(seed: int = RNG_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    wards = load_wards()
    city_rain = _base_rainfall_series(rng)
    n = len(city_rain)

    # three separate monsoon seasons, not one continuous stretch
    season_len = SEASON_DAYS * STEPS_PER_DAY
    ts_frames = []
    for s in range(SEASONS):
        yr_start = pd.Timestamp(f"{2023 + s}-06-01")
        ts_frames.append(pd.date_range(yr_start, periods=season_len, freq="3h"))
    timestamps = ts_frames[0].append(ts_frames[1]).append(ts_frames[2])

    rows = []
    for _, w in wards.iterrows():
        # each ward gets a mild multiplier so rain isn't perfectly city-uniform
        jitter = rng.normal(1.0, 0.12, size=n).clip(0.6, 1.5)
        ward_rain = city_rain * jitter
        df = pd.DataFrame({
            "ward": w.ward,
            "timestamp": timestamps,
            "rain_mm": ward_rain,
        })
        for col in ["lat", "lon", "elevation_m", "slope_deg", "dist_river_km", "drainage_quality"]:
            df[col] = w[col]
        rows.append(df)

    data = pd.concat(rows, ignore_index=True).sort_values(["ward", "timestamp"]).reset_index(drop=True)
    return data


def add_labels(data: pd.DataFrame) -> pd.DataFrame:
    data = data.copy()
    g = data.groupby("ward")

    data["rain_3h"] = data["rain_mm"]
    data["rain_6h"] = g["rain_mm"].transform(lambda s: s.rolling(2, min_periods=1).sum())
    data["rain_24h"] = g["rain_mm"].transform(lambda s: s.rolling(8, min_periods=1).sum())

    # rainfall category target: what will the next 3h bring
    next_rain = g["rain_mm"].shift(-1)
    bins = [-0.1, 2.5, 12, 30, 1e6]
    labels = ["light", "moderate", "heavy", "extreme"]
    data["rain_category_next"] = pd.cut(next_rain, bins=bins, labels=labels)

    # --- flood index -------------------------------------------------
    # terrain vulnerability is a 0-1ish multiplier on rain-driven risk,
    # not an additive constant - a low-lying ward should still be fine
    # on a dry day, it just tips over faster once real rain falls
    drainage_factor = (1 - data["drainage_quality"])
    flat_factor = 2.5 / (data["slope_deg"] + 2.5)
    river_factor = 1 / (data["dist_river_km"] + 1)
    elevation_norm = ((611 - data["elevation_m"]) / 71).clip(0, 1)
    vulnerability = (drainage_factor + flat_factor + river_factor + elevation_norm) / 4

    rng = np.random.default_rng(RNG_SEED + 1)
    noise = rng.normal(0, 0.12, size=len(data))
    rain_pressure = 0.02 * data["rain_6h"] + 0.006 * data["rain_24h"]
    data["flood_index_now"] = (vulnerability * rain_pressure + noise).clip(lower=0)

    # target: worst flood index over the following two steps (next 6h)
    data["flood_index_future6h"] = (
        data.groupby("ward")["flood_index_now"]
        .transform(lambda s: s.shift(-1).rolling(2, min_periods=1).max())
    )

    q = data["flood_index_future6h"]
    cuts = q.quantile([0.60, 0.85, 0.95]).values
    risk_bins = [-1e6, cuts[0], cuts[1], cuts[2], 1e6]
    risk_labels = ["safe", "watch", "warning", "danger"]
    data["flood_risk_future"] = pd.cut(q, bins=risk_bins, labels=risk_labels)

    return data


def load_or_build(path: str = "data/dataset.csv", force: bool = False) -> pd.DataFrame:
    p = Path(path)
    if p.exists() and not force:
        return pd.read_csv(p, parse_dates=["timestamp"])
    data = build_dataset()
    data = add_labels(data)
    data = data.dropna(subset=["rain_category_next", "flood_risk_future"]).reset_index(drop=True)
    p.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(p, index=False)
    return data


if __name__ == "__main__":
    df = load_or_build(force=True)
    print(df.shape)
    print(df["rain_category_next"].value_counts())
    print(df["flood_risk_future"].value_counts())
    print(df.groupby("ward")["flood_risk_future"].apply(lambda s: (s == "danger").mean()).sort_values())
