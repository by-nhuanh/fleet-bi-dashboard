from pathlib import Path
import duckdb
import pandas as pd
import altair as alt
import streamlit as st
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ui import setup, page_header, filter_title, section, metric_card, metric_grid, note

st.set_page_config(page_title="Fleet BI | Fuel Diagnostics",page_icon="⛽",layout="wide",initial_sidebar_state="collapsed")
DB=Path(__file__).resolve().parents[1]/"database"/"fleet_analysis.duckdb"
if not DB.is_file():
    st.error("Chưa tìm thấy cơ sở dữ liệu cảm biến phục vụ phân tích nhiên liệu.")
    st.stop()

setup(12)

@st.cache_resource
def connect():
    return duckdb.connect(str(DB),read_only=True)
con=connect()

@st.cache_data(ttl=600)
def get_trip_options():
    return con.execute("""
        SELECT g.trip_id,
               COUNT(*) AS gps_points,
               COUNT(*) FILTER(
                   WHERE g.anomaly_type IS NOT NULL
                     AND TRIM(CAST(g.anomaly_type AS VARCHAR)) NOT IN ('','NORMAL','NONE')
               ) AS flagged_points
        FROM dds.Fact_GPS_Points g
        WHERE g.trip_id IS NOT NULL
        GROUP BY 1
        ORDER BY flagged_points DESC, gps_points DESC, g.trip_id
    """).df()

options=get_trip_options()
if options.empty:
    st.warning("Chưa có chuyến có dữ liệu GPS.")
    st.stop()

page_header(12, "Phân tích nhiên liệu",
    "Đối chiếu tín hiệu IoT mô phỏng và các tình huống bất thường được gắn nhãn.")
st.info(
    "Dữ liệu cảm biến ở trang này được **sinh mô phỏng**, "
    "với vận tốc tính từ tọa độ nội suy và nhiên liệu tiêu hao theo công thức. "
    "Nhãn bất thường là tình huống được chủ động tạo, không phải sự cố đã xảy ra thực tế."
)

@st.cache_data(ttl=600)
def fuel_consistency_summary():
    return con.execute("""
        SELECT
            COUNT(*) FILTER (WHERE f.vehicle_key IS DISTINCT FROM t.vehicle_key)
                AS surrogate_key_differences,
            COUNT(*) FILTER (WHERE pv.truck_id IS DISTINCT FROM tv.truck_id)
                AS different_truck_ids
        FROM dds.Fact_Fuel_Purchases f
        JOIN dds.Fact_Trips t ON f.trip_id=t.trip_id
        LEFT JOIN dds.Dim_Vehicle pv ON f.vehicle_key=pv.vehicle_key
        LEFT JOIN dds.Dim_Vehicle tv ON t.vehicle_key=tv.vehicle_key
    """).fetchone()

surrogate_differences,actual_vehicle_differences=fuel_consistency_summary()
if actual_vehicle_differences:
    st.warning(
        f"Đối soát phương tiện: {actual_vehicle_differences:,} giao dịch có "
        "mã xe truck_id khác với chuyến liên kết, cần xác minh nguồn."
    )
elif surrogate_differences:
    st.caption(
        f"Đối soát phương tiện: {surrogate_differences:,} giao dịch có "
        "vehicle_key khác giữa giao dịch và chuyến, nhưng truck_id vẫn khớp. "
        "Đây là khác khóa phiên bản trong chiều phương tiện, "
        "không được kết luận sai xe."
    )

section("Tổng quan dữ liệu cảm biến", "CHỈ SỐ TỪ CÁC CHUYẾN CÓ GPS")
metric_grid([
    metric_card("Chuyến có dữ liệu GPS", f"{len(options):,}",
                "Chuyến có bản ghi cảm biến", "truck", render=False),
    metric_card("Chuyến có cảnh báo cần xác minh",
                f"{(options.flagged_points>0).sum():,}",
                "Các chuyến có tín hiệu cần rà soát", "alert", render=False),
    metric_card("Điểm GPS mang nhãn cảnh báo",
                f"{options.flagged_points.sum():,}",
                "Số điểm có nhãn cần theo dõi", "location", render=False),
], columns=3)

