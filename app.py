# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
from modules.scheduler_service import start_scheduler
from modules.database import get_connection
from modules.inventory_manager import (
    get_all_products,
    set_min_stock,
    update_stock,
    adjust_stock_by_sale
)
import load_products_from_csv

if "scheduler_started" not in st.session_state:
    start_scheduler()
    st.session_state.scheduler_started = True

st.set_page_config(
    layout="wide",
    page_title="StockSense · Inventory Intelligence",
    page_icon="📦",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg:      #0d1117;
    --surf:    #141d2e;
    --surf2:   #1a2235;
    --surf3:   #1e2840;
    --bdr:     #242d40;
    --bdr2:    #2d384f;
    --accent:  #3b82f6;
    --violet:  #8b5cf6;
    --green:   #10b981;
    --amber:   #f59e0b;
    --red:     #ef4444;
}

*, *::before, *::after { box-sizing: border-box; }

html, body,
.stApp, .stApp > div,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > div,
[data-testid="stAppViewContainer"] > section,
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
.main, .main > div,
section[data-testid="stMain"] > div,
[class*="css"] {
    font-family: 'Outfit', sans-serif !important;
    background-color: #0d1117 !important;
    color: #e2eaf8 !important;
    -webkit-font-smoothing: antialiased;
}

.block-container {
    padding: 0 2.75rem 5rem 2.75rem !important;
    max-width: 1560px;
    background-color: #0d1117 !important;
}

#MainMenu, footer, header { visibility: hidden; }

::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #2d384f; border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: #3d4f6a; }

