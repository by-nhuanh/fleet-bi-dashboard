from pathlib import Path
import duckdb
import pandas as pd
import altair as alt
import pydeck as pdk
import streamlit as st

st.set_page_config(page_title="Fleet BI | GIS & Routes", page_icon="🗺️", layout="wide")

DB = Path(__file__).resolve().parents[1] / "database" / "fleet_analysis.duckdb"
if not DB.exists():
    st.error("Chưa có database Task 11–12: database/fleet_analysis.duckdb. Cần tải bản xuất từ DDS lên GitHub.")
    st.stop()

st.markdown("""
<style>
html,body,[data-testid="stApp"],[data-testid="stAppViewContainer"]{background:#F4F7FA!important;color:#172E40!important;color-scheme:light}
.block-container{max-width:1490px;padding-top:1.45rem}
[data-testid="stVerticalBlockBorderWrapper"]>div{border-radius:14px!important;border-color:#E2EAF0!important;background:#fff!important}
[data-testid="stSidebar"]{background:#F4F7FA!important}
.hd{background:#102D40;color:#fff;border-radius:13px;padding:1.1rem 1.4rem;margin-bottom:1.2rem}
.hd strong{color:white;font-size:1.15rem}.hd small{color:#C4D8DC}
.subtle{color:#62798A;font-size:.86rem}
.sec{font-size:1.16rem;color:#193748;font-weight:760;margin:1.5rem 0 .5rem}
.note{background:#E8F1F2;padding:.85rem 1rem;border-left:3px solid #3F9696;color:#375F70;border-radius:0 9px 9px 0}
</style>
<div class="hd"><strong>FLEET BI &nbsp; / &nbsp; Route Intelligence</strong>
<small style="float:right">TASK 11 · GIS DASHBOARD</small></div>
""",unsafe_allow_html=True)


# Navigation between deliverables (visible even when the Streamlit sidebar is collapsed).
nav1,nav2,nav3=st.columns(3)
with nav1:
    st.page_link("app.py",label="01 · Tổng quan vận hành",use_container_width=True)
with nav2:
    st.page_link("pages/2_Route_GIS.py",label="02 · GIS & tuyến đường",use_container_width=True)
with nav3:
    st.page_link("pages/3_Fuel_Analytics.py",label="03 · Phân tích nhiên liệu",use_container_width=True)

@st.cache_resource
def connect():
    return duckdb.connect(str(DB),read_only=True)

con=connect()

@st.cache_data
def lookups():
    dates=con.execute("""
        SELECT MIN(d.full_date),MAX(d.full_date)
        FROM dds.Fact_GPS_Points g JOIN dds.Dim_Date d ON g.date_key=d.date_key
    """).fetchone()
    routes=con.execute("""
        SELECT route_id
        FROM dds.Dim_Route WHERE route_id IS NOT NULL ORDER BY route_id
    """).df()["route_id"].tolist()
    return dates,routes

bounds,routes=lookups()
st.title("Phân tích tuyến đường & điểm nghẽn")
st.caption("Bản đồ GPS, vùng vận tốc thấp và hiệu suất tuyến đường · dữ liệu DDS thực tế")

if bounds[0] is None:
    st.warning("Không tìm thấy bản ghi GPS.")
    st.stop()

col1,col2,col3=st.columns([1.5,1,1])
with col1:
    dates=st.date_input("Khoảng ngày GPS",value=(bounds[0],bounds[1]),
                        min_value=bounds[0],max_value=bounds[1])
with col2:
    route=st.selectbox("Tuyến đường",["Tất cả"]+routes)
with col3:
    threshold=st.slider("Vận tốc thấp ≤ (km/h)",0,80,20,5,
                        help="Ngưỡng phân tích do người xem chọn, không phải chứng cứ kẹt xe.")
if len(dates)!=2:
    st.info("Chọn ngày bắt đầu và ngày kết thúc.")
    st.stop()

conditions=["d.full_date BETWEEN ? AND ?"]
params=[dates[0],dates[1]]
if route!="Tất cả":
    conditions.append("r.route_id=?")
    params.append(route)
w=" AND ".join(conditions)

