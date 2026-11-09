from pathlib import Path
import duckdb
import pandas as pd
import altair as alt
import streamlit as st

st.set_page_config(
    page_title="Fleet BI | Fleet Operations",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DB_PATH = Path(__file__).resolve().parent / "database" / "fleet_dw.duckdb"
if not DB_PATH.is_file():
    st.error(f"Không tìm thấy dữ liệu: {DB_PATH}")
    st.stop()

st.markdown("""
<style>
:root {
    --navy: #203a51;
    --ink: #213449;
    --muted: #708293;
    --sage: #549d90;
    --blue: #628eae;
    --line: #e4ecef;
}
html, body, [data-testid="stApp"] {
    font-family: "Inter", "Segoe UI", sans-serif;
}
[data-testid="stAppViewContainer"] {
    background: #f3f7f7;
}
[data-testid="stHeader"] {
    background: transparent;
}
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 3.3rem;
    max-width: 1540px;
}
section[data-testid="stSidebar"] {
    background: #f7faf9;
}
.hero {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 1.1rem 1.6rem;
    border-radius: 18px;
    background: linear-gradient(110deg, #203b53 0%, #2e606d 100%);
    color: white;
    box-shadow: 0 12px 28px rgba(22, 55, 68, .12);
    margin-bottom: 1.35rem;
}
.hero-brand {
    font-size: 1.45rem;
    font-weight: 760;
    letter-spacing: -.025em;
}
.hero-note {
    font-size: .86rem;
    color: #d9e6e8;
}
.title-line {
    font-size: 2.05rem;
    letter-spacing: -.045em;
    font-weight: 780;
    color: var(--ink);
    margin: .1rem 0 .2rem;
    line-height: 1.2;
}
.subtitle {
    color: var(--muted);
    margin-bottom: 1rem;
    font-size: .91rem;
}
.filter-label {
    font-size: .77rem;
    color: #667c87;
    font-weight: 700;
    letter-spacing: .055em;
    text-transform: uppercase;
    margin: .2rem 0 .25rem;
}
[data-testid="stDateInput"], [data-testid="stMultiSelect"] {
    margin-bottom: .15rem;
}
div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
    border-radius: 11px;
}
.metric-tile {
    min-height: 175px;
    padding: 1.2rem 1.28rem 1.05rem;
    background: white;
    border: 1px solid var(--line);
    border-radius: 17px;
    box-shadow: 0 7px 22px rgba(28, 63, 76, .055);
    overflow: hidden;
}
.metric-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: .4rem;
}
.metric-label {
    font-size: .91rem;
    font-weight: 650;
    color: #50687a;
}
.metric-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 42px;
    height: 42px;
    border-radius: 13px;
    background: #edf6f4;
    font-size: 1.35rem;
}
.metric-value {
    color: #1c3448;
    font-size: clamp(1.45rem, 2.45vw, 2.25rem);
    font-weight: 785;
    letter-spacing: -.045em;
    margin: .65rem 0 .25rem;
    white-space: nowrap;
}
.metric-hint {
    font-size: .78rem;
    color: #7d8d9b;
    line-height: 1.35;
}
.section-title {
    margin: 1.5rem 0 .65rem;
    font-size: 1.22rem;
    font-weight: 750;
    letter-spacing: -.02em;
    color: var(--ink);
}
.chart-heading {
    color: #293f52;
    font-weight: 710;
    font-size: 1rem;
    padding: .15rem 0 .25rem;
}
.chart-sub {
    color: #84929b;
    font-size: .8rem;
    margin-bottom: .5rem;
}
.note {
    margin-top: 1rem;
    border-left: 3px solid #7aaca3;
    padding: .7rem 1rem;
    color: #637b86;
    font-size: .82rem;
    background: #eaf3f1;
    border-radius: 0 10px 10px 0;
}
div[data-testid="stVerticalBlockBorderWrapper"] > div {
    border-radius: 17px !important;
    border-color: var(--line) !important;
    background: #fff;
}
[data-testid="stExpander"] {
    border-radius: 12px;
    background: white;
}
@media (max-width: 750px) {
    .hero { padding: .9rem 1rem; }
    .hero-brand { font-size: 1.15rem; }
    .hero-note { font-size: .72rem; }
    .title-line { font-size: 1.65rem; }
    .metric-tile { min-height: 155px; }
}
</style>
""", unsafe_allow_html=True)

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

st.markdown("""
<div class="hero">
  <div class="hero-brand">🚚 &nbsp; Fleet BI <span style="font-weight:400;opacity:.7">/ Operations</span></div>
  <div class="hero-note">FLEET INTELLIGENCE &nbsp; • &nbsp; OVERVIEW</div>
</div>
<div class="title-line">Tổng quan vận hành</div>
<div class="subtitle">Theo dõi chuyến đi, giao hàng trễ và chi phí mua nhiên liệu từ kho dữ liệu DDS.</div>
""", unsafe_allow_html=True)

facility_types = sorted(locations["facility_type"].dropna().unique().tolist())
location_options = {
    f"{r.facility_name} [{r.location_key}]": int(r.location_key)
    for r in locations.itertuples()
}

filter_cols = st.columns([1.45, 1, 1.1], gap="medium")
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
    st.markdown('<div class="filter-label">Loại cơ sở xuất phát</div>', unsafe_allow_html=True)
    selected_types = st.multiselect(
        "Loại cơ sở xuất phát",
        facility_types,
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

with st.expander("⚙️  Bộ lọc nâng cao · Địa điểm xuất phát và điểm đến", expanded=False):
    loc_left, loc_right = st.columns(2)
    with loc_left:
        origin_labels = st.multiselect(
            "Địa điểm xuất phát",
            list(location_options),
            placeholder="Tất cả điểm xuất phát",
        )
    with loc_right:
        destination_labels = st.multiselect(
            "Địa điểm đến",
            list(location_options),
            placeholder="Tất cả điểm đến",
        )

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

def metric_card(label, value, detail, emoji, accent):
    st.markdown(
        f'<div class="metric-tile" style="border-top:3px solid {accent}">'
        f'<div class="metric-top"><span class="metric-label">{label}</span>'
        f'<span class="metric-icon">{emoji}</span></div>'
        f'<div class="metric-value">{value}</div>'
        f'<div class="metric-hint">{detail}</div></div>',
        unsafe_allow_html=True,
    )

st.markdown('<div class="section-title">Chỉ số vận hành</div>', unsafe_allow_html=True)
cards = st.columns(4, gap="medium")
with cards[0]:
    metric_card("Tổng số chuyến", f"{total:,}", "Chuyến theo bộ lọc hiện tại", "🚚", "#6e9fbe")
with cards[1]:
    metric_card(
        "Tỷ lệ giao hàng trễ",
        f"{late_pct:.2f}%" if late_pct is not None else "N/A",
        f"{late:,} chuyến trễ / {eligible:,} chuyến đủ điều kiện",
        "⏱️", "#e4ae76",
    )
with cards[2]:
    metric_card("Chi phí mua nhiên liệu", f"${fuel:,.2f}", "USD · Theo chuyến liên kết", "⛽", "#70b5a1")
with cards[3]:
    metric_card("Chuyến đủ điều kiện KPI", f"{eligible:,}", "Mẫu số tính tỷ lệ giao hàng trễ", "✓", "#9eabc2")

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

st.markdown('<div class="section-title">Phân tích xu hướng</div>', unsafe_allow_html=True)
left, right = st.columns(2, gap="medium")
with left:
    with st.container(border=True):
        st.markdown('<div class="chart-heading">Số chuyến theo tháng</div><div class="chart-sub">Phân bố tổng chuyến theo thời điểm khởi hành</div>', unsafe_allow_html=True)
        st.altair_chart(trips_chart.properties(height=280), use_container_width=True)
with right:
    with st.container(border=True):
        st.markdown('<div class="chart-heading">Tỷ lệ giao hàng trễ</div><div class="chart-sub">Tỷ lệ trên các chuyến đủ điều kiện KPI</div>', unsafe_allow_html=True)
        st.altair_chart(late_chart.properties(height=280), use_container_width=True)

with st.container(border=True):
    st.markdown('<div class="chart-heading">Chi phí mua nhiên liệu theo tháng</div><div class="chart-sub">Gắn chi phí mua nhiên liệu với ngày bắt đầu của chuyến liên kết</div>', unsafe_allow_html=True)
    st.altair_chart(fuel_chart.properties(height=250), use_container_width=True)

st.markdown(
    '<div class="note"><b>Quy ước dữ liệu:</b> Lọc theo ngày bắt đầu chuyến; '
    'giao trễ khi chuyến đủ điều kiện và delay_minutes &gt; 0. '
    'Chi phí nhiên liệu tính từ giao dịch mua liên kết với chuyến, '
    'không theo ngày mua nhiên liệu. Không sử dụng số liệu minh họa.</div>',
    unsafe_allow_html=True,
)

with st.expander("📋  Bảng dữ liệu đối soát theo tháng"):
    display = monthly[[
        "period", "total_trips", "eligible_trips", "late_trips",
        "late_rate_pct", "fuel_cost_usd",
    ]].rename(columns={
        "period": "Tháng",
        "total_trips": "Tổng chuyến",
        "eligible_trips": "Đủ điều kiện",
        "late_trips": "Chuyến trễ",
        "late_rate_pct": "Tỷ lệ trễ (%)",
        "fuel_cost_usd": "Chi phí nhiên liệu (USD)",
    })
    st.dataframe(display, use_container_width=True, hide_index=True)
