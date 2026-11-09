"""Export real DDS tables for Task 11 (GIS) and Task 12 (fuel diagnostics).

Run in Google Colab after mounting the existing Project folder.
This script never modifies the original warehouse database.
"""
from pathlib import Path
import duckdb

def export_analysis_db(source: Path, destination: Path):
    source = Path(source).resolve()
    destination = Path(destination).resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Missing original DDS: {source}")
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(destination))
    source_sql = str(source).replace("'", "''")
    try:
        con.execute(f"ATTACH '{source_sql}' AS src (READ_ONLY)")
        con.execute("CREATE SCHEMA dds")
        definitions = {
            "Fact_Trips": (
                "trip_id,start_date_key,vehicle_key,driver_key,route_key,"
                "origin_location_key,dest_location_key,actual_distance_km,"
                "duration_minutes,idle_time_minutes,fuel_consumed_liters,"
                "delay_minutes,is_kpi_eligible"
            ),
            "Dim_Date": "date_key,full_date,year,month",
            "Dim_Time": "time_key,hour_24,minute",
            "Dim_Vehicle": "vehicle_key,truck_id,make,fuel_type",
            "Dim_Route": (
                "route_key,route_id,origin_city,origin_state,"
                "destination_city,destination_state,typical_distance_km,"
                "typical_transit_days"
            ),
            "Dim_Location": (
                "location_key,facility_id,facility_name,facility_type,"
                "city,state,latitude,longitude,geofence_radius_meters"
            ),
            "Fact_Fuel_Purchases": (
                "fuel_purchase_id,trip_id,vehicle_key,date_key,"
                "liters_purchased,total_cost_usd"
            ),
            "Fact_GPS_Points": (
                "message_id,trip_id,vehicle_key,date_key,time_key,"
                "latitude,longitude,speed_kmh,derived_speed_kmh,"
                "distance_from_prev_km,fuel_level_pct,"
                "fuel_liters_remaining,is_idle_stop,engine_status,anomaly_type"
            ),
        }
        for table, fields in definitions.items():
            con.execute(f"CREATE TABLE dds.{table} AS "
                        f"SELECT {fields} FROM src.dds.{table}")
            n = con.execute(f"SELECT COUNT(*) FROM dds.{table}").fetchone()[0]
            print(f"{table}: {n:,}")
        rows = con.execute("""
            SELECT COUNT(*),COUNT(DISTINCT trip_id)
            FROM dds.Fact_GPS_Points
        """).fetchone()
        assert rows == (1435571,746), f"Unexpected GPS counts: {rows}"
        gps_groups = con.execute("""
            SELECT anomaly_type,COUNT(*)
            FROM dds.Fact_GPS_Points
            GROUP BY anomaly_type ORDER BY anomaly_type
        """).fetchall()
        print("GPS anomaly labels:", gps_groups)
        con.execute("CHECKPOINT")
        print(f"Export completed: {destination}")
    finally:
        con.close()
    print(f"Size: {destination.stat().st_size / 1024**2:.2f} MB")
    return destination

if __name__ == "__main__":
    raise SystemExit("Import export_analysis_db and pass source and destination paths.")
