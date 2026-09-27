"""
The one file that's supposed to change when MOSDAC/IMD access comes
through. Everything else in this project - the models, the API, the
dashboard - only ever calls get_history(ward, mode). Today "live"
mode just raises a clear error; the day real access exists, replace
the body of _fetch_live() with the actual API call and nothing else
in this codebase needs to know.
"""

import pandas as pd
from pathlib import Path

from data.make_dataset import load_or_build

_REPLAY_CACHE = None
_REPLAY_POINTER = {}  # per-ward index into the replay stream, so repeated calls advance in time


def _load_replay():
    global _REPLAY_CACHE
    if _REPLAY_CACHE is None:
        df = load_or_build()
        _REPLAY_CACHE = df.sort_values(["ward", "timestamp"]).reset_index(drop=True)
    return _REPLAY_CACHE


def _fetch_demo(ward: str, window: int = 8) -> pd.DataFrame:
    """
    Plays back the synthetic dataset like a live stream: each call
    advances one 3h step further into that ward's history. Good enough
    to make a dashboard behave like data is arriving in real time.
    """
    df = _load_replay()
    wdf = df[df.ward == ward].reset_index(drop=True)

    pos = _REPLAY_POINTER.get(ward, window)
    pos = min(pos, len(wdf) - 1)
    _REPLAY_POINTER[ward] = pos + 1 if pos + 1 < len(wdf) else window

    start = max(0, pos - window + 1)
    return wdf.iloc[start:pos + 1][["timestamp", "rain_mm"]].reset_index(drop=True)


def _fetch_live(ward: str, window: int = 8) -> pd.DataFrame:
    # TODO once MOSDAC/IMD access is approved: call the real API here,
    # reshape the response into the same two columns (timestamp, rain_mm)
    # as _fetch_demo returns, and switch DEFAULT_MODE below to "live".
    raise NotImplementedError(
        "live MOSDAC/IMD access isn't wired up yet - use mode='demo', "
        "or implement this function once API access is approved"
    )


DEFAULT_MODE = "demo"


def get_history(ward: str, mode: str = None, window: int = 8) -> pd.DataFrame:
    mode = mode or DEFAULT_MODE
    if mode == "demo":
        return _fetch_demo(ward, window)
    if mode == "live":
        return _fetch_live(ward, window)
    raise ValueError(f"unknown mode '{mode}', expected 'demo' or 'live'")


def list_wards():
    df = _load_replay()
    return sorted(df["ward"].unique().tolist())