@st.cache_data(ttl=600)
def get_labels():
    return con.execute("""
        SELECT COALESCE(CAST(anomaly_type AS VARCHAR),'(NULL)') AS anomaly_type,
               COUNT(*) AS point_count,
               COUNT(DISTINCT trip_id) AS trip_count
        FROM dds.Fact_GPS_Points
        GROUP BY 1
        ORDER BY point_count DESC
    """).df()

with st.expander("Phân bố nhãn bất thường gốc trong DDS",expanded=False):
    st.dataframe(get_labels(),hide_index=True,use_container_width=True)

# Expose the anomaly inventory as a real-data visual, not inferred diagnoses.
recorded_labels = get_labels()
alert_labels = recorded_labels[
    ~recorded_labels["anomaly_type"].isin(["NORMAL", "NONE", "", "(NULL)"])
].copy()
if not alert_labels.empty:
    section("Cơ cấu tín hiệu cần rà soát")
    with st.container(border=False, key="chart_panel_anomaly_mix"):
        alert_labels["label_vi"] = alert_labels["anomaly_type"].replace({
            "FUEL_THEFT": "Dấu hiệu thất thoát nhiên liệu",
            "IDLE_EXTENDED": "Dừng chờ kéo dài",
            "FUEL_RECEIPT_MISMATCH": "Chênh lệch giao dịch nhiên liệu",
            "GPS_JUMP_RECOVERY": "Điểm GPS cần kiểm tra",
        })
        chart_alert = alt.Chart(alert_labels.sort_values("point_count")).mark_bar(
            color="#CA8650", cornerRadiusEnd=4
        ).encode(
            x=alt.X("point_count:Q", title="Số điểm có nhãn"),
            y=alt.Y("label_vi:N", sort=None, title=None),
            tooltip=[
                alt.Tooltip("anomaly_type:N", title="Nhãn dữ liệu"),
                alt.Tooltip("point_count:Q", title="Số điểm", format=","),
                alt.Tooltip("trip_count:Q", title="Số chuyến", format=","),
            ]
        ).properties(height=235).configure(background="#FFFFFF").configure_view(
            stroke=None
        ).configure_axis(labelColor="#172D43", titleColor="#172D43", gridColor="#E6EEF2")
        st.altair_chart(chart_alert, use_container_width=True, theme=None)
        st.caption(
            "Tổng hợp nhãn có sẵn trong kho GPS. Các nhãn đại diện tình huống mô phỏng, "
            "không xác nhận thất thoát hoặc hỏng hóc thực tế."
        )

section("Phân tích chi tiết theo chuyến", "CHỌN CHUYẾN VÀ ĐIỂM HIỂN THỊ")
trip_list=options["trip_id"].tolist()
index_options={row.trip_id:row for row in options.itertuples()}
with st.container(border=False, key="filter_bar"):
    filter_title()
    left,right=st.columns([2,1])
    with left:
        trip=st.selectbox("Chọn chuyến để chẩn đoán",trip_list,
                          format_func=lambda x:f"{x} · {int(index_options[x].flagged_points)} điểm có nhãn")
    with right:
        point_limit=st.selectbox("Điểm hiển thị tối đa",[2500,5000,10000],index=1)

