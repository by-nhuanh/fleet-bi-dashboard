"""Shared visual system for the three Fleet BI Streamlit pages.

This file controls presentation only. Business metrics always come from DDS.
"""
import html
import streamlit as st

STYLES = r"""
<style>
:root{color-scheme:light;--bg:#F4F7FB;--white:#FFF;--ink:#172B40;
--muted:#30465B;--line:#E1E8EF;--accent:#277ABF}
html,body,[data-testid="stApp"],[data-testid="stAppViewContainer"]{
 background:var(--bg)!important;color:var(--ink)!important;color-scheme:light!important;
 font-family:Inter,"Segoe UI",Arial,sans-serif!important}
section[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"],[data-testid="stSidebarNav"]{display:none!important}
[data-testid="stHeader"]{background:transparent!important}
[data-testid="stMain"] .block-container{max-width:1460px;padding:.65rem 1.65rem 2.5rem}
[data-testid="stMain"] p,[data-testid="stMain"] label,[data-testid="stMain"] h1,
[data-testid="stMain"] h2,[data-testid="stMain"] h3{color:var(--ink)}
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] *,
[data-testid="stMain"] small{color:#26394C!important}
[data-testid="stMain"] [data-testid="stHorizontalBlock"]{gap:1.12rem!important;align-items:stretch!important}
[data-testid="stMain"] [data-testid="stHorizontalBlock"]>[data-testid="stColumn"]{min-width:0}
[data-baseweb="select"]>div,[data-baseweb="input"]>div,
[data-testid="stDateInput"] input{background:#FFFFFF!important;color:#142C44!important;
 border:1px solid #D7E1EA!important;border-radius:9px!important}
[data-testid="stMain"] [data-testid="stExpander"]{
 background:#FFFFFF!important;border:1px solid #E1E8EF!important;border-radius:11px!important}
[data-testid="stExpander"] summary,[data-testid="stExpander"] summary *{color:#172B40!important}
[data-testid="stDataFrame"]{background:#FFFFFF;color-scheme:light}
[data-testid="stMain"] [data-testid="stVegaLiteChart"],
[data-testid="stMain"] .vega-embed,[data-testid="stMain"] .vega-embed>div{background:#FFFFFF!important}

/* Top navigation, visually connected to the application header. */
.browser-brand{display:flex;align-items:center;justify-content:space-between;
 padding:8px 15px;gap:12px;background:#142E49;border-radius:12px 12px 0 0}
.browser-logo{display:flex;align-items:center;gap:9px;color:#FFF!important;
 font-weight:740;font-size:.98rem;letter-spacing:-.02em}
.browser-logo-mark{height:28px;width:28px;border-radius:8px;background:#277BC6;
 display:flex;align-items:center;justify-content:center}
.browser-logo-mark svg{height:19px;width:19px;stroke:#FFF;fill:none;stroke-width:1.8;
 stroke-linecap:round;stroke-linejoin:round}
.browser-brand-right{font-size:.7rem;color:#D8E6F3;font-weight:540}
div[class*="st-key-browser_tabs"]{background:#EAF0F6!important;
 border:1px solid #DFE7EF!important;border-top:0!important;
 padding:5px 7px 0!important;border-radius:0 0 11px 11px!important;
 margin-bottom:1.05rem!important}
div[class*="st-key-browser_tabs"] [data-testid="stHorizontalBlock"]{gap:6px!important;align-items:end!important}
div[class*="st-key-browser_tabs"] [data-testid="stButton"] button{
 display:flex!important;align-items:center!important;justify-content:center!important;
 gap:8px!important;min-height:36px!important;width:100%!important;
 padding:7px 10px!important;border-radius:8px 8px 0 0!important;
 border:1px solid transparent!important;box-shadow:none!important;
 background:#EAF0F6!important;color:#314A60!important;
 font-weight:600!important;font-size:.83rem!important}
div[class*="st-key-browser_tabs"] [data-testid="stButton"] button:hover{
 background:#DEE8F2!important;color:#172F47!important}
div[class*="st-key-browser_tabs"] [data-testid="stButton"] button[kind="primary"]{
 background:#FFFFFF!important;color:#133752!important;
 border-color:#D9E3EC!important;border-bottom-color:#FFF!important;
 font-weight:760!important;box-shadow:none!important}
div[class*="st-key-browser_tabs"] [data-testid="stButton"] button p{font-size:inherit!important;color:inherit!important}
div[class*="st-key-browser_tabs"] [data-testid="stButton"] button [data-testid="stIconMaterial"]{
 font-size:19px!important;color:inherit!important}
div[class*="st-key-browser_tabs"] [data-testid="stButton"] button:focus-visible{
 outline:2px solid #267AC8!important;outline-offset:1px!important}

/* Compact page title */
.dashboard-header{display:flex;align-items:center;justify-content:space-between;
 gap:12px;padding:0 0 .9rem;margin-bottom:1rem;border-bottom:1px solid var(--line)}
.dashboard-title-area{padding:0;border:0}
.dashboard-eyebrow{font-weight:680;font-size:.67rem;color:#496176;letter-spacing:.07em;margin-bottom:.25rem}
.dashboard-title{font-size:clamp(1.55rem,2.3vw,1.94rem);font-weight:780;
 color:#172F46;line-height:1.25;letter-spacing:-.035em}
.dashboard-description{font-size:.82rem;color:#30465B;margin-top:.23rem}
.dashboard-chip{background:#EFF4F9;color:#35536A;border:1px solid #DFE8F0;
 border-radius:8px;padding:.4rem .68rem;font-size:.69rem;font-weight:680;white-space:nowrap}

/* Filters: one continuous white toolbar with predictable spacing. */
div[class*="st-key-filter_bar"]{background:#FFFFFF!important;border:1px solid var(--line)!important;
 border-radius:13px!important;padding:14px 17px 12px!important;
 box-shadow:0 3px 10px rgba(22,50,80,.025)!important;margin-bottom:1.15rem!important}
div[class*="st-key-filter_bar"] [data-testid="stVerticalBlock"]{row-gap:.5rem!important}
.filter-caption{display:flex;align-items:center;gap:8px;color:#193C57;
 font-weight:740;font-size:.82rem;margin:0 0 .45rem}
.filter-caption svg{height:17px;width:17px;stroke:#267DB7;stroke-width:1.8;fill:none;stroke-linecap:round}
.filter-label{color:#1A3248;font-size:.76rem;font-weight:650;margin-bottom:4px}

/* KPI grid: compact, evenly spaced and completely neutral borders. */
.panel-heading{display:flex;align-items:center;margin:1.25rem 0 .65rem}
.panel-heading-title{display:flex;align-items:center;gap:9px;
 font-weight:750;font-size:1.02rem;letter-spacing:-.015em;color:#19344C}
.panel-heading-icon{display:inline-flex;align-items:center;justify-content:center;
 width:27px;height:27px;border-radius:8px;background:#ECF2F8;color:#32729F}
.panel-heading-icon svg{width:16px;height:16px;stroke:currentColor;
 stroke-width:1.9;fill:none;stroke-linecap:round;stroke-linejoin:round}
.kpi-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;
 margin:3px 0 13px;align-items:stretch}
.kpi-grid.kpi-grid-three{grid-template-columns:repeat(3,minmax(0,1fr))}
.kpi-card{background:#FFF;border:1px solid #DFE7EF;border-radius:13px;
 box-sizing:border-box;min-height:119px;min-width:0;padding:13px 15px;
 display:flex;flex-direction:column;gap:6px;box-shadow:0 3px 10px rgba(20,43,70,.035)}
.kpi-card-top{display:flex;align-items:center;justify-content:space-between;gap:7px}
.kpi-label{font-size:.78rem;font-weight:680;line-height:1.3;color:#1D354B;max-width:calc(100% - 40px)}
.kpi-icon{width:32px;height:32px;border-radius:9px;flex-shrink:0;
 display:flex;align-items:center;justify-content:center;
 background:#E8F1FC;color:#2872B8}
.kpi-grid .kpi-card:nth-child(4n+2) .kpi-icon{background:#FFF1E5;color:#B46C36}
.kpi-grid .kpi-card:nth-child(4n+3) .kpi-icon{background:#E6F5ED;color:#247956}
.kpi-grid .kpi-card:nth-child(4n+4) .kpi-icon{background:#F0ECFA;color:#745EB2}
.kpi-icon svg{height:19px;width:19px;stroke:currentColor;stroke-width:1.8;fill:none;
 stroke-linecap:round;stroke-linejoin:round}
.kpi-value{font-size:clamp(1.3rem,1.7vw,1.85rem);line-height:1.12;
 color:#142B43;letter-spacing:-.035em;font-weight:780;overflow-wrap:anywhere}
.kpi-foot{font-size:.72rem;color:#354B5F;line-height:1.32;margin-top:auto}

/* Precisely target actual keyed chart containers, never just the plotting canvas. */
[data-testid="stMain"] div[class*="st-key-chart_panel"]{
 background:#FFFFFF!important;background-color:#FFFFFF!important;
 background-image:none!important;border:1px solid #DEE6EE!important;
 border-radius:13px!important;padding:15px 17px!important;
 box-sizing:border-box!important;box-shadow:0 3px 12px rgba(22,50,80,.025)!important;
 margin-bottom:4px!important}
[data-testid="stMain"] div[class*="st-key-chart_panel"] [data-testid="stVerticalBlock"],
[data-testid="stMain"] div[class*="st-key-chart_panel"] [data-testid="stElementContainer"],
[data-testid="stMain"] div[class*="st-key-chart_panel"] [data-testid="stVegaLiteChart"],
[data-testid="stMain"] div[class*="st-key-chart_panel"] .vega-embed{
 background:#FFFFFF!important}
.chart-heading{font-size:.88rem;color:#18354C;font-weight:720;margin:0 0 4px}
.chart-subtitle{font-size:.75rem;color:#30485D;margin:0 0 6px}
.note-panel{padding:.75rem .95rem;background:#ECF4F7;border:1px solid #DDE8ED;
 border-radius:10px;color:#233C4F;font-size:.78rem;line-height:1.55;margin:.8rem 0}
.insight-strip{background:#FFFFFF;border:1px solid #DEE7EF;border-radius:10px;
 padding:11px 15px;color:#233C4F;font-size:.8rem;margin:10px 0}
.insight-strip strong{color:#285E88}
@media(max-width:1120px){
 .kpi-grid,.kpi-grid.kpi-grid-three{grid-template-columns:repeat(2,minmax(0,1fr))}
}
@media(max-width:700px){
 [data-testid="stMain"] .block-container{padding:.7rem .7rem 2rem}
 .browser-brand-right,.dashboard-chip{display:none}
 .dashboard-header{align-items:flex-start}
 div[class*="st-key-browser_tabs"] [data-testid="stButton"] button{
  min-height:45px!important;padding:6px 3px!important;font-size:.69rem!important;gap:3px!important}
 .kpi-grid,.kpi-grid.kpi-grid-three{grid-template-columns:1fr;gap:11px}
 .kpi-card{min-height:107px}
}
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
    "chart": '<path d="M3 3v18h18"/><path d="M7 15l4-5 4 3 5-7"/>',
    "table": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18M9 10v10M15 10v10"/>',
}


def icon_svg(name):
    return '<svg viewBox="0 0 24 24" aria-hidden="true">' + ICONS[name] + '</svg>'


def setup(page):
    """Top-of-page, Chrome-style tabs replacing the entire sidebar."""
    st.markdown(STYLES, unsafe_allow_html=True)
    st.markdown(
        '<div class="browser-brand theme-page-' + str(page) + '"><span class="browser-logo">'
        '<span class="browser-logo-mark">' + icon_svg("truck") + '</span>'
        'Fleet BI Dashboard</span>'
        '<span class="browser-brand-right">PHÂN TÍCH VẬN HÀNH ĐỘI XE</span></div>',
        unsafe_allow_html=True,
    )
    destinations = (
        ("app.py", "Tổng quan vận hành", ":material/dashboard:", 10),
        ("pages/2_Route_GIS.py", "Phân tích tuyến đường", ":material/map:", 11),
        ("pages/3_Fuel_Analytics.py", "Phân tích nhiên liệu", ":material/local_gas_station:", 12),
    )
    st.markdown(
        '<style>:root{--page-accent:' +
        {10:"#2678C8",11:"#168C88",12:"#CA8650"}.get(page,"#2678C8") +
        ';--page-tint:' +
        {10:"#EAF3FF",11:"#E7F7F4",12:"#FFF1E5"}.get(page,"#EAF3FF") +
        ';}</style>', unsafe_allow_html=True,
    )
    with st.container(key="browser_tabs"):
        columns = st.columns(3, gap="small")
        for column, (path, label, icon, page_number) in zip(columns, destinations):
            with column:
                if st.button(
                    label, icon=icon, key=f"top_tab_{page_number}",
                    type="primary" if page == page_number else "secondary",
                    help=f"Chuyển đến {label.lower()}",
                    use_container_width=True,
                ):
                    if page != page_number:
                        st.switch_page(path)


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
    """Section heading with a meaningful, nondecorative icon."""
    name = "chart"
    t = title.lower()
    if any(x in t for x in ("gps", "vị trí", "tuyến", "hành trình", "bản đồ")):
        name = "route"
    elif any(x in t for x in ("nhiên liệu", "cảm biến", "cảnh báo", "động cơ")):
        name = "fuel"
    elif any(x in t for x in ("phân bổ", "hiệu quả", "xu hướng", "so sánh")):
        name = "chart"
    elif any(x in t for x in ("danh sách", "chi tiết", "giao dịch")):
        name = "table"
    st.markdown(
        '<div class="panel-heading"><div class="panel-heading-title">'
        '<span class="panel-heading-icon">' + icon_svg(name) + '</span>'
        + html.escape(title) + '</div></div>',
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
