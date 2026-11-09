# BI Group 10 — Task 10–12 Acceptance Review

Reviewed: 2026-11-09 (Vietnam). Data source: repository code, DDS schema audit, the stored baseline/integrity audits, and Google Drive deployment dataset. **This is not a successful production acceptance certificate.**

## Verified source and code
- GitHub repository: `by-nhuanh/fleet-bi-dashboard`.
- Deployment datasets: `database/fleet_dw.duckdb` and `database/fleet_analysis.duckdb` present in repository.
- Analysis DuckDB source (Google Drive) was fetched with size 64,499,712 bytes (61.51 MiB); user-provided extraction verified 1,435,571 GPS observations for 746 trips.
- DDS audit: 85,410 trips (unique trip_id), 77,959 KPI-eligible trips, 51,970 eligible late trips, 196,442 fuel purchase records, USD 95,592,992.04 purchase cost. Late rate = 51,970 / 77,959 = 66.66%.
- Original DDS integrity audit: 1,435,571 GPS message IDs unique; no orphan GPS-trip links; no unmatched GPS date/time links; no invalid geographic coordinates or negative GPS speed.
- Recorded GPS labels: NORMAL 1,435,491; IDLE_EXTENDED 36; GPS_JUMP_RECOVERY 16; FUEL_THEFT 15; FUEL_RECEIPT_MISMATCH 13.
- Only 746/85,410 trips have GPS. Avoid extrapolating GPS anomalies to the whole fleet.
- Original DDS integrity audit also records 204 fuel-purchase/linked-trip vehicle mismatches. Fuel cost grouped using trip keys is distinct from a purchase-vehicle-level total.

## Task 10 — Overview
**Code present**: connected DDS DuckDB; trip count, KPI-eligible late-delivery rate, linked fuel-purchase cost; monthly trends; time, vehicle, origin-facility, origin-facility-type and destination filters.

**Accepted as implemented in code, not live browser**:
- Metric definitions use `is_kpi_eligible=1` and `delay_minutes>0`.
- Origin facility is the explicit operational proxy for a branch. No independent branch dimension was verified.
- SQL joins Fact_Trips → Dim_Date, Dim_Vehicle, Dim_Location, and fuel purchases by trip_id.
- Streamlit was adopted as an alternative to the originally named Power BI/PBIX deliverable.

**Not yet verified**: automatic acceptance tests actually passing on GitHub Actions/Streamlit Cloud; UI contrast on all browsers; the report chapters 4.1–4.2 as formally submitted artifacts.

## Task 11 — GIS and route analysis
**Code present**: GPS heatmap using user-selected low-speed threshold, route-level trip counts and eligible late-delivery rate, separate selected-trip observed GPS point map.

**Important limit**: low-speed telemetry, including points near origin/destination facilities, does not itself prove a traffic jam. An evidence-based geofence dwell-time classification and a validated road-congestion conclusion are not yet implemented. The map is based on recorded GPS points, not true road-network geometry.

**Not yet verified**: live rendering/performance and GIS output figures for chapter 4.3.

## Task 12 — Fuel analysis
**Code present**: individual-trip time-series of fuel level and vehicle speed, engine status, observed anomaly labels, fleet-wide flagged-vehicle listing, and conditional diagnostic guidance.

**Important limit**: The existing labels are mock-data annotations. There is no validated automatic inference of theft, prolonged engine idle, or a mechanical fault from measured sequences with approved quantitative thresholds; such an inference must not be claimed as completed. `FUEL_THEFT` is a warning label, not a verified theft allegation.

**Not yet verified**: live rendering/performance and a validated classification of the three required causal scenarios; chapter 4.4 output narrative.

## Tests committed to repository
- `tests/test_overview.py`: KPI totals, dimension key uniqueness and fact links, fuel reconciliation, monthly aggregates.
- `tests/test_geo_fuel.py`: GPS counts, dimension links, anomaly-label distribution.
- `tests/test_pages_smoke.py`: headless Streamlit runtime execution for all three pages.
- `.github/workflows/validate.yml`: runs Python syntax and unit tests after pushes.

**Execution evidence**: The files and workflow were committed. A passing test run could not be independently retrieved in this review (GitHub commit status response returned no statuses). DuckDB/Streamlit were unavailable for local execution in the reviewer environment. Therefore test outcomes must remain **unverified**, not PASS.

## Acceptance decision
- Task 10: core implementation completed; **conditional acceptance pending CI and deployed UI validation**, branch proxy terminology and written report.
- Task 11: functional prototype delivered; **not full acceptance** until required geofence/traffic distinctions and live validation.
- Task 12: functional prototype and warning inventory delivered; **not full acceptance** until scenario decision logic is validated and the reporting narrative is completed.

No numerical threshold, root-cause verdict, or missing evidence was invented to make the acceptance status appear complete.
