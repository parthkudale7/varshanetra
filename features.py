"""
Feature building, kept separate from the training scripts so the API
can import the exact same function instead of re-implementing it.

RAW_COLS is the "just the numbers" feature set. ENGINEERED_COLS are the
extra interaction terms - ablation.py checks whether these are actually
worth having.
"""

import pandas as pd

RAW_COLS = [
    "rain_3h", "rain_6h", "rain_24h",
    "elevation_m", "slope_deg", "dist_river_km", "drainage_quality",
]

ENGINEERED_COLS = [
    "rain_trend", "rain24_anomaly", "runoff_pressure", "river_pressure",
]

ALL_COLS = RAW_COLS + ENGINEERED_COLS


def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    g = df.groupby("ward")

    df["rain_trend"] = g["rain_3h"].diff().fillna(0)

    ward_norm = g["rain_24h"].transform("mean").replace(0, 1)
    df["rain24_anomaly"] = df["rain_24h"] / ward_norm

    df["runoff_pressure"] = df["rain_6h"] * (1 - df["drainage_quality"]) / (df["slope_deg"] + 0.5)
    df["river_pressure"] = df["rain_24h"] / (df["dist_river_km"] + 0.5)

    return df


def build_feature_table(dataset_path: str = "data/dataset.csv") -> pd.DataFrame:
    df = pd.read_csv(dataset_path, parse_dates=["timestamp"])
    df = df.sort_values(["ward", "timestamp"]).reset_index(drop=True)
    df = add_engineered_features(df)
    return df


def chronological_split(df: pd.DataFrame, train=0.70, val=0.15):
    """
    Split by date, not randomly - see roadmap stage 2 for why. Splits
    on the global timestamp so every ward's train/val/test boundary
    lines up on the same real dates.
    """
    dates = df["timestamp"].sort_values().unique()
    n = len(dates)
    train_end = dates[int(n * train)]
    val_end = dates[int(n * (train + val))]

    train_df = df[df.timestamp <= train_end]
    val_df = df[(df.timestamp > train_end) & (df.timestamp <= val_end)]
    test_df = df[df.timestamp > val_end]
    return train_df, val_df, test_df


if __name__ == "__main__":
    df = build_feature_table()
    tr, va, te = chronological_split(df)
    print(f"train {tr.timestamp.min().date()} - {tr.timestamp.max().date()}  ({len(tr)} rows)")
    print(f"val   {va.timestamp.min().date()} - {va.timestamp.max().date()}  ({len(va)} rows)")
    print(f"test  {te.timestamp.min().date()} - {te.timestamp.max().date()}  ({len(te)} rows)")
