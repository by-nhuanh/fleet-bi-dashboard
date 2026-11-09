"""Shared visual system for the three Fleet BI Streamlit pages.

This file controls presentation only. Business metrics always come from DDS.
"""
import html
import streamlit as st

STYLES = r"""
<style>
:root{color-scheme:light;--navy:#102F4B;--blue:#287CF0;--ink:#18324B;--muted:#657D94;--line:#E0E9F3;--surface:#FFFFFF;--canvas:#F4F7FC}
html,body,[data-testid="stApp"],[data-testid="stAppViewContainer"]{
 background:var(--canvas)!important;color:var(--ink)!important;color-scheme:light!important;
 font-family:Inter,"Segoe UI",Arial,sans-serif!important
}
[data-testid="stHeader"]{background:transparent!important}
[data-testid="stMain"] .block-container{max-width:1450px;padding:2rem 2.1rem 3rem}
[data-testid="stMain"] p,[data-testid="stMain"] label,[data-testid="stMain"] h1,
[data-testid="stMain"] h2,[data-testid="stMain"] h3{color:var(--ink)}
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] *{color:#203548!important}
[data-testid="stVerticalBlockBorderWrapper"]>div{
 background:#FFFFFF!important;border:1px solid var(--line)!important;
 border-radius:16px!important;box-shadow:0 4px 16px rgba(26,53,85,.035)
}
[data-testid="stExpander"]{border:1px solid var(--line)!important;border-radius:12px!important;background:#fff!important}
[data-testid="stExpander"] summary,[data-testid="stExpander"] summary *{color:var(--ink)!important}
[data-testid="stDataFrame"]{background:white;color-scheme:light}
[data-baseweb="select"]>div,[data-baseweb="input"]>div,[data-testid="stDateInput"] input{
 background:#FFF!important;color:#19364E!important;border:1px solid #D8E3EE!important;border-radius:10px!important
}
[data-testid="stDateInput"] input::placeholder,[data-testid="stMultiSelect"] input::placeholder{color:#111827!important;opacity:1}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#102F4B 0%,#153D63 76%,#19456C 100%)!important}
[data-testid="stSidebar"]>div{background:transparent!important}
[data-testid="stSidebarNav"]{display:none!important}
[data-testid="stSidebar"] [data-testid="stSidebarContent"]{padding-top:1rem!important}
[data-testid="stSidebar"] p,[data-testid="stSidebar"] label{color:#D7E6F5!important}
[data-testid="stSidebar"] [data-testid="stPageLink"]{width:100%}
[data-testid="stSidebar"] [data-testid="stPageLink"] a,
[data-testid="stSidebar"] a[data-testid*="stPageLink"]{
 display:flex!important;align-items:center!important;gap:.75rem!important;
 width:100%!important;min-height:56px!important;
 padding:.82rem .8rem!important;border-radius:12px!important;
 background:rgba(255,255,255,.065)!important;border:1px solid rgba(206,226,248,.14)!important;
 color:#EAF4FF!important;text-decoration:none!important;
 font-size:.89rem!important;font-weight:650!important;
 transition:background-color .15s ease,border-color .15s ease,transform .15s ease
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a *,
[data-testid="stSidebar"] a[data-testid*="stPageLink"] *{color:inherit!important}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover,
[data-testid="stSidebar"] a[data-testid*="stPageLink"]:hover{
 background:#245A89!important;border-color:#70B5FB!important;transform:translateX(2px)
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"],
[data-testid="stSidebar"] a[data-testid*="stPageLink"][aria-current="page"],
[data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-selected="true"]{
 background:linear-gradient(105deg,#2384F8,#1765C6)!important;
 border:1px solid #77B8FF!important;color:#FFFFFF!important;
 box-shadow:0 6px 14px rgba(3,20,48,.23)!important;font-weight:760!important
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:focus-visible{
 outline:3px solid #BCE1FF!important;outline-offset:2px
}
.nav-brand{display:flex;align-items:center;gap:.8rem;padding:.7rem .15rem 1.05rem;color:#fff}
.nav-brand-icon{width:44px;height:44px;background:#247CE2;border-radius:12px;display:flex;align-items:center;justify-content:center}
.nav-brand-icon svg{width:27px;height:27px;stroke:#fff;stroke-width:1.7;fill:none;stroke-linecap:round;stroke-linejoin:round}
.nav-brand-text{color:#fff;font-weight:790;font-size:1.06rem;letter-spacing:-.025em;line-height:1.32}
.nav-brand-sub{font-size:.7rem;color:#AFC9E2;letter-spacing:.11em;font-weight:700}
.nav-label{font-size:.68rem;color:#8EAFD0;font-weight:730;letter-spacing:.13em;margin:.6rem .25rem .6rem}
.nav-divider{height:1px;background:rgba(207,226,249,.18);margin:1.15rem 0}
.nav-bottom{font-size:.72rem;color:#B8CEE1;padding:.2rem .25rem;line-height:1.7}
.dashboard-header{display:flex;align-items:flex-start;justify-content:space-between;gap:1.2rem;
 padding:0 0 1.3rem;border-bottom:1px solid #DFE8F2;margin-bottom:1.15rem}
.dashboard-title-area{border-left:4px solid #2985F4;padding-left:1.1rem}
.dashboard-eyebrow{color:#317BC6;font-weight:780;font-size:.7rem;letter-spacing:.12em;margin-bottom:.38rem}
.dashboard-title{font-weight:790;color:#17324E;font-size:clamp(1.55rem,2.5vw,2rem);line-height:1.25;letter-spacing:-.035em}
.dashboard-description{color:#111827;font-size:.86rem;margin-top:.35rem;line-height:1.45}
.dashboard-chip{flex-shrink:0;background:#E8F0FC;color:#2A669E;padding:.48rem .75rem;
 border:1px solid #D6E5F7;border-radius:10px;font-size:.75rem;font-weight:760}
.filter-caption{display:flex;align-items:center;gap:.5rem;font-size:.85rem;font-weight:760;color:#264B72;margin-bottom:.6rem}
.filter-caption svg{height:18px;width:18px;stroke:#287CF0;stroke-width:1.9;fill:none;stroke-linecap:round}
.panel-heading{display:flex;align-items:center;justify-content:space-between;gap:.75rem;margin:1.45rem 0 .75rem}
.panel-heading-title{font-weight:770;font-size:1.07rem;letter-spacing:-.02em;color:#1B3753}
.panel-heading-hint{color:#111827;font-size:.72rem;font-weight:620;text-align:right}
.kpi-card{background:#FFF;border:1px solid #E1EAF4;border-radius:15px;
 padding:1.04rem 1.14rem;height:184px;box-sizing:border-box;display:flex;flex-direction:column;justify-content:space-between;box-shadow:0 4px 16px rgba(27,59,90,.045);
 border-top:1px solid #E1EAF4}
.kpi-card-top{display:flex;align-items:flex-start;justify-content:space-between;gap:.5rem}
.kpi-label{font-size:.78rem;color:#111827;font-weight:680;line-height:1.35}
.kpi-icon{height:38px;width:38px;border-radius:11px;background:var(--tint);color:var(--accent);
 display:flex;align-items:center;justify-content:center;flex-shrink:0}
.kpi-icon svg{width:21px;height:21px;stroke:currentColor;stroke-width:1.8;fill:none;stroke-linecap:round;stroke-linejoin:round}
.kpi-value{margin:.62rem 0 .29rem;font-weight:790;font-size:clamp(1.16rem,1.65vw,1.82rem);
 letter-spacing:-.04em;color:#142C46;white-space:normal;overflow-wrap:anywhere}
.kpi-foot{color:#111827;font-size:.735rem;line-height:1.4}
.chart-heading{font-size:.93rem;font-weight:750;color:#23405A;margin:.15rem 0 .35rem}
.chart-subtitle{font-size:.76rem;color:#111827;margin:.1rem 0 .6rem}
.note-panel{padding:.87rem 1.05rem;border-left:3px solid #2B94A0;border-radius:0 10px 10px 0;
 background:#EAF4F5;color:#152638;font-size:.8rem;line-height:1.62;margin:1rem 0}
[data-testid="stMetric"]{background:#fff;border:1px solid #E1EAF4;border-radius:15px;
 padding:1rem 1.15rem;box-shadow:0 4px 16px rgba(27,59,90,.04)}
[data-testid="stMetricLabel"]{color:#60788F}
[data-testid="stMetricValue"]{color:#19364F}
@media(max-width:900px){
 [data-testid="stMain"] .block-container{padding:1.1rem .9rem 2rem}
 .dashboard-header{flex-direction:column}
 .kpi-card{height:184px}
 .kpi-value{font-size:1.55rem}
 .panel-heading-hint{display:none}
}

/* Uniform contrast, card rhythm and white chart panels */
[data-testid="stMain"] [data-testid="stCaptionContainer"],
[data-testid="stMain"] [data-testid="stCaptionContainer"] *,
[data-testid="stMain"] small,
[data-testid="stMain"] .chart-subtitle,
[data-testid="stMain"] .kpi-foot,
[data-testid="stMain"] .kpi-label,
[data-testid="stMain"] .dashboard-description,
[data-testid="stMain"] .panel-heading-hint {
 color:#111827!important;
}
[data-testid="stMain"] [data-testid="stVerticalBlock"]{row-gap:.8rem}
[data-testid="stMain"] [data-testid="stHorizontalBlock"]{gap:1.15rem!important;align-items:stretch!important}
[data-testid="stMain"] [data-testid="stHorizontalBlock"]>div[data-testid="stColumn"]{min-width:0}
[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"]>div{
 background:#FFFFFF!important;
}
[data-testid="stMain"] [data-testid="stVegaLiteChart"],
[data-testid="stMain"] [data-testid="stArrowVegaLiteChart"],
[data-testid="stMain"] [data-testid="stVegaLiteChart"] > div{
 background:#FFFFFF!important;
 border-radius:8px!important;
}
[data-testid="stSidebar"] button[kind="secondary"]{
 background:#2D5B83!important;border:1px solid #789FC1!important;
 color:white!important;font-weight:700!important;border-radius:10px!important;
}
[data-testid="stSidebar"] button[kind="secondary"]:hover{background:#317EC0!important}

</style>
"""

