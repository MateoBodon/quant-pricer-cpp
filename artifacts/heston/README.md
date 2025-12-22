# Heston calibration artifacts

Tracked artifacts exclude per-strike fit tables (e.g., `fit_YYYYMMDD.csv`) because they can resemble raw market quote surfaces. Generate those tables locally with `scripts/calibrate_heston.py` or `scripts/calibrate_heston_series.py` and keep them untracked unless they are explicitly synthetic/public-source.
