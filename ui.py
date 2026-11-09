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
/* Consistent compact business navigation */
section[data-testid="stSidebar"]{
  background:#142F49!important;
  min-width:254px!important;width:254px!important;
  border-right:1px solid #28445F!important;
}
section[data-testid="stSidebar"]>div{background:transparent!important}
section[data-testid="stSidebar"] [data-testid="stSidebarContent"]{
  padding:12px 16px 20px!important;
}
[data-testid="stSidebarNav"]{display:none!important}
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{
  gap:9px!important;
}
section[data-testid="stSidebar"] [data-testid="stPageLink"]{width:100%;margin:0!important}
section[data-testid="stSidebar"] [data-testid="stPageLink"] a{
  display:flex!important;align-items:center!important;gap:11px!important;
  min-height:44px!important;padding:10px 12px!important;
  width:100%!important;border:0!important;border-radius:9px!important;
  color:#E5EDF4!important;background:transparent!important;
  font-size:.87rem!important;font-weight:620!important;
  text-decoration:none!important;box-shadow:none!important;
  transition:background .15s ease!important;
}
section[data-testid="stSidebar"] [data-testid="stPageLink"] a *{color:inherit!important}
section[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover{
  background:#244967!important;
}
section[data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"],
section[data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-selected="true"]{
  background:#2365A5!important;color:#FFFFFF!important;font-weight:730!important;
}
section[data-testid="stSidebar"] [data-testid="stPageLink"] a:focus-visible{
  outline:2px solid #C5E5FF!important;outline-offset:2px!important;
}
.nav-brand{
  display:flex;align-items:center;gap:10px;
  padding:6px 2px 12px!important;min-width:0;
  color:#FFFFFF;
}
.nav-brand-icon{
  width:36px;height:36px;flex:0 0 36px;display:flex;
  align-items:center;justify-content:center;border-radius:9px;background:#2879C8;
}
.nav-brand-icon svg{width:22px;height:22px;stroke:#FFFFFF;stroke-width:1.8;fill:none}
.nav-brand-copy{min-width:0}
.nav-brand-text{font-size:1rem;color:#FFFFFF;font-weight:780;line-height:1.24;white-space:nowrap}
.nav-brand-sub{font-size:.68rem;color:#BCD1E3;font-weight:550;margin-top:3px;white-space:nowrap}
.nav-label{font-size:.66rem;font-weight:720;letter-spacing:.1em;color:#B5CBDD;margin:13px 9px 4px}
.nav-divider{height:1px;background:rgba(201,225,242,.14);margin:14px 0 10px}
.nav-bottom{font-size:.71rem;color:#C3D3E1;padding:4px 7px;line-height:1.75}
section[data-testid="stSidebar"] [data-testid="stButton"] button{
  border:1px solid rgba(207,230,245,.17)!important;
  border-radius:8px!important;background:transparent!important;
  color:#EAF4FE!important;box-shadow:none!important;font-size:.77rem!important;
  min-height:34px!important;padding:5px 9px!important;
}
section[data-testid="stSidebar"] [data-testid="stButton"] button:hover{background:#244967!important}
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
.kpi-grid{
 display:grid;grid-template-columns:repeat(4,minmax(0,1fr));
 gap:20px;margin:4px 0 18px;align-items:stretch;
}
.kpi-grid.kpi-grid-three{grid-template-columns:repeat(3,minmax(0,1fr))}
.kpi-card{
 display:flex;flex-direction:column;gap:7px;
 padding:15px 17px;background:#FFFFFF;
 border:1px solid #E2EAF2;border-radius:14px;
 box-sizing:border-box;min-width:0;min-height:130px;
 box-shadow:0 3px 12px rgba(27,59,90,.035)
}
.kpi-card-top{display:flex;align-items:center;justify-content:space-between;gap:8px}
.kpi-label{font-size:.79rem;font-weight:700;line-height:1.3;color:#111827;max-width:calc(100% - 40px)}
.kpi-icon{width:34px;height:34px;flex-shrink:0;display:flex;
 align-items:center;justify-content:center;background:#EFF4F8;color:#234F76;border-radius:9px}
.kpi-icon svg{width:19px;height:19px;stroke:currentColor;stroke-width:1.8;fill:none;stroke-linecap:round;stroke-linejoin:round}
.kpi-value{font-size:clamp(1.3rem,1.7vw,1.84rem);line-height:1.13;
 font-weight:790;color:#142C46;letter-spacing:-.04em;overflow-wrap:anywhere;margin:2px 0 0}
.kpi-foot{color:#111827;font-size:.72rem;line-height:1.3;margin-top:auto}
@media(max-width:1150px){
 .kpi-grid,.kpi-grid.kpi-grid-three{grid-template-columns:repeat(2,minmax(0,1fr))}
}
@media(max-width:640px){
 .kpi-grid,.kpi-grid.kpi-grid-three{grid-template-columns:1fr;gap:12px}
 .kpi-card{min-height:116px}
}
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
 .kpi-card{min-height:116px}
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
    """Compact, top-aligned navigation shared by all dashboard pages."""
    st.markdown(STYLES, unsafe_allow_html=True)
    if "navigation_compact" not in st.session_state:
        st.session_state.navigation_compact = False
    compact = st.session_state.navigation_compact

    with st.sidebar:
        if compact:
            st.markdown(
                '<div class="nav-brand nav-brand-compact"><span class="nav-brand-icon">'
                + icon_svg("truck") + '</span></div>',
                unsafe_allow_html=True,
            )
            if st.button(" ", icon=":material/chevron_right:", help="Mở rộng menu",
                         key="toggle_navigation", use_container_width=True):
                st.session_state.navigation_compact = False
                st.rerun()
            entries = [
                ("app.py", "Tổng quan vận hành", ":material/dashboard:", 10),
                ("pages/2_Route_GIS.py", "Phân tích tuyến đường", ":material/map:", 11),
                ("pages/3_Fuel_Analytics.py", "Phân tích nhiên liệu", ":material/local_gas_station:", 12),
            ]
            for path, title, icon, code in entries:
                if st.button(
                    " ", icon=icon, key=f"nav_compact_{code}", help=title,
                    type="primary" if page == code else "secondary",
                    use_container_width=True,
                ):
                    st.switch_page(path)
        else:
            head, toggle = st.columns([5, 1], vertical_alignment="center", gap="small")
            with head:
                st.markdown(
                    '<div class="nav-brand"><span class="nav-brand-icon">'
                    + icon_svg("truck")
                    + '</span><span class="nav-brand-copy">'
                    '<span class="nav-brand-text">Fleet BI</span>'
                    '<span class="nav-brand-sub">Vận hành đội xe</span></span></div>',
                    unsafe_allow_html=True,
                )
            with toggle:
                if st.button(" ", icon=":material/chevron_left:", help="Thu gọn menu",
                             key="toggle_navigation", use_container_width=True):
                    st.session_state.navigation_compact = True
                    st.rerun()

            st.markdown('<div class="nav-label">DANH MỤC PHÂN TÍCH</div>', unsafe_allow_html=True)
            st.page_link("app.py", label="Tổng quan vận hành",
                         icon=":material/dashboard:", use_container_width=True)
            st.page_link("pages/2_Route_GIS.py", label="Phân tích tuyến đường",
                         icon=":material/map:", use_container_width=True)
            st.page_link("pages/3_Fuel_Analytics.py", label="Phân tích nhiên liệu",
                         icon=":material/local_gas_station:", use_container_width=True)
            st.markdown(
                '<div class="nav-divider"></div>'
                '<div class="nav-bottom">Nguồn dữ liệu: DuckDB'
                '<div>Dữ liệu vận hành lịch sử</div></div>',
                unsafe_allow_html=True,
            )

    if compact:
        st.markdown("""<style>
        section[data-testid="stSidebar"]{
          width:74px!important;min-width:74px!important;max-width:74px!important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarContent"]{
          width:74px!important;min-width:74px!important;padding:12px 9px!important;
        }
        section[data-testid="stSidebar"] .nav-brand-compact{
          justify-content:center!important;padding:5px 0 9px!important;
        }
        section[data-testid="stSidebar"] [data-testid="stButton"] button{
          width:52px!important;min-width:52px!important;max-width:52px!important;
          height:44px!important;min-height:44px!important;
          display:flex!important;align-items:center!important;justify-content:center!important;
          padding:0!important;margin:0 auto!important;border:0!important;
          border-radius:10px!important;
        }
        section[data-testid="stSidebar"] [data-testid="stButton"] button p{
          font-size:0!important;width:0!important;overflow:hidden!important;
        }
        section[data-testid="stSidebar"] [data-testid="stButton"] button [data-testid="stIconMaterial"]{
          font-size:23px!important;color:#EAF4FF!important;line-height:1!important;
        }
        section[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"]{
          background:#2576C5!important;color:white!important;
        }
        section[data-testid="stSidebar"] [data-testid="stButton"] button[kind="secondary"]{
          background:transparent!important;
        }
        section[data-testid="stSidebar"] [data-testid="stButton"] button:hover{
          background:#285373!important;
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
    """Display only the operational section title, without redundant all-caps notes."""
    st.markdown(
        '<div class="panel-heading"><div class="panel-heading-title">' +
        html.escape(title) + '</div></div>',
        unsafe_allow_html=True,
    )


def metric_card(label, value, detail, icon="truck", accent="#287CF0", tint="#E9F2FF", render=True):
    """Return the card HTML for a responsive grid; render directly if requested."""
    markup = (
        '<div class="kpi-card">'
        '<div class="kpi-card-top"><span class="kpi-label">' + html.escape(str(label)) + '</span>'
        '<span class="kpi-icon">' + icon_svg(icon) + '</span></div>'
        '<div class="kpi-value">' + html.escape(str(value)) + '</div>'
        '<div class="kpi-foot">' + html.escape(str(detail)) + '</div></div>'
    )
    if render:
        st.markdown(markup, unsafe_allow_html=True)
    return markup


def metric_grid(cards, columns=4):
    """Cards in one HTML grid avoid Streamlit column spacing and height drift."""
    kind = "kpi-grid-three" if columns == 3 else ""
    st.markdown('<div class="kpi-grid ' + kind + '">' + "".join(cards) + '</div>',
                unsafe_allow_html=True)


def note(content):
    st.markdown('<div class="note-panel">' + html.escape(content) + '</div>', unsafe_allow_html=True)
