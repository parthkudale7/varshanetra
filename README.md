# Varshanetra

**AI/ML-based heavy rainfall early warning and inundation prediction system** for Pune, built for **Smart India Hackathon 2026**.

> Developed as a prototype AI/ML solution for heavy rainfall early warning and inundation prediction. This is a hackathon/research-stage project — it is **not** a government-deployed or operationally-certified system. See [Current Prototype Status](#current-prototype-status) below.

**Team Vortex** · Team ID **ZIH120** · Problem Statement **SIH26071** · Theme: **Disaster Management**

---

## Problem

Heavy rainfall events in Indian cities can escalate into urban flooding with very little warning. Forecasts are often city-wide or district-wide, when what actually matters is **which specific ward floods, and how much lead time residents get** — late or inaccurate warnings, rainfall forecasts that don't translate into flood forecasts, and a lack of actionable, ward-level inundation maps all compound the damage. Emergency response ends up reactive instead of predictive.

## Solution

Varshanetra is an AI-powered early-warning tool that predicts **where** in Pune flooding is likely during heavy rain, not just that heavy rain is coming. It runs two coupled models:

- **Model A — Rainfall Outlook**: predicts rainfall severity (light / moderate / heavy / extreme) for the next 3 hours, from recent rainfall history.
- **Model B — Flood Risk**: predicts ward-level flood risk (safe / watch / warning / danger) for the next 6 hours, combining Model A's rainfall signal with each ward's terrain — elevation, slope, drainage quality, and distance to the nearest river.

Both feed a colour-coded risk map and a ward-by-ward dashboard, with an explainability layer that shows **why** a given ward was flagged, not just that it was.

## Key Innovation

Most rainfall-nowcasting systems stop at "how much rain." Varshanetra's flood-risk model explicitly fuses rainfall with **terrain vulnerability**, so the same rainfall total can correctly register as low risk in a well-drained, elevated ward and high risk in a low-lying, poorly-drained one next door — which is what actually determines flooding, not rainfall alone.

An honest finding from the project's own ablation study (see [Model](#model)): the hand-engineered interaction features (`runoff_pressure`, `river_pressure`) rank as the model's *most*-relied-on inputs by internal importance, yet removing them doesn't measurably hurt test accuracy. Tree-based models evidently reconstruct the same interaction from the raw rainfall and terrain columns on their own. Reported here as-is, not smoothed over — it's a more credible result than a scripted "everything improved."

## System Architecture

```
Rainfall history (1h/3h/6h/24h) ──┐
                                    ├──► Feature engineering ──► Model A (rainfall) ──┐
Ward terrain (elevation, slope,   │                                                  │
  drainage, distance to river) ───┘                                                  ▼
                                                          Model B (flood risk, per ward)
                                                                      │
                                                                      ▼
                                                    Explainability ("why" factors)
                                                                      │
                                                                      ▼
                                                   FastAPI inference service (/predict)
                                                                      │
                                                                      ▼
                                                        10-view dashboard (HTML/JS)
```

## Features

- Two-model pipeline: rainfall nowcast (Model A) + terrain-aware flood risk (Model B)
- Chronological train/validation/test split with a held-out real storm event — never a random shuffle, since that would let the model "see the future" (see [Model](#model))
- Baseline-vs-engineered-features ablation study with real, reported numbers
- Per-prediction explainability ("why" factors behind each flood-risk call)
- Swappable data-feed design (`api/data_feed.py`): a demo-replay feed today, one function to change for a live MOSDAC/IMD feed later — nothing else in the pipeline needs to change
- FastAPI inference service with a demo-mode endpoint for testing without a live sensor feed
- A 10-view dashboard: Dashboard, Real-time Data, Rainfall Forecast, Inundation Map (real OpenStreetMap tiles, with a current-risk / terrain-vulnerability toggle), Risk Analysis, Safe Route Advisory, Alerts log, Historical Analysis, Reports (with print/PDF export), and About
- Clearly labelled demo/replay mode throughout — the dashboard says so on screen, it isn't hidden

## Technology Stack

```
Data & modelling:
  Python, pandas, NumPy
  scikit-learn (Random Forest baseline)
  XGBoost — falls back automatically to scikit-learn's
  HistGradientBoostingClassifier if xgboost isn't installed
  joblib (model persistence)
  SHAP — falls back to a permutation-importance based explainer
  if shap isn't installed

Backend:
  FastAPI, Pydantic, Uvicorn

Dashboard:
  HTML, CSS, JavaScript (single self-contained file, no build step)
  Leaflet.js + OpenStreetMap tiles (real map, live internet required)
  Font Awesome (icons), IBM Plex Sans / Mono (typefaces)
```

## Project Structure

```
varshanetra-model/
├── README.md
├── PROJECT_NOTES.md            what's real vs. simulated, in detail
├── requirements.txt
│
├── data/
│   ├── wards.py                 15 Pune wards + terrain attributes
│   └── make_dataset.py          builds the training dataset
│
├── features.py                  shared feature engineering (training + API)
├── train_baseline.py            Random Forest models
├── train_boosted.py             gradient-boosted upgrade (XGBoost or fallback)
├── ablation.py                  raw-vs-engineered-features study
├── explain.py                   per-prediction explainability
├── predict_service.py           core predict(ward, history) logic
│
├── api/
│   ├── data_feed.py              swappable demo/live data source
│   └── main.py                    FastAPI app
│
├── generate_demo_feed.py         bakes real predictions for the dashboard demo
├── generate_extra_views_data.py  historical stats + feature importance
├── dashboard_template.html       dashboard source (HTML/CSS/JS)
├── build_dashboard.py            fills the template with real model output
├── dashboard.html                 the built dashboard — open this directly
│
├── models/                       trained model files (.joblib)
└── reports/                      metrics, ablation results, demo data (.json)
```

## Installation

### Prerequisites

- Python 3.10+
- (optional) Node/npm — not required; the dashboard is a single static HTML file

### Setup

```bash
git clone https://github.com/parthkudale7/varshanetra.git
cd varshanetra

python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
```

## Running It

```bash
python data/make_dataset.py
python train_baseline.py
python train_boosted.py
python ablation.py
python generate_demo_feed.py
python generate_extra_views_data.py
python build_dashboard.py
```

Then open `dashboard.html` directly in a browser — no server required to view it.

To run the live API instead:

```bash
uvicorn api.main:app --reload --port 8000
curl -X POST localhost:8000/predict -H "Content-Type: application/json" -d '{"ward": "kharadi", "mode": "demo"}'
```

## API

| Method | Path                    | Purpose                                             |
|--------|-------------------------|------------------------------------------------------|
| GET    | `/health`               | Service status                                       |
| GET    | `/wards`                | List of all 15 Pune wards                             |
| POST   | `/predict`               | Full prediction for a ward (`{"ward": "...", "mode": "demo"}`) |
| GET    | `/demo/predict/{ward}`   | Same as above, as a plain GET — handy for a quick browser check |

## Model

Both models are trained and evaluated on a chronological split (never a random shuffle — see [`features.py`](features.py)), with one real storm window held out entirely for testing. Random Forest is the baseline; the boosted upgrade uses XGBoost where installed, or scikit-learn's `HistGradientBoostingClassifier` automatically otherwise — same family of model, same interface, no other code changes needed either way.

Flood risk (Model B) reaches roughly 85% accuracy and around 90% recall on the "danger" class specifically — recall matters more than raw accuracy here, since missing a real danger case is the costly failure mode for an alert system. Rainfall nowcasting (Model A) is meaningfully harder — around 44–49% accuracy — which is a genuine finding, not a weak spot to hide: predicting the next 3 hours of rain from rainfall history alone, with no live satellite/radar input yet, has a real ceiling. It's the strongest argument for why real MOSDAC/IMD access matters. Exact current figures are in `reports/baseline_metrics.json` and `reports/boosted_metrics.json`.

Full explanation of features, the ablation study, and the explainability approach: [`PROJECT_NOTES.md`](PROJECT_NOTES.md).

## Current Prototype Status

Stated plainly:

- **Training data is synthetic**, not real IMD/MOSDAC history — built to be physically plausible (seasonal rainfall patterns, real storm events, terrain-driven flood risk), but not observed data. Real access is a registration process still in progress.
- **Ward terrain values are plausible placeholders**, not extracted from a real elevation survey (DEM) — that extraction is the next real step once real terrain data is sourced.
- **The dashboard replays a real trained model's output across a real storm window**, rather than connecting to a live feed — every number is genuine model output, just not live yet. This is stated on screen, not hidden.
- **The Inundation Map uses real OpenStreetMap tiles** when the dashboard is opened with an internet connection; ward positions are real coordinates.
- **Safe Route Advisory reports risk levels honestly but does not compute an actual road route** — that needs real road-network data and a routing engine, a solid next step rather than something to claim exists today.

## Future Scope

- Real historical rainfall/flood data (IMD, data.gov.in, or MOSDAC archive access) to retrain on — the single highest-impact upgrade
- A real DEM and drainage-network extract, replacing the placeholder terrain values
- Live MOSDAC/IMD access, replacing the demo replay feed (a one-function swap — see `api/data_feed.py`)
- A real routing engine (e.g. OSRM) with actual road-network data, for genuine safe-route calculation
- Expanded coverage beyond the current 15 wards

## SIH 2026

Developed by Team Vortex as an AI/ML-based solution for heavy rainfall early warning and inundation prediction, submitted for Smart India Hackathon 2026 evaluation. A working prototype and architecture, not a deployed or government-endorsed operational system.

## License

ZCOER - see LICENSE .
