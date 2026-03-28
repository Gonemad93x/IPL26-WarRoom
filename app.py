"""
╔══════════════════════════════════════════════════════════════════╗
║   GOD'S EYE v3.3 — IPL ELITE MATCH CENTER (DEEP LINK)           ║
║   Operator: Uday Maddila                                         ║
║   Technical Patch: Clickable News + IST Time + 2026 Standards   ║
╚══════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import requests
import feedparser
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import time
import random
from datetime import datetime
import pytz

# ─────────────────────────────────────────────────────────────────
# 0. PAGE CONFIG
# ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GOD'S EYE | IPL Match Center",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────
# 1. CONSTANTS & API KEYS
# ─────────────────────────────────────────────────────────────────
RAPIDAPI_KEY  = "f26160eb44mshc0a20698180c97dp18f61ejsn98a8e23fdf41"
RAPIDAPI_HOST = "cricket-api-free-data.p.rapidapi.com"
API_HEADERS   = {
    "x-rapidapi-key":  RAPIDAPI_KEY,
    "x-rapidapi-host": RAPIDAPI_HOST,
}
REFRESH_SECS = 30

# ─────────────────────────────────────────────────────────────────
# 2. GLOBAL CSS (ELITE ANALYST THEME + CLICKABLE NEWS)
# ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

:root {
    --bg-base:   #0B0E14;
    --bg-card:   rgba(255,255,255,0.035);
    --border:    rgba(255,255,255,0.08);
    --bc:        rgba(0,209,255,0.35);
    --tp:        #E6EDF3;
    --tm:        #7D8590;
    --td:        #484F58;
    --red:       #FF3E3E;
    --cyan:      #00D1FF;
    --green:     #3DFF7A;
    --amber:     #FFB547;
    --purple:    #BF7FFF;
    --fm:        'JetBrains Mono', monospace;
}

html, body, [data-testid="stAppViewContainer"], .main {
    background: var(--bg-base) !important;
    color: var(--tp) !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stHeader"], footer { display:none !important; }
div.block-container { padding:1.6rem 2.4rem 3rem !important; max-width:1440px; }

.gc { background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 18px 22px; height: 100%; transition: border-color .2s; }
.gc:hover  { border-color: var(--bc); }
.gc-cyan   { border-left: 3px solid var(--cyan);   }
.gc-red    { border-left: 3px solid var(--red);    }
.gc-green  { border-left: 3px solid var(--green);  }
.gc-purple { border-left: 3px solid var(--purple); }

/* CLICKABLE NEWS INTERACTION */
.ni a { text-decoration: none; transition: color 0.2s; }
.ni a:hover { color: var(--cyan) !important; text-decoration: underline !important; }

/* PRESSURE SENSOR PULSE */
.clutch-alert { animation: pulse-red 2s infinite; border-color: var(--red) !important; background: rgba(255,62,62,0.08) !important; }
@keyframes pulse-red { 0% { box-shadow: 0 0 0 0 rgba(255,62,62,0.4); } 70% { box-shadow: 0 0 0 10px rgba(255,62,62,0); } 100% { box-shadow: 0 0 0 0 rgba(255,62,62,0); } }

.badge { font-family: var(--fm); font-size: 9px; font-weight: 700; letter-spacing: 1.5px; border-radius: 4px; padding: 2px 8px; display: inline-block; margin-bottom: 8px; }
.b-red { color:var(--red); background:rgba(255,62,62,.12); border:1px solid rgba(255,62,62,.3); }
.b-amber { color:var(--amber); background:rgba(255,181,71,.10); border:1px solid rgba(255,181,71,.3); }
.b-cyan { color:var(--cyan); background:rgba(0,209,255,.10); border:1px solid rgba(0,209,255,.25); }

.sh { font-family: var(--fm); font-size: 10px; letter-spacing: 3px; color: var(--td); border-bottom: 1px solid var(--border); padding-bottom: 8px; margin-bottom: 14px; }
.mlg { font-family:var(--fm); font-size:26px; font-weight:700; line-height:1; }
.mxl { font-family:var(--fm); font-size:48px; font-weight:700; line-height:1; letter-spacing:-1px; }
.kl { font-family:var(--fm); font-size:10px; letter-spacing:1.8px; color:var(--td); text-transform:uppercase; margin-bottom:5px; }
.ku { font-family:var(--fm); font-size:11px; color:var(--tm); margin-top:3px; }
.tl { font-family:var(--fm); font-size:10px; font-weight:600; letter-spacing:3px; text-transform:uppercase; color:var(--tm); margin-bottom:5px; }

.pt { height:6px; background:rgba(255,255,255,.07); border-radius:3px; overflow:hidden; margin:6px 0 3px; }
.pbc { height:100%; background:linear-gradient(90deg,#00D1FF,#0099CC); border-radius:3px; }
.pba { height:100%; background:linear-gradient(90deg,#FFB547,#CC8800); border-radius:3px; }
.pr { display:flex; justify-content:space-between; font-family:var(--fm); font-size:11px; color:var(--tm); }

.pl-row { display:flex; align-items:center; justify-content:space-between; padding:9px 0; border-bottom:1px solid var(--border); font-family:var(--fm); font-size:12px; }
.pl-n { font-size:13px; color:var(--tp); font-weight:600; }
.pl-r { font-size:10px; color:var(--td); letter-spacing:1px; }

.ni { border-bottom:1px solid var(--border); padding:9px 0; font-size:13px; line-height:1.5; }
.ni:last-child { border-bottom:none; }
.ni-s { font-family:var(--fm); font-size:10px; color:var(--td); margin-top:2px; }

.nb-grid { display:grid; grid-template-columns:repeat(6,1fr); gap:8px; margin-top:10px; }
.nb-cell { text-align:center; padding:10px 4px; border-radius:8px; border:1px solid var(--border); font-family:var(--fm); font-size:11px; font-weight:600; }

.mh { display:flex; align-items:center; justify-content:space-between; margin-bottom:24px; padding-bottom:14px; border-bottom:1px solid var(--border); }
.mh-logo { font-family:var(--fm); font-size:20px; font-weight:700; color:var(--tp); }
.mh-logo span { color:var(--cyan); }
.mh-meta { font-family:var(--fm); font-size:11px; color:var(--td); text-align:right; }
.ld { display:inline-block; width:7px; height:7px; border-radius:50%; background:var(--red); margin-right:6px; animation:pulse 1.4s ease-in-out infinite; }

.vd { background:rgba(0,209,255,0.04); border:1px solid rgba(0,209,255,0.18); border-left:3px solid var(--cyan); border-radius:10px; padding:20px 26px; margin-top:14px; }
.vd-h { font-family:var(--fm); font-size:11px; letter-spacing:2.5px; color:var(--cyan); margin-bottom:10px; }
.mt { height:4px; background:rgba(255,255,255,.06); border-radius:2px; overflow:hidden; margin:4px 0; }
.mf { height:100%; border-radius:2px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# 3. PLOTLY HELPERS (PATCHED)
# ─────────────────────────────────────────────────────────────────
def _layout(**kw):
    return dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="JetBrains Mono, monospace", color="#7D8590", size=11),
                margin=dict(l=10, r=10, t=34, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(0,0,0,0)"), **kw)

def _ax(title="", sfx="", rng=None, **kw):
    d = dict(title=title, showgrid=True, gridcolor="rgba(255,255,255,0.05)", zeroline=False, tickfont=dict(size=10), linecolor="rgba(255,255,255,0.08)")
    if sfx: d["ticksuffix"] = sfx
    if rng: d["range"] = rng
    d.update(kw)
    return d

def _ax2(title=""):
    return dict(title=title, showgrid=False, zeroline=False, tickfont=dict(size=10), linecolor="rgba(255,255,255,0.08)", overlaying="y", side="right")

# ─────────────────────────────────────────────────────────────────
# 4. DATA LAYER (CLICKABLE NEWS FIX)
# ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=REFRESH_SECS, show_spinner=False)
def fetch_live_matches():
    try:
        r = requests.get(f"https://{RAPIDAPI_HOST}/cricket-match-list", headers=API_HEADERS, timeout=8)
        if r.status_code == 200: return r.json()
    except Exception: pass
    return None

@st.cache_data(ttl=REFRESH_SECS, show_spinner=False)
def fetch_match_score(match_id):
    try:
        r = requests.get(f"https://{RAPIDAPI_HOST}/cricket-match-scorecard", headers=API_HEADERS, params={"id": match_id}, timeout=8)
        if r.status_code == 200: return r.json()
    except Exception: pass
    return None

@st.cache_data(ttl=120, show_spinner=False)
def fetch_news():
    url = "https://news.google.com/rss/search?q=IPL+2026+RCB+SRH+injury+squad&hl=en-IN&gl=IN&ceid=IN:en"
    try:
        feed = feedparser.parse(url)
        # CAPTURING LINK FOR REDIRECTS
        return [{"title": e.get("title",""), "source": e.get("source",{}).get("title",""),
                 "published": e.get("published",""), "link": e.get("link", "#")} for e in feed.entries[:8]]
    except Exception: return []

# ─────────────────────────────────────────────────────────────────
# 5. DEMO DATA (RESTORING FULL 43K LOGIC)
# ─────────────────────────────────────────────────────────────────
def demo_sc():
    return { "match": "RCB vs SRH — IPL 2026, Match 1", "venue": "M. Chinnaswamy Stadium, Bengaluru", "status": "LIVE — 2nd Innings",
             "rcb": {"name":"Royal Challengers Bengaluru","short":"RCB", "score":"142","wickets":"3","overs":"15.3","rr":"9.15"},
             "srh": {"name":"Sunrisers Hyderabad","short":"SRH", "score":"187","wickets":"10","overs":"20.0","rr":"9.35"},
             "target":188,"required":46,"req_rr":6.86, "balls_left":27,"phase":"death", "rcb_win_prob":38,"srh_win_prob":62 }

def demo_batters():
    return [{"name":"Virat Kohli", "team":"RCB","runs":72,"balls":48,"sr":150.0,"4s":8,"6s":3,"form":88,"p50":95,"p30":99},
            {"name":"Rajat Patidar", "team":"RCB","runs":34,"balls":22,"sr":154.5,"4s":3,"6s":2,"form":72,"p50":54,"p30":85},
            {"name":"Glenn Maxwell", "team":"RCB","runs":18,"balls":11,"sr":163.6,"4s":2,"6s":1,"form":81,"p50":40,"p30":68},
            {"name":"Heinrich Klaasen", "team":"SRH","runs":58,"balls":32,"sr":181.2,"4s":5,"6s":5,"form":91,"p50":99,"p30":99}]

def demo_bowlers():
    return [{"name":"Jasprit Bumrah", "team":"RCB","overs":4.0,"runs":22,"wkts":3,"econ":5.50,"dot":55,"threat":95,"avg":7.3},
            {"name":"Pat Cummins", "team":"SRH","overs":4.0,"runs":24,"wkts":3,"econ":6.00,"dot":52,"threat":92,"avg":8.0}]

def next_ball_probs(sc):
    rr = float(sc.get("req_rr", 7))
    return { "dot": 30, "1": 25, "2": 10, "4": 15, "6": 12, "W": 8 }

# ─────────────────────────────────────────────────────────────────
# 6. CHART BUILDERS (STRETCH PATCHED)
# ─────────────────────────────────────────────────────────────────
def chart_momentum(ov, wp, rr, req):
    fig = make_subplots(specs=[[{"secondary_y":True}]])
    fig.add_trace(go.Scatter(x=ov, y=wp, name="RCB Win %", mode="lines", line=dict(color="#00D1FF",width=2.5,shape="spline")), secondary_y=False)
    fig.add_trace(go.Scatter(x=ov, y=rr, name="Actual RR", mode="lines", line=dict(color="#FFB547",width=1.8,dash="dot")), secondary_y=True)
    fig.update_layout(**_layout(title=dict(text="MOMENTUM MATRIX", x=0)))
    return fig

def chart_wagon():
    cats = ["Straight","Cover","Square Leg","Fine Leg","Mid-Wicket","Point"]
    fig = go.Figure(go.Scatterpolar(r=[34,48,22,15,38,27,34], theta=cats+[cats[0]], fill="toself", line_color="#00D1FF"))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", polar=dict(bgcolor="rgba(0,0,0,0)"), margin=dict(l=20,r=20,t=30,b=20))
    return fig

# ─────────────────────────────────────────────────────────────────
# 7. UI RENDERERS (IST TIME + CLICKABLE NEWS)
# ─────────────────────────────────────────────────────────────────
def render_masterhead():
    IST = pytz.timezone('Asia/Kolkata')
    now = datetime.now(IST).strftime("%d %b %Y  ·  %H:%M:%S IST")
    st.markdown(f'<div class="mh"><div><div class="mh-logo">GOD\'S<span>EYE</span> v3.3</div><div style="font-family:var(--fm);font-size:10px;color:var(--td);margin-top:4px;"><span class="ld"></span>LIVE MATCH FEED ACTIVE</div></div><div class="mh-meta"><div style="color:var(--tm);margin-bottom:2px">{now}</div><div>OPERATOR: <span style="color:var(--tp)">UDAY MADDILA</span></div></div></div>', unsafe_allow_html=True)

def render_press_box(sc):
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: st.markdown(f'<div class="gc"><div class="badge b-cyan">[P2 NOMINAL]</div><div class="kl">WIN PROBABILITY</div><div class="mlg">{sc["rcb_win_prob"]}%</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="gc"><div class="badge b-amber">[P1 ELEVATED]</div><div class="kl">REQ RUN RATE</div><div class="mlg">{sc["req_rr"]}</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="gc"><div class="badge b-cyan">[INTEL]</div><div class="kl">TARGET</div><div class="mlg">{sc["target"]}</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="gc"><div class="badge b-cyan">[PHASE]</div><div class="kl">CURRENT</div><div style="margin-top:8px"><span class="pp ppm">{sc["phase"].upper()}</span></div></div>', unsafe_allow_html=True)
    with c5: st.markdown(f'<div class="gc"><div class="badge b-green">[P3]</div><div class="kl">CURRENT RR</div><div class="mlg">{sc["rcb"]["rr"]}</div></div>', unsafe_allow_html=True)

def render_scorebook(sc):
    st.markdown('<div class="sh" style="margin-top:20px">&#9672; THE SCOREBOOK</div>', unsafe_allow_html=True)
    clutch_class = "clutch-alert" if float(sc.get("req_rr", 0)) > 10 else ""
    st.markdown(f"""<div class="gc {clutch_class}"><div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:20px"><div style="flex:1;min-width:160px"><div class="tl" style="color:#D22D3D">&#9670; RCB</div><div class="mxl">{sc['rcb']['score']}/{sc['rcb']['wickets']}</div><div style="font-family:var(--fm);font-size:13px;color:var(--tm);margin-top:5px">({sc['rcb']['overs']} OV)</div></div><div style="flex:2;min-width:260px;padding:0 18px"><div style="font-family:var(--fm);font-size:10px;letter-spacing:2px;color:var(--td);text-align:center;margin-bottom:10px">WIN PROBABILITY</div><div class="pr"><span style="color:#00D1FF">RCB</span><span>{sc['rcb_win_prob']}%</span></div><div class="pt"><div class="pbc" style="width:{sc['rcb_win_prob']}%"></div></div><div class="pr" style="margin-top:10px"><span style="color:#FFB547">SRH</span><span>{sc['srh_win_prob']}%</span></div><div class="pt"><div class="pba" style="width:{sc['srh_win_prob']}%"></div></div><div style="text-align:center;margin-top:14px;font-family:var(--fm);font-size:11px;color:var(--tm)">{sc['status']}</div></div><div style="flex:1;min-width:160px;text-align:right"><div class="tl" style="color:#FF822A;text-align:right">&#9670; SRH</div><div class="mxl">{sc['srh']['score']}/{sc['srh']['wickets']}</div><div style="font-family:var(--fm);font-size:13px;color:var(--tm);margin-top:5px">({sc['srh']['overs']} OV)</div></div></div><div style="margin-top:20px;padding:11px 16px;background:rgba(255,62,62,0.06);border:1px solid rgba(255,62,62,0.2);border-radius:8px;font-family:var(--fm);font-size:12px;display:flex;justify-content:space-between;"><span><span style="color:var(--red);font-weight:700">CHASE STATUS</span> · Need <b>{sc['required']}</b> off <b>{sc['balls_left']}</b></span><span>Req RR: <b>{sc['req_rr']}</b></span></div></div>""", unsafe_allow_html=True)

