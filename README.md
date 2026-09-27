# Varshanetra - model prototype

Team Vortex, SIH26071. This is the ML piece behind the dashboard: two
models (rainfall nowcast + flood risk) trained end to end, wrapped in
a small API, with a swappable data feed so the live MOSDAC/IMD hookup
can be dropped in later without touching the models.

## What's real and what isn't, right now

Trained on a synthetic monsoon dataset for 15 Pune wards
(`data/make_dataset.py`), not real IMD/MOSDAC history - that access is
still pending. Terrain numbers (elevation, slope, drainage, distance
to river) are plausible placeholders per ward, not a DEM extract.
Everything downstream - features, models, API - is real and runs on
whatever data it's pointed at, so swapping in real data later is a
data-loading change, not a rebuild. Say this plainly in the report;
see `PROJECT_NOTES.md` for the longer version of this paragraph.

## Layout

```
data/
  wards.py          15 Pune wards with terrain attributes
  make_dataset.py   builds the synthetic rainfall + flood-risk dataset
features.py         feature engineering, shared by training + API
train_baseline.py   Random Forest, stage 4
train_boosted.py    XGBoost (falls back to sklearn HGB if xgboost
                     isn't installed), stage 5
ablation.py          raw vs engineered features, stage 6
explain.py           SHAP if installed, else a permutation-importance
                     fallback with the same interface
predict_service.py   the actual predict(ward, history) call, no web
                     framework dependency
api/
  data_feed.py       demo replay now, one place to wire up live data later
  main.py            FastAPI wrapper around predict_service
generate_demo_feed.py       bakes real predictions across a demo storm
                             window -> reports/demo_feed.json
generate_extra_views_data.py  historical stats + feature importance ->
                               reports/historical_summary.json, feature_importance.json
dashboard_template.html     the dashboard's HTML/CSS/JS, with data placeholders
build_dashboard.py          fills the template with reports/ data -> dashboard.html
dashboard.html               the actual dashboard - open this directly, already built
reports/             metrics + ablation + demo-feed json, written by
                     the scripts above
models/              trained model files (joblib), written by the
                     scripts above
```

## Running it

```
pip install -r requirements.txt

python data/make_dataset.py      # writes data/dataset.csv
python train_baseline.py         # writes models/*_rf.joblib
python train_boosted.py          # writes models/*_boosted.joblib
python ablation.py               # writes reports/ablation.json
python explain.py                # prints one worked example

uvicorn api.main:app --reload --port 8000
```

Then, e.g.:

```
curl -X POST localhost:8000/predict -H "Content-Type: application/json" \
  -d '{"ward": "kharadi", "mode": "demo"}'
```

`/demo/predict/{ward}` does the same thing as a plain GET, if you just
want to check it in a browser.

## Current numbers

RF baseline vs boosted, on a chronological test split that includes
one held-out storm event (see `reports/*.json` for exact figures):

- Flood risk (model B): ~84-85% accuracy, ~90% recall on the "danger"
  class specifically - the recall number matters more than accuracy
  here, since missing a real danger case is the costly mistake.
- Rainfall nowcast (model A): ~43-47% accuracy. Genuinely harder
  problem - predicting the next 3h of rain from rainfall history alone,
  with no live satellite/radar input yet, has a real ceiling. This
  matches the "prediction accuracy during extreme events" challenge
  already named on the feasibility slide, and is the strongest
  argument for why the MOSDAC access actually matters, not just a box
  to tick.
- Ablation: the hand-engineered interaction features (runoff_pressure,
  river_pressure, etc) made no meaningful difference for either model
  once Random Forest already has the raw columns - trees pick up that
  kind of interaction on their own. Worth a line in the report; not
  worth overselling the feature engineering.

## Dashboard

`dashboard.html` in this folder is already built — open it directly in
a browser, no server, no build step needed. It has 10 sections
(sidebar nav): Dashboard, Real-time Data, Rainfall Forecast,
Inundation Map, Risk Analysis, Safe Routes, Alerts, Historical
Analysis, Reports, About — all driven by real model output, replayed
across a real storm window, not hand-typed numbers.

If you change the model, data, or the time window and want to rebuild
it, run these in order:

```
python data/make_dataset.py          # (only if you changed data generation)
python train_baseline.py
python train_boosted.py
python ablation.py
python generate_demo_feed.py         # bakes predictions across the demo window
python generate_extra_views_data.py  # historical + feature-importance data
python build_dashboard.py            # writes dashboard.html, ready to open
```

`build_dashboard.py` reads `dashboard_template.html` plus everything
in `reports/` and writes the final `dashboard.html` — that's the only
file you actually open.

To go from this to a truly live dashboard: stand up `api/main.py`
somewhere reachable from a browser (even just your own laptop on the
same wifi as your demo screen), then replace the `const RAW = ...`
line in `dashboard_template.html` with a `fetch()` call to your
`/predict` endpoint instead, and rebuild. Same UI, live data.



Two separate upgrades, don't conflate them:

1. **Live current conditions** - implement `_fetch_live()` in
   `api/data_feed.py`, point `DEFAULT_MODE` at `"live"`. Nothing else
   changes; models and API are already shaped for it.
2. **Retraining on real history** - once real historical rainfall/flood
   data is available (IMD, data.gov.in, or MOSDAC's archive), replace
   `data/make_dataset.py`'s output with that data in the same column
   shape and rerun `train_baseline.py` / `train_boosted.py` as-is. This
   is the upgrade that actually makes predictions reliable, not just
   demoable - do it if there's time before the deadline, but it's not
   required to have a working prototype.
