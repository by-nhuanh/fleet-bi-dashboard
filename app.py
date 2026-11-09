from pathlib import Path
import duckdb
import pandas as pd
import altair as alt
import streamlit as st
from ui import setup, page_header, filter_title, section, metric_card, note

st.set_page_config(
    page_title="Fleet BI | Fleet Operations",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = Path(__file__).resolve().parent / "database" / "fleet_dw.duckdb"
if not DB_PATH.is_file():
    st.error(f"Không tìm thấy dữ liệu: {DB_PATH}")
    st.stop()

setup(10)



@st.cache_resource
def connect_db():
    return duckdb.connect(str(DB_PATH), read_only=True)

con = connect_db()

@st.cache_data
def get_filter_data():
    bounds = con.execute("""
        SELECT MIN(d.full_date), MAX(d.full_date)
        FROM dds.Fact_Trips t
        JOIN dds.Dim_Date d ON t.start_date_key = d.date_key
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
if bounds[0] is None or bounds[1] is None:
    st.warning("Không có chuyến đi trong dữ liệu.")
    st.stop()

page_header(10, "Tổng quan vận hành",
    "Theo dõi số chuyến, tỷ lệ giao hàng trễ và chi phí mua nhiên liệu theo phạm vi đã chọn.")
filter_title()

facility_types = sorted(locations["facility_type"].dropna().unique().tolist())
location_options = {
    f"{r.facility_name} [{r.location_key}]": int(r.location_key)
    for r in locations.itertuples()
}

filter_cols = st.columns([1.45, 1.45, 1], gap="medium")
with filter_cols[0]:
    st.markdown('<div class="filter-label">Khoảng ngày bắt đầu chuyến</div>', unsafe_allow_html=True)
    date_range = st.date_input(
        "Khoảng ngày bắt đầu chuyến",
        value=(bounds[0], bounds[1]),
        min_value=bounds[0],
        max_value=bounds[1],
        label_visibility="collapsed",
    )
with filter_cols[1]:
    st.markdown('<div class="filter-label">Chi nhánh / cơ sở xuất phát</div>', unsafe_allow_html=True)
    origin_labels = st.multiselect(
        "Cơ sở xuất phát",
        list(location_options),
        placeholder="Tất cả cơ sở",
        label_visibility="collapsed",
    )
with filter_cols[2]:
    st.markdown('<div class="filter-label">Phương tiện</div>', unsafe_allow_html=True)
    vehicle_ids = st.multiselect(
        "Phương tiện",
        vehicles,
        placeholder="Tất cả phương tiện",
        label_visibility="collapsed",
    )

with st.expander("Bộ lọc nâng cao · Loại cơ sở và địa điểm đến", expanded=False):
    loc_left, loc_right = st.columns(2)
    with loc_left:
        selected_types = st.multiselect(
            "Loại cơ sở xuất phát",
            facility_types,
            placeholder="Tất cả loại cơ sở",
        )
    with loc_right:
        destination_labels = st.multiselect(
            "Địa điểm đến",
            list(location_options),
            placeholder="Tất cả điểm đến",
        )

st.caption("Quy ước bộ lọc: cơ sở xuất phát được dùng để phân nhóm như chi nhánh vận hành; dữ liệu nguồn chưa có trường chi nhánh độc lập.")

if len(date_range) != 2:
    st.info("Chọn đủ ngày bắt đầu và ngày kết thúc để xem Dashboard.")
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

try:
    kpi = con.execute(kpi_sql, params).df().iloc[0]
    monthly = con.execute(monthly_sql, params).df()
except Exception as exc:
    st.error("Không thể truy vấn kho dữ liệu DDS.")
    st.exception(exc)
    st.stop()

total = int(kpi["total_trips"])
eligible = int(kpi["eligible_trips"])
late = int(kpi["late_trips"])
fuel = float(kpi["fuel_cost_usd"])
late_pct = 100 * late / eligible if eligible else None

section("Chỉ số vận hành", "TỔNG HỢP THEO BỘ LỌC")
cards = st.columns(4, gap="large")
with cards[0]:
    metric_card("Tổng số chuyến", f"{total:,}",
                "Số chuyến thuộc phạm vi đang chọn", "truck", "#287CF0", "#E7F1FF")
with cards[1]:
    metric_card("Tỷ lệ giao hàng trễ",
                f"{late_pct:.2f}%" if late_pct is not None else "N/A",
                f"{late:,} chuyến trễ / {eligible:,} chuyến đủ điều kiện",
                "alert", "#C87C56", "#FCEDF0")
with cards[2]:
    metric_card("Chi phí mua nhiên liệu", f"${fuel:,.2f}",
                "USD · Theo chuyến liên kết", "fuel", "#23936F", "#E5F7EE")
with cards[3]:
    metric_card("Chuyến đủ điều kiện đánh giá", f"{eligible:,}",
                "Số chuyến được tính trong tỷ lệ giao trễ", "check", "#7467B6", "#F0EDFB")

if monthly.empty:
    st.warning("Không có chuyến nào phù hợp bộ lọc hiện tại.")
    st.stop()

monthly["period"] = pd.to_datetime(
    monthly["year"].astype(str) + "-" + monthly["month"].astype(str) + "-01"
)
monthly["late_rate_pct"] = (
    100 * monthly["late_trips"] / monthly["eligible_trips"].replace(0, float("nan"))
)

base = alt.Chart(monthly).encode(
    x=alt.X("period:T", title="Tháng", axis=alt.Axis(format="%m/%Y", labelAngle=-35))
)
trips_chart = base.mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color="#628eae").encode(
    y=alt.Y("total_trips:Q", title="Số chuyến"),
    tooltip=[
        alt.Tooltip("period:T", title="Tháng", format="%m/%Y"),
        alt.Tooltip("total_trips:Q", title="Số chuyến", format=","),
    ],
)
late_chart = base.mark_line(
    color="#dc996d", strokeWidth=3, point=alt.OverlayMarkDef(size=45, filled=True)
).encode(
    y=alt.Y("late_rate_pct:Q", title="Tỷ lệ (%)", scale=alt.Scale(zero=False)),
    tooltip=[
        alt.Tooltip("period:T", title="Tháng", format="%m/%Y"),
        alt.Tooltip("late_rate_pct:Q", title="Tỷ lệ trễ", format=".2f"),
    ],
)
fuel_chart = base.mark_area(
    line={"color": "#549d90", "strokeWidth": 2.5},
    color=alt.Gradient(
        gradient="linear",
        stops=[alt.GradientStop(color="#549d90", offset=0), alt.GradientStop(color="#e9f4ef", offset=1)],
        x1=1, x2=1, y1=0, y2=1,
    ),
).encode(
    y=alt.Y("fuel_cost_usd:Q", title="Chi phí (USD)"),
    tooltip=[
        alt.Tooltip("period:T", title="Tháng", format="%m/%Y"),
        alt.Tooltip("fuel_cost_usd:Q", title="Chi phí (USD)", format=",.2f"),
    ],
)


# Explicit chart colors prevent black chart canvases in dark OS/browser mode.
def make_chart_light(chart):
    return (
        chart.configure(
            background="#ffffff",
            padding={"left": 8, "right": 12, "top": 12, "bottom": 12},
        )
        .configure_view(stroke=None, fill="#ffffff")
        .configure_axis(
            labelColor="#344b60",
            titleColor="#344b60",
            domainColor="#becdd5",
            tickColor="#becdd5",
            gridColor="#e9eff1",
            labelFontSize=11,
            titleFontSize=12,
        )
        .configure_legend(labelColor="#344b60", titleColor="#344b60")
        .configure_title(color="#203a51")
    )

trips_chart = make_chart_light(trips_chart)
late_chart = make_chart_light(late_chart)
fuel_chart = make_chart_light(fuel_chart)

section("Xu hướng vận hành", hint="THỐNG KÊ THEO THÁNG")
left, right = st.columns(2, gap="large")
with left:
    with st.container(border=True):
        st.markdown('<div class="chart-heading">Số chuyến theo tháng</div><div class="chart-subtitle">Phân bố tổng chuyến theo thời điểm khởi hành</div>', unsafe_allow_html=True)
        st.altair_chart(trips_chart.properties(height=280), use_container_width=True, theme=None)
with right:
    with st.container(border=True):
        st.markdown('<div class="chart-heading">Tỷ lệ giao hàng trễ</div><div class="chart-subtitle">Tỷ lệ trên các chuyến đủ điều kiện KPI</div>', unsafe_allow_html=True)
        st.altair_chart(late_chart.properties(height=280), use_container_width=True, theme=None)

with st.container(border=True):
    st.markdown('<div class="chart-heading">Chi phí mua nhiên liệu theo tháng</div><div class="chart-subtitle">Gắn chi phí mua nhiên liệu với ngày bắt đầu của chuyến liên kết</div>', unsafe_allow_html=True)
    st.altair_chart(fuel_chart.properties(height=250), use_container_width=True, theme=None)

note("Lọc theo ngày bắt đầu chuyến; giao trễ khi chuyến đủ điều kiện và delay_minutes > 0. Chi phí mua nhiên liệu được gắn theo chuyến liên kết, không theo ngày giao dịch mua.")

with st.expander("Bảng dữ liệu đối soát theo tháng"):
    display = monthly[[
        "period", "total_trips", "eligible_trips", "late_trips",
        "late_rate_pct", "fuel_cost_usd",
    ]].rename(columns={
        "period": "Tháng",
        "total_trips": "Tổng chuyến",
        "eligible_trips": "Đủ điều kiện",
        "late_trips": "Chuyến trễ",
        "late_rate_pct": "Tỷ lệ trễ (%)",
        "fuel_cost_usd": "Chi phí mua nhiên liệu (USD)",
    })
    st.dataframe(display, use_container_width=True, hide_index=True)


