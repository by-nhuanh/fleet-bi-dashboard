"""Shared visual system for the three Fleet BI Streamlit pages.

This file controls presentation only. Business metrics always come from DDS.
"""
import html
import streamlit as st

STYLES = r"""
<style>
:root {
  color-scheme:light;
  --ink:#172D43; --muted:#26394D; --line:#DDE6EF;
  --page:#F4F7FB; --white:#FFFFFF; --chrome:#E8EEF5; --blue:#176CBF;
}
html,body,[data-testid="stApp"],[data-testid="stAppViewContainer"]{
  background:var(--page)!important;
  color:var(--ink)!important;color-scheme:light!important;
  font-family:Inter,"Segoe UI",Arial,sans-serif!important;
}
/* Navigation is now at the TOP, not in a side panel. */
section[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"],
[data-testid="stSidebarNav"]{display:none!important}
[data-testid="stAppViewContainer"] [data-testid="stHeader"]{
  background:transparent!important;
}
[data-testid="stMain"] .block-container{
  max-width:1510px;padding:1rem 2rem 3rem;
}
[data-testid="stMain"] p,[data-testid="stMain"] label,
[data-testid="stMain"] h1,[data-testid="stMain"] h2,
[data-testid="stMain"] h3{color:var(--ink)}
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] *{color:#172D43!important}
[data-baseweb="select"]>div,[data-baseweb="input"]>div,
[data-testid="stDateInput"] input{
  background:#FFFFFF!important;color:#172D43!important;
  border:1px solid #D8E3EE!important;border-radius:9px!important;
}
[data-testid="stDateInput"] input::placeholder,
[data-testid="stMultiSelect"] input::placeholder{color:#172D43!important;opacity:1}
[data-testid="stMain"] [data-testid="stHorizontalBlock"]{
  gap:1.15rem!important;align-items:stretch!important;
}
[data-testid="stMain"] [data-testid="stHorizontalBlock"]>div[data-testid="stColumn"]{
  min-width:0;
}
[data-testid="stMain"] [data-testid="stVerticalBlock"]{row-gap:.8rem}
[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"]>div,
[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"],
[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stElementContainer"],
[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVegaLiteChart"],
[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stArrowVegaLiteChart"]{
  background:#FFFFFF!important;background-color:#FFFFFF!important;
}
[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"]{
  border:1px solid #DEE7EF!important;border-radius:14px!important;
}
[data-testid="stMain"] [data-testid="stVegaLiteChart"],
[data-testid="stMain"] [data-testid="stArrowVegaLiteChart"],
[data-testid="stMain"] .vega-embed,
[data-testid="stMain"] .vega-embed>div{background:#FFFFFF!important}
[data-testid="stExpander"]{
  border:1px solid var(--line)!important;background:#FFFFFF!important;
  border-radius:11px!important;
}
[data-testid="stExpander"] summary,[data-testid="stExpander"] summary *{
  color:var(--ink)!important;
}
[data-testid="stDataFrame"]{color-scheme:light;background:#FFFFFF}

/* Chrome-inspired browser tabs: clickable Streamlit buttons, not dummy markup. */
.browser-brand{
 display:flex;align-items:center;justify-content:space-between;
 gap:12px;padding:10px 16px;
 background:#122F4D;border-radius:14px 14px 0 0;
 color:#FFFFFF;
}
.browser-logo{display:flex;align-items:center;gap:11px;
 color:#FFFFFF;font-weight:770;font-size:1.02rem;letter-spacing:-.025em}
.browser-logo-mark{height:31px;width:31px;border-radius:9px;
 display:flex;align-items:center;justify-content:center;background:#2679CB;color:#FFFFFF}
.browser-logo-mark svg{height:21px;width:21px;stroke:#FFFFFF;fill:none;
 stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.browser-brand-right{font-size:.73rem;color:#DCEAF6;font-weight:540}
div[class*="st-key-browser_tabs"]{
  background:#E8EEF5!important;
  border:1px solid #D6E2ED!important;border-top:0!important;
  border-radius:0 0 13px 13px!important;
  padding:7px 9px 0!important;margin-bottom:1.35rem!important;
}
div[class*="st-key-browser_tabs"] [data-testid="stHorizontalBlock"]{
  gap:6px!important;align-items:end!important;
}
div[class*="st-key-browser_tabs"] [data-testid="stButton"] button{
  min-height:45px!important;width:100%!important;
  border:1px solid transparent!important;border-radius:10px 10px 0 0!important;
  color:#385166!important;background:#DDE6EF!important;
  display:flex!important;align-items:center!important;justify-content:flex-start!important;
  gap:8px!important;padding:10px 14px!important;
  box-shadow:none!important;font-weight:620!important;font-size:.84rem!important;
  transition:background-color .15s ease!important;
}
div[class*="st-key-browser_tabs"] [data-testid="stButton"] button:hover{
  background:#CEDCEB!important;color:#14344F!important;
}
div[class*="st-key-browser_tabs"] [data-testid="stButton"] button[kind="primary"]{
  background:#FFFFFF!important;color:#14344F!important;
  border:1px solid #C9D9E9!important;border-bottom:1px solid #FFFFFF!important;
  font-weight:780!important;
}
div[class*="st-key-browser_tabs"] [data-testid="stButton"] button p{
  color:inherit!important;font-size:inherit!important;line-height:1.25!important;
}
div[class*="st-key-browser_tabs"] [data-testid="stButton"] button [data-testid="stIconMaterial"]{
  color:inherit!important;font-size:21px!important;
}
div[class*="st-key-browser_tabs"] [data-testid="stButton"] button:focus-visible{
  outline:2px solid #277EC7!important;outline-offset:2px!important;
}

.dashboard-header{display:flex;align-items:flex-start;justify-content:space-between;
  gap:1.1rem;padding:0 0 1.2rem;border-bottom:1px solid var(--line);margin-bottom:1.2rem}
.dashboard-title-area{padding-left:14px;border-left:3px solid #2775BE}
.dashboard-eyebrow{color:#305978;font-size:.7rem;font-weight:760;letter-spacing:.07em;margin-bottom:.28rem}
.dashboard-title{font-size:clamp(1.55rem,2.35vw,2rem);font-weight:790;color:#172D43;
 letter-spacing:-.035em;line-height:1.25}
.dashboard-description{font-size:.84rem;line-height:1.4;color:#172D43;margin-top:.34rem}
.dashboard-chip{font-size:.74rem;color:#245277;font-weight:700;background:#E4EFFA;
 border:1px solid #D2E1F0;padding:.46rem .7rem;border-radius:9px;white-space:nowrap}
.filter-caption{display:flex;align-items:center;gap:.55rem;color:#213F5B;
 font-size:.86rem;font-weight:750;margin:.15rem 0 .62rem}
.filter-caption svg{height:18px;width:18px;stroke:#287BC5;stroke-width:1.8;
 fill:none;stroke-linecap:round}
.panel-heading{display:flex;align-items:center;margin:1.5rem 0 .75rem}
.panel-heading-title{font-size:1.09rem;color:#172D43;font-weight:760;letter-spacing:-.02em}
.kpi-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));
 gap:20px;margin:4px 0 18px;align-items:stretch}
.kpi-grid.kpi-grid-three{grid-template-columns:repeat(3,minmax(0,1fr))}
.kpi-card{display:flex;flex-direction:column;gap:7px;
 padding:15px 17px;background:#FFFFFF;border:1px solid #DEE7F0;
 border-radius:14px;box-sizing:border-box;min-width:0;min-height:130px;
 box-shadow:0 3px 12px rgba(27,59,90,.035)}
.kpi-card-top{display:flex;align-items:center;justify-content:space-between;gap:8px}
.kpi-label{font-size:.79rem;font-weight:700;line-height:1.3;color:#111827;
 max-width:calc(100% - 40px)}
.kpi-icon{width:34px;height:34px;flex-shrink:0;display:flex;
 align-items:center;justify-content:center;background:#EDF3F8;color:#234F76;border-radius:9px}
.kpi-icon svg{width:19px;height:19px;stroke:currentColor;stroke-width:1.8;
 fill:none;stroke-linecap:round;stroke-linejoin:round}
.kpi-value{font-size:clamp(1.3rem,1.7vw,1.84rem);line-height:1.13;font-weight:790;
 color:#142C46;letter-spacing:-.04em;overflow-wrap:anywhere;margin:2px 0 0}
.kpi-foot{color:#111827;font-size:.72rem;line-height:1.3;margin-top:auto}
.chart-heading{font-size:.93rem;font-weight:750;color:#213E55;margin:.15rem 0 .35rem}
.chart-subtitle{font-size:.76rem;color:#172D43;margin:.1rem 0 .6rem}
.note-panel{padding:.87rem 1.05rem;background:#EAF4F5;border-left:3px solid #2B94A0;
 border-radius:0 10px 10px 0;color:#152638;font-size:.8rem;line-height:1.62;margin:1rem 0}
@media(max-width:1150px){
 .kpi-grid,.kpi-grid.kpi-grid-three{grid-template-columns:repeat(2,minmax(0,1fr))}
}
@media(max-width:700px){
 [data-testid="stMain"] .block-container{padding:1rem .85rem 2rem}
 .dashboard-header{flex-direction:column}
 .browser-brand-right,.dashboard-chip{display:none}
 div[class*="st-key-browser_tabs"] [data-testid="stButton"] button{
   font-size:.7rem!important;padding:7px 5px!important;gap:4px!important;
   justify-content:center!important;min-height:53px!important;
 }
 .kpi-grid,.kpi-grid.kpi-grid-three{grid-template-columns:1fr;gap:12px}
 .kpi-card{min-height:116px}
}

/* Chart card surface: style the keyed container AND the actual outer Streamlit wrapper.
   Avoid relying on the Altair canvas, which only paints the plot rectangle. */
[data-testid="stMain"] div[class*="st-key-chart_panel"],
[data-testid="stMain"] div[class*="st-key-chart_panel"] > div,
[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has([class*="st-key-chart_panel"]),
[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has([class*="st-key-chart_panel"]) > div,
[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has([class*="st-key-chart_panel"]) [data-testid="stVerticalBlock"] {
 background-color:#FFFFFF!important;
 background:#FFFFFF!important;
 background-image:none!important;
}
[data-testid="stMain"] div[class*="st-key-chart_panel"] {
 border:1px solid #DFE7F0!important;
 border-radius:14px!important;
 padding:15px 17px!important;
 box-sizing:border-box!important;
 overflow:hidden!important;
 box-shadow:0 2px 10px rgba(27,59,90,.025)!important;
}
[data-testid="stMain"] div[class*="st-key-chart_panel"] [data-testid="stVegaLiteChart"],
[data-testid="stMain"] div[class*="st-key-chart_panel"] [data-testid="stVegaLiteChart"] > div,
[data-testid="stMain"] div[class*="st-key-chart_panel"] .vega-embed,
[data-testid="stMain"] div[class*="st-key-chart_panel"] .vega-embed > div {
 background-color:#FFFFFF!important;
}

/* Each dashboard has its own restrained accent without sacrificing contrast. */
div[class*="st-key-browser_tabs"] [class*="st-key-top_tab_10"] button:not([kind="primary"]){
 background:#E6F0FB!important;color:#205985!important;
}
div[class*="st-key-browser_tabs"] [class*="st-key-top_tab_11"] button:not([kind="primary"]){
 background:#E3F2F0!important;color:#1C6865!important;
}
div[class*="st-key-browser_tabs"] [class*="st-key-top_tab_12"] button:not([kind="primary"]){
 background:#FFF0E3!important;color:#855024!important;
}
div[class*="st-key-browser_tabs"] [data-testid="stButton"] button[kind="primary"]{
 color:var(--page-accent)!important;
 box-shadow:inset 0 3px 0 var(--page-accent)!important;
}
.dashboard-title-area{border-left-color:var(--page-accent)!important}
.dashboard-eyebrow{color:var(--page-accent)!important}
.dashboard-chip{background:var(--page-tint)!important;color:var(--page-accent)!important}
.panel-heading-title{display:flex;align-items:center;gap:10px}
.panel-heading-title:before{content:"";height:19px;width:4px;
 border-radius:3px;background:var(--page-accent);display:inline-block}
.kpi-grid .kpi-card:nth-child(4n+1) .kpi-icon{background:#E7F1FF;color:#246BB5}
.kpi-grid .kpi-card:nth-child(4n+2) .kpi-icon{background:#FFF0E5;color:#B56B35}
.kpi-grid .kpi-card:nth-child(4n+3) .kpi-icon{background:#E5F6EE;color:#207C5F}
.kpi-grid .kpi-card:nth-child(4n+4) .kpi-icon{background:#EFEAFF;color:#7053B5}
.kpi-card{border-color:#DEE7EF!important;box-shadow:0 4px 14px rgba(24,56,81,.045)}
.insight-strip{background:#FFFFFF;border:1px solid #DCE5ED;border-left:4px solid var(--page-accent);
 border-radius:10px;padding:12px 17px;margin:12px 0;color:#203A4E;font-size:.82rem}
.insight-strip strong{color:var(--page-accent)}

/* Neutral card edges — color belongs to charts and icons, not card borders. */
.dashboard-title-area{border-left:0!important;padding-left:0!important}
.dashboard-chip{border-color:#DDE6EF!important}
.panel-heading-title:before{display:none!important}
.note-panel,.insight-strip{
 border:1px solid #DFE7F0!important;
 border-left:1px solid #DFE7F0!important;
 border-radius:10px!important;
}
.kpi-card,[data-testid="stMain"] div[class*="st-key-chart_panel"],
[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]{
 border-color:#DFE7F0!important;
}
div[class*="st-key-browser_tabs"] [data-testid="stButton"] button[kind="primary"]{
 border-color:#DDE6EF!important;
 border-bottom-color:#FFFFFF!important;
 box-shadow:none!important;
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