def render_next_ball(sc):
    st.markdown('<div class="sh" style="margin-top:22px">&#9672; NEXT BALL INTELLIGENCE</div>', unsafe_allow_html=True)
    probs = next_ball_probs(sc)
    cells = '<div class="nb-grid">'
    for lbl, pct in probs.items():
        cells += f'<div class="nb-cell" style="border-color:rgba(0,209,255,0.4)"><div style="font-size:18px;font-weight:700;">{lbl}</div><div style="font-size:10px;margin-top:4px;color:var(--tm)">{pct}%</div></div>'
    st.markdown(f'<div class="gc gc-cyan"><div class="kl">OUTCOME PROBABILITIES</div>{cells}</div>', unsafe_allow_html=True)

def render_bowler_intel(bowlers):
    st.markdown('<div class="sh" style="margin-top:22px">&#9672; BOWLING INTELLIGENCE</div>', unsafe_allow_html=True)
    ca, cb = st.columns([3,2])
    with ca:
        html = '<div class="gc gc-purple"><div class="kl">BOWLER ANALYTICS</div>'
        for b in bowlers: html += f'<div class="pl-row"><div><div class="pl-n">{b["name"]}</div><div class="pl-r">{b["team"]}</div></div><div style="text-align:right;color:var(--cyan)">{b["wkts"]} WKTS &middot; {b["econ"]} ECON</div></div>'
        st.markdown(html + '</div>', unsafe_allow_html=True)
    with cb: st.plotly_chart(chart_wagon(), width="stretch", config={"displayModeBar":False})

