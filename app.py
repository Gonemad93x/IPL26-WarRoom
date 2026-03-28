"""
╔══════════════════════════════════════════════════════════════════╗
║   GOD'S EYE v3.2 — IPL ELITE MATCH CENTER (FULL UNIFIED)         ║
║   Operator: Uday Maddila                                         ║
║   Technical Patch: IST Timezone + 2026 Chart Standards           ║
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
    page_title="GOD'S  EYE | IPL Match Center",
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
# 2. GLOBAL CSS (ELITE ANALYST THEME + PRESSURE SENSORS)
# ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

:root {
    --bg-base:   #0B0E14;
    --bg-card:   rgba(255,255,255,0.035);
    --bg-hover:  rgba(255,255,255,0.055);
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
    --fp:        'Inter', sans-serif;
    --fm:        'JetBrains Mono', monospace;
}

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"], .main {
    background: var(--bg-base) !important;
    color: var(--tp) !important;
    font-family: var(--fp) !important;
}
[data-testid="stHeader"], [data-testid="stToolbar"], footer { display:none !important; }
section[data-testid="stSidebar"] { display:none !important; }
div.block-container { padding:1.6rem 2.4rem 3rem !important; max-width:1440px; }
.stMarkdown { padding:0 !important; }
[data-testid="stHorizontalBlock"] > div { padding:0 5px; }

.gc {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 18px 22px;
    height: 100%;
    transition: border-color .2s;
}
.gc:hover  { border-color: var(--bc); }
.gc-cyan   { border-left: 3px solid var(--cyan);   }
.gc-red    { border-left: 3px solid var(--red);    }
.gc-green  { border-left: 3px solid var(--green);  }
.gc-amber  { border-left: 3px solid var(--amber);  }
.gc-purple { border-left: 3px solid var(--purple); }

/* PRESSURE SENSOR PULSE [v3.2] */
.clutch-alert { 
    animation: pulse-red 2s infinite; 
    border-color: var(--red) !important; 
    background: rgba(255,62,62,0.08) !important;
}
@keyframes pulse-red { 
    0% { box-shadow: 0 0 0 0 rgba(255,62,62,0.4); } 
    70% { box-shadow: 0 0 0 10px rgba(255,62,62,0); } 
    100% { box-shadow: 0 0 0 0 rgba(255,62,62,0); } 
}

.badge {
    font-family: var(--fm); font-size: 9px; font-weight: 700; letter-spacing: 1.5px;
    border-radius: 4px; padding: 2px 8px; display: inline-block; margin-bottom: 8px;
}
.b-red    { color:var(--red);    background:rgba(255,62,62,.12);   border:1px solid rgba(255,62,62,.3);   }
.b-amber  { color:var(--amber);  background:rgba(255,181,71,.10);  border:1px solid rgba(255,181,71,.3);  }
.b-cyan   { color:var(--cyan);   background:rgba(0,209,255,.10);   border:1px solid rgba(0,209,255,.25);  }
.b-green  { color:var(--green);  background:rgba(61,255,122,.10);  border:1px solid rgba(61,255,122,.25); }
.b-purple { color:var(--purple); background:rgba(191,127,255,.10); border:1px solid rgba(191,127,255,.3); }

.sh { font-family: var(--fm); font-size: 10px; letter-spacing: 3px; color: var(--td); border-bottom: 1px solid var(--border); padding-bottom: 8px; margin-bottom: 14px; }
.mlg { font-family:var(--fm); font-size:26px; font-weight:700; color:var(--tp); line-height:1; }
.mxl { font-family:var(--fm); font-size:48px; font-weight:700; color:var(--tp); line-height:1; letter-spacing:-1px; }
.kl  { font-family:var(--fm); font-size:10px; letter-spacing:1.8px; color:var(--td); text-transform:uppercase; margin-bottom:5px; }
.ku  { font-family:var(--fm); font-size:11px; color:var(--tm); margin-top:3px; }
.tl  { font-family:var(--fp); font-size:10px; font-weight:600; letter-spacing:3px; text-transform:uppercase; color:var(--tm); margin-bottom:5px; }

.pp  { font-family:var(--fm); font-size:11px; font-weight:700; letter-spacing:2px; text-transform:uppercase; padding:4px 14px; border-radius:20px; display:inline-block; }
.ppp { background:rgba(0,209,255,.15);  color:var(--cyan);  border:1px solid rgba(0,209,255,.4);  }
.ppm { background:rgba(255,181,71,.12); color:var(--amber); border:1px solid rgba(255,181,71,.35);}
.ppd { background:rgba(255,62,62,.14);  color:var(--red);   border:1px solid rgba(255,62,62,.4);  }

.pt  { height:6px; background:rgba(255,255,255,.07); border-radius:3px; overflow:hidden; margin:6px 0 3px; }
.pbc { height:100%; background:linear-gradient(90deg,#00D1FF,#0099CC); border-radius:3px; }
.pba { height:100%; background:linear-gradient(90deg,#FFB547,#CC8800); border-radius:3px; }
.pr  { display:flex; justify-content:space-between; font-family:var(--fm); font-size:11px; color:var(--tm); }

.pl-row { display:flex; align-items:center; justify-content:space-between; padding:9px 0; border-bottom:1px solid var(--border); font-family:var(--fm); font-size:12px; }
.pl-row:last-child { border-bottom:none; }
.pl-n { font-size:13px; color:var(--tp); font-weight:600; }
.pl-r { font-size:10px; color:var(--td); letter-spacing:1px; }

.nb-grid { display:grid; grid-template-columns:repeat(6,1fr); gap:8px; margin-top:10px; }
.nb-cell { text-align:center; padding:10px 4px; border-radius:8px; border:1px solid var(--border); font-family:var(--fm); font-size:11px; font-weight:600; }

.mh { display:flex; align-items:center; justify-content:space-between; margin-bottom:24px; padding-bottom:14px; border-bottom:1px solid var(--border); }
.mh-logo { font-family:var(--fm); font-size:20px; font-weight:700; color:var(--tp); }
.mh-logo span { color:var(--cyan); }
.mh-meta { font-family:var(--fm); font-size:11px; color:var(--td); text-align:right; }
.ld { display:inline-block; width:7px; height:7px; border-radius:50%; background:var(--red); margin-right:6px; animation:pulse 1.4s ease-in-out infinite; }
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1);} 50%{opacity:.4;transform:scale(.8);} }

.ni { border-bottom:1px solid var(--border); padding:9px 0; font-size:13px; line-height:1.5; }
.ni:last-child { border-bottom:none; }
.ni-s { font-family:var(--fm); font-size:10px; color:var(--td); margin-top:2px; }

.vd { background:rgba(0,209,255,0.04); border:1px solid rgba(0,209,255,0.18); border-left:3px solid var(--cyan); border-radius:10px; padding:20px 26px; margin-top:14px; }
.vd-h { font-family:var(--fm); font-size:11px; letter-spacing:2.5px; color:var(--cyan); margin-bottom:10px; }

.mt { height:4px; background:rgba(255,255,255,.06); border-radius:2px; overflow:hidden; margin:4px 0; }
.mf { height:100%; border-radius:2px; }

.pb1 { background:rgba(0,209,255,.05);   border:1px solid rgba(0,209,255,.18);   border-left:3px solid var(--cyan);   border-radius:8px; padding:14px 18px; margin-bottom:10px; }
.pb2 { background:rgba(255,62,62,.05);   border:1px solid rgba(255,62,62,.18);   border-left:3px solid var(--red);    border-radius:8px; padding:14px 18px; margin-bottom:10px; }
.pb3 { background:rgba(255,181,71,.05);  border:1px solid rgba(255,181,71,.18);  border-left:3px solid var(--amber);  border-radius:8px; padding:14px 18px; margin-bottom:10px; }
.pb4 { background:rgba(191,127,255,.05); border:1px solid rgba(191,127,255,.18); border-left:3px solid var(--purple); border-radius:8px; padding:14px 18px; margin-bottom:10px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# 3. PLOTLY HELPERS (PATCHED FOR 2026 STANDARDS)
# ─────────────────────────────────────────────────────────────────
BG   = "rgba(0,0,0,0)"
GRID = "rgba(255,255,255,0.05)"
FC   = "#7D8590"
FF   = "JetBrains Mono, monospace"

def _layout(**kw):
    return dict(
        paper_bgcolor=BG, plot_bgcolor=BG,
        font=dict(family=FF, color=FC, size=11),
        margin=dict(l=10, r=10, t=34, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1, bgcolor=BG, font=dict(size=10)),
        **kw,
    )

def _ax(title="", sfx="", rng=None, **kw):
    d = dict(title=title, showgrid=True, gridcolor=GRID,
             zeroline=False, tickfont=dict(size=10),
             linecolor="rgba(255,255,255,0.08)")
    if sfx:   d["ticksuffix"] = sfx
    if rng:   d["range"] = rng
    d.update(kw)
    return d

def _ax2(title=""):
    return dict(title=title, showgrid=False, zeroline=False,
                tickfont=dict(size=10), linecolor="rgba(255,255,255,0.08)",
                overlaying="y", side="right")

# ─────────────────────────────────────────────────────────────────
# 4. DATA LAYER
# ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=REFRESH_SECS, show_spinner=False)
def fetch_live_matches():
    try:
        r = requests.get(f"https://{RAPIDAPI_HOST}/cricket-match-list",
                         headers=API_HEADERS, timeout=8)
        if r.status_code == 200:
            return r.json()
    except Exception: pass
    return None

@st.cache_data(ttl=REFRESH_SECS, show_spinner=False)
def fetch_match_score(match_id):
    try:
        r = requests.get(f"https://{RAPIDAPI_HOST}/cricket-match-scorecard",
                         headers=API_HEADERS, params={"id": match_id}, timeout=8)
        if r.status_code == 200:
            return r.json()
    except Exception: pass
    return None

@st.cache_data(ttl=120, show_spinner=False)
def fetch_news():
    url = "https://news.google.com/rss/search?q=IPL+2026+RCB+SRH+injury+squad&hl=en-IN&gl=IN&ceid=IN:en"
    try:
        feed = feedparser.parse(url)
        return [{"title": e.get("title",""),
                 "source": e.get("source",{}).get("title",""),
                 "published": e.get("published","")} for e in feed.entries[:8]]
    except Exception: return []

# ─────────────────────────────────────────────────────────────────
# 5. DEMO DATA (ALL PRESERVED)
# ─────────────────────────────────────────────────────────────────
def demo_sc():
    return {
        "match":  "RCB vs SRH — IPL 2026, Match 1",
        "venue":  "M. Chinnaswamy Stadium, Bengaluru",
        "status": "LIVE — 2nd Innings",
        "rcb": {"name":"Royal Challengers Bengaluru","short":"RCB",
                "score":"142","wickets":"3","overs":"15.3","rr":"9.15"},
        "srh": {"name":"Sunrisers Hyderabad","short":"SRH",
                "score":"187","wickets":"10","overs":"20.0","rr":"9.35"},
        "target":188,"required":46,"req_rr":6.86,
        "balls_left":27,"phase":"death",
        "rcb_win_prob":38,"srh_win_prob":62,
    }

def demo_batters():
    return [
        {"name":"Virat Kohli",      "team":"RCB","runs":72,"balls":48,"sr":150.0,"4s":8,"6s":3,"form":88,"p50":95,"p30":99},
        {"name":"Rajat Patidar",    "team":"RCB","runs":34,"balls":22,"sr":154.5,"4s":3,"6s":2,"form":72,"p50":54,"p30":85},
        {"name":"Glenn Maxwell",    "team":"RCB","runs":18,"balls":11,"sr":163.6,"4s":2,"6s":1,"form":81,"p50":40,"p30":68},
        {"name":"Heinrich Klaasen", "team":"SRH","runs":58,"balls":32,"sr":181.2,"4s":5,"6s":5,"form":91,"p50":99,"p30":99},
        {"name":"Pat Cummins",      "team":"SRH","runs":24,"balls":15,"sr":160.0,"4s":2,"6s":2,"form":74,"p50":22,"p30":61},
        {"name":"Travis Head",      "team":"SRH","runs":9, "balls":8, "sr":112.5,"4s":1,"6s":0,"form":66,"p50":10,"p30":28},
    ]

def demo_bowlers():
    return [
        {"name":"Jasprit Bumrah",    "team":"RCB","overs":4.0,"runs":22,"wkts":3,"econ":5.50,"dot":55,"threat":95,"avg":7.3},
        {"name":"Yuzvendra Chahal",  "team":"RCB","overs":3.0,"runs":28,"wkts":1,"econ":9.33,"dot":38,"threat":70,"avg":28.0},
        {"name":"Cameron Green",     "team":"RCB","overs":2.0,"runs":24,"wkts":1,"econ":12.0,"dot":30,"threat":55,"avg":24.0},
        {"name":"Pat Cummins",       "team":"SRH","overs":4.0,"runs":24,"wkts":3,"econ":6.00,"dot":52,"threat":92,"avg":8.0},
        {"name":"Bhuvneshwar Kumar", "team":"SRH","overs":3.0,"runs":21,"wkts":2,"econ":7.00,"dot":45,"threat":80,"avg":10.5},
        {"name":"Jaydev Unadkat",    "team":"SRH","overs":2.0,"runs":28,"wkts":0,"econ":14.0,"dot":22,"threat":30,"avg":0},
    ]

def demo_partnerships():
    return [
        {"wkt":1,"runs":42,"balls":28,"rate":9.0, "pair":"Kohli & du Plessis"},
        {"wkt":2,"runs":68,"balls":41,"rate":9.95,"pair":"Kohli & Patidar"},
        {"wkt":3,"runs":32,"balls":18,"rate":10.67,"pair":"Kohli & Maxwell"},
    ]

def demo_history():
    random.seed(7)
    cum, data = 0, []
    for o in range(1, 16):
        r = random.randint(5, 18)
        w = random.choices([0,1,2], weights=[70,25,5])[0]
        cum += r
        data.append({"over":o,"runs":r,"wkts":w,"cum":cum})
    return data

def demo_momentum():
    random.seed(42)
    ov, wp, rr, req = [], [], [], []
    prob = 55
    for i in range(1, 16):
        prob = max(5, min(95, prob + random.randint(-8,8)))
        ov.append(i); wp.append(prob)
        rr.append(round(random.uniform(6.5,14.5),2))
        req.append(round(random.uniform(5.0,16.0),2))
    return ov, wp, rr, req

def next_ball_probs(sc):
    rr = float(sc.get("req_rr", 7))
    pressure = min(1.0, rr / 18.0)
    dot  = max(10, 30 - pressure*10); one  = max(15, 22 - pressure*5); two  = max(8,  14 - pressure*3)
    four = max(12, 18 + pressure*5); six  = max(8,  10 + pressure*8); wkt  = max(4,   6 + pressure*6)
    tot  = dot+one+two+four+six+wkt
    return { "dot": round(dot/tot*100), "1": round(one/tot*100), "2":   round(two/tot*100), "4": round(four/tot*100), "6":   round(six/tot*100), "W": round(wkt/tot*100) }

# ─────────────────────────────────────────────────────────────────
# 6. CHART BUILDERS
# ─────────────────────────────────────────────────────────────────
def chart_momentum(ov, wp, rr, req):
    fig = make_subplots(specs=[[{"secondary_y":True}]])
    fig.add_trace(go.Scatter(x=ov, y=wp, name="RCB Win Prob %", mode="lines", line=dict(color="#00D1FF",width=2.5,shape="spline",smoothing=1.1), fill="tozeroy", fillcolor="rgba(0,209,255,0.06)"), secondary_y=False)
    fig.add_trace(go.Scatter(x=ov, y=rr, name="Actual RR", mode="lines", line=dict(color="#FFB547",width=1.8,dash="dot",shape="spline")), secondary_y=True)
    fig.add_trace(go.Scatter(x=ov, y=req, name="Required RR", mode="lines", line=dict(color="#FF3E3E",width=1.8,dash="dash",shape="spline")), secondary_y=True)
    fig.add_hline(y=50, secondary_y=False, line_dash="dot", line_color="rgba(255,255,255,0.10)", line_width=1)
    fig.update_layout(**_layout(title=dict(text="WIN PROBABILITY & RUN RATE MATRIX", font=dict(size=11,color="#484F58"),x=0,xanchor="left"), xaxis=_ax("Over"), yaxis=_ax("Win Prob (%)", sfx="%", rng=[0,100]), yaxis2=_ax2("Run Rate")))
    return fig

def chart_run_progression(hist):
    ov = [h["over"] for h in hist]; runs = [h["runs"] for h in hist]; cum = [h["cum"]  for h in hist]
    wo = [h["over"] for h in hist if h["wkts"]>0]; wc = [h["cum"]  for h in hist if h["wkts"]>0]
    fig = make_subplots(specs=[[{"secondary_y":True}]])
    fig.add_trace(go.Bar(x=ov, y=runs, name="Runs/Over", marker=dict(color=["#FF3E3E" if r>14 else ("#FFB547" if r>10 else "#00D1FF") for r in runs], opacity=0.8)), secondary_y=False)
    fig.add_trace(go.Scatter(x=ov, y=cum, name="Cumulative", mode="lines+markers", line=dict(color="#3DFF7A",width=2), marker=dict(size=5,color="#3DFF7A")), secondary_y=True)
    if wo: fig.add_trace(go.Scatter(x=wo, y=wc, name="Wicket", mode="markers", marker=dict(symbol="x",size=12,color="#FF3E3E",line=dict(width=2,color="#FF3E3E"))), secondary_y=True)
    fig.update_layout(**_layout(title=dict(text="RUN PROGRESSION — OVER BY OVER", font=dict(size=11,color="#484F58"),x=0), xaxis=_ax("Over"), yaxis=_ax("Runs/Over"), yaxis2=_ax2("Cumulative")))
    return fig

def chart_wagon():
    cats = ["Straight","Cover","Square Leg","Fine Leg","Mid-Wicket","Point"]
    rcb  = [34,48,22,15,38,27]; srh = [41,35,30,18,42,22]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=rcb+[rcb[0]],theta=cats+[cats[0]],name="RCB", fill="toself",line=dict(color="#00D1FF",width=2),fillcolor="rgba(0,209,255,0.08)"))
    fig.add_trace(go.Scatterpolar(r=srh+[srh[0]],theta=cats+[cats[0]],name="SRH", fill="toself",line=dict(color="#FFB547",width=2),fillcolor="rgba(255,181,71,0.06)"))
    fig.update_layout(paper_bgcolor=BG, polar=dict(bgcolor=BG, radialaxis=dict(visible=True,range=[0,55],gridcolor="rgba(255,255,255,0.06)"), angularaxis=dict(gridcolor="rgba(255,255,255,0.06)")), font=dict(family=FF,color=FC,size=10), legend=dict(orientation="h",yanchor="top",y=-0.05,xanchor="center",x=0.5), margin=dict(l=20,r=20,t=30,b=20), title=dict(text="SHOT ZONE DISTRIBUTION",font=dict(size=11,color="#484F58"),x=0.5))
    return fig

def chart_bowler_radar(bowlers, team):
    bw = [b for b in bowlers if b["team"]==team]; cats = ["Wickets","Economy(inv)","Dot %","Avg(inv)","Threat"]; clrs = ["#00D1FF","#FFB547","#3DFF7A","#FF3E3E","#BF7FFF"]
    fig = go.Figure()
    for i, b in enumerate(bw):
        ei = max(0, 100 - b["econ"]*6); ai = max(0, 100 - b["avg"]*2) if b["avg"]>0 else 80
        vals = [b["wkts"]*25, ei, b["dot"], ai, b["threat"]]; c = clrs[i % len(clrs)]; r,g,bl = int(c[1:3],16), int(c[3:5],16), int(c[5:7],16)
        fig.add_trace(go.Scatterpolar(r=vals+[vals[0]], theta=cats+[cats[0]], name=b["name"].split()[-1], fill="toself", line=dict(color=c,width=2), fillcolor=f"rgba({r},{g},{bl},0.07)"))
    fig.update_layout(paper_bgcolor=BG, polar=dict(bgcolor=BG, radialaxis=dict(visible=True,range=[0,100],gridcolor="rgba(255,255,255,0.05)"), angularaxis=dict(gridcolor="rgba(255,255,255,0.06)")), font=dict(family=FF,color=FC,size=10), legend=dict(orientation="h",yanchor="top",y=-0.08,xanchor="center",x=0.5), margin=dict(l=20,r=20,t=30,b=20), title=dict(text=f"{team} BOWLING THREAT RADAR",font=dict(size=11,color="#484F58"),x=0.5))
    return fig

def chart_partnership(parts):
    labels = [f"P{p['wkt']}: {p['pair']}" for p in parts]; runs = [p["runs"] for p in parts]
    fig = go.Figure(go.Bar(x=runs, y=labels, orientation="h", marker=dict(color=["#00D1FF","#FFB547","#3DFF7A"],opacity=0.8), text=[f"{r} runs · {p['balls']} balls" for r,p in zip(runs,parts)], textfont=dict(family=FF,size=10), textposition="inside"))
    fig.update_layout(**_layout(title=dict(text="PARTNERSHIP ANALYSIS",font=dict(size=11),x=0), xaxis=_ax("Runs"), yaxis=dict(showgrid=False), height=180))
    return fig

def chart_batter_compare(batters):
    names = [b["name"].split()[-1] for b in batters]; runs = [b["runs"] for b in batters]; sr = [b["sr"] for b in batters]
    colors = ["#00D1FF" if b["team"]=="RCB" else "#FFB547" for b in batters]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=names,y=runs,name="Runs", marker=dict(color=colors,opacity=0.75)))
    fig.add_trace(go.Scatter(x=names,y=sr,name="Strike Rate", mode="lines+markers",yaxis="y2", line=dict(color="#3DFF7A",width=2), marker=dict(size=8,color="#3DFF7A")))
    fig.update_layout(**_layout(title=dict(text="BATTER COMPARISON",font=dict(size=11),x=0), xaxis=_ax(""), yaxis=_ax("Runs"), yaxis2=_ax2("Strike Rate")))
    return fig

# ─────────────────────────────────────────────────────────────────
# 7. UI RENDERERS
# ─────────────────────────────────────────────────────────────────
def render_masterhead():
    IST = pytz.timezone('Asia/Kolkata')
    now = datetime.now(IST).strftime("%d %b %Y  ·  %H:%M:%S IST")
    st.markdown(
        f'<div class="mh">'
        f'<div><div class="mh-logo">GOD\'S<span>EYE</span> v3.2&nbsp;'
        f'<span style="font-size:11px;color:var(--td);font-weight:400">IPL MATCH CENTER</span></div>'
        f'<div style="font-family:var(--fm);font-size:10px;color:var(--td);margin-top:4px;">'
        f'<span class="ld"></span>LIVE FEED ACTIVE — RCB vs SRH</div></div>'
        f'<div class="mh-meta"><div style="color:var(--tm);margin-bottom:2px">{now}</div>'
        f'<div>OPERATOR: <span style="color:var(--tp)">UDAY MADDILA</span></div></div>'
        f'</div>',
        unsafe_allow_html=True)

def render_press_box(sc):
    rr = sc.get("req_rr", 0); wp = sc.get("rcb_win_prob", 50)
    wp_b = "b-red" if wp<30 else ("b-amber" if wp<50 else "b-cyan")
    wp_lbl = "[P0 CRITICAL]" if wp<25 else ("[P1 ELEVATED]" if wp<50 else "[P2 NOMINAL]")
    rr_c = "var(--red)" if rr>12 else ("var(--amber)" if rr>9 else "var(--green)")
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: st.markdown(f'<div class="gc"><div class="badge {wp_b}">{wp_lbl}</div><div class="kl">WIN PROBABILITY</div><div class="mlg">{wp}%</div><div class="ku">RCB · SRH {sc.get("srh_win_prob",50)}%</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="gc"><div class="badge b-amber">[P1 ELEVATED]</div><div class="kl">REQUIRED RUN RATE</div><div class="mlg" style="color:{rr_c}">{rr}</div><div class="ku">{sc.get("required")} runs · {sc.get("balls_left")} balls</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="gc"><div class="badge b-cyan">[INTELLIGENCE]</div><div class="kl">MATCH TARGET</div><div class="mlg">{sc.get("target")}</div><div class="ku">SRH total (1st innings)</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="gc"><div class="badge b-cyan">[MATCH PHASE]</div><div class="kl">CURRENT PHASE</div><div style="margin-top:8px"><span class="pp ppm">{sc.get("phase", "MIDDLE").upper()}</span></div></div>', unsafe_allow_html=True)
    with c5: st.markdown(f'<div class="gc"><div class="badge b-green">[P3 NOMINAL]</div><div class="kl">CURRENT RR</div><div class="mlg">{sc.get("rcb",{}).get("rr")}</div><div class="ku">SRH CRR: {sc.get("srh",{}).get("rr")}</div></div>', unsafe_allow_html=True)

def render_scorebook(sc):
    st.markdown('<div class="sh" style="margin-top:20px">&#9672; THE SCOREBOOK</div>', unsafe_allow_html=True)
    rcb = sc.get("rcb",{}); srh = sc.get("srh",{})
    # PRESSURE SENSOR [v3.2 Fix]
    clutch_class = "clutch-alert" if float(sc.get("req_rr", 0)) > 10 else ""
    st.markdown(
        f'<div class="gc {clutch_class}">'
        '<div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:20px">'
        '<div style="flex:1;min-width:160px">'
        f'<div class="tl" style="color:#D22D3D">&#9670; {rcb.get("short","RCB")}</div>'
        f'<div class="mxl">{rcb.get("score","&mdash;")}/{rcb.get("wickets","&mdash;")}</div>'
        f'<div style="font-family:var(--fm);font-size:13px;color:var(--tm);margin-top:5px">({rcb.get("overs","&mdash;")} OV) &nbsp;CRR: {rcb.get("rr","&mdash;")}</div>'
        '</div>'
        '<div style="flex:2;min-width:260px;padding:0 18px">'
        '<div style="font-family:var(--fm);font-size:10px;letter-spacing:2px;color:var(--td);text-align:center;margin-bottom:10px">WIN PROBABILITY</div>'
        f'<div class="pr"><span style="color:#00D1FF">RCB</span><span>{sc.get("rcb_win_prob")}%</span></div>'
        f'<div class="pt"><div class="pbc" style="width:{sc.get("rcb_win_prob")}%"></div></div>'
        f'<div class="pr" style="margin-top:10px"><span style="color:#FFB547">SRH</span><span>{sc.get("srh_win_prob")}%</span></div>'
        f'<div class="pt"><div class="pba" style="width:{sc.get("srh_win_prob")}%"></div></div>'
        f'<div style="text-align:center;margin-top:14px;font-family:var(--fm);font-size:10px;color:var(--td)">{sc.get("venue")}</div>'
        '</div>'
        '<div style="flex:1;min-width:160px;text-align:right">'
        f'<div class="tl" style="color:#FF822A;text-align:right">&#9670; {srh.get("short","SRH")}</div>'
        f'<div class="mxl">{srh.get("score")}/{srh.get("wickets")}</div>'
        f'<div style="font-family:var(--fm);font-size:13px;color:var(--tm);margin-top:5px">({srh.get("overs")} OV) &nbsp;CRR: {srh.get("rr")}</div>'
        '</div></div>'
        f'<div style="margin-top:20px;padding:11px 16px;background:rgba(255,62,62,0.06);border:1px solid rgba(255,62,62,0.2);border-radius:8px;font-family:var(--fm);font-size:12px;display:flex;justify-content:space-between;">'
        f'<span><span style="color:var(--red);font-weight:700">RCB CHASE STATUS</span> · Need <b>{sc.get("required")}</b> off <b>{sc.get("balls_left")}</b></span>'
        f'<span>Req RR: <b>{sc.get("req_rr")}</b></span></div></div>', unsafe_allow_html=True)

def render_next_ball(sc):
    st.markdown('<div class="sh" style="margin-top:22px">&#9672; NEXT BALL INTELLIGENCE</div>', unsafe_allow_html=True)
    probs = next_ball_probs(sc); cells = '<div class="nb-grid">'
    styles = {"dot":("#484F58","rgba(72,79,88,0.2)"), "1":("#7D8590","rgba(125,133,144,0.15)"), "2":("#FFB547","rgba(255,181,71,0.15)"), "4":("#00D1FF","rgba(0,209,255,0.15)"), "6":("#3DFF7A","rgba(61,255,122,0.15)"), "W":("#FF3E3E","rgba(255,62,62,0.15)")}
    for lbl, pct in probs.items():
        clr, bg = styles[lbl]; cells += f'<div class="nb-cell" style="color:{clr};background:{bg};border-color:{clr}40"><div style="font-size:18px;font-weight:700">{lbl}</div><div style="font-size:10px;margin-top:4px;color:var(--tm)">{pct}%</div></div>'
    ca, cb = st.columns([3,2], gap="medium")
    with ca: st.markdown(f'<div class="gc gc-cyan"><div class="kl">NEXT BALL — OUTCOME PROBABILITIES</div>{cells}</div>', unsafe_allow_html=True)
    with cb:
        pressure = min(100, int(float(sc.get("req_rr", 0))/18*100)); pc = "var(--red)" if pressure>70 else "var(--green)"
        st.markdown(f'<div class="gc gc-red"><div class="kl">BATTING PRESSURE INDEX</div><div style="font-family:var(--fm);font-size:42px;font-weight:700;color:{pc}">{pressure}</div><div class="pt"><div class="mf" style="width:{pressure}%;background:{pc}"></div></div></div>', unsafe_allow_html=True)

def render_batter_predictor(batters):
    st.markdown('<div class="sh" style="margin-top:22px">&#9672; BATTER MILESTONE PREDICTOR</div>', unsafe_allow_html=True)
    ca, cb = st.columns(2, gap="medium")
    for col, team in [(ca,"RCB"),(cb,"SRH")]:
        with col:
            html = f'<div class="gc" style="border-left:3px solid {"#D22D3D" if team=="RCB" else "#FF822A"}"><div class="kl">{team} BATTERS</div>'
            for b in [bat for bat in batters if bat["team"]==team]:
                p50c = "var(--green)" if b["p50"]>75 else "var(--red)"
                html += f'<div class="pl-row"><div><div class="pl-n">{b["name"]}</div><div class="pl-r">{b["runs"]}r ({b["balls"]}b) SR:{b["sr"]}</div></div><div style="text-align:right"><div style="font-size:10px;color:{p50c}">{b["p50"]}% HIT 50</div></div></div>'
            st.markdown(html + '</div>', unsafe_allow_html=True)

def render_bowler_intel(bowlers):
    st.markdown('<div class="sh" style="margin-top:22px">&#9672; BOWLING INTELLIGENCE</div>', unsafe_allow_html=True)
    ca, cb = st.columns([3,2], gap="medium")
    with ca:
        html = '<div class="gc gc-purple"><div class="kl">BOWLER ANALYTICS</div>'
        for b in bowlers: html += f'<div class="pl-row"><div><div class="pl-n">{b["name"]}</div><div class="pl-r">{b["team"]}</div></div><div style="text-align:right">{b["wkts"]} WKTS &middot; {b["econ"]} ECON</div></div>'
        st.markdown(html + '</div>', unsafe_allow_html=True)
    with cb: st.plotly_chart(chart_bowler_radar(bowlers, "SRH"), width="stretch", config={"displayModeBar":False})

def render_momentum_matrix(sc):
    st.markdown('<div class="sh" style="margin-top:22px">&#9672; MOMENTUM MATRIX</div>', unsafe_allow_html=True)
    ov, wp, rr, req = demo_momentum()
    c1, c2 = st.columns([3,2], gap="medium")
    with c1: st.plotly_chart(chart_momentum(ov,wp,rr,req), width="stretch", config={"displayModeBar":False})
    with c2: st.plotly_chart(chart_wagon(), width="stretch", config={"displayModeBar":False})
    c3, c4 = st.columns([3,2], gap="medium")
    with c3: st.plotly_chart(chart_run_progression(demo_history()), width="stretch", config={"displayModeBar":False})
    with c4:
        st.plotly_chart(chart_partnership(demo_partnerships()), width="stretch", config={"displayModeBar":False})
        st.plotly_chart(chart_batter_compare(demo_batters()), width="stretch", config={"displayModeBar":False})

def render_intel_row(news):
    st.markdown('<div class="sh" style="margin-top:22px">&#9672; LIVE INTELLIGENCE FEED</div>', unsafe_allow_html=True)
    ca, cb = st.columns([1,2], gap="medium")
    with ca: st.markdown('<div class="gc gc-cyan"><div class="kl">KEY METRICS</div><div style="font-size:14px;font-weight:700;">V. Kohli: 72(48)<br>P. Cummins: 3/24</div></div>', unsafe_allow_html=True)
    with cb:
        html = '<div class="gc"><div class="kl">PRESS BOX INTEL</div>'
        for n in news[:4]: html += f'<div class="ni"><div>{n["title"]}</div><div class="ni-s">{n["source"]}</div></div>'
        st.markdown(html + '</div>', unsafe_allow_html=True)

def render_neural_verdict(sc, batters, bowlers):
    st.markdown(f'<div class="vd"><div class="vd-h">&#9672; 3RD UMPIRE AI · NEURAL PATTERN ANALYSIS</div><div style="font-size:14px;line-height:1.7">Neural analysis indicates high-pressure for RCB. Required rate {sc.get("req_rr")} achieved only 24% of the time at this venue.</div></div>', unsafe_allow_html=True)

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
        st.info("📡 Awaiting Live Broadcast: RCB vs SRH starts tonight at 7:30 PM IST. Displaying demo metrics.")
        sc = demo_sc()
    news = fetch_news(); batters = demo_batters(); bowlers = demo_bowlers()

render_press_box(sc); render_scorebook(sc); render_next_ball(sc)
render_batter_predictor(batters); render_bowler_intel(bowlers); render_momentum_matrix(sc)
render_intel_row(news); render_neural_verdict(sc, batters, bowlers)

if st.sidebar.toggle("Auto-Refresh (30s)", value=True):
    time.sleep(REFRESH_SECS); st.rerun()