@st.cache_data(ttl=600)
def get_trace(trip_id):
    return con.execute("""
        SELECT
          g.message_id,
          d.full_date,
          tm.hour_24,
          tm.minute,
          g.speed_kmh,
          g.derived_speed_kmh,
          g.fuel_level_pct,
          g.fuel_liters_remaining,
          CAST(g.engine_status AS VARCHAR) AS engine_status,
          CAST(g.anomaly_type AS VARCHAR) AS anomaly_type,
          g.is_idle_stop
        FROM dds.Fact_GPS_Points g
        JOIN dds.Dim_Date d ON g.date_key=d.date_key
        JOIN dds.Dim_Time tm ON g.time_key=tm.time_key
        WHERE g.trip_id=?
        ORDER BY d.full_date,tm.hour_24,tm.minute,g.message_id
    """,[trip_id]).df()

trace=get_trace(trip)
if trace.empty:
    st.info("Chuyến được chọn không có bản ghi cảm biến.")
    st.stop()

trace["event_minute"]=pd.to_datetime(
    trace["full_date"].astype(str)+" "+
    trace["hour_24"].astype(int).astype(str).str.zfill(2)+":"+
    trace["minute"].astype(int).astype(str).str.zfill(2)+":00",
    errors="coerce"
)
trace["point_index"]=range(1,len(trace)+1)
# Cross-check the signal characteristics without silently smoothing raw measurements.
ordered_delta = trace["fuel_level_pct"].diff().dropna()
speed_changes = int((trace["speed_kmh"].diff().abs()>0.01).sum())
unique_minutes = int(trace[["full_date","hour_24","minute"]].drop_duplicates().shape[0])
if len(trace) >= 30 and speed_changes < max(5, len(trace) * 0.002):
    st.info(
        f"Kiểm tra cảm biến: {len(trace):,} điểm GPS nhưng chỉ có "
        f"{speed_changes:,} lần vận tốc thay đổi trên 0,01 km/h giữa hai điểm. "
        "Dạng đường gần như thẳng là đặc tính của dữ liệu này, "
        "phù hợp với phương pháp sinh dữ liệu GPS nội suy, không phải phép đo tốc độ xe thực tế."
    )
if len(trace) >= 30 and not ordered_delta.empty and (ordered_delta <= 0).all():
    st.caption(
        "Dữ liệu nhiên liệu của chuyến không ghi nhận lần tăng mức nhiên liệu nào; "
        "theo nguồn gốc notebook 04, nhiên liệu là tín hiệu mô phỏng dựa trên công thức tiêu hao, không phải phép đo từ bình nhiên liệu thực."
    )
if unique_minutes < len(trace):
    st.caption(
        f"Trong {len(trace):,} điểm có {unique_minutes:,} mốc phút phân biệt; "
        "nhiều điểm cùng phút không được coi là cách nhau một phút."
    )

