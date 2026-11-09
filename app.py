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
:root { color-scheme:light; --ink:#172E40; --muted:#607586; --surface:#fff; --line:#e2eaf0; --teal:#176F76; }
html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"] {
  background:#F4F7FA!important; color:#172E40!important; color-scheme:light;
  font-family: "Inter", "Segoe UI", Arial, sans-serif;
}
[data-testid="stHeader"] { background:transparent!important; }
[data-testid="stToolbar"] { visibility:hidden; }
.block-container { max-width:1510px; padding:1.1rem 3rem 3.1rem; }
[data-testid="stSidebar"] { background:#F4F7FA!important; }
[data-testid="stMain"] p, [data-testid="stMain"] label { color:#172E40; }
[data-baseweb="select"]>div, [data-baseweb="input"]>div,
[data-testid="stDateInput"] input {
 background:white!important; color:#172E40!important; border-color:#D9E4EA!important; border-radius:9px!important;
}
[data-testid="stExpander"] {
 background:#fff!important; border:1px solid #E2EAF0!important; border-radius:12px!important;
}
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary * {color:#254457!important;}
div[data-testid="stVerticalBlockBorderWrapper"] > div { background:#fff!important; border:1px solid #e2eaf0!important; border-radius:16px!important; }
[data-testid="stCaptionContainer"] {color:#607586!important;}
.dashboard-top {
 display:flex; align-items:center; justify-content:space-between;
 padding:1rem 1.3rem; background:#102D40; border-radius:14px;
 color:#fff; margin-bottom:1.55rem;
}
.brand {display:flex; align-items:center; gap:.72rem; font-size:1.04rem; font-weight:760; letter-spacing:-.025em; color:#fff;}
.brand-mark {display:flex; align-items:center; justify-content:center; width:37px;height:37px; border-radius:10px;background:#2B6770;color:#fff;}
.brand-mark svg {width:23px;height:23px;stroke:currentColor;stroke-width:1.8;fill:none;stroke-linecap:round;stroke-linejoin:round;}
.brand-sub {font-weight:450;color:#B7D1D5}
.top-right {color:#B9D1D7;font-size:.76rem;letter-spacing:.1em;font-weight:650}
.page-heading {display:flex; align-items:end;justify-content:space-between;gap:1rem;margin:0 0 1.1rem}
.page-eyebrow {font-size:.75rem;font-weight:780;color:#21767C;letter-spacing:.12em;margin-bottom:.26rem}
.page-title {color:#172E40;font-size:1.85rem;font-weight:780;letter-spacing:-.045em;line-height:1.25}
.page-description {color:#6A7C8C;font-size:.84rem;margin-top:.35rem}
.period-tag {background:#E4EFF0;color:#28666B;padding:.52rem .78rem;border-radius:99px;font-size:.74rem;font-weight:700;white-space:nowrap}
.filter-head {display:flex;align-items:center;gap:.6rem;color:#304F60;font-size:.82rem;font-weight:730;margin:.2rem 0 .8rem}
.filter-head svg,.section-icon svg {width:17px;height:17px;stroke:currentColor;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.filter-label {color:#647989;font-size:.72rem;letter-spacing:.055em;text-transform:uppercase;font-weight:720;margin:0 0 .34rem}
.section-heading {display:flex;align-items:center;justify-content:space-between;margin:1.35rem 0 .72rem}
.section-heading .section-left {display:flex;align-items:center;gap:.55rem;color:#19384A;font-size:1.03rem;font-weight:760}
.section-icon {display:flex;align-items:center;justify-content:center;background:#E5EFF1;color:#26727B;border-radius:8px;width:30px;height:30px}
.section-hint {color:#8496A3;font-size:.74rem}
.kpi-card {
 background:white;border:1px solid #e2eaf0;border-radius:16px;padding:1.1rem 1.15rem 1.05rem;
 min-height:156px; box-shadow:0 5px 19px rgba(30,65,90,.035);
 position:relative;overflow:hidden
}
.kpi-card:before {content:"";position:absolute;left:0;top:0;height:100%;width:3px;background:var(--accent)}
.kpi-head {display:flex;justify-content:space-between;align-items:center;gap:.4rem}
.kpi-label {color:#667B8C;font-weight:650;font-size:.8rem}
.kpi-icon {display:flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:9px;background:var(--tint);color:var(--accent)}
.kpi-icon svg {width:19px;height:19px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.kpi-value {color:#172F40;font-weight:790;font-size:clamp(1.3rem,2.1vw,2rem);letter-spacing:-.055em;margin:.62rem 0 .26rem;white-space:nowrap}
.kpi-foot {color:#8999A7;font-size:.735rem;line-height:1.45}
.chart-title {color:#1D394A;font-size:.94rem;font-weight:730}
.chart-subtitle {color:#8495A1;font-size:.76rem;margin:.22rem 0 .5rem}
.data-note {background:#EEF5F5;border-left:3px solid #3E9694;border-radius:0 10px 10px 0;padding:.75rem .95rem;color:#456775;font-size:.77rem;line-height:1.65;margin:1rem 0}
.footer-line {color:#95A5B0;font-size:.72rem;text-align:center;padding:1.2rem 0 .2rem}
@media(max-width:820px) {
 .block-container {padding:1rem 1.1rem 2rem}
 .page-title{font-size:1.52rem}
 .top-right,.period-tag,.section-hint{display:none}
 .kpi-card{min-height:135px;padding:.95rem}
 .kpi-value{font-size:1.5rem}
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
<div class="dashboard-top">
  <div class="brand">
    <span class="brand-mark"><svg viewBox="0 0 24 24"><path d="M3 7h11v10H3zM14 10h4l3 3v4h-7z"/><circle cx="7.5" cy="18" r="1.8"/><circle cx="17.5" cy="18" r="1.8"/><path d="M6 7V5h5"/></svg></span>
    <span>FLEET <span class="brand-sub">/ INTELLIGENCE</span></span>
  </div>
  <div class="top-right">OPERATIONS ANALYTICS &nbsp; / &nbsp; 01</div>
</div>
<div class="page-heading">
  <div><div class="page-eyebrow">FLEET OPERATIONS</div>
  <div class="page-title">Tổng quan vận hành</div>
  <div class="page-description">Hiệu suất chuyến đi, tỷ lệ trễ và chi phí nhiên liệu trên dữ liệu DDS.</div></div>
  <span class="period-tag">DỮ LIỆU THỰC TẾ · 2022–2024</span>
</div>
<div class="filter-head"><svg viewBox="0 0 24 24"><path d="M4 6h16M7 12h10M10 18h4"/></svg>Bộ lọc dữ liệu</div>
""", unsafe_allow_html=True)

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
        "Chi nhánh / cơ sở xuất phát",
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

ICONS = {
    "route": '<path d="M5 5h.01M19 19h.01"/><circle cx="5" cy="5" r="2"/><circle cx="19" cy="19" r="2"/><path d="M7 5h8a4 4 0 0 1 0 8H9a4 4 0 0 0 0 8h8"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l4 2"/>',
    "fuel": '<path d="M4 21V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v16M3 21h14M7 7h6v5H7z"/><path d="M16 9h2l3 4v5a2 2 0 0 1-4 0v-3"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
    "chart": '<path d="M4 19V5M4 19h16M8 15l4-5 4 3 4-7"/>',
}

def section(title, icon="chart", hint=""):
    st.markdown(
        '<div class="section-heading"><div class="section-left">'
        '<span class="section-icon"><svg viewBox="0 0 24 24">' + ICONS[icon] + '</svg></span>'
        + title + '</div><span class="section-hint">' + hint + '</span></div>',
        unsafe_allow_html=True,
    )

def metric_card(label, value, detail, icon, accent, tint):
    st.markdown(
        f'<div class="kpi-card" style="--accent:{accent};--tint:{tint}">'
        f'<div class="kpi-head"><span class="kpi-label">{label}</span>'
        f'<span class="kpi-icon"><svg viewBox="0 0 24 24">{ICONS[icon]}</svg></span></div>'
        f'<div class="kpi-value">{value}</div><div class="kpi-foot">{detail}</div></div>',
        unsafe_allow_html=True,
    )

section("Chỉ số cốt lõi", hint="TỔNG HỢP THEO BỘ LỌC ĐANG CHỌN")
cards = st.columns(4, gap="medium")
with cards[0]:
    metric_card("Tổng chuyến đi", f"{total:,}", "Tổng số chuyến đã ghi nhận", "route", "#347F96", "#E6F3F6")
with cards[1]:
    metric_card("Tỷ lệ giao trễ", f"{late_pct:.2f}%" if late_pct is not None else "N/A",
                f"{late:,} chuyến trễ / {eligible:,} chuyến hợp lệ", "clock", "#BE8056", "#FBF1E8")
with cards[2]:
    metric_card("Chi phí nhiên liệu", f"${fuel:,.2f}", "USD · Chi phí mua theo chuyến", "fuel", "#308D80", "#E3F3EF")
with cards[3]:
    metric_card("Chuyến hợp lệ KPI", f"{eligible:,}", "Mẫu số của tỷ lệ giao trễ", "check", "#637EA3", "#EDF1F7")

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
left, right = st.columns(2, gap="medium")
with left:
    with st.container(border=True):
        st.markdown('<div class="chart-title">Số chuyến theo tháng</div><div class="chart-subtitle">Phân bố tổng chuyến theo thời điểm khởi hành</div>', unsafe_allow_html=True)
        st.altair_chart(trips_chart.properties(height=280), use_container_width=True, theme=None)
with right:
    with st.container(border=True):
        st.markdown('<div class="chart-title">Tỷ lệ giao hàng trễ</div><div class="chart-subtitle">Tỷ lệ trên các chuyến đủ điều kiện KPI</div>', unsafe_allow_html=True)
        st.altair_chart(late_chart.properties(height=280), use_container_width=True, theme=None)

with st.container(border=True):
    st.markdown('<div class="chart-title">Chi phí mua nhiên liệu theo tháng</div><div class="chart-subtitle">Gắn chi phí mua nhiên liệu với ngày bắt đầu của chuyến liên kết</div>', unsafe_allow_html=True)
    st.altair_chart(fuel_chart.properties(height=250), use_container_width=True, theme=None)

st.markdown(
    '<div class="data-note"><b>Quy ước dữ liệu:</b> Lọc theo ngày bắt đầu chuyến; '
    'giao trễ khi chuyến đủ điều kiện và delay_minutes &gt; 0. '
    'Chi phí nhiên liệu tính từ giao dịch mua liên kết với chuyến, '
    'không theo ngày mua nhiên liệu. Không sử dụng số liệu minh họa.</div>',
    unsafe_allow_html=True,
)

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
        "fuel_cost_usd": "Chi phí nhiên liệu (USD)",
    })
    st.dataframe(display, use_container_width=True, hide_index=True)

st.markdown('<div class="footer-line">FLEET BI &nbsp; · &nbsp; OPERATIONS OVERVIEW &nbsp; · &nbsp; DDS WAREHOUSE</div>', unsafe_allow_html=True)
