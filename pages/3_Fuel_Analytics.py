from pathlib import Path
import duckdb
import pandas as pd
import altair as alt
import streamlit as st

st.set_page_config(page_title="Fleet BI | Fuel Diagnostics",page_icon="⛽",layout="wide")
DB=Path(__file__).resolve().parents[1]/"database"/"fleet_analysis.duckdb"
if not DB.is_file():
    st.error("Chưa có database/fleet_analysis.duckdb. Hãy bổ sung bản dữ liệu GPS đã xuất từ DDS.")
    st.stop()

st.markdown("""
<style>
html,body,[data-testid="stApp"],[data-testid="stAppViewContainer"]{background:#F4F7FA!important;color:#172E40!important;color-scheme:light}
.block-container{max-width:1490px;padding-top:1.45rem}
[data-testid="stVerticalBlockBorderWrapper"]>div{border-radius:14px!important;border-color:#E2EAF0!important;background:#fff!important}
[data-testid="stSidebar"]{background:#F4F7FA!important}
.hd{background:#102D40;color:#fff;border-radius:13px;padding:1.1rem 1.4rem;margin-bottom:1.2rem}
.hd strong{color:white;font-size:1.15rem}.hd small{color:#C4D8DC}
.section{font-size:1.16rem;color:#193748;font-weight:760;margin:1.5rem 0 .5rem}
.note{background:#E8F1F2;padding:.85rem 1rem;border-left:3px solid #3F9696;color:#375F70;border-radius:0 9px 9px 0}
</style>
<div class="hd"><strong>FLEET BI &nbsp; / &nbsp; Fuel Diagnostics</strong>
<small style="float:right">TASK 12 · FUEL ANALYTICS</small></div>
""",unsafe_allow_html=True)

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

st.title("Chẩn đoán bất thường nhiên liệu")
st.caption("Đối chiếu dữ liệu cảm biến nhiên liệu, vận tốc, động cơ và nhãn sự kiện trong DDS")

a,b,c=st.columns(3)
a.metric("Chuyến có dữ liệu GPS",f"{len(options):,}")
b.metric("Chuyến có nhãn cần kiểm tra",f"{(options.flagged_points>0).sum():,}")
c.metric("Điểm GPS có nhãn",f"{options.flagged_points.sum():,}")

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

st.markdown('<div class="section">Chuỗi thời gian cảm biến</div>',unsafe_allow_html=True)
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

st.markdown('<div class="section">Danh sách điểm được gắn nhãn</div>',unsafe_allow_html=True)
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

st.markdown('<div class="section">Cây quyết định hỗ trợ chẩn đoán</div>',unsafe_allow_html=True)
with st.container(border=True):
    st.markdown("""
**Bước 1 – Đối chiếu tín hiệu:** Kiểm tra thứ tự điểm đo, vận tốc, trạng thái động cơ, chênh lệch nhiên liệu và nhãn gốc.

**Bước 2 – Phân biệt các giả thuyết:**

- Xe đứng yên + động cơ tắt + mức nhiên liệu giảm nhanh: **nghi vấn thất thoát nhiên liệu**, cần kiểm tra thêm.
- Xe đứng yên + động cơ bật + nhiên liệu giảm theo thời gian: **nghi vấn tiêu hao do nổ máy chờ**.
- Xe di chuyển + nhiên liệu giảm bất thường: **cần kiểm tra tình trạng kỹ thuật và chất lượng phép đo**.

**Bước 3 – Xác minh:** So sánh với giao dịch mua nhiên liệu, lịch sử chuyến, dữ liệu đo lặp và kiểm tra hiện trường. Các quy tắc này là *logic diễn giải*, không tự sinh kết luận gian lận từ một ngưỡng chưa được phê duyệt.
""")

st.markdown("""
<div class="note"><b>Giới hạn phân tích:</b> Chỉ các chuyến có GPS mới được chẩn đoán.
Nhãn FUEL_THEFT, IDLE_EXTENDED hoặc các nhãn khác là dữ liệu có sẵn,
không khẳng định đã xảy ra trộm cắp hoặc hỏng hóc.
Bản Dashboard chưa thiết lập ngưỡng giảm nhiên liệu để tự động kết luận nguyên nhân.</div>
""",unsafe_allow_html=True)
