# Fleet BI — Logistics Operations Analytics

Streamlit dashboard for Task 10–12, using original DDS DuckDB (no generated KPI values).

## Pages
- **Task 10 — Overview** (`app.py`): trip count, late-delivery rate, fuel-purchase cost; start-date, origin facility (operational branch proxy), vehicle, origin type and destination filters.
- **Task 11 — Route GIS** (`pages/2_Route_GIS.py`): observed GPS location heatmap, operator-selected low-speed threshold, route trip volume and late rates. Slow GPS points are *not* proof of traffic congestion.
- **Task 12 — Fuel Analytics** (`pages/3_Fuel_Analytics.py`): individual-trip fuel and speed traces, engine status, recorded anomaly labels and a diagnostic decision guide. Labels are **not** proven fraud or mechanical defects.

## Data
- `database/fleet_dw.duckdb`: compact DDS for Overview (85,410 trips, 77,959 KPI eligible, 51,970 late, USD 95,592,992.04 in linked fuel purchases).
- `database/fleet_analysis.duckdb`: compact DDS for GIS/Fuel, produced from original shared-project database using `scripts/export_analysis_db.py`. Expected 1,435,571 GPS points covering 746 trips; about 61.51 MiB. Upload this separately from the original large warehouse file.
- The analytics app does not represent live vehicle telemetry.

## Definitions and limitations
- Late delivery rate: **count of eligible trips where delay_minutes > 0 / count of eligible trips**. No use of `is_late_delivery` flag.
- Fuel purchase cost in Overview is tied to **trip start date** via `trip_id`, not fuel transaction date.
- There is no independently validated `branch` dimension. **Origin operational facility** is used as a *proxy* for site-level filtering, clearly labelled as such.
- GPS covers **746 of 85,410 trips**, so GIS/Fuel insights only apply to trips with telemetry.
- Task 12 decision logic is a guide to testing hypotheses. Automated root-cause classification would require approved fuel-change thresholds and validation evidence.

## Local launch
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Automated acceptance checks
```bash
python -m unittest discover -s tests -v
```
GitHub Actions runs the test suite and Python syntax checks on every push to `main`. Only passing runs provide evidence of validation; merely committing test files does not.

## Deliverables
- Dashboard: https://fleet-bi-dashboard.streamlit.app/
- Source code, README, and test suite in this repository.
- Screenshots for chapter 4.1–4.4 should be captured from the deployed real-data dashboard after validation.
