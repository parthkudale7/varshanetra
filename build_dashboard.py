"""
Builds the actual dashboard.html from dashboard_template.html plus real
model output. This is the ONLY build script now - it supersedes the
earlier single-page version.

Run order (from a clean checkout):
    python data/make_dataset.py
    python train_baseline.py
    python train_boosted.py
    python ablation.py
    python generate_demo_feed.py
    python generate_extra_views_data.py
    python build_dashboard.py          <- this file, run last
"""

import json
from pathlib import Path

template = Path("dashboard_template.html").read_text(encoding='utf-8')
raw = json.loads(Path("reports/demo_feed.json").read_text(encoding='utf-8'))

extra = {
    "metrics": {
        **json.loads(Path("reports/baseline_metrics.json").read_text(encoding='utf-8')),
        **json.loads(Path("reports/boosted_metrics.json").read_text(encoding='utf-8')),
    },
    "ablation": json.loads(Path("reports/ablation.json").read_text(encoding='utf-8')),
    "historical": json.loads(Path("reports/historical_summary.json").read_text(encoding='utf-8')),
    "importance": json.loads(Path("reports/feature_importance.json").read_text(encoding='utf-8')),
}

out = template.replace("__DATA_JSON__", json.dumps(raw)).replace("__EXTRA_JSON__", json.dumps(extra))
assert "__DATA_JSON__" not in out and "__EXTRA_JSON__" not in out, "template placeholder wasn't filled - check reports/ files exist"

out_path = Path("dashboard.html")
out_path.write_text(out, encoding='utf-8')
print(f"wrote {out_path.resolve()}  ({out_path.stat().st_size/1024:.0f} KB)")
print("open this file directly in a browser - no server needed")
