"""
Static ward table for the Pune prototype.

Elevation/slope/drainage numbers here are plausible placeholders, not
survey data - swap this file for a real DEM + drainage-network extract
(the GeoPandas/Rasterio step in the roadmap) once that's available.
"""

import pandas as pd

WARDS = [
    # name, lat, lon, elevation_m, slope_deg, dist_river_km, drainage_quality (0=poor,1=good)
    ("kothrud",        18.5074, 73.8077, 585, 3.2, 2.8, 0.62),
    ("shivajinagar",   18.5308, 73.8475, 561, 1.1, 0.6, 0.55),
    ("hadapsar",       18.5089, 73.9260, 552, 0.8, 1.4, 0.41),
    ("kondhwa",        18.4650, 73.8933, 570, 1.6, 2.1, 0.48),
    ("yerwada",        18.5535, 73.8800, 549, 0.6, 0.3, 0.58),
    ("aundh",          18.5590, 73.8077, 564, 1.9, 1.8, 0.66),
    ("baner",          18.5590, 73.7868, 592, 2.7, 3.4, 0.70),
    ("katraj",         18.4520, 73.8642, 611, 4.1, 4.6, 0.57),
    ("warje",          18.4809, 73.8060, 578, 2.4, 1.1, 0.51),
    ("dhankawadi",     18.4620, 73.8420, 596, 3.0, 3.0, 0.53),
    ("bibvewadi",      18.4680, 73.8630, 567, 1.3, 2.4, 0.39),
    ("wanowrie",       18.4880, 73.8990, 558, 1.0, 1.9, 0.44),
    ("vishrantwadi",   18.5670, 73.8790, 545, 0.5, 0.4, 0.35),
    ("sinhagad_road",  18.4630, 73.8180, 602, 3.6, 3.9, 0.60),
    ("kharadi",        18.5510, 73.9420, 540, 0.4, 0.2, 0.32),
]

COLUMNS = ["ward", "lat", "lon", "elevation_m", "slope_deg", "dist_river_km", "drainage_quality"]


def load_wards() -> pd.DataFrame:
    return pd.DataFrame(WARDS, columns=COLUMNS)


if __name__ == "__main__":
    df = load_wards()
    df.to_csv("data/wards.csv", index=False)
    print(df)
