# Notes for the report - what's real vs simulated

Use/adapt this directly for the limitations section of the report or
for answering a judge's question on the spot.

## Data

The current prototype is trained on a synthetic monsoon dataset we
generated for 15 Pune wards, not on real IMD/MOSDAC/radar history.
Real access to MOSDAC is a registration process we've started but
hasn't come through yet. The synthetic data was built to be physically
plausible, not arbitrary: rainfall follows a seasonal wet-probability
curve with short-term autocorrelation and a handful of deliberate
multi-day storm events, and flood risk is computed from that rainfall
combined with each ward's terrain (elevation, slope, drainage quality,
distance to river) with added noise, so it isn't a clean deterministic
lookup table either.

Terrain numbers per ward (elevation, slope, drainage, distance to
river) are plausible placeholders based on general knowledge of Pune's
geography, not extracted from a real DEM or drainage-network survey.
That extraction (via GeoPandas/Rasterio, as named in the technical
approach) is the next real step once real terrain data is sourced.

## Models

Two models, both genuinely trained and evaluated on a held-out,
chronologically-split test set (never shuffled randomly - see
features.py):

- Model A (rainfall nowcast, 3h ahead): Random Forest baseline,
  upgraded to gradient-boosted trees. Real accuracy figures in
  reports/boosted_metrics.json.
- Model B (flood risk, 6h ahead): same structure, uses Model A's
  rainfall signal plus terrain. Recall on the "danger" class is the
  headline number, not raw accuracy, because a missed flood is the
  costly failure mode for an alert system.

The gradient-boosting library is XGBoost where available; the code
falls back to scikit-learn's HistGradientBoostingClassifier
automatically if xgboost isn't installed, with no other code changes.
Both are the same family of model (gradient-boosted decision trees).

## Explainability

Uses SHAP where installed; falls back to a permutation-importance
based local explanation with the same interface if not. If you end up
demoing with the fallback, call it a "feature-contribution estimate,"
not SHAP specifically - it's a reasonable stand-in, not the same math.

## What an ablation study told us

We compared the models with only raw rainfall/terrain columns against
the same models with added hand-engineered interaction features
(rainfall trend, rainfall anomaly vs ward average, a runoff-pressure
term, a river-proximity term). On this dataset, the engineered
features made no measurable difference for either model - tree-based
models can already approximate those interactions from the raw columns
via their split structure. We're reporting this honestly rather than
overstating the feature engineering; it's still worth mentioning as
evidence we tested the idea rather than assumed it.

## What would most improve this system next

In order of expected impact: (1) real historical rainfall/flood data
to train on instead of synthetic data, (2) real terrain data from a
DEM instead of placeholder per-ward numbers, (3) live MOSDAC/IMD
access for current conditions, replacing the demo replay feed. All
three are additive - the modeling code doesn't need to change shape
for any of them, only the data sources feeding it.
