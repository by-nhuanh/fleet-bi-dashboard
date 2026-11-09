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
    "Theo dõi mức nhiên liệu, vận tốc, trạng thái động cơ và các dấu hiệu cần xác minh.")

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
            "Tổng hợp nhãn có sẵn trong kho GPS. Các nhãn chỉ hỗ trợ ưu tiên kiểm tra, "
            "không tự động xác nhận thất thoát hay hỏng hóc."
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

section("Diễn biến nhiên liệu và vận tốc", "NHIÊN LIỆU · VẬN TỐC · ĐỘNG CƠ")
st.caption("Dữ liệu thời gian trong bản DDS triển khai có độ phân giải đến phút. "
           "Trục ngang dùng thứ tự điểm đo để tránh gộp các bản ghi cùng phút.")

def line(data,field,color,y_label):
    base=alt.Chart(data).encode(
        x=alt.X("point_index:Q",title="Thứ tự điểm đo"),
        tooltip=[
            alt.Tooltip("event_minute:T",title="Thời gian",format="%d/%m/%Y %H:%M"),
            alt.Tooltip("point_index:Q",title="Điểm",format=","),
            alt.Tooltip(field+":Q",title=y_label,format=".2f"),
            alt.Tooltip("anomaly_type:N",title="Nhãn"),
        ],
    )
    return base.mark_line(color=color,strokeWidth=2).encode(
        y=alt.Y(field+":Q",title=y_label)
    ).properties(height=240).configure(
        background="#FFFFFF"
    ).configure_view(stroke=None).configure_axis(
        labelColor="#111827",titleColor="#111827",gridColor="#E6EEF2"
    )

c1,c2=st.columns(2,gap="large")
with c1:
    with st.container(border=False, key="chart_panel_fuel_level"):
        st.markdown("**Mức nhiên liệu trong bình (%)**")
        st.altair_chart(line(display_trace,"fuel_level_pct","#2F9183","Nhiên liệu (%)"),
                        use_container_width=True,theme=None)
with c2:
    with st.container(border=False, key="chart_panel_speed"):
        st.markdown("**Vận tốc phương tiện (km/h)**")
        st.altair_chart(line(display_trace,"speed_kmh","#3B85AB","Vận tốc (km/h)"),
                        use_container_width=True,theme=None)

with st.container(border=False, key="chart_panel_engine"):
    st.markdown("**Trạng thái động cơ và các điểm cần xác minh**")
    status=display_trace[["point_index","engine_status"]].copy()
    status["engine_status"]=status["engine_status"].fillna("UNKNOWN")
    engine_chart=alt.Chart(status).mark_circle(size=40,color="#63809D").encode(
        x=alt.X("point_index:Q",title="Thứ tự điểm đo"),
        y=alt.Y("engine_status:N",title="Trạng thái ghi nhận"),
        tooltip=["point_index:Q","engine_status:N"]
    ).properties(height=145).configure(background="#FFFFFF").configure_view(
        stroke=None
    ).configure_axis(labelColor="#111827",titleColor="#111827",gridColor="#E6EEF2")
    st.altair_chart(engine_chart,use_container_width=True,theme=None)

# A single aligned diagnostic view allows comparing sensor changes at
# the same GPS observation, without inventing a timestamp ordering.
section("Đối chiếu nhiên liệu, vận tốc và trạng thái động cơ")
with st.container(border=False, key="chart_panel_sensor_comparison"):
    st.markdown(
        '<div class="chart-heading">Diễn biến tín hiệu trên cùng trục điểm đo</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Ba dải biểu đồ dùng chung thứ tự bản ghi GPS. Vạch cam thể hiện vị trí "
        "được gắn nhãn cần kiểm tra; không phải kết luận nguyên nhân."
    )
    comparison = display_trace[[
        "point_index", "fuel_level_pct", "speed_kmh", "engine_status", "anomaly_type"
    ]].copy()
    comparison["engine_status"] = comparison["engine_status"].fillna("Không xác định")
    alert_positions = flagged[["point_index", "anomaly_type"]].drop_duplicates(
        subset=["point_index"]
    ).head(120)
    common_x = alt.X("point_index:Q", title="Thứ tự điểm GPS")
    alert_rule = alt.Chart(alert_positions).mark_rule(
        color="#CD8755", strokeDash=[3, 4], opacity=0.6
    ).encode(
        x=common_x,
        tooltip=[
            alt.Tooltip("point_index:Q", title="Điểm GPS"),
            alt.Tooltip("anomaly_type:N", title="Nhãn"),
        ]
    )
    fuel_line = alt.Chart(comparison).mark_line(
        color="#178B83", strokeWidth=2
    ).encode(
        x=common_x,
        y=alt.Y("fuel_level_pct:Q", title="Nhiên liệu (%)"),
        tooltip=[
            alt.Tooltip("point_index:Q", title="Điểm GPS"),
            alt.Tooltip("fuel_level_pct:Q", title="Nhiên liệu (%)", format=".2f"),
        ],
    )
    speed_line = alt.Chart(comparison).mark_line(
        color="#337FB6", strokeWidth=2
    ).encode(
        x=common_x,
        y=alt.Y("speed_kmh:Q", title="Vận tốc (km/h)"),
        tooltip=[
            alt.Tooltip("point_index:Q", title="Điểm GPS"),
            alt.Tooltip("speed_kmh:Q", title="Vận tốc (km/h)", format=".2f"),
        ],
    )
    engine_points = alt.Chart(comparison).mark_tick(
        thickness=2, size=17, color="#8062B5"
    ).encode(
        x=common_x,
        y=alt.Y("engine_status:N", title="Động cơ"),
        tooltip=[
            alt.Tooltip("point_index:Q", title="Điểm GPS"),
            alt.Tooltip("engine_status:N", title="Trạng thái"),
        ],
    )
    aligned = alt.vconcat(
        alt.layer(fuel_line, alert_rule).properties(height=140),
        alt.layer(speed_line, alert_rule).properties(height=140),
        alt.layer(engine_points, alert_rule).properties(height=105),
        spacing=17,
    ).resolve_scale(x="shared").configure(
        background="#FFFFFF"
    ).configure_view(
        stroke=None
    ).configure_axis(
        labelColor="#172D43", titleColor="#172D43", gridColor="#E7EEF3"
    )
    st.altair_chart(aligned, use_container_width=True, theme=None)

# Source purchase transactions for the selected trip: cross-check evidence only.
@st.cache_data(ttl=600)
def trip_fuel_purchases(trip_id):
    return con.execute("""
        SELECT f.fuel_purchase_id, d.full_date AS purchase_date,
               f.liters_purchased, f.total_cost_usd, v.truck_id AS purchase_vehicle
        FROM dds.Fact_Fuel_Purchases f
        LEFT JOIN dds.Dim_Date d ON f.date_key=d.date_key
        LEFT JOIN dds.Dim_Vehicle v ON f.vehicle_key=v.vehicle_key
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
            "purchase_vehicle":"Phương tiện ghi nhận",
        }),hide_index=True,use_container_width=True)
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