/* ── Top nav ── */
.topnav {
    display:flex; align-items:center; justify-content:space-between;
    padding: 22px 0 20px 0; border-bottom: 1px solid #242d40; margin-bottom: 36px;
}
.brand { display:flex; align-items:center; gap:12px; }
.brand-icon {
    width:42px; height:42px; border-radius:12px; flex-shrink:0;
    background: linear-gradient(135deg,#3b82f6,#8b5cf6);
    display:flex; align-items:center; justify-content:center; font-size:20px;
    box-shadow: 0 4px 20px rgba(59,130,246,.2);
}
.brand-name {
    font-size:1.45rem; font-weight:800; letter-spacing:-0.04em; line-height:1;
    background: linear-gradient(90deg,#60a5fa,#a78bfa);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
}
.brand-tagline {
    font-size:.68rem; letter-spacing:.12em; text-transform:uppercase; margin-top:3px; font-weight:500;
    color:#7c8db5 !important; -webkit-text-fill-color:#7c8db5 !important;
}
.topnav-right { display:flex; align-items:center; gap:10px; }
.nav-badge {
    display:inline-flex; align-items:center; gap:6px; padding:6px 14px;
    border-radius:999px; font-size:.72rem; font-weight:600; letter-spacing:.04em;
    border:1px solid #242d40; background:#111620;
    color:#c0d0e8 !important; -webkit-text-fill-color:#c0d0e8 !important;
}
.nav-badge .dot {
    width:6px; height:6px; border-radius:50%; background:#10b981;
    display:inline-block; box-shadow:0 0 6px #10b981;
    animation: pulse-dot 2s ease-in-out infinite;
}
@keyframes pulse-dot { 0%,100%{opacity:1} 50%{opacity:.4} }

/* ── KPI cards ── */
.kpi-card {
    background:#111620; border:1px solid #242d40; border-radius:18px;
    padding:22px 22px 20px; position:relative; overflow:hidden;
    transition: border-color .2s, transform .2s, box-shadow .2s; cursor:default;
}
.kpi-card:hover { border-color:#2d384f; transform:translateY(-2px); box-shadow:0 4px 20px rgba(0,0,0,.45); }
.kpi-card-accent { position:absolute; top:0; left:0; right:0; height:2px; border-radius:18px 18px 0 0; }
.kpi-top { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:14px; }
.kpi-icon-wrap { width:36px; height:36px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:16px; }
.kpi-label {
    font-size:.72rem; font-weight:600; letter-spacing:.1em; text-transform:uppercase; margin-bottom:6px;
    color:#8ca0c0 !important; -webkit-text-fill-color:#8ca0c0 !important;
}
.kpi-value {
    font-size:2rem; font-weight:800; letter-spacing:-0.04em; line-height:1;
    font-family:'Outfit',sans-serif !important;
    color:#ffffff !important; -webkit-text-fill-color:#ffffff !important;
}

/* ── Cards ── */
.card {
    background:#111620; border:1px solid #242d40; border-radius:18px;
    padding:22px 24px; margin-bottom:18px;
}
.card-title { font-size:.92rem; font-weight:700; margin-bottom:8px; color:#ffffff !important; -webkit-text-fill-color:#ffffff !important; }
.card-body  { font-size:.84rem; line-height:1.75; color:#9db0cc !important; -webkit-text-fill-color:#9db0cc !important; }

/* ── Chart panel ── */
.chart-panel {
    background:#111620; border:1px solid #242d40; border-radius:18px;
    padding:22px 24px 10px; margin-bottom:20px;
}
.chart-title {
    font-size:.92rem; font-weight:700; margin-bottom:16px;
    display:flex; align-items:center; gap:8px;
    color:#ffffff !important; -webkit-text-fill-color:#ffffff !important;
}

/* ── Pills ── */
.pill {
    display:inline-flex; align-items:center; gap:5px; padding:3px 10px;
    border-radius:999px; font-size:.68rem; font-weight:700; letter-spacing:.06em; text-transform:uppercase; line-height:1.5;
}
.pill-green { background:rgba(16,185,129,.18); color:#34d399 !important; -webkit-text-fill-color:#34d399 !important; border:1px solid rgba(16,185,129,.3); }
.pill-amber { background:rgba(245,158,11,.18); color:#fbbf24 !important; -webkit-text-fill-color:#fbbf24 !important; border:1px solid rgba(245,158,11,.3); }
.pill-red   { background:rgba(239,68,68,.18);  color:#f87171 !important; -webkit-text-fill-color:#f87171 !important; border:1px solid rgba(239,68,68,.3); }
.pill-blue  { background:rgba(59,130,246,.18); color:#60a5fa !important; -webkit-text-fill-color:#60a5fa !important; border:1px solid rgba(59,130,246,.3); }

/* ── Stock display — bigger integer, vivid color, unchanged background ── */
.stock-display {
    display:inline-flex; flex-direction:column; gap:2px;
    background:#1d2436; border:1px solid #2d384f; border-radius:12px;
    padding:14px 20px; margin:12px 0 18px 0;
}
.stock-display-label {
    font-size:.65rem; font-weight:700; letter-spacing:.14em; text-transform:uppercase;
    color:#7eb3ff !important; -webkit-text-fill-color:#7eb3ff !important;
}
.stock-display-value {
    font-size:2.6rem !important;
    font-weight:800 !important;
    letter-spacing:-0.04em;
    font-family:'Outfit',sans-serif !important;
    line-height:1;
}

/* ── Insight cards ── */
.insight-card { border-radius:12px; padding:16px 18px; display:flex; align-items:flex-start; gap:14px; margin-bottom:18px; }
.insight-card-green { background:rgba(16,185,129,.15); border:1px solid rgba(16,185,129,.35); }
.insight-card-amber { background:rgba(245,158,11,.15);  border:1px solid rgba(245,158,11,.35); }
.insight-emoji { font-size:1.4rem; flex-shrink:0; margin-top:1px; }
.insight-tag  { font-size:.62rem; font-weight:700; letter-spacing:.16em; text-transform:uppercase; margin-bottom:3px; }
.insight-name { font-size:.95rem; font-weight:700; margin-bottom:3px; color:#ffffff !important; -webkit-text-fill-color:#ffffff !important; text-shadow:0 1px 4px rgba(0,0,0,.4); }
.insight-meta { font-size:.76rem; font-weight:500; color:#d1d9e8 !important; -webkit-text-fill-color:#d1d9e8 !important; }

/* ── Health card ── */
.health-card { background:#161c2a; border:1px solid #242d40; border-radius:12px; padding:18px 20px; margin-top:14px; }
.health-title { font-size:.78rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; margin-bottom:10px; color:#7eb3ff !important; -webkit-text-fill-color:#7eb3ff !important; }
.health-bar-bg { background:#242d40; height:6px; border-radius:99px; margin-bottom:8px; overflow:hidden; }
.health-bar-fill { height:100%; border-radius:99px; transition:width .8s ease; }
.health-sub { font-size:.74rem; font-weight:500; color:#8ca0c0 !important; -webkit-text-fill-color:#8ca0c0 !important; }

/* ── Empty state ── */
.empty-state { text-align:center; padding:64px 24px; background:#111620; border:1px solid #242d40; border-radius:24px; }
.empty-title { font-size:1.1rem; font-weight:700; margin-bottom:8px; color:#ffffff !important; -webkit-text-fill-color:#ffffff !important; }
.empty-sub   { font-size:.84rem; color:#8ca0c0 !important; -webkit-text-fill-color:#8ca0c0 !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] { background:#0d1117 !important; border-right:1px solid #242d40 !important; }
[data-testid="stSidebar"] .block-container { padding:1.75rem 1.25rem 2rem !important; }
.sidebar-status { background:#161c2a; border:1px solid #242d40; border-radius:12px; padding:14px 16px; margin-top:6px; }
.sidebar-status-row { display:flex; justify-content:space-between; align-items:center; padding:5px 0; }
.sidebar-status-label { font-size:.8rem; font-weight:500; color:#c0d0e8 !important; -webkit-text-fill-color:#c0d0e8 !important; }
.sidebar-version { font-size:.65rem; margin-top:24px; padding-top:16px; border-top:1px solid #242d40; font-family:'JetBrains Mono',monospace !important; color:#4a5a72 !important; -webkit-text-fill-color:#4a5a72 !important; }

/* ── Form labels ── */
label, .stSelectbox label, .stNumberInput label, .stTextInput label,
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] span, [data-testid="stWidgetLabel"] label,
[class*="stFormLabel"], [class*="stFormLabel"] p,
div[data-testid] label, div[data-testid] label p, div[data-testid] label span {
    color:#c0d0e8 !important; -webkit-text-fill-color:#c0d0e8 !important;
    font-size:.82rem !important; font-weight:600 !important; letter-spacing:.02em !important; background:transparent !important;
}
[data-testid="stSidebarContent"] [data-testid="stWidgetLabel"] p,
[data-testid="stSidebarContent"] label,
[data-testid="stSidebarContent"] label p {
    color:#7c92b8 !important; -webkit-text-fill-color:#7c92b8 !important;
    font-size:.62rem !important; text-transform:uppercase !important; letter-spacing:.14em !important; font-weight:700 !important;
}

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div {
    background:#161c2a !important; border:1px solid #242d40 !important;
    border-radius:8px !important; color:#e2eaf8 !important; font-size:.88rem !important;
}
[data-testid="stSelectbox"] > div > div:focus-within { border-color:#3b82f6 !important; box-shadow:0 0 0 3px rgba(59,130,246,.25) !important; }
[data-testid="stSelectbox"] svg { color:#94a3b8 !important; }
[data-testid="stSelectbox"] span { color:#e2eaf8 !important; -webkit-text-fill-color:#e2eaf8 !important; }

/* ── Number input ── */
[data-testid="stNumberInput"] input {
    background:#161c2a !important; border:1px solid #242d40 !important;
    color:#e2eaf8 !important; -webkit-text-fill-color:#e2eaf8 !important;
    border-radius:8px !important; font-size:.92rem !important;
}
[data-testid="stNumberInput"] input:focus { border-color:#3b82f6 !important; box-shadow:0 0 0 3px rgba(59,130,246,.25) !important; outline:none !important; }
[data-testid="stNumberInput"] button { background:#161c2a !important; border-color:#242d40 !important; color:#94a3b8 !important; -webkit-text-fill-color:#94a3b8 !important; }

/* FIX 3: Hide "Press Enter to apply" tooltip — Streamlit renders it via
   data-testid="InputInstructions" inside the number input wrapper.
   We target every known variant to be version-proof. */
[data-testid="InputInstructions"],
[data-testid="stNumberInput"] [data-testid="InputInstructions"],
[data-testid="stNumberInput"] ~ div[class*="instructions"],
[data-testid="stNumberInput"] div[class*="instructions"],
[data-testid="stNumberInput"] small,
[data-testid="stNumberInput"] span[class*="placeholder"],
[data-testid="stNumberInput"] div[class*="placeholder"] {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
}

/* ── Buttons ── */
.stButton > button {
    background:#3b82f6 !important; color:#ffffff !important; -webkit-text-fill-color:#ffffff !important;
    border:1px solid rgba(59,130,246,.5) !important; border-radius:8px !important;
    font-family:'Outfit',sans-serif !important; font-weight:600 !important;
    font-size:.84rem !important; padding:9px 22px !important;
    transition:all .18s ease !important; box-shadow:0 2px 10px rgba(59,130,246,.25) !important;
}
.stButton > button:hover { background:#2563eb !important; box-shadow:0 4px 18px rgba(59,130,246,.4) !important; transform:translateY(-1px) !important; }

/* ── Tabs ── */
[data-baseweb="tab-list"] {
    background:#161c2a !important; border-radius:8px !important;
    padding:4px !important; border:1px solid #242d40 !important; gap:3px !important; margin-bottom:22px !important;
}
[data-baseweb="tab"] { border-radius:6px !important; font-size:.83rem !important; font-weight:600 !important; padding:8px 20px !important; color:#94a3b8 !important; -webkit-text-fill-color:#94a3b8 !important; }
[aria-selected="true"][data-baseweb="tab"] { background:#3b82f6 !important; color:#ffffff !important; -webkit-text-fill-color:#ffffff !important; box-shadow:0 2px 8px rgba(59,130,246,.3) !important; }
[data-baseweb="tab"] p, [data-baseweb="tab"] span { color:inherit !important; -webkit-text-fill-color:inherit !important; }

/* ── Expander ── */
[data-testid="stExpander"] { background:#111620 !important; border:1px solid #242d40 !important; border-radius:12px !important; }
[data-testid="stExpander"] summary p { color:#e2eaf8 !important; -webkit-text-fill-color:#e2eaf8 !important; font-weight:600 !important; }

/* ── Alerts ── */
[data-testid="stAlert"] { border-radius:8px !important; font-size:.84rem !important; }
.stSuccess > div { color:#ffffff !important; -webkit-text-fill-color:#ffffff !important; }
.stError   > div { color:#ffffff !important; -webkit-text-fill-color:#ffffff !important; }
.stWarning > div { color:#1a1a1a !important; -webkit-text-fill-color:#1a1a1a !important; }

/* ── Markdown / loose text ── */
.stMarkdown p, .stMarkdown li, .stMarkdown span,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span {
    color:#b0c4de !important; -webkit-text-fill-color:#b0c4de !important; font-size:.875rem;
}
.stMarkdown strong,
[data-testid="stMarkdownContainer"] strong { color:#e8f0fc !important; -webkit-text-fill-color:#e8f0fc !important; }
.element-container p, .element-container span { color:#b0c4de !important; }

[data-testid="stSpinner"] p { color:#94a3b8 !important; -webkit-text-fill-color:#94a3b8 !important; }
hr { border-color:#242d40 !important; margin:18px 0 !important; }

/* ══════════════════════════════════════════════
   TABLES
   ══════════════════════════════════════════════ */
[data-testid="stDataFrame"],
[data-testid="stDataEditor"] {
    border-radius: 12px !important;
    border: 1px solid #2d384f !important;
    overflow: hidden !important;
    box-shadow: 0 4px 24px rgba(0,0,0,0.4) !important;
}
[data-testid="stDataFrame"] > div,
[data-testid="stDataEditor"] > div {
    border-radius: 11px !important;
    overflow: hidden !important;
}
[data-testid="stDataFrame"] [data-testid="stElementToolbar"],
[data-testid="stDataEditor"] [data-testid="stElementToolbar"] {
    background: #131a27 !important;
    border-bottom: 1px solid #2d384f !important;
}
[data-testid="stElementToolbar"] button { color: #7eb3ff !important; }
[data-testid="stDataEditor"] input,
[data-testid="stDataEditor"] textarea,
[data-testid="stDataEditor"] [contenteditable] {
    background: #1a2235 !important;
    color: #e2eaf8 !important;
    -webkit-text-fill-color: #e2eaf8 !important;
    border: 1px solid #3b82f6 !important;
    border-radius: 6px !important;
    caret-color: #60a5fa !important;
}
[data-testid="stDataFrame"] ::-webkit-scrollbar,
[data-testid="stDataEditor"] ::-webkit-scrollbar { width: 5px; height: 5px; }
[data-testid="stDataFrame"] ::-webkit-scrollbar-track,
[data-testid="stDataEditor"] ::-webkit-scrollbar-track { background: #1a2235; }
[data-testid="stDataFrame"] ::-webkit-scrollbar-thumb,
[data-testid="stDataEditor"] ::-webkit-scrollbar-thumb { background: #2d384f; border-radius: 99px; }
[data-testid="stDataFrame"] ::-webkit-scrollbar-thumb:hover,
[data-testid="stDataEditor"] ::-webkit-scrollbar-thumb:hover { background: #3b4f6e; }

/* ══════════════════════════════════════════════
   YES/NO DROPDOWN  ─  body-level portal
   ══════════════════════════════════════════════ */
[data-baseweb="popover"],
[data-baseweb="popover"] > div,
[data-baseweb="popover"] > div > div {
    background-color: #1a2235 !important;
    border: 1px solid #2d384f !important;
    border-radius: 8px !important;
}
[data-baseweb="menu"],
[data-baseweb="menu"] > ul,
[role="listbox"] {
    background-color: #1a2235 !important;
    border-color: #2d384f !important;
}
[data-baseweb="menu"] [role="option"],
li[role="option"],
[role="listbox"] [role="option"],
[role="listbox"] > li {
    background:           #1a2235 !important;
    background-color:     #1a2235 !important;
    color:                #dce8f8 !important;
    -webkit-text-fill-color: #dce8f8 !important;
    opacity:              1 !important;
    padding:              9px 14px !important;
    font-size:            .88rem !important;
    font-weight:          500 !important;
    cursor:               pointer !important;
}
[data-baseweb="menu"] [role="option"] *,
li[role="option"] *,
[role="listbox"] [role="option"] *,
[role="listbox"] > li * {
    color:                #dce8f8 !important;
    -webkit-text-fill-color: #dce8f8 !important;
    opacity:              1 !important;
}
[data-baseweb="menu"] [role="option"]:hover,
li[role="option"]:hover,
[role="listbox"] [role="option"]:hover,
[role="listbox"] > li:hover {
    background:           #223050 !important;
    background-color:     #223050 !important;
    color:                #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}
[data-baseweb="menu"] [role="option"]:hover *,
li[role="option"]:hover *,
[role="listbox"] [role="option"]:hover *,
[role="listbox"] > li:hover * {
    color:                #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}
[data-baseweb="menu"] [role="option"][aria-selected="true"],
li[role="option"][aria-selected="true"],
[role="listbox"] [role="option"][aria-selected="true"],
[data-baseweb="menu"] [class*="highlighted"],
[data-baseweb="menu"] [class*="active"] {
    background:           #1a3560 !important;
    background-color:     #1a3560 !important;
    color:                #93c5fd !important;
    -webkit-text-fill-color: #93c5fd !important;
}
[data-baseweb="menu"] [role="option"][aria-selected="true"] *,
li[role="option"][aria-selected="true"] *,
[role="listbox"] [role="option"][aria-selected="true"] *,
[data-baseweb="menu"] [class*="highlighted"] * {
    color:                #93c5fd !important;
    -webkit-text-fill-color: #93c5fd !important;
}

/* Email trigger buttons */
.email-btn-wrap .stButton > button {
    width:100% !important; background:#161c2a !important;
    color:#e2eaf8 !important; -webkit-text-fill-color:#e2eaf8 !important;
    border:1px solid #2d384f !important; box-shadow:none !important;
}
.email-btn-wrap .stButton > button:hover {
    background:#1d2842 !important; border-color:#3b82f6 !important;
    box-shadow:0 2px 12px rgba(59,130,246,.25) !important;
}
</style>
""", unsafe_allow_html=True)




# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def topnav(low_stock_count=0):
    pill_class = "pill-red" if low_stock_count > 0 else "pill-green"
    alert_label = f"&#9888; {low_stock_count} Low Stock" if low_stock_count > 0 else "&#9679; All Healthy"
    st.markdown(f"""
    <div class="topnav">
        <div class="brand">
            <div class="brand-icon">&#128230;</div>
            <div>
                <div class="brand-name">StockSense</div>
                <div class="brand-tagline">Inventory Intelligence</div>
            </div>
        </div>
        <div class="topnav-right">
            <span class="nav-badge"><span class="dot"></span>Live</span>
            <span class="pill {pill_class}">{alert_label}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def page_header(title, subtitle=""):
    sub_html = (
        f'<div style="font-size:.875rem;font-weight:400;margin:5px 0 0 0;'
        f'color:#8ca0c0;-webkit-text-fill-color:#8ca0c0">{subtitle}</div>'
    ) if subtitle else ""
    st.markdown(
        f'<div style="margin-bottom:28px">'
        f'<div style="font-size:1.7rem;font-weight:800;letter-spacing:-0.04em;'
        f'line-height:1.1;margin:0;color:#ffffff;-webkit-text-fill-color:#ffffff;'
        f'font-family:Outfit,sans-serif">{title}</div>{sub_html}</div>',
        unsafe_allow_html=True,
    )


def section_label(text):
    st.markdown(
        f'<div style="font-size:.68rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase;'
        f'color:#7eb3ff;-webkit-text-fill-color:#7eb3ff;margin-bottom:14px;'
        f'display:flex;align-items:center;gap:8px">{text}'
        f'<span style="flex:1;height:1px;background:#242d40;display:inline-block;margin-left:8px"></span></div>',
        unsafe_allow_html=True,
    )


def kpi_row(items):
    cols = st.columns(len(items))
    for col, (label, value, icon, color, icon_bg) in zip(cols, items):
        with col:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-card-accent" style="background:{color}"></div>
                <div class="kpi-top">
                    <div class="kpi-icon-wrap" style="background:{icon_bg}">{icon}</div>
                </div>
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
            </div>
            """, unsafe_allow_html=True)


def plotly_theme(height=400):
    return dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Outfit, sans-serif", color="#94a3b8", size=12),
        margin=dict(l=20, r=20, t=16, b=56), height=height,
        xaxis=dict(gridcolor="rgba(36,45,64,.8)", linecolor="rgba(36,45,64,.8)",
                   tickfont=dict(color="#64748b", size=11), title_font=dict(color="#94a3b8", size=12),
                   showgrid=True, zeroline=False),
        yaxis=dict(gridcolor="rgba(36,45,64,.8)", linecolor="rgba(36,45,64,.8)",
                   tickfont=dict(color="#64748b", size=11), title_font=dict(color="#94a3b8", size=12),
                   showgrid=True, zeroline=False),
        legend=dict(font=dict(color="#94a3b8", size=12), bgcolor="rgba(0,0,0,0)", bordercolor="rgba(36,45,64,0)"),
    )


# ─────────────────────────────────────────────
# AUTO IMPORT CSV
# ─────────────────────────────────────────────
try:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(1) as cnt FROM products")
    cnt = cur.fetchone()["cnt"]
    conn.close()
    if cnt == 0:
        csv_path = os.path.join("data", "products.csv")
        if os.path.exists(csv_path):
            load_products_from_csv.load_products()
except Exception as e:
    print("Auto import failed:", e)


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
products_all = get_all_products()
total_count = len(products_all) if products_all else 0
low_count_sidebar = sum(
    1 for p in products_all
    if (p.get("current_stock") or 0) <= (p.get("min_stock") or 0)
) if products_all else 0

with st.sidebar:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;padding-bottom:22px;
                border-bottom:1px solid #242d40;margin-bottom:4px">
        <div style="width:34px;height:34px;background:linear-gradient(135deg,#3b82f6,#8b5cf6);
                    border-radius:9px;display:flex;align-items:center;justify-content:center;
                    font-size:16px;flex-shrink:0">&#128230;</div>
        <div style="font-size:1.05rem;font-weight:800;letter-spacing:-0.03em;
                    background:linear-gradient(90deg,#60a5fa,#a78bfa);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                    background-clip:text">StockSense</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="font-size:.62rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:#6b7fa0;-webkit-text-fill-color:#6b7fa0;margin:20px 0 8px 0">Navigation</div>', unsafe_allow_html=True)
    menu = st.selectbox(
        "NAVIGATE",
        ["🏠  Home", "📋  Products", "🔄  Update Stock", "🛒  Record Sale", "📊  Dashboard"],
        label_visibility="collapsed",
    )


# ─────────────────────────────────────────────
# ROUTE
# ─────────────────────────────────────────────
active = menu.split("  ")[-1]
topnav(low_count_sidebar)


# ═══════════════════════════════════════════════
# HOME
# ═══════════════════════════════════════════════
if active == "Home":
    page_header("Overview", "Real-time inventory health and platform activity")
    from modules.alerts import send_daily_essential_forecast, send_non_essential_forecast

    products = get_all_products()
    df = pd.DataFrame(products) if products else pd.DataFrame()

    total_products  = len(df) if not df.empty else 0
    total_stock     = int(df["current_stock"].fillna(0).sum()) if (not df.empty and "current_stock" in df.columns) else 0
    low_ct          = int((df["current_stock"].fillna(0) <= df["min_stock"].fillna(0)).sum()) if (not df.empty and "min_stock" in df.columns) else 0
    essential_count = int(df["is_essential"].fillna(0).sum()) if (not df.empty and "is_essential" in df.columns) else 0

    kpi_row([
        ("Total Products",  total_products,     "🗂",  "linear-gradient(135deg,#3b82f6,#6366f1)", "rgba(59,130,246,.15)"),
        ("Units in Stock",  f"{total_stock:,}", "📦",  "linear-gradient(135deg,#06b6d4,#3b82f6)", "rgba(6,182,212,.15)"),
        ("Low Stock",       low_ct,             "⚠",   "linear-gradient(135deg,#ef4444,#f97316)", "rgba(239,68,68,.15)"),
        ("Essential Items", essential_count,    "⭐",  "linear-gradient(135deg,#f59e0b,#ef4444)", "rgba(245,158,11,.15)"),
    ])

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    col_left, col_right = st.columns([3, 1], gap="large")

    with col_left:
        section_label("Product Inventory")
        if not df.empty:
            display_df = df.drop(columns=["min_stock", "early_warning_stock", "is_essential"], errors="ignore").reset_index(drop=True)
            st.dataframe(display_df, use_container_width=True, height=420)
        else:
            st.markdown('<div class="empty-state"><div style="font-size:3rem;margin-bottom:16px">📭</div><div class="empty-title">No products found</div><div class="empty-sub">Import a CSV to get started</div></div>', unsafe_allow_html=True)

    with col_right:
        section_label("Email Triggers")
        st.markdown('<div class="card"><div class="card-title">Forecast Emails</div><div class="card-body">Manually trigger alert emails for testing the notification system.</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="email-btn-wrap">', unsafe_allow_html=True)

        if st.button("📧  Non-Essential Forecast", use_container_width=True):
            with st.spinner("Sending..."):
                send_non_essential_forecast()
            st.success("Email sent!")
        st.markdown("</div>", unsafe_allow_html=True)

        if not df.empty and "current_stock" in df.columns and "min_stock" in df.columns:
            healthy = total_products - low_ct
            pct = int((healthy / total_products) * 100) if total_products else 0
            h_color = "#10b981" if pct >= 75 else "#f59e0b" if pct >= 40 else "#ef4444"
            st.markdown(f"""
            <div class="health-card">
                <div class="health-title">Stock Health</div>
                <div style="font-size:2rem;font-weight:800;letter-spacing:-.04em;line-height:1;margin-bottom:8px;
                            color:{h_color};-webkit-text-fill-color:{h_color};font-family:Outfit,sans-serif">{pct}%</div>
                <div class="health-bar-bg"><div class="health-bar-fill" style="width:{pct}%;background:{h_color}"></div></div>
                <div class="health-sub">{healthy} of {total_products} products healthy</div>
            </div>
            """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════
# PRODUCTS
# ═══════════════════════════════════════════════
elif active == "Products":
    page_header("Products", "Manage your product catalog, flags, and stock thresholds")

    products = get_all_products()
    df = pd.DataFrame(products) if products else pd.DataFrame()
    tab1, tab2 = st.tabs(["  📑  Product List  ", "  ⚙️  Thresholds  "])

    with tab1:
        if not df.empty:
            df = df.reset_index(drop=True)
            if "price" in df.columns:
                df = df.drop(columns=["price"])
            # FIX 1: Map values cleanly — use only "Yes" / "No" (no None/blank option).
            # fillna("No") ensures every row has a value so SelectboxColumn never
            # auto-inserts a blank placeholder at the top of the list.
            df["is_essential"] = df["is_essential"].map({1: "Yes", 0: "No"}).fillna("No")
            st.markdown('<p style="color:#9db0cc;font-size:.84rem;margin-bottom:14px">Edit the <strong style="color:#e2eaf8">Is Essential</strong> column inline, then click Save Changes.</p>', unsafe_allow_html=True)
            edited_df = st.data_editor(
                df,
                column_config={
                    "is_essential": st.column_config.SelectboxColumn(
                        "Is Essential",
                        options=["Yes", "No"],   # FIX 1: exactly two options, no blank/None
                        required=True,            # FIX 1: required=True removes the blank row Streamlit adds by default
                    )
                },
                hide_index=True, use_container_width=True, height=440,
            )
            col_btn, _ = st.columns([1, 5])
            with col_btn:
                if st.button("💾  Save Changes"):
                    conn = get_connection(); cur = conn.cursor()
                    for _, row in edited_df.iterrows():
                        pid = int(row["product_id"])
                        val = 1 if row["is_essential"] == "Yes" else 0
                        cur.execute("UPDATE products SET is_essential=? WHERE product_id=?", (val, pid))
                        if val == 1:
                            cur.execute("INSERT OR IGNORE INTO essential_products(product_id) VALUES(?)", (pid,))
                        else:
                            cur.execute("DELETE FROM essential_products WHERE product_id=?", (pid,))
                    conn.commit(); conn.close()
                    st.success("Changes saved successfully")
        else:
            st.markdown('<div class="empty-state"><div style="font-size:3rem;margin-bottom:16px">📭</div><div class="empty-title">No products available</div></div>', unsafe_allow_html=True)

    with tab2:
        section_label("Stock Thresholds")
        st.markdown('<p style="color:#9db0cc;font-size:.84rem;margin-bottom:20px">Set minimum and early-warning stock levels per product.</p>', unsafe_allow_html=True)
        product_map = {p["name"]: p["product_id"] for p in products} if products else {}
        if not product_map:
            st.info("No products available.")
        else:
            selected_product = st.selectbox("Select Product", ["— select a product —"] + list(product_map.keys()))
            if selected_product and selected_product != "— select a product —":
                pid = product_map[selected_product]
                st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
                col1, col2 = st.columns(2, gap="medium")
                with col1:
                    min_stock = st.number_input("🔴  Min Stock", min_value=0, value=0, help="Reorder alert fires at or below this level")
                with col2:
                    early_warning = st.number_input("🟡  Early Warning Stock", min_value=0, value=0, help="Must exceed Min Stock")
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                col_btn2, _ = st.columns([1, 5])
                with col_btn2:
                    if st.button("💾  Save Thresholds"):
                        if early_warning <= min_stock:
                            st.error("Early Warning must be greater than Min Stock")
                        else:
                            ok, _ = set_min_stock(pid, int(min_stock), int(early_warning))
                            # FIX 2: Always show a clean static message — never dump the
                            # raw return value from set_min_stock() which can be a long
                            # verbose string (Delta proto / Streamlit internals).
                            if ok:
                                st.success("Thresholds updated successfully")
                            else:
                                st.error("Failed to update thresholds. Please try again.")


# ═══════════════════════════════════════════════
# UPDATE STOCK
# ═══════════════════════════════════════════════
elif active == "Update Stock":
    page_header("Update Stock", "Add or manually adjust inventory units")
    products = get_all_products()
    product_map = {p["name"]: p["product_id"] for p in products} if products else {}
    col_form, col_info = st.columns([2, 1], gap="large")

    with col_form:
        st.markdown('<div class="card"><div class="card-title">Stock Adjustment</div><div class="card-body">Add or remove units from inventory.<br><strong style="color:#e2eaf8">Positive</strong> = restock &nbsp;&middot;&nbsp; <strong style="color:#e2eaf8">Negative</strong> = correction (damage, shrinkage, etc.)</div></div>', unsafe_allow_html=True)
        if not product_map:
            st.info("No products available.")
        else:
            selected = st.selectbox("Select Product", ["— select —"] + list(product_map.keys()))
            if selected and selected != "— select —":
                pid = product_map[selected]
                product_data = next((p for p in products if p["product_id"] == pid), None)
                current = (product_data.get("current_stock") or 0) if product_data else 0
                st.markdown(f'<div class="stock-display"><span class="stock-display-label">Current Stock</span><span class="stock-display-value" style="color:#38bdf8 !important;-webkit-text-fill-color:#38bdf8 !important;text-shadow:0 0 16px rgba(56,189,248,0.4)">{current}</span></div>', unsafe_allow_html=True)
            qty = st.number_input("Quantity to Add / Remove", value=0, help="Positive to add, negative to remove")
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            if st.button("🔄  Apply Adjustment"):
                if selected and selected != "— select —":
                    pid = product_map[selected]; res = update_stock(pid, int(qty))
                    if res == "NEGATIVE_STOCK_ERROR": st.error("Stock cannot go below zero")
                    elif res == "MAX_STOCK_LIMIT": st.error("Stock cannot exceed 9,999 units")
                    else: st.success(f"Stock updated! New level: **{res}** units"); st.balloons()
                else: st.warning("Please select a product first")

    with col_info:
        st.markdown('<div class="card"><div class="card-title">💡 How it works</div><div class="card-body">1. Select a product<br>2. Enter the adjustment quantity<br>3. Positive = add stock (restock)<br>4. Negative = remove stock (correction)<br>5. Max cap is 9,999 units</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="card"><div class="card-title">⚠️ Use negatives for</div><div class="card-body">&bull; Damaged or expired goods<br>&bull; Shrinkage or theft<br>&bull; Stock count discrepancies<br>&bull; Returns to supplier</div></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════
# RECORD SALE
# ═══════════════════════════════════════════════
elif active == "Record Sale":
    page_header("Record Sale", "Log completed sales and deduct from live inventory")
    products = get_all_products()
    product_map = {p["name"]: p["product_id"] for p in products} if products else {}
    col_form, col_info = st.columns([2, 1], gap="large")

    with col_form:
        st.markdown('<div class="card"><div class="card-title">Log a Sale</div><div class="card-body">Record a completed sale to deduct stock and update forecasting data.</div></div>', unsafe_allow_html=True)
        if not product_map:
            st.info("No products available.")
        else:
            selected = st.selectbox("Select Product", ["— select —"] + list(product_map.keys()))
            if selected and selected != "— select —":
                pid = product_map[selected]
                product_data = next((p for p in products if p["product_id"] == pid), None)
                current = (product_data.get("current_stock") or 0) if product_data else 0
                st.markdown(f'<div class="stock-display"><span class="stock-display-label">Available Stock</span><span class="stock-display-value" style="color:#fb923c !important;-webkit-text-fill-color:#fb923c !important;text-shadow:0 0 16px rgba(251,146,60,0.4)">{current}</span></div>', unsafe_allow_html=True)
            qty = st.number_input("Quantity Sold", min_value=1, value=1)
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            if st.button("🛒  Record Sale"):
                if selected and selected != "— select —":
                    pid = product_map[selected]; res = adjust_stock_by_sale(pid, int(qty))
                    if res == "NEGATIVE_STOCK_ERROR": st.error("Sale would cause negative stock — check current levels")
                    else: st.success(f"Sale recorded! Remaining stock: **{res}** units")
                else: st.warning("Please select a product first")

    with col_info:
        st.markdown('<div class="card"><div class="card-title">📌 What happens</div><div class="card-body">&bull; Deduct quantity from current stock<br>&bull; Log the transaction for analytics<br>&bull; Trigger low-stock alerts if needed<br>&bull; Update demand forecast data</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="card"><div class="card-title">🔔 Low Stock Alerts</div><div class="card-body">If stock drops to or below the minimum threshold after recording a sale, an alert email is triggered automatically.</div></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════
elif active == "Dashboard":
    page_header("Sales Dashboard", "Analytics, trends and product performance insights")

    import plotly.express as px
    import plotly.graph_objects as go
    from modules.dashboard import (
        get_sales_data, get_daily_sales, get_weekly_sales, get_monthly_sales,
        get_top_products, get_total_revenue, get_slow_products
    )

    df = get_sales_data()
    if df is None or df.empty:
        st.markdown('<div class="empty-state"><div style="font-size:3rem;margin-bottom:16px">📭</div><div class="empty-title">No Sales Data Yet</div><div class="empty-sub">Record some sales to see dashboard analytics here.</div></div>', unsafe_allow_html=True)
    else:
        daily   = get_daily_sales(df)
        weekly  = get_weekly_sales(df)
        monthly = get_monthly_sales(df)
        top_df  = get_top_products()
        slow_df = get_slow_products()
        revenue = get_total_revenue() or 0

        today_sales = int(daily.iloc[-1])   if (daily   is not None and len(daily)   > 0) else 0
        week_sales  = int(weekly.iloc[-1])  if (weekly  is not None and len(weekly)  > 0) else 0
        month_sales = int(monthly.iloc[-1]) if (monthly is not None and len(monthly) > 0) else 0

        kpi_row([
            ("Today's Sales", today_sales,           "📅", "linear-gradient(135deg,#3b82f6,#6366f1)", "rgba(59,130,246,.15)"),
            ("This Week",     week_sales,             "📆", "linear-gradient(135deg,#06b6d4,#3b82f6)", "rgba(6,182,212,.15)"),
            ("This Month",    month_sales,            "🗓", "linear-gradient(135deg,#8b5cf6,#6366f1)", "rgba(139,92,246,.15)"),
            ("Total Revenue", f"₹{revenue:,.0f}",    "💰", "linear-gradient(135deg,#10b981,#06b6d4)", "rgba(16,185,129,.15)"),
        ])
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

        ins_cols = st.columns(2, gap="medium")
        if top_df is not None and not top_df.empty:
            with ins_cols[0]:
                st.markdown(f'<div class="insight-card insight-card-green"><div class="insight-emoji">🔥</div><div><div class="insight-tag" style="color:#34d399;-webkit-text-fill-color:#34d399">Best Seller</div><div class="insight-name">{top_df.iloc[0]["name"]}</div><div class="insight-meta">{int(top_df.iloc[0]["total_sales"])} units sold</div></div></div>', unsafe_allow_html=True)
        if slow_df is not None and not slow_df.empty:
            with ins_cols[1]:
                st.markdown(f'<div class="insight-card insight-card-amber"><div class="insight-emoji">🐢</div><div><div class="insight-tag" style="color:#fbbf24;-webkit-text-fill-color:#fbbf24">Slow Mover</div><div class="insight-name">{slow_df.iloc[0]["name"]}</div><div class="insight-meta">Needs attention</div></div></div>', unsafe_allow_html=True)

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

        # Sales Trend
        st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
        th, tc = st.columns([3, 1])
        with th: st.markdown('<div class="chart-title">📈 Sales Trend</div>', unsafe_allow_html=True)
        with tc: view = st.selectbox("Period", ["Daily", "Weekly", "Monthly"], label_visibility="collapsed")
        data = (daily if view == "Daily" else weekly if view == "Weekly" else monthly).reset_index()
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=data["sale_date"], y=data["sale_qty"], mode="lines+markers",
            line=dict(color="#3b82f6", width=2.5, shape="spline"),
            marker=dict(size=6, color="#6366f1", line=dict(color="#3b82f6", width=2)),
            fill="tozeroy", fillcolor="rgba(59,130,246,.07)", name="Units Sold",
        ))
        lyt = plotly_theme(height=360)
        lyt["xaxis"]["title"] = "Date"; lyt["yaxis"]["title"] = "Units"; lyt["margin"] = dict(l=52, r=16, t=8, b=56)
        fig_line.update_layout(**lyt)
        st.plotly_chart(fig_line, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        PALETTE = ["#3b82f6","#8b5cf6","#10b981","#f59e0b","#ef4444","#06b6d4","#a855f7","#ec4899"]
        col_bar, col_pie = st.columns(2, gap="large")

        with col_bar:
            st.markdown('<div class="chart-panel"><div class="chart-title">🏆 Top Products by Sales</div>', unsafe_allow_html=True)
            if top_df is not None and not top_df.empty:
                fig_bar = go.Figure()
                for i, row in top_df.iterrows():
                    fig_bar.add_trace(go.Bar(
                        x=[row["name"]], y=[row["total_sales"]], marker_color=PALETTE[i % len(PALETTE)],
                        marker_line_color="rgba(0,0,0,0)", name=row["name"], showlegend=False,
                        text=[str(int(row["total_sales"]))], textposition="outside", textfont=dict(color="#94a3b8", size=11),
                    ))
                lb = plotly_theme(height=400)
                lb["xaxis"]["tickangle"] = -28; lb["xaxis"]["tickfont"] = dict(color="#64748b", size=10)
                lb["margin"] = dict(l=48, r=16, t=16, b=100); lb["bargap"] = 0.35
                fig_bar.update_layout(**lb)
                st.plotly_chart(fig_bar, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_pie:
            st.markdown('<div class="chart-panel"><div class="chart-title">📐 Sales Share</div>', unsafe_allow_html=True)
            if top_df is not None and not top_df.empty:
                fig_pie = px.pie(top_df, names="name", values="total_sales", hole=0.52, color_discrete_sequence=PALETTE)
                fig_pie.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Outfit, sans-serif", color="#94a3b8", size=12),
                    margin=dict(l=10, r=10, t=10, b=10), height=400,
                    legend=dict(font=dict(color="#94a3b8", size=11), bgcolor="rgba(0,0,0,0)", orientation="v", x=1.02, y=0.5, xanchor="left"),
                )
                fig_pie.update_traces(textinfo="none",
                    hovertemplate="<b>%{label}</b><br>%{value} units (%{percent})<extra></extra>",
                    marker=dict(line=dict(color="#080b10", width=2)))
                st.plotly_chart(fig_pie, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        if slow_df is not None and not slow_df.empty:
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            st.markdown('<div class="chart-panel"><div class="chart-title">🐌 Slow-Moving Products <span class="pill pill-amber" style="margin-left:8px;font-size:.65rem">Needs Attention</span></div>', unsafe_allow_html=True)
            st.dataframe(slow_df, use_container_width=True, height=260)
            st.markdown("</div>", unsafe_allow_html=True)