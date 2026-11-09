from pathlib import Path
import duckdb
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Fleet BI | Overview",
    page_icon="🚚",
    layout="wide"
)

DB_PATH = Path(__file__).resolve().parent / "database" / "fleet_dw.duckdb"

if not DB_PATH.is_file():
    st.error(f"Không tìm thấy DuckDB: {DB_PATH}")
    st.stop()

@st.cache_resource
def connect_db():
    return duckdb.connect(str(DB_PATH), read_only=True)

con = connect_db()

st.title("🚚 Fleet Operations Overview")
st.caption("Nguồn: DDS DuckDB | Task 10")

@st.cache_data
def get_filter_data():
    bounds = con.execute("""
        SELECT MIN(d.full_date), MAX(d.full_date)
        FROM dds.Fact_Trips t
        JOIN dds.Dim_Date d
          ON t.start_date_key = d.date_key
    """).fetchone()

    vehicles = con.execute("""
        SELECT DISTINCT truck_id
        FROM dds.Dim_Vehicle
        WHERE truck_id IS NOT NULL
        ORDER BY truck_id
    """).df()["truck_id"].tolist()

    locations = con.execute("""
        SELECT location_key, facility_name, facility_type
        FROM dds.Dim_Location
        WHERE facility_type <> 'Unknown'
        ORDER BY facility_name, location_key
    """).df()

    return bounds, vehicles, locations

bounds, vehicles, locations = get_filter_data()

st.sidebar.header("Bộ lọc")

date_range = st.sidebar.date_input(
    "Ngày bắt đầu chuyến",
    value=(bounds[0], bounds[1]),
    min_value=bounds[0],
    max_value=bounds[1]
)

vehicle_ids = st.sidebar.multiselect("Phương tiện", vehicles)
facility_types = sorted(locations["facility_type"].dropna().unique().tolist())
selected_types = st.sidebar.multiselect("Loại cơ sở xuất phát", facility_types)

location_options = {
    f"{r.facility_name} [{r.location_key}]": int(r.location_key)
    for r in locations.itertuples()
}

origin_labels = st.sidebar.multiselect("Địa điểm xuất phát", list(location_options))
destination_labels = st.sidebar.multiselect("Địa điểm đến", list(location_options))

if len(date_range) != 2:
    st.info("Chọn đủ ngày bắt đầu và ngày kết thúc.")
    st.stop()

conditions = ["d.full_date BETWEEN ? AND ?"]
params = [date_range[0], date_range[1]]

def add_in_filter(column, values):
    if values:
        conditions.append(column + " IN (" + ",".join(["?"] * len(values)) + ")")
        params.extend(values)

add_in_filter("v.truck_id", vehicle_ids)
add_in_filter("origin.facility_type", selected_types)
add_in_filter("t.origin_location_key", [location_options[x] for x in origin_labels])
add_in_filter("t.dest_location_key", [location_options[x] for x in destination_labels])

where_clause = " AND ".join(conditions)

cte = f"""
WITH filtered_trips AS (
    SELECT t.trip_id, t.is_kpi_eligible, t.delay_minutes, d.year, d.month
    FROM dds.Fact_Trips t
    JOIN dds.Dim_Date d ON t.start_date_key = d.date_key
    JOIN dds.Dim_Vehicle v ON t.vehicle_key = v.vehicle_key
    JOIN dds.Dim_Location origin ON t.origin_location_key = origin.location_key
    WHERE {where_clause}
),
fuel_by_trip AS (
    SELECT f.trip_id, SUM(f.total_cost_usd) AS fuel_cost
    FROM dds.Fact_Fuel_Purchases f
    JOIN filtered_trips t ON f.trip_id = t.trip_id
    GROUP BY f.trip_id
)
"""

kpi_sql = cte + """
SELECT
    COUNT(*) AS total_trips,
    COUNT(*) FILTER (WHERE is_kpi_eligible = 1) AS eligible_trips,
    COUNT(*) FILTER (WHERE is_kpi_eligible = 1 AND delay_minutes > 0) AS late_trips,
    (SELECT COALESCE(SUM(fuel_cost), 0) FROM fuel_by_trip) AS fuel_cost_usd
FROM filtered_trips
"""

monthly_sql = cte + """
SELECT
    t.year, t.month,
    COUNT(*) AS total_trips,
    COUNT(*) FILTER (WHERE t.is_kpi_eligible = 1) AS eligible_trips,
    COUNT(*) FILTER (WHERE t.is_kpi_eligible = 1 AND t.delay_minutes > 0) AS late_trips,
    COALESCE(SUM(f.fuel_cost), 0) AS fuel_cost_usd
FROM filtered_trips t
LEFT JOIN fuel_by_trip f ON t.trip_id = f.trip_id
GROUP BY t.year, t.month
ORDER BY t.year, t.month
"""

kpi = con.execute(kpi_sql, params).df().iloc[0]
monthly = con.execute(monthly_sql, params).df()

total = int(kpi["total_trips"])
eligible = int(kpi["eligible_trips"])
late = int(kpi["late_trips"])
fuel = float(kpi["fuel_cost_usd"])
late_pct = 100 * late / eligible if eligible else None

c1, c2, c3 = st.columns(3)
c1.metric("Tổng chuyến", f"{total:,}")
c2.metric("Tỷ lệ giao hàng trễ", f"{late_pct:.2f}%" if late_pct is not None else "N/A")
c3.metric("Chi phí mua nhiên liệu", f"${fuel:,.2f}")
st.caption(f"Chuyến đủ điều kiện: {eligible:,} | Chuyến trễ: {late:,}")

if monthly.empty:
    st.warning("Không có dữ liệu phù hợp với bộ lọc.")
    st.stop()

monthly["period"] = pd.to_datetime(
    monthly["year"].astype(str) + "-" + monthly["month"].astype(str) + "-01"
)
monthly["late_rate_pct"] = (
    100 * monthly["late_trips"] / monthly["eligible_trips"].replace(0, float("nan"))
)

st.subheader("Xu hướng vận hành theo tháng")
left, right = st.columns(2)
with left:
    st.markdown("**Số chuyến**")
    st.bar_chart(monthly.set_index("period")["total_trips"])
with right:
    st.markdown("**Tỷ lệ giao hàng trễ (%)**")
    st.line_chart(monthly.set_index("period")["late_rate_pct"])

st.subheader("Chi phí mua nhiên liệu theo tháng")
st.bar_chart(monthly.set_index("period")["fuel_cost_usd"])
st.caption(
    "Bộ lọc thời gian theo ngày bắt đầu chuyến. "
    "Chi phí nhiên liệu được quy về chuyến liên kết, "
    "không phải ngày phát sinh giao dịch mua."
)
with st.expander("Dữ liệu đối soát"):
    st.dataframe(monthly, use_container_width=True)
