from pathlib import Path
import duckdb
import pandas as pd
import altair as alt
import streamlit as st
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ui import setup, page_header, filter_title, section, metric_card, note

st.set_page_config(page_title="Fleet BI | Fuel Diagnostics",page_icon="⛽",layout="wide",initial_sidebar_state="expanded")
DB=Path(__file__).resolve().parents[1]/"database"/"fleet_analysis.duckdb"
if not DB.is_file():
    st.error("Chưa có database/fleet_analysis.duckdb. Hãy bổ sung bản dữ liệu GPS đã xuất từ DDS.")
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

page_header(12, "Chẩn đoán bất thường nhiên liệu",
    "Đối chiếu nhiên liệu, vận tốc, trạng thái động cơ và các nhãn ghi nhận từ DDS.")

section("Tổng quan cảm biến", "CHỈ SỐ TỪ CÁC CHUYẾN CÓ GPS")
a,b,c=st.columns(3, gap="medium")
with a:
    metric_card("Chuyến có dữ liệu GPS",f"{len(options):,}",
                "Chuyến có bản ghi cảm biến", "truck", "#287CF0", "#E7F1FF")
with b:
    metric_card("Chuyến có nhãn cần kiểm tra",f"{(options.flagged_points>0).sum():,}",
                "Không đồng nghĩa đã xác nhận sự cố", "alert", "#C87C56", "#FCEDF0")
with c:
    metric_card("Điểm GPS có nhãn",f"{options.flagged_points.sum():,}",
                "Bao gồm các nhãn bất thường DDS", "location", "#7467B6", "#F0EDFB")

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

section("Phân tích chi tiết chuyến", "CHỌN CHUYẾN VÀ ĐIỂM HIỂN THỊ")
trip_list=options["trip_id"].tolist()
index_options={row.trip_id:row for row in options.itertuples()}
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

section("Diễn biến cảm biến", "NHIÊN LIỆU · VẬN TỐC · ĐỘNG CƠ")
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
        labelColor="#294459",titleColor="#294459",gridColor="#E6EEF2"
    )

c1,c2=st.columns(2)
with c1:
    with st.container(border=True):
        st.markdown("**Mức nhiên liệu trong bình (%)**")
        st.altair_chart(line(display_trace,"fuel_level_pct","#2F9183","Nhiên liệu (%)"),
                        use_container_width=True,theme=None)
with c2:
    with st.container(border=True):
        st.markdown("**Vận tốc phương tiện (km/h)**")
        st.altair_chart(line(display_trace,"speed_kmh","#3B85AB","Vận tốc (km/h)"),
                        use_container_width=True,theme=None)

with st.container(border=True):
    st.markdown("**Trạng thái động cơ và các điểm cần xác minh**")
    status=display_trace[["point_index","engine_status"]].copy()
    status["engine_status"]=status["engine_status"].fillna("UNKNOWN")
    engine_chart=alt.Chart(status).mark_circle(size=40,color="#63809D").encode(
        x=alt.X("point_index:Q",title="Thứ tự điểm đo"),
        y=alt.Y("engine_status:N",title="Trạng thái ghi nhận"),
        tooltip=["point_index:Q","engine_status:N"]
    ).properties(height=145).configure(background="#FFFFFF").configure_view(
        stroke=None
    ).configure_axis(labelColor="#294459",titleColor="#294459",gridColor="#E6EEF2")
    st.altair_chart(engine_chart,use_container_width=True,theme=None)

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
section("Danh sách xe có nhãn cần xác minh", "CẢNH BÁO CHƯA PHẢI KẾT LUẬN")
st.caption("Danh sách tổng hợp toàn đội xe trong dữ liệu GPS, không phụ thuộc chuyến đang chọn. "
           "Nhãn FUEL_THEFT chỉ là dấu hiệu cần kiểm tra, chưa chứng minh hành vi gian lận.")
if flagged_vehicles.empty:
    st.info("Không tìm thấy xe có nhãn nhiên liệu hoặc nổ máy chờ.")
else:
    st.dataframe(flagged_vehicles.rename(columns={
        "vehicle_id":"Mã xe","recorded_label":"Nhãn gốc DDS",
        "flagged_points":"Điểm có nhãn","affected_trips":"Chuyến liên quan",
    }),hide_index=True,use_container_width=True)


section("Chi tiết điểm có nhãn", "ĐỐI SOÁT BẢN GHI GPS")
if flagged.empty:
    st.info("Không có điểm được gắn nhãn bất thường trong chuyến này.")
else:
    st.dataframe(
        flagged[[
            "event_minute","message_id","anomaly_type",
            "speed_kmh","engine_status","fuel_level_pct",
            "fuel_liters_remaining"
        ]].rename(columns={
            "event_minute":"Thời gian","message_id":"ID điểm","anomaly_type":"Nhãn DDS",
            "speed_kmh":"Vận tốc (km/h)","engine_status":"Động cơ",
            "fuel_level_pct":"Nhiên liệu (%)","fuel_liters_remaining":"Nhiên liệu (L)"
        }),use_container_width=True,hide_index=True
    )

section("Cây quyết định hỗ trợ chẩn đoán", "HƯỚNG DẪN XÁC MINH")
with st.container(border=True):
    st.markdown("""
**Bước 1 – Đối chiếu tín hiệu:** Kiểm tra thứ tự điểm đo, vận tốc, trạng thái động cơ, chênh lệch nhiên liệu và nhãn gốc.

**Bước 2 – Phân biệt các giả thuyết:**

- Xe đứng yên + động cơ tắt + mức nhiên liệu giảm nhanh: **nghi vấn thất thoát nhiên liệu**, cần kiểm tra thêm.
- Xe đứng yên + động cơ bật + nhiên liệu giảm theo thời gian: **nghi vấn tiêu hao do nổ máy chờ**.
- Xe di chuyển + nhiên liệu giảm bất thường: **cần kiểm tra tình trạng kỹ thuật và chất lượng phép đo**.

**Bước 3 – Xác minh:** So sánh với giao dịch mua nhiên liệu, lịch sử chuyến, dữ liệu đo lặp và kiểm tra hiện trường. Các quy tắc này là *logic diễn giải*, không tự sinh kết luận gian lận từ một ngưỡng chưa được phê duyệt.
""")

note("Giới hạn: Chỉ các chuyến có GPS mới được chẩn đoán. Nhãn FUEL_THEFT hay IDLE_EXTENDED là nhãn được ghi nhận, không khẳng định gian lận hay hỏng hóc. Chưa có ngưỡng định lượng đã duyệt để tự động suy ra nguyên nhân.")
