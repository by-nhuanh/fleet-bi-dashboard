"""Targeted, read-only investigation of DDS fuel mismatches and sensor regularity."""
import json
from pathlib import Path
from datetime import date, datetime
import duckdb

ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/"database"/"fleet_analysis.duckdb"
OUT=ROOT/"audit"/"exceptions_investigation.json"

def query(con,sql,params=None):
    q=con.execute(sql,params or [])
    cols=[d[0] for d in q.description]
    return [dict(zip(cols,row)) for row in q.fetchall()]

def encode(v):
    if isinstance(v,(date,datetime)):return v.isoformat()
    if isinstance(v,list):return [encode(x) for x in v]
    if isinstance(v,dict):return {str(k):encode(x) for k,x in v.items()}
    return v

def main():
    con=duckdb.connect(str(DB),read_only=True)
    result={"source":"database/fleet_analysis.duckdb",
            "status":"Investigative observations, not changes to source",
            "fuel_mismatch":{},"gps_signal":{},"limitations":[]}
    try:
        result["fuel_mismatch"]["summary"]=query(con,"""
          WITH mismatch AS (
            SELECT f.trip_id,f.fuel_purchase_id,f.vehicle_key AS purchase_key,
              t.vehicle_key AS trip_key,f.total_cost_usd,f.liters_purchased
            FROM dds.Fact_Fuel_Purchases f
            JOIN dds.Fact_Trips t ON t.trip_id=f.trip_id
            WHERE f.vehicle_key IS DISTINCT FROM t.vehicle_key
          )
          SELECT COUNT(*) AS rows,COUNT(DISTINCT trip_id) AS affected_trips,
                 COUNT(DISTINCT purchase_key) AS purchase_vehicle_keys,
                 COUNT(DISTINCT trip_key) AS trip_vehicle_keys,
                 SUM(total_cost_usd) AS total_usd,
                 SUM(liters_purchased) AS total_liters,
                 COUNT(*) FILTER (WHERE purchase_key IS NULL OR trip_key IS NULL) AS null_key_rows
          FROM mismatch
        """)[0]
        result["fuel_mismatch"]["by_purchase_month"]=query(con,"""
          SELECT d.year,d.month,COUNT(*) AS mismatch_rows,
                 COUNT(DISTINCT f.trip_id) AS trips,
                 ROUND(SUM(f.total_cost_usd),2) AS cost_usd
          FROM dds.Fact_Fuel_Purchases f
          JOIN dds.Fact_Trips t ON t.trip_id=f.trip_id
          JOIN dds.Dim_Date d ON d.date_key=f.date_key
          WHERE f.vehicle_key IS DISTINCT FROM t.vehicle_key
          GROUP BY 1,2 ORDER BY mismatch_rows DESC,year,month LIMIT 18
        """)
        result["fuel_mismatch"]["top_vehicle_pairs"]=query(con,"""
          SELECT COALESCE(v1.truck_id,'(unknown)') AS purchased_vehicle,
                 COALESCE(v2.truck_id,'(unknown)') AS trip_vehicle,
                 COUNT(*) AS mismatch_rows,
                 COUNT(DISTINCT f.trip_id) AS trips,
                 ROUND(SUM(f.total_cost_usd),2) AS cost_usd
          FROM dds.Fact_Fuel_Purchases f
          JOIN dds.Fact_Trips t ON t.trip_id=f.trip_id
          LEFT JOIN dds.Dim_Vehicle v1 ON v1.vehicle_key=f.vehicle_key
          LEFT JOIN dds.Dim_Vehicle v2 ON v2.vehicle_key=t.vehicle_key
          WHERE f.vehicle_key IS DISTINCT FROM t.vehicle_key
          GROUP BY 1,2 ORDER BY mismatch_rows DESC,cost_usd DESC LIMIT 15
        """)
        result["fuel_mismatch"]["by_transaction_trip_match"]=query(con,"""
          SELECT CASE WHEN f.vehicle_key=t.vehicle_key THEN 'match'
                      ELSE 'mismatch' END AS status,
                 COUNT(*) AS transactions,
                 COUNT(DISTINCT f.trip_id) AS trips,
                 ROUND(SUM(f.total_cost_usd),2) AS total_cost_usd
          FROM dds.Fact_Fuel_Purchases f
          JOIN dds.Fact_Trips t ON t.trip_id=f.trip_id
          GROUP BY 1 ORDER BY 1
        """)
        result["fuel_mismatch"]["overlap_with_gps_labels"]=query(con,"""
          WITH mismatched_trips AS (
             SELECT DISTINCT f.trip_id
             FROM dds.Fact_Fuel_Purchases f JOIN dds.Fact_Trips t USING(trip_id)
             WHERE f.vehicle_key IS DISTINCT FROM t.vehicle_key
          )
          SELECT COUNT(*) AS mismatched_trips,
            COUNT(*) FILTER(WHERE gps.trip_id IS NOT NULL) AS with_gps,
            COUNT(*) FILTER(WHERE mismatch.trip_id IS NOT NULL) AS with_receipt_label
          FROM mismatched_trips mt
          LEFT JOIN (SELECT DISTINCT trip_id FROM dds.Fact_GPS_Points) gps USING(trip_id)
          LEFT JOIN (SELECT DISTINCT trip_id FROM dds.Fact_GPS_Points
                     WHERE anomaly_type='FUEL_RECEIPT_MISMATCH') mismatch USING(trip_id)
        """)[0]
        # Distribution over all GPS trips, comparing stable speed and fuel delta.
        result["gps_signal"]["trip_distribution"]=query(con,"""
          WITH signals AS (
            SELECT g.trip_id,g.speed_kmh,g.fuel_level_pct,g.anomaly_type,
                   LAG(g.speed_kmh) OVER
                     (PARTITION BY g.trip_id ORDER BY g.date_key,g.time_key,g.message_id) AS prev_speed,
                   LAG(g.fuel_level_pct) OVER
                     (PARTITION BY g.trip_id ORDER BY g.date_key,g.time_key,g.message_id) AS prev_fuel,
                   g.date_key,g.time_key
            FROM dds.Fact_GPS_Points g
          ), trip_stats AS (
            SELECT trip_id,COUNT(*) AS n,
              COUNT(DISTINCT speed_kmh) AS speed_unique,
              COUNT(*) FILTER(WHERE prev_speed IS NOT NULL AND ABS(speed_kmh-prev_speed)>.01)
                AS speed_changes,
              STDDEV_POP(fuel_level_pct-prev_fuel) AS fuel_delta_std,
              AVG(fuel_level_pct-prev_fuel) AS fuel_delta_avg,
              COUNT(*) FILTER(WHERE fuel_level_pct>prev_fuel+.000001) AS fuel_increases,
              COUNT(DISTINCT date_key::VARCHAR || '/' || time_key::VARCHAR) AS unique_minutes
            FROM signals GROUP BY trip_id
          )
          SELECT COUNT(*) AS trips,
             MIN(n) AS min_points,MAX(n) AS max_points,
             ROUND(AVG(n),1) AS mean_points,
             COUNT(*) FILTER(WHERE speed_changes<=4) AS trips_speed_changes_lte4,
             COUNT(*) FILTER(WHERE speed_changes<=10) AS trips_speed_changes_lte10,
             COUNT(*) FILTER(WHERE n>=1000 AND speed_changes<=4) AS long_trips_speed_changes_lte4,
             COUNT(*) FILTER(WHERE fuel_delta_std<.001) AS trips_fuel_delta_std_lt001,
             COUNT(*) FILTER(WHERE fuel_increases=0) AS trips_without_fuel_increase,
             COUNT(*) FILTER(WHERE unique_minutes<n) AS trips_with_duplicate_minute,
             ROUND(AVG(speed_changes),2) AS mean_speed_changes,
             ROUND(AVG(fuel_delta_std),6) AS mean_fuel_delta_std
          FROM trip_stats
        """)[0]
        result["gps_signal"]["selected_trip_breakdown"]=query(con,"""
          WITH s AS (
            SELECT g.message_id,g.date_key,g.time_key,g.speed_kmh,
                   g.fuel_level_pct,g.engine_status,g.anomaly_type,
                   ROW_NUMBER() OVER (ORDER BY g.date_key,g.time_key,g.message_id) AS n,
                   LAG(g.speed_kmh) OVER
                     (ORDER BY g.date_key,g.time_key,g.message_id) AS prev_speed
            FROM dds.Fact_GPS_Points g
            WHERE trip_id='TRIP00078810'
          )
          SELECT n,date_key,time_key,ROUND(prev_speed,3) AS previous_speed,
                 ROUND(speed_kmh,3) AS current_speed,
                 ROUND(fuel_level_pct,4) AS fuel_pct,
                 engine_status,anomaly_type
          FROM s WHERE prev_speed IS NOT NULL AND ABS(speed_kmh-prev_speed)>.01
          ORDER BY n
        """)
        result["gps_signal"]["idle_alert_intervals"]=query(con,"""
          SELECT g.trip_id,COUNT(*) AS label_points,COUNT(DISTINCT g.time_key) AS distinct_time_keys,
                 MIN(d.full_date) AS first_date,MAX(d.full_date) AS last_date,
                 MIN(tm.hour_24*60+tm.minute) AS earliest_minute_of_day,
                 MAX(tm.hour_24*60+tm.minute) AS latest_minute_of_day
          FROM dds.Fact_GPS_Points g
          JOIN dds.Dim_Date d ON g.date_key=d.date_key
          JOIN dds.Dim_Time tm ON g.time_key=tm.time_key
          WHERE anomaly_type='IDLE_EXTENDED'
          GROUP BY 1 ORDER BY label_points DESC,trip_id
        """)
        result["limitations"]=[
            "Cannot determine whether mismatch vehicles are deliberate anomaly injection, erroneous purchase records or ETL mapping without source transactions and ETL notebooks.",
            "A near-linear sensor series does not prove that the physical sensor output was generated by interpolation; upstream provenance is required.",
            "The per-minute timestamp resolution prevents exact stop duration and event chronology within each minute.",
            "Do not automatically reassign purchases, delete rows, smooth signals or relabel anomalies."
        ]
    finally:con.close()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(encode(result),indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps(encode(result),indent=2,ensure_ascii=False))

if __name__=="__main__": main()