@st.cache_data(ttl=600)
def load_map(where_clause,values,limit_speed):
    base=f"""
        FROM dds.Fact_GPS_Points g
        JOIN dds.Dim_Date d ON g.date_key=d.date_key
        JOIN dds.Fact_Trips t ON g.trip_id=t.trip_id
        JOIN dds.Dim_Route r ON t.route_key=r.route_key
        WHERE {where_clause}
        AND g.latitude BETWEEN -90 AND 90
        AND g.longitude BETWEEN -180 AND 180
    """
    allcount=con.execute(f"""
        SELECT COUNT(*),COUNT(DISTINCT g.trip_id),
               COUNT(*) FILTER (WHERE g.speed_kmh <= ? AND g.speed_kmh >= 0)
        {base}
    """,[limit_speed]+list(values)).fetchone()
    spots=con.execute(f"""
        SELECT ROUND(g.latitude,2) AS latitude,
               ROUND(g.longitude,2) AS longitude,
               COUNT(*) AS weight
        {base} AND g.speed_kmh BETWEEN 0 AND ?
        GROUP BY 1,2
        ORDER BY weight DESC
        LIMIT 12000
    """,list(values)+[limit_speed]).df()
    return allcount,spots

try:
    (gps_count,trip_count,low_count),spots=load_map(w,tuple(params),threshold)
except Exception as exc:
    st.error("Truy vấn GPS không thành công")
    st.exception(exc)
    st.stop()

a,b,c=st.columns(3)
a.metric("Điểm GPS trong bộ lọc",f"{gps_count:,}")
b.metric("Chuyến có GPS",f"{trip_count:,}")
c.metric("Điểm vận tốc thấp",f"{low_count:,}")

st.markdown('<div class="sec">Bản đồ mật độ điểm vận tốc thấp</div>',unsafe_allow_html=True)
if spots.empty:
    st.info("Không có điểm GPS phù hợp ngưỡng vận tốc.")
else:
    center_lat=float(spots["latitude"].mean())
    center_lon=float(spots["longitude"].mean())
    layer=pdk.Layer(
        "HeatmapLayer",
        data=spots,
        get_position="[longitude, latitude]",
        get_weight="weight",
        aggregation="SUM",
        radius_pixels=35,
        opacity=.77,
    )
    st.pydeck_chart(pdk.Deck(
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        initial_view_state=pdk.ViewState(
            latitude=center_lat,longitude=center_lon,zoom=3.4,pitch=0
        ),
        layers=[layer],
        tooltip={"text":"Điểm trong ô: {weight}"},
    ),use_container_width=True)
    st.caption(
        f"Bản đồ tổng hợp {len(spots):,} ô tọa độ (làm tròn 0,01 độ), "
        f"hiển thị tối đa 12.000 ô có nhiều điểm nhất. "
        f"Ngưỡng đang chọn: {threshold} km/h. "
        "Đây là mật độ xe chạy chậm/dừng, không phải kết luận tắc đường."
    )

@st.cache_data(ttl=600)
def gps_trip_choices(start,end,route_value):
    sql="""
        SELECT DISTINCT g.trip_id
        FROM dds.Fact_GPS_Points g
        JOIN dds.Dim_Date d ON g.date_key=d.date_key
        JOIN dds.Fact_Trips t ON g.trip_id=t.trip_id
        JOIN dds.Dim_Route r ON t.route_key=r.route_key
        WHERE d.full_date BETWEEN ? AND ?
    """
    values=[start,end]
    if route_value!="Tất cả":
        sql+=" AND r.route_id=?"
        values.append(route_value)
    sql+=" ORDER BY g.trip_id LIMIT 1000"
    return con.execute(sql,values).df()["trip_id"].tolist()

st.markdown('<div class="sec">Điểm GPS theo hành trình của một chuyến</div>',unsafe_allow_html=True)
available_trips=gps_trip_choices(dates[0],dates[1],route)
if not available_trips:
    st.info("Không có chuyến GPS trong khoảng thời gian và tuyến đang chọn.")