ICONS = {
    "truck": '<path d="M3 7h11v10H3zM14 10h4l3 3v4h-7z"/><circle cx="7.5" cy="18" r="1.8"/><circle cx="17.5" cy="18" r="1.8"/>',
    "route": '<circle cx="5" cy="5" r="2"/><circle cx="19" cy="19" r="2"/><path d="M7 5h8a4 4 0 0 1 0 8H9a4 4 0 0 0 0 8h8"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l4 2"/>',
    "fuel": '<path d="M4 21V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v16M3 21h14M7 7h6v5H7z"/><path d="M16 9h2l3 4v5a2 2 0 0 1-4 0v-3"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
    "location": '<path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.5"/>',
    "alert": '<path d="M12 3 2.5 20h19z"/><path d="M12 9v5M12 17h.01"/>',
}


def icon_svg(name):
    return '<svg viewBox="0 0 24 24" aria-hidden="true">' + ICONS[name] + '</svg>'


def setup(page):
    """Navigation shared across pages. Compact mode renders actual icon buttons."""
    st.markdown(STYLES, unsafe_allow_html=True)
    if "navigation_compact" not in st.session_state:
        st.session_state.navigation_compact = False

    compact = st.session_state.navigation_compact
    with st.sidebar:
        if st.button(
            " " if compact else "Thu gọn thanh điều hướng",
            icon=":material/left_panel_open:" if compact else ":material/left_panel_close:",
            key="toggle_navigation",
            help="Mở rộng thanh điều hướng" if compact else "Thu gọn thanh điều hướng",
            use_container_width=True,
        ):
            st.session_state.navigation_compact = not compact
            st.rerun()

        if compact:
            st.markdown(
                '<div class="nav-brand compact-brand"><span class="nav-brand-icon">' +
                icon_svg("truck") + '</span></div>',
                unsafe_allow_html=True,
            )
            pages = [
                ("app.py", "Tổng quan vận hành", ":material/dashboard:", 10),
                ("pages/2_Route_GIS.py", "Phân tích tuyến đường", ":material/map:", 11),
                ("pages/3_Fuel_Analytics.py", "Phân tích nhiên liệu", ":material/local_gas_station:", 12),
            ]
            for path, label, icon, page_num in pages:
                if st.button(
                    " ",
                    icon=icon,
                    key=f"nav_compact_{page_num}",
                    help=label,
                    use_container_width=True,
                    type="primary" if page == page_num else "secondary",
                ):
                    st.switch_page(path)
        else:
            st.markdown(
                '<div class="nav-brand"><span class="nav-brand-icon">' +
                icon_svg("truck") +
                '</span><span><span class="nav-brand-text">Fleet BI Dashboard</span>'
                '<span class="nav-brand-sub">Vận hành đội xe</span></span></div>'
                '<div class="nav-label">DANH MỤC PHÂN TÍCH</div>',
                unsafe_allow_html=True,
            )
            st.page_link(
                "app.py", label="Tổng quan vận hành",
                icon=":material/dashboard:", use_container_width=True,
            )
            st.page_link(
                "pages/2_Route_GIS.py", label="Phân tích tuyến đường",
                icon=":material/map:", use_container_width=True,
            )
            st.page_link(
                "pages/3_Fuel_Analytics.py", label="Phân tích nhiên liệu",
                icon=":material/local_gas_station:", use_container_width=True,
            )
            st.markdown(
                '<div class="nav-divider"></div>'
                '<div class="nav-bottom">Nguồn dữ liệu: DDS / DuckDB'
                '<div>Không phải dữ liệu thời gian thực</div></div>',
                unsafe_allow_html=True,
            )

    if compact:
        st.markdown("""<style>
        section[data-testid="stSidebar"] {
            width:88px!important;min-width:88px!important;max-width:88px!important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
            width:88px!important;min-width:88px!important;
            padding:12px 10px!important;
        }
        section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            gap:12px!important;
        }
        section[data-testid="stSidebar"] .compact-brand {
            justify-content:center!important;padding:.35rem 0 .75rem!important;
        }
        section[data-testid="stSidebar"] .compact-brand .nav-brand-icon {
            width:44px!important;height:44px!important;
        }
        section[data-testid="stSidebar"] [data-testid="stButton"] button {
            width:58px!important;min-width:58px!important;max-width:58px!important;
            height:54px!important;min-height:54px!important;
            border-radius:13px!important;
            display:flex!important;align-items:center!important;justify-content:center!important;
            padding:0!important;box-shadow:none!important;
        }
        section[data-testid="stSidebar"] [data-testid="stButton"] button p {
            margin:0!important;line-height:0!important;font-size:0!important;
        }
        section[data-testid="stSidebar"] [data-testid="stButton"] button span[data-testid="stIconMaterial"],
        section[data-testid="stSidebar"] [data-testid="stButton"] button [data-testid="stIconMaterial"] {
            font-size:25px!important;line-height:1!important;color:#FFFFFF!important;
        }
        section[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] {
            background:#2683EF!important;border:1px solid #80BBFF!important;
        }
        section[data-testid="stSidebar"] [data-testid="stButton"] button[kind="secondary"] {
            background:rgba(255,255,255,.075)!important;
            border:1px solid rgba(213,232,248,.16)!important;
        }
        section[data-testid="stSidebar"] [data-testid="stButton"] button:hover {
            background:#296B9C!important;border-color:#90C5F6!important;
        }
        </style>""",unsafe_allow_html=True)


