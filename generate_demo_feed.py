"""
Runs the actual trained models across a real 10-day window (including
the Sept-2025 storm) for every ward, and writes the result as one JSON
file the dashboard can load directly - no live server required to
demo it. This is the same "replay" idea as api/data_feed.py, just
pre-computed instead of computed on each request.
"""

import json
import pandas as pd
from pathlib import Path

from data.make_dataset import load_or_build
from data.wards import load_wards
from predict_service import predict

WINDOW_START = "2025-09-05 00:00:00"
WINDOW_END = "2025-09-14 21:00:00"


def main():
    df = load_or_build().sort_values(["ward", "timestamp"]).reset_index(drop=True)
    wards = load_wards()

    start = pd.Timestamp(WINDOW_START)
    end = pd.Timestamp(WINDOW_END)

    frames = []
    for ward in wards["ward"]:
        wdf = df[df.ward == ward].reset_index(drop=True)
        target_idxs = wdf.index[(wdf.timestamp >= start) & (wdf.timestamp <= end)]

        for idx in target_idxs:
            if idx < 7:
                continue  # not enough history yet for a 24h window
            history = wdf.iloc[idx - 7: idx + 1][["timestamp", "rain_mm"]]
            result = predict(ward, history)
            frames.append({
                "ward": ward,
                "timestamp": wdf.iloc[idx]["timestamp"].isoformat(),
                "rain_mm_actual": round(float(wdf.iloc[idx]["rain_mm"]), 1),
                "rainfall_category": result["rainfall_outlook"]["category"],
                "rainfall_confidence": result["rainfall_outlook"]["confidence"],
                "flood_risk": result["flood_risk"]["level"],
                "flood_confidence": result["flood_risk"]["confidence"],
                "actual_flood_label": wdf.iloc[idx]["flood_risk_future"],
                "why": result["why"],
            })

    out = {
        "generated_window": {"start": WINDOW_START, "end": WINDOW_END},
        "wards": wards.to_dict(orient="records"),
        "predictions": frames,
    }

    Path("reports").mkdir(exist_ok=True)
    with open("reports/demo_feed.json", "w") as f:
        json.dump(out, f)

    print(f"{len(frames)} predictions across {wards.shape[0]} wards")
    print(f"file size: {Path('reports/demo_feed.json').stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