else:
    selected_trip=st.selectbox("Chọn chuyến có GPS",available_trips,key="route_trip")
    @st.cache_data(ttl=600)
    def trip_points(trip_id,start,end):
        return con.execute("""
            SELECT g.latitude,g.longitude,g.speed_kmh,
                   d.full_date,tm.hour_24,tm.minute
            FROM dds.Fact_GPS_Points g
            JOIN dds.Dim_Date d ON g.date_key=d.date_key
            JOIN dds.Dim_Time tm ON g.time_key=tm.time_key
            WHERE g.trip_id=? AND d.full_date BETWEEN ? AND ?
              AND g.latitude BETWEEN -90 AND 90
              AND g.longitude BETWEEN -180 AND 180
            ORDER BY d.full_date,tm.hour_24,tm.minute,g.message_id
        """,[trip_id,start,end]).df()
    gps_trip=trip_points(selected_trip,dates[0],dates[1])
    if gps_trip.empty:
        st.info("Không có tọa độ GPS hợp lệ trong khoảng thời gian đã chọn.")
    else:
        if len(gps_trip)>3000:
            sample_step=max(1,(len(gps_trip)+2999)//3000)
            gps_map=gps_trip.iloc[::sample_step].copy()
        else:
            gps_map=gps_trip
        st.pydeck_chart(pdk.Deck(
            map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
            initial_view_state=pdk.ViewState(
                latitude=float(gps_map["latitude"].mean()),
                longitude=float(gps_map["longitude"].mean()),
                zoom=4.2,pitch=0,
            ),
            layers=[pdk.Layer(
                "ScatterplotLayer",data=gps_map,
                get_position="[longitude, latitude]",
                get_fill_color=[44,132,159,145],
                get_radius=350,
                pickable=True,
            )],
            tooltip={"text":"Vận tốc ghi nhận: {speed_kmh} km/h"},
        ),use_container_width=True)
        st.caption(
            f"Chuyến {selected_trip}: {len(gps_trip):,} điểm GPS trong khoảng ngày; "
            f"bản đồ hiển thị {len(gps_map):,} điểm đo thực tế. "
            "Các dấu chấm là vị trí ghi nhận, không suy ra tuyến đường được quy hoạch."
        )

@st.cache_data(ttl=600)
def route_performance(start,end,route_value):
    sql="""
      SELECT r.route_id,r.origin_city,r.destination_city,
        COUNT(*) AS trips,
        COUNT(*) FILTER (WHERE t.is_kpi_eligible=1) AS eligible,
        COUNT(*) FILTER (WHERE t.is_kpi_eligible=1 AND t.delay_minutes>0) AS late,
        ROUND(AVG(t.duration_minutes),1) AS avg_duration_minutes,
        ROUND(AVG(t.actual_distance_km),1) AS avg_distance_km
      FROM dds.Fact_Trips t
      JOIN dds.Dim_Date d ON t.start_date_key=d.date_key
      JOIN dds.Dim_Route r ON t.route_key=r.route_key
      WHERE d.full_date BETWEEN ? AND ?
    """
    values=[start,end]
    if route_value!="Tất cả":
        sql+=" AND r.route_id=?"
        values.append(route_value)
    sql+=" GROUP BY 1,2,3 ORDER BY trips DESC"
    df=con.execute(sql,values).df()
    if not df.empty:
        df["late_rate_pct"]=100*df["late"]/df["eligible"].replace(0,float("nan"))
        df["route_name"]=df["origin_city"]+" → "+df["destination_city"]
    return df

routes_df=route_performance(dates[0],dates[1],route)
st.markdown('<div class="sec">Hiệu suất tuyến đường theo chuyến</div>',unsafe_allow_html=True)
if routes_df.empty:
    st.info("Không có chuyến thuộc bộ lọc.")
else:
    left,right=st.columns([1.25,1])
    with left:
        with st.container(border=True):
            st.markdown("**10 tuyến có nhiều chuyến nhất**")
            top=routes_df.head(10).sort_values("trips")
            chart=alt.Chart(top).mark_bar(color="#347F96",cornerRadiusEnd=4).encode(
                x=alt.X("trips:Q",title="Số chuyến"),
                y=alt.Y("route_name:N",sort=None,title=None),
                tooltip=["route_id:N","trips:Q"]
            ).properties(height=360).configure(
                background="#FFFFFF"
            ).configure_view(stroke=None).configure_axis(
                labelColor="#294459",titleColor="#294459",gridColor="#E6EEF2"
            )
            st.altair_chart(chart,use_container_width=True,theme=None)
    with right:
        with st.container(border=True):
            st.markdown("**Đối soát tỷ lệ giao trễ theo tuyến**")
            display=routes_df[[
                "route_id","route_name","trips","eligible","late","late_rate_pct"
            ]].head(12).rename(columns={
                "route_id":"Mã tuyến","route_name":"Tuyến",
                "trips":"Chuyến","eligible":"Hợp lệ","late":"Trễ",
                "late_rate_pct":"Trễ (%)"
            })
            st.dataframe(display,use_container_width=True,hide_index=True,height=390)

st.markdown("""
<div class="note">
<b>Diễn giải vận hành:</b> Điểm vận tốc thấp tại gần cơ sở có thể liên quan hoạt động
bốc dỡ hoặc dừng chờ; điểm trên đường chỉ là vị trí cần kiểm tra thêm.
Không suy ra ùn tắc giao thông khi thiếu dữ liệu giao thông thực tế.
</div>
""",unsafe_allow_html=True)
