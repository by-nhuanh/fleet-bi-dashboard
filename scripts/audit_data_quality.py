"""Read-only DDS audit. Outputs aggregate observations, never alters the warehouse."""
import json
from pathlib import Path
from datetime import date, datetime
import duckdb

DB = Path(__file__).resolve().parents[1] / "database" / "fleet_analysis.duckdb"
OUT = Path(__file__).resolve().parents[1] / "audit" / "data_quality_report.json"

def rows(con, sql, args=None):
    cur=con.execute(sql, args or [])
    names=[d[0] for d in cur.description]
    return [dict(zip(names,r)) for r in cur.fetchall()]

def one(con,sql,args=None):
    return rows(con,sql,args)[0]

def safe(x):
    if isinstance(x,(date,datetime)):return x.isoformat()
    if isinstance(x,dict):return {str(k):safe(v) for k,v in x.items()}
    if isinstance(x,list):return [safe(v) for v in x]
    if isinstance(x,tuple):return [safe(v) for v in x]
    return x

def main():
    if not DB.exists():raise FileNotFoundError(DB)
    con=duckdb.connect(str(DB),read_only=True)
    result={"source":"database/fleet_analysis.duckdb",
            "scope":"All deployed DDS rows; observations are not corrections",
            "tables":{}, "tests":{}, "gps":{}, "fuel":{},
            "overview":{}, "trip_case":{}, "notes":[]}
    expected={"Fact_Trips":85410,"Fact_GPS_Points":1435571,
              "Fact_Fuel_Purchases":196442,"Dim_Date":2192,"Dim_Time":1441,
              "Dim_Route":59,"Dim_Location":51,"Dim_Vehicle":241}
    try:
        for table,expect in expected.items():
            r=one(con,f"SELECT COUNT(*) AS count FROM dds.{table}")
            result["tables"][table]={"actual":r["count"],"expected":expect,
                                      "pass":r["count"]==expect}
        result["overview"]=one(con,"""
          SELECT COUNT(*) AS trips,
          COUNT(*) FILTER(WHERE is_kpi_eligible=1) AS eligible,
          COUNT(*) FILTER(WHERE is_kpi_eligible=1 AND delay_minutes>0) AS late
          FROM dds.Fact_Trips
        """)
        result["fuel"]["purchases"]=one(con,"""
          SELECT COUNT(*) AS transactions,
          COUNT(DISTINCT fuel_purchase_id) AS distinct_ids,
          COUNT(*) FILTER(WHERE total_cost_usd<0 OR liters_purchased<0) AS negative_values,
          SUM(total_cost_usd) AS total_cost_usd
          FROM dds.Fact_Fuel_Purchases
        """)
        result["fuel"]["vehicle_reconciliation"]=one(con,"""
          SELECT COUNT(*) FILTER(WHERE f.vehicle_key <> t.vehicle_key) AS mismatch_rows,
                 SUM(CASE WHEN f.vehicle_key <> t.vehicle_key
                          THEN f.total_cost_usd ELSE 0 END) AS mismatch_cost_usd,
                 COUNT(*) FILTER(WHERE t.trip_id IS NULL) AS unmatched_trip_rows
          FROM dds.Fact_Fuel_Purchases f
          LEFT JOIN dds.Fact_Trips t ON f.trip_id=t.trip_id
        """)
        result["fuel"]["truck_id_reconciliation"]=one(con,"""
          SELECT COUNT(*) FILTER(WHERE pv.truck_id IS DISTINCT FROM tv.truck_id)
                    AS different_truck_ids,
                 COUNT(*) FILTER(WHERE f.vehicle_key IS DISTINCT FROM t.vehicle_key)
                    AS different_vehicle_version_keys
          FROM dds.Fact_Fuel_Purchases f
          JOIN dds.Fact_Trips t ON f.trip_id=t.trip_id
          LEFT JOIN dds.Dim_Vehicle pv ON f.vehicle_key=pv.vehicle_key
          LEFT JOIN dds.Dim_Vehicle tv ON t.vehicle_key=tv.vehicle_key
        """)
        result["gps"]["integrity"]=one(con,"""
          SELECT COUNT(*) AS gps_rows, COUNT(DISTINCT g.message_id) AS unique_message_ids,
             COUNT(DISTINCT g.trip_id) AS trips_with_gps,
             COUNT(*) FILTER(WHERE t.trip_id IS NULL) AS unmatched_trips,
             COUNT(*) FILTER(WHERE t.trip_id IS NOT NULL AND g.vehicle_key <> t.vehicle_key)
                AS vehicle_mismatches,
             COUNT(*) FILTER(WHERE g.speed_kmh < 0) AS negative_speed,
             COUNT(*) FILTER(WHERE g.fuel_level_pct NOT BETWEEN 0 AND 100)
                AS invalid_fuel_percent,
             COUNT(*) FILTER(WHERE g.latitude NOT BETWEEN -90 AND 90
               OR g.longitude NOT BETWEEN -180 AND 180
               OR g.latitude IS NULL OR g.longitude IS NULL) AS invalid_coordinates
          FROM dds.Fact_GPS_Points g LEFT JOIN dds.Fact_Trips t ON g.trip_id=t.trip_id
        """)
        result["gps"]["anomaly_distribution"]=rows(con,"""
          SELECT anomaly_type,COUNT(*) AS points,COUNT(DISTINCT trip_id) AS trips
          FROM dds.Fact_GPS_Points GROUP BY 1 ORDER BY 2 DESC
        """)
        result["gps"]["engine_distribution"]=rows(con,"""
          SELECT engine_status, COUNT(*) AS points
          FROM dds.Fact_GPS_Points GROUP BY 1 ORDER BY 2 DESC
        """)
        result["gps"]["clock_resolution"]=one(con,"""
          SELECT COUNT(*) AS rows,
                 COUNT(*) FILTER(WHERE tm.hour_24 IS NULL OR tm.minute IS NULL)
                    AS unresolved_time_keys,
                 COUNT(*) FILTER(WHERE tm.hour_24=0 AND tm.minute=0)
                    AS midnight_time_rows
          FROM dds.Fact_GPS_Points g
          LEFT JOIN dds.Dim_Time tm ON g.time_key=tm.time_key
        """)
        # Full GPS audit: repeated value and monotonically declining fuel by trip.
        result["gps"]["value_repetition"]=one(con,"""
          WITH signal AS (
            SELECT g.trip_id,g.message_id,g.speed_kmh,g.fuel_level_pct,
              LAG(g.speed_kmh) OVER (
                PARTITION BY g.trip_id
                ORDER BY g.date_key,g.time_key,g.message_id) AS previous_speed,
              LAG(g.fuel_level_pct) OVER (
                PARTITION BY g.trip_id
                ORDER BY g.date_key,g.time_key,g.message_id) AS previous_fuel
            FROM dds.Fact_GPS_Points g
          )
          SELECT COUNT(*) AS rows,
              COUNT(*) FILTER(WHERE previous_speed IS NOT NULL) AS transitions,
              COUNT(*) FILTER(WHERE speed_kmh=previous_speed) AS repeated_speed,
              COUNT(*) FILTER(WHERE speed_kmh BETWEEN 14.9 AND 15.1) AS around_15_kmh,
              COUNT(*) FILTER(WHERE previous_fuel IS NOT NULL) AS fuel_transitions,
              COUNT(*) FILTER(WHERE fuel_level_pct>previous_fuel+0.000001) AS fuel_increases,
              COUNT(*) FILTER(WHERE fuel_level_pct<previous_fuel-0.000001) AS fuel_decreases,
              COUNT(*) FILTER(WHERE ABS(fuel_level_pct-previous_fuel)<=0.000001) AS fuel_unchanged
          FROM signal
        """)
        # 1 trip referenced by the dashboard screenshots and existing report.
        trip="TRIP00078810"
        result["trip_case"]["trip_id"]=trip
        result["trip_case"]["signals"]=one(con,"""
          SELECT COUNT(*) AS gps_points, COUNT(DISTINCT speed_kmh) AS unique_speed_values,
                 COUNT(DISTINCT ROUND(fuel_level_pct,4)) AS unique_fuel_values,
                 MIN(speed_kmh) AS min_speed, MAX(speed_kmh) AS max_speed,
                 MIN(fuel_level_pct) AS min_fuel_pct,
                 MAX(fuel_level_pct) AS max_fuel_pct,
                 COUNT(*) FILTER(WHERE speed_kmh=15) AS exactly_15_kmh_points,
                 COUNT(*) FILTER(WHERE engine_status='Idling') AS idling_points,
                 COUNT(*) FILTER(WHERE anomaly_type='IDLE_EXTENDED') AS idle_alert_points,
                 COUNT(DISTINCT g.date_key::VARCHAR || '/' || g.time_key::VARCHAR)
                    AS distinct_date_minute_keys
          FROM dds.Fact_GPS_Points g WHERE trip_id=?
        """,[trip])
        result["trip_case"]["ordering_and_fuel"]=one(con,"""
          WITH v AS (
             SELECT fuel_level_pct,speed_kmh,engine_status,anomaly_type,date_key,time_key,
               ROW_NUMBER() OVER (ORDER BY date_key,time_key,message_id) AS seq,
               LAG(fuel_level_pct) OVER (ORDER BY date_key,time_key,message_id) AS prev_fuel,
               LAG(speed_kmh) OVER (ORDER BY date_key,time_key,message_id) AS prev_speed
             FROM dds.Fact_GPS_Points WHERE trip_id=?
          )
          SELECT COUNT(*) FILTER(WHERE prev_fuel IS NOT NULL) AS transitions,
                 MIN(fuel_level_pct-prev_fuel) AS min_fuel_change,
                 MAX(fuel_level_pct-prev_fuel) AS max_fuel_change,
                 AVG(fuel_level_pct-prev_fuel) AS mean_fuel_change,
                 STDDEV_POP(fuel_level_pct-prev_fuel) AS stddev_fuel_change,
                 COUNT(*) FILTER(WHERE ABS(speed_kmh-prev_speed)>.01) AS speed_changes,
                 COUNT(*) FILTER(WHERE fuel_level_pct>prev_fuel+.000001)
                    AS fuel_increases,
                 COUNT(*) FILTER(WHERE anomaly_type='IDLE_EXTENDED')
                    AS idle_alert_points
          FROM v
        """,[trip])
        result["trip_case"]["alert_span"]=rows(con,"""
          SELECT g.anomaly_type,
             COUNT(*) AS points,
             MIN(d.full_date) AS first_date,MAX(d.full_date) AS last_date,
             MIN(tm.hour_24*60+tm.minute) AS min_minute_in_day,
             MAX(tm.hour_24*60+tm.minute) AS max_minute_in_day,
             COUNT(DISTINCT g.date_key::VARCHAR || '/' || g.time_key::VARCHAR)
                 AS distinct_date_minute_keys
          FROM dds.Fact_GPS_Points g
          JOIN dds.Dim_Date d ON d.date_key=g.date_key
          JOIN dds.Dim_Time tm ON tm.time_key=g.time_key
          WHERE g.trip_id=? AND g.anomaly_type NOT IN ('NORMAL','NONE','')
          GROUP BY 1
        """,[trip])
        result["tests"]={
           "table_counts":all(v["pass"] for v in result["tables"].values()),
           "expected_kpis":result["overview"]=={"trips":85410,"eligible":77959,"late":51970},
           "gps_relationships":result["gps"]["integrity"]["unmatched_trips"]==0,
           "gps_unique_ids":result["gps"]["integrity"]["gps_rows"]==result["gps"]["integrity"]["unique_message_ids"],
           "fuel_relationships":result["fuel"]["vehicle_reconciliation"]["unmatched_trip_rows"]==0,
           "fuel_vehicle_consistency":result["fuel"]["truck_id_reconciliation"]["different_truck_ids"]==0
        }
        result["notes"]=[
            "Repeated GPS values are valid database values but cannot by themselves prove physical sensor accuracy.",
            "Datetime resolution is one minute; consecutive messages in the same minute must not be interpreted as one minute apart.",
            "Fuel purchase vehicle_key differences must be compared by Dim_Vehicle.truck_id before classifying a business vehicle mismatch.",
            "GPS labels are observations, not confirmed operational incidents.",
            "No synthetic signal smoothing, interpolation or automatic label correction is performed."
        ]
    finally:
        con.close()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(safe(result),ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(safe(result),ensure_ascii=False,indent=2))
    print("AUDIT PASS / REVIEW counts:",
          sum(bool(v) for v in result["tests"].values()),"/",len(result["tests"]))

if __name__=="__main__":
    main()