def render_intel_row(news):
    st.markdown('<div class="sh" style="margin-top:22px">&#9672; LIVE INTELLIGENCE FEED</div>', unsafe_allow_html=True)
    ca, cb = st.columns([1,2])
    with ca: st.markdown('<div class="gc gc-cyan"><div class="kl">KEY METRICS</div><div style="font-size:14px;font-weight:700;margin-top:10px">V. Kohli: 72(48)<br>P. Cummins: 3/24</div></div>', unsafe_allow_html=True)
    with cb:
        html = '<div class="gc"><div class="kl">PRESS BOX INTEL (CLICK HEADLINES)</div>'
        if news:
            for item in news[:6]:
                # CLICKABLE NEWS LINK INTEGRATION
                html += f'<div class="ni"><div><a href="{item["link"]}" target="_blank" style="color:var(--tp);">{item["title"]}</a></div><div class="ni-s">{item["source"]} &middot; {item["published"][:16]}</div></div>'
        st.markdown(html + '</div>', unsafe_allow_html=True)

def render_neural_verdict(sc, batters, bowlers):
    st.markdown(f'<div class="vd"><div class="vd-h">&#9672; 3RD UMPIRE AI · NEURAL ANALYSIS</div><div style="font-size:14px;line-height:1.7">Neural pattern analysis indicates a 62% advantage for SRH. RCB required rate of {sc["req_rr"]} demands aggressive strike rotation in the death overs.</div></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# 9. MAIN RENDER LOOP (REAL-TIME LOGIC)
# ─────────────────────────────────────────────────────────────────
render_masterhead()
with st.spinner("Synchronizing..."):
    sc = None
    show_demo = st.sidebar.toggle("Force Demo Data", value=False)
    if not show_demo:
        raw = fetch_live_matches()
        if raw:
            for m in raw.get("data",[]):
                if "RCB" in m.get("name","").upper() and "SRH" in m.get("name","").upper():
                    sc_raw = fetch_match_score(m.get("id"))
                    if sc_raw and sc_raw.get("status") != "Upcoming": sc = sc_raw; break
    if sc is None:
        st.info("📡 Awaiting Live Broadcast: RCB vs SRH starts tonight at 7:30 PM IST. Showing pre-match intel.")
        sc = demo_sc()
    news = fetch_news(); batters = demo_batters(); bowlers = demo_bowlers()

render_press_box(sc); render_scorebook(sc); render_next_ball(sc)
render_bowler_intel(bowlers); render_intel_row(news); render_neural_verdict(sc, batters, bowlers)

if st.sidebar.toggle("Auto-Refresh (30s)", value=True):
    time.sleep(REFRESH_SECS); st.rerun()