def page_header(number, title, subtitle, badge="DỮ LIỆU LỊCH SỬ"):
    st.markdown(
        '<div class="dashboard-header"><div class="dashboard-title-area">'
        '<div class="dashboard-eyebrow">PHÂN TÍCH VẬN HÀNH ĐỘI XE</div>'
        '<div class="dashboard-title">' + html.escape(title) + '</div>'
        '<div class="dashboard-description">' + html.escape(subtitle) + '</div></div>'
        '<div class="dashboard-chip">' + html.escape(badge) + '</div></div>',
        unsafe_allow_html=True,
    )


def filter_title():
    st.markdown(
        '<div class="filter-caption"><svg viewBox="0 0 24 24">'
        '<path d="M3 5h18M6 12h12M10 19h4"/></svg>Bộ lọc dữ liệu</div>',
        unsafe_allow_html=True,
    )


def section(title, hint=""):
    st.markdown(
        '<div class="panel-heading"><div class="panel-heading-title">' +
        html.escape(title) + '</div><div class="panel-heading-hint">' +
        html.escape(hint) + '</div></div>',
        unsafe_allow_html=True,
    )


def metric_card(label, value, detail, icon="truck", accent="#287CF0", tint="#E9F2FF"):
    st.markdown(
        '<div class="kpi-card" style="--accent:' + accent + ';--tint:' + tint + '">'
        '<div class="kpi-card-top"><span class="kpi-label">' + html.escape(str(label)) + '</span>'
        '<span class="kpi-icon">' + icon_svg(icon) + '</span></div>'
        '<div class="kpi-value">' + html.escape(str(value)) + '</div>'
        '<div class="kpi-foot">' + html.escape(str(detail)) + '</div></div>',
        unsafe_allow_html=True,
    )


def note(content):
    st.markdown('<div class="note-panel">' + html.escape(content) + '</div>', unsafe_allow_html=True)