flagged=trace[
    trace["anomaly_type"].notna()
    & ~trace["anomaly_type"].isin(["","NORMAL","NONE"])
].copy()
display_trace=trace
if len(trace)>point_limit:
    step=max(1,(len(trace)+point_limit-1)//point_limit)
    display_trace=pd.concat([trace.iloc[::step],flagged],ignore_index=True)
    display_trace=display_trace.drop_duplicates(subset=["point_index"]).sort_values("point_index")
    st.caption(f"Chuỗi có {len(trace):,} điểm; biểu đồ hiển thị {len(display_trace):,} "
               "điểm thực (lấy mẫu theo thứ tự và luôn giữ điểm có nhãn).")

section("Khảo sát tín hiệu theo chuyến")
st.caption(
    "Các phép đo được sắp theo ngày, phút và ID bản tin. Trục ngang là thứ tự "
    "bản ghi GPS để giữ riêng những phép đo cùng phút."
)

def chart_style(chart):
    return chart.configure(background="#FFFFFF").configure_view(
        stroke=None
    ).configure_axis(
        labelColor="#172D43", titleColor="#172D43",
        gridColor="#E8EFF4", labelFontSize=11
    )

def series_line(data, field, color, title, height=155):
    return alt.Chart(data).mark_line(
        color=color, strokeWidth=2.1
    ).encode(
        x=alt.X("point_index:Q", title="Thứ tự điểm GPS"),
        y=alt.Y(field + ":Q", title=title, scale=alt.Scale(zero=False)),
        tooltip=[
            alt.Tooltip("point_index:Q", title="Điểm GPS", format=","),
            alt.Tooltip("event_minute:T", title="Thời gian", format="%d/%m/%Y %H:%M"),
            alt.Tooltip(field + ":Q", title=title, format=".2f"),
            alt.Tooltip("anomaly_type:N", title="Nhãn ghi nhận"),
        ],
    ).properties(height=height)

# Full-trip context is deliberately compact. Exact evidence is examined
# in the focused window below.
section("Toàn cảnh hành trình")
with st.container(border=False, key="chart_panel_trip_overview"):
    overview_left, overview_right = st.columns(2, gap="large")
    with overview_left:
        st.markdown('<div class="chart-heading">Nhiên liệu trong toàn chuyến</div>',
                    unsafe_allow_html=True)
        st.altair_chart(
            chart_style(series_line(
                display_trace, "fuel_level_pct", "#178E83", "Nhiên liệu (%)", 170
            )), use_container_width=True, theme=None,
        )
    with overview_right:
        st.markdown('<div class="chart-heading">Vận tốc trong toàn chuyến</div>',
                    unsafe_allow_html=True)
        st.altair_chart(
            chart_style(series_line(
                display_trace, "speed_kmh", "#337FB6", "Vận tốc (km/h)", 170
            )), use_container_width=True, theme=None,
        )
    st.caption(
        f"Toàn chuyến có {len(trace):,} điểm GPS; đang vẽ {len(display_trace):,} "
        "điểm thực. Cần phóng vào điểm có nhãn để đánh giá sự thay đổi ngắn hạn."
    )

section("Phóng to vùng cần xác minh")
with st.container(border=False, key="filter_bar_focus"):
    focus_cols = st.columns([2, 1], gap="large")
    with focus_cols[0]:
        if flagged.empty:
            selected_point = int(trace["point_index"].iloc[len(trace)//2])
            st.info("Chuyến không có điểm được gắn nhãn; hiển thị vùng giữa chuyến.")
        else:
            flagged_ids = flagged["point_index"].astype(int).tolist()
            selected_point = st.selectbox(
                "Điểm cảnh báo cần xem",
                flagged_ids,
                format_func=lambda p: (
                    f"Điểm {p:,} · " +
                    str(trace.loc[trace["point_index"].eq(p), "anomaly_type"].iloc[0])
                ),
                key="fuel_focus_alert",
            )
    with focus_cols[1]:
        radius = st.select_slider(
            "Số điểm quan sát mỗi phía", options=[30, 50, 100, 200],
            value=100, key="fuel_focus_radius",
        )

window = trace.loc[
    trace["point_index"].between(
        max(1, selected_point-radius), selected_point+radius
    )
].copy()
selected_row = trace.loc[trace["point_index"].eq(selected_point)].iloc[0]
# Focused readout separates measured values from inferred duration.
focus_fuel = window["fuel_level_pct"].dropna()
focus_speed = window["speed_kmh"].dropna()
if not focus_fuel.empty and not focus_speed.empty:
    insight_cols = st.columns(3, gap="large")
    insight_cols[0].metric(
        "Chênh lệch nhiên liệu trong cửa sổ",
        f"{focus_fuel.iloc[-1]-focus_fuel.iloc[0]:+.3f} điểm %"
    )
    insight_cols[1].metric(
        "Vận tốc thấp nhất",
        f"{focus_speed.min():.2f} km/h"
    )
    insight_cols[2].metric(
        "Điểm có động cơ Idling",
        f"{int(window['engine_status'].eq('Idling').sum()):,}"
    )

st.markdown(
    f'<div class="insight-strip"><strong>Điểm GPS {selected_point:,}</strong> · '
    f'Nhãn: {selected_row["anomaly_type"] if pd.notna(selected_row["anomaly_type"]) else "Không có nhãn"}'
    f' · Vận tốc: {selected_row["speed_kmh"] if pd.notna(selected_row["speed_kmh"]) else "N/A"} km/h'
    f' · Động cơ: {selected_row["engine_status"] if pd.notna(selected_row["engine_status"]) else "Không xác định"}'
    '</div>', unsafe_allow_html=True,
)

# Only the selected anomaly is highlighted; other labels remain available
# in the underlying point table.
selected_rule = alt.Chart(pd.DataFrame({
    "point_index": [selected_point]
})).mark_rule(
    color="#D58C4D", strokeDash=[5, 4], strokeWidth=2
).encode(x="point_index:Q")
shared_x = alt.X(
    "point_index:Q", title="Thứ tự điểm GPS",
    scale=alt.Scale(domain=[
        int(window["point_index"].min()), int(window["point_index"].max())
    ]),
)
fuel_chart = alt.Chart(window).mark_line(
    color="#159487", strokeWidth=2.4
).encode(
    x=shared_x,
    y=alt.Y("fuel_level_pct:Q", title="Nhiên liệu (%)",
            scale=alt.Scale(zero=False)),
    tooltip=[
        alt.Tooltip("point_index:Q", title="Điểm GPS", format=","),
        alt.Tooltip("fuel_level_pct:Q", title="Nhiên liệu (%)", format=".2f"),
    ],
)
speed_chart = alt.Chart(window).mark_line(
    color="#337FB6", strokeWidth=2.4
).encode(
    x=shared_x,
    y=alt.Y("speed_kmh:Q", title="Vận tốc (km/h)",
            scale=alt.Scale(zero=True)),
    tooltip=[
        alt.Tooltip("point_index:Q", title="Điểm GPS", format=","),
        alt.Tooltip("speed_kmh:Q", title="Vận tốc", format=".2f"),
    ],
)
# Each categorical state is a colored segment, rather than thousands of
# misleading connected dots. Boundaries follow observed point order.
engine_window = window[["point_index", "engine_status"]].copy()
engine_window["engine_status"] = (
    engine_window["engine_status"].fillna("Unknown").astype(str)
)
engine_window["next_point"] = engine_window["point_index"] + 1
engine_bands = alt.Chart(engine_window).mark_rect(
    opacity=.88
).encode(
    x=shared_x,
    x2="next_point:Q",
    y=alt.Y("engine_status:N", title="Trạng thái động cơ"),
    color=alt.Color(
        "engine_status:N", title="Động cơ",
        scale=alt.Scale(
            domain=["Running", "Idling", "Off", "Unknown"],
            range=["#6B76B6", "#E2A05E", "#8795A3", "#B4BEC9"],
        ),
        legend=alt.Legend(orient="bottom"),
    ),
    tooltip=[
        alt.Tooltip("point_index:Q", title="Điểm GPS"),
        alt.Tooltip("engine_status:N", title="Trạng thái"),
    ],
)
comparison = alt.vconcat(
    alt.layer(fuel_chart, selected_rule).properties(height=150),
    alt.layer(speed_chart, selected_rule).properties(height=150),
    alt.layer(engine_bands, selected_rule).properties(height=95),
    spacing=13,
).resolve_scale(x="shared")
with st.container(border=False, key="chart_panel_focus_sensors"):
    st.markdown(
        '<div class="chart-heading">Ba tín hiệu tại vùng quan sát</div>',
        unsafe_allow_html=True,
    )
    st.altair_chart(
        chart_style(comparison), use_container_width=True, theme=None,
    )
    st.caption(
        "Vạch cam chỉ điểm GPS đang chọn. Nhiên liệu, vận tốc và trạng thái "
        "động cơ được đối chiếu cùng thứ tự điểm đo; đây là hỗ trợ kiểm tra, "
        "không phải kết luận về sự cố vận hành thực tế."
    )

# Source purchase transactions for the selected trip: cross-check evidence only.
@st.cache_data(ttl=600)
def trip_fuel_purchases(trip_id):
    return con.execute("""
        SELECT f.fuel_purchase_id, d.full_date AS purchase_date,
               f.liters_purchased, f.total_cost_usd, v.truck_id AS purchase_vehicle,
               trip_vehicle.truck_id AS trip_vehicle,
               CASE WHEN pv.truck_id IS DISTINCT FROM tv.truck_id
                    THEN 'Khác mã xe - cần xác minh'
                    WHEN f.vehicle_key IS DISTINCT FROM t.vehicle_key
                    THEN 'Cùng xe, khác khóa phiên bản'
                    ELSE 'Khớp khóa phương tiện' END AS vehicle_reconciliation
        FROM dds.Fact_Fuel_Purchases f
        JOIN dds.Fact_Trips t ON f.trip_id=t.trip_id
        LEFT JOIN dds.Dim_Date d ON f.date_key=d.date_key
        LEFT JOIN dds.Dim_Vehicle v ON f.vehicle_key=v.vehicle_key
        LEFT JOIN dds.Dim_Vehicle trip_vehicle ON t.vehicle_key=trip_vehicle.vehicle_key
        LEFT JOIN dds.Dim_Vehicle pv ON f.vehicle_key=pv.vehicle_key
        LEFT JOIN dds.Dim_Vehicle tv ON t.vehicle_key=tv.vehicle_key
        WHERE f.trip_id=?
        ORDER BY d.full_date,f.fuel_purchase_id
    """,[trip_id]).df()

purchases=trip_fuel_purchases(trip)
section("Đối chiếu giao dịch mua nhiên liệu của chuyến")
with st.container(border=False, key="chart_panel_fuel_purchases"):
    if purchases.empty:
        st.info("Chuyến này chưa có giao dịch mua nhiên liệu liên kết trong DDS.")
    else:
        p1,p2=st.columns(2,gap="large")
        p1.metric("Nhiên liệu mua ghi nhận",f"{purchases['liters_purchased'].sum():,.2f} L")
        p2.metric("Tổng chi phí mua",f"${purchases['total_cost_usd'].sum():,.2f}")
        st.dataframe(purchases.rename(columns={
            "fuel_purchase_id":"Mã giao dịch",
            "purchase_date":"Ngày mua",
            "liters_purchased":"Lượng mua (L)",
            "total_cost_usd":"Chi phí (USD)",
            "purchase_vehicle":"Xe trên giao dịch",
            "trip_vehicle":"Xe của chuyến",
            "vehicle_reconciliation":"Đối soát phương tiện",
        }),hide_index=True,use_container_width=True)
        actual_mismatch_count=int(
            purchases["vehicle_reconciliation"].eq("Khác mã xe - cần xác minh").sum()
        )
        if actual_mismatch_count:
            st.warning(
                f"Chuyến này có {actual_mismatch_count} giao dịch khác mã xe truck_id. "
                "Cần đối chiếu chứng từ trước khi sử dụng làm bằng chứng."
            )
        elif purchases["vehicle_reconciliation"].eq(
            "Cùng xe, khác khóa phiên bản"
        ).any():
            st.caption(
                "Có giao dịch dùng khóa phiên bản Dim_Vehicle khác với chuyến, "
                "nhưng mã xe truck_id vẫn trùng khớp."
            )
        st.caption(
            "Các giao dịch được liên kết bằng trip_id. Lượng nhiên liệu mua không đồng nhất "
            "với lượng nhiên liệu tiêu hao từ cảm biến; cần kiểm tra xe và thời điểm mua "
            "trước khi đánh giá chênh lệch."
        )

@st.cache_data(ttl=600)
def get_flagged_vehicles():
    return con.execute("""
        SELECT v.truck_id AS vehicle_id,
               CAST(g.anomaly_type AS VARCHAR) AS recorded_label,
               COUNT(*) AS flagged_points,
               COUNT(DISTINCT g.trip_id) AS affected_trips
        FROM dds.Fact_GPS_Points g
        JOIN dds.Dim_Vehicle v ON g.vehicle_key=v.vehicle_key
        WHERE g.anomaly_type IN (
            'FUEL_THEFT','IDLE_EXTENDED','FUEL_RECEIPT_MISMATCH'
        )
        GROUP BY v.truck_id, g.anomaly_type
        ORDER BY affected_trips DESC, flagged_points DESC, v.truck_id
    """).df()

flagged_vehicles=get_flagged_vehicles()
section("Danh sách phương tiện cần xác minh", "CẢNH BÁO CHƯA PHẢI KẾT LUẬN")
st.caption("Danh sách tổng hợp toàn đội xe trong dữ liệu GPS, không phụ thuộc chuyến đang chọn. "
           "Nhãn FUEL_THEFT chỉ là dấu hiệu cần kiểm tra, chưa chứng minh hành vi gian lận.")
if flagged_vehicles.empty:
    st.info("Không tìm thấy xe có nhãn nhiên liệu hoặc nổ máy chờ.")
else:
    st.dataframe(flagged_vehicles.rename(columns={
        "vehicle_id":"Mã xe","recorded_label":"Nhãn ghi nhận",
        "flagged_points":"Điểm có nhãn","affected_trips":"Chuyến liên quan",
    }),hide_index=True,use_container_width=True)


section("Danh sách điểm cảnh báo", "ĐỐI SOÁT BẢN GHI GPS")
if flagged.empty:
    st.info("Không có điểm được gắn nhãn bất thường trong chuyến này.")
else:
    st.dataframe(
        flagged[[
            "event_minute","message_id","anomaly_type",
            "speed_kmh","engine_status","fuel_level_pct",
            "fuel_liters_remaining"
        ]].rename(columns={
            "event_minute":"Thời gian","message_id":"ID điểm","anomaly_type":"Nhãn ghi nhận",
            "speed_kmh":"Vận tốc (km/h)","engine_status":"Động cơ",
            "fuel_level_pct":"Nhiên liệu (%)","fuel_liters_remaining":"Nhiên liệu (L)"
        }),use_container_width=True,hide_index=True
    )

section("Hướng dẫn phân tích nguyên nhân", "HƯỚNG DẪN XÁC MINH")
with st.container(border=False, key="chart_panel_decision"):
    st.markdown("""
**Bước 1 – Đối chiếu tín hiệu:** Kiểm tra thứ tự điểm đo, vận tốc, trạng thái động cơ, chênh lệch nhiên liệu và nhãn gốc.

**Bước 2 – Phân biệt các giả thuyết:**

- Xe đứng yên + động cơ tắt + mức nhiên liệu giảm nhanh: **nghi vấn thất thoát nhiên liệu**, cần kiểm tra thêm.
- Xe đứng yên + động cơ bật + nhiên liệu giảm theo thời gian: **nghi vấn tiêu hao do nổ máy chờ**.
- Xe di chuyển + nhiên liệu giảm bất thường: **cần kiểm tra tình trạng kỹ thuật và chất lượng phép đo**.

**Bước 3 – Xác minh:** So sánh với giao dịch mua nhiên liệu, lịch sử chuyến, dữ liệu đo lặp và kiểm tra hiện trường. Các quy tắc này là *logic diễn giải*, không tự sinh kết luận gian lận từ một ngưỡng chưa được phê duyệt.
""")

note("Giới hạn: Chỉ các chuyến có GPS mới được chẩn đoán. Nhãn FUEL_THEFT hay IDLE_EXTENDED là nhãn được ghi nhận, không khẳng định gian lận hay hỏng hóc. Chưa có ngưỡng định lượng đã duyệt để tự động suy ra nguyên nhân.")
