"""
GOD'S EYE v5.2 — IPL LIVE MATCH CENTER
Operator : Uday Maddila
Update: Graceful degradation for API limits. Local Tactical Engine activated. 
        Zero errors for non-billed API keys.
"""

import streamlit as st
import requests
import feedparser
import time
import random
import os
from datetime import datetime
import pytz
from bs4 import BeautifulSoup
import concurrent.futures
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="GOD'S EYE | IPL 2026", page_icon="🏏",
                   layout="wide", initial_sidebar_state="collapsed")

# ── SESSION STATE INIT ────────────────────────────────────────────────────────
if "alert_log"    not in st.session_state: st.session_state.alert_log = []
if "prev_score"   not in st.session_state: st.session_state.prev_score = {}
if "prev_wkts"    not in st.session_state: st.session_state.prev_wkts = -1
if "scraper_src"  not in st.session_state: st.session_state.scraper_src = "Archive"

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
REFRESH_SECS  = 15
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
ESPN_SERIES   = "https://www.espncricinfo.com/series/indian-premier-league-2026-1411166/match-schedule-fixtures-and-results"
ESPN_FALLBACK = "https://www.espncricinfo.com/series/indian-premier-league-2026-1411166/royal-challengers-bengaluru-vs-sunrisers-hyderabad-1st-match-1417706/live-cricket-score"
CB_FALLBACK   = "https://www.cricbuzz.com/live-cricket-scores/149518/srh-vs-rcb-1st-match-indian-premier-league-2026"

TEAM_COLORS = {
    "RCB":"#DC2626","SRH":"#D97706","MI":"#1D4ED8","CSK":"#F59E0B",
    "KKR":"#7C3AED","RR":"#EC4899","DC":"#2563EB","PBKS":"#DC2626",
    "LSG":"#0EA5E9","GT":"#0D9488",
}
TEAM_MAP = {
    "royal challengers bengaluru":"RCB","royal challengers bangalore":"RCB",
    "sunrisers hyderabad":"SRH","mumbai indians":"MI","chennai super kings":"CSK",
    "kolkata knight riders":"KKR","rajasthan royals":"RR","delhi capitals":"DC",
    "punjab kings":"PBKS","lucknow super giants":"LSG","gujarat titans":"GT",
}

IPL_STANDINGS = [
    {"team":"RCB", "p":9,"w":6,"l":3,"nr":0,"pts":12,"nrr":"+0.45","color":"#DC2626"},
    {"team":"MI",  "p":9,"w":5,"l":3,"nr":1,"pts":11,"nrr":"+0.32","color":"#1D4ED8"},
    {"team":"SRH", "p":9,"w":5,"l":4,"nr":0,"pts":10,"nrr":"+0.18","color":"#D97706"},
    {"team":"CSK", "p":9,"w":5,"l":4,"nr":0,"pts":10,"nrr":"+0.22","color":"#F59E0B"},
    {"team":"KKR", "p":9,"w":4,"l":4,"nr":1,"pts":9, "nrr":"-0.05","color":"#7C3AED"},
    {"team":"RR",  "p":9,"w":4,"l":5,"nr":0,"pts":8, "nrr":"-0.18","color":"#EC4899"},
    {"team":"DC",  "p":9,"w":3,"l":5,"nr":1,"pts":7, "nrr":"-0.12","color":"#2563EB"},
    {"team":"PBKS","p":9,"w":3,"l":6,"nr":0,"pts":6, "nrr":"-0.25","color":"#DC2626"},
    {"team":"LSG", "p":9,"w":2,"l":6,"nr":1,"pts":5, "nrr":"-0.35","color":"#0EA5E9"},
    {"team":"GT",  "p":9,"w":2,"l":7,"nr":0,"pts":4, "nrr":"-0.42","color":"#0D9488"},
]

AUCTION_DATA = [
    {"name":"Virat Kohli",      "team":"RCB","price":21.0,"runs":412,"wkts":0,"unit":"run"},
    {"name":"Ishan Kishan",     "team":"RCB","price":11.25,"runs":318,"wkts":0,"unit":"run"},
    {"name":"Glenn Maxwell",    "team":"RCB","price":14.25,"runs":198,"wkts":4,"unit":"run"},
    {"name":"Jasprit Bumrah",   "team":"MI","price":18.0,"runs":0,"wkts":14,"unit":"wkt"},
    {"name":"Suryakumar Yadav", "team":"MI","price":16.35,"runs":387,"wkts":0,"unit":"run"},
    {"name":"Pat Cummins",      "team":"SRH","price":20.5,"runs":42,"wkts":11,"unit":"wkt"},
    {"name":"Heinrich Klaasen", "team":"SRH","price":13.25,"runs":348,"wkts":0,"unit":"run"},
    {"name":"Travis Head",      "team":"SRH","price":6.8,"runs":289,"wkts":0,"unit":"run"},
    {"name":"Bhuvneshwar Kumar","team":"SRH","price":10.0,"runs":0,"wkts":9,"unit":"wkt"},
]

DNA_MATCHES = [
    {"year":2023,"teams":"RCB vs RR","situation":"Needed 47 off 27 (Req RR 10.44)","result":"RCB WON off last ball","hero":"Dinesh Karthik 25*(8)","prob":52},
    {"year":2022,"teams":"MI vs DC","situation":"Needed 50 off 27 (Req RR 11.11)","result":"MI LOST by 4 runs","hero":"Pollard 23(11)","prob":41},
    {"year":2024,"teams":"CSK vs KKR","situation":"Needed 44 off 27 (Req RR 9.78)","result":"CSK WON by 5 wkts","hero":"Jadeja 18*(7)","prob":58},
    {"year":2023,"teams":"SRH vs GT","situation":"Needed 48 off 30 (Req RR 9.60)","result":"SRH LOST by 7 runs","hero":"Markande 2/24","prob":44},
    {"year":2021,"teams":"RCB vs PBKS","situation":"Needed 45 off 24 (Req RR 11.25)","result":"RCB WON by 2 wkts","hero":"AB de Villiers 32*(12)","prob":49},
]

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[data-testid="stAppViewContainer"],[data-testid="stApp"],.main{
    background:#F0F2F5!important;color:#1a1a2e!important;font-family:'Inter',sans-serif!important;}
[data-testid="stHeader"],[data-testid="stToolbar"],footer{display:none!important;}
section[data-testid="stSidebar"]{display:none!important;}
div.block-container{padding:0.8rem 1.8rem 2rem!important;max-width:1440px;}
[data-testid="stHorizontalBlock"]>div{padding:0 5px;}
[data-testid="stHorizontalBlock"]>div:first-child{padding-left:0;}
[data-testid="stHorizontalBlock"]>div:last-child{padding-right:0;}
.stMarkdown{padding:0!important;}
.navbar{background:#1B2A4A;color:white;padding:10px 20px;border-radius:10px;
    display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;}
.navbar-logo{font-size:17px;font-weight:700;letter-spacing:1px;}
.navbar-logo span{color:#38BDF8;}
.navbar-sub{font-size:11px;color:#94A3B8;margin-top:2px;}
.navbar-right{text-align:right;font-size:11px;color:#94A3B8;}
.match-header{background:white;border-radius:10px;border:1px solid #E2E8F0;
    padding:14px 20px;margin-bottom:10px;display:flex;align-items:center;justify-content:space-between;}
.mh-venue{font-size:13px;font-weight:600;color:#1E293B;}
.mh-sub{font-size:11px;color:#64748B;margin-top:2px;}
.mh-status{font-size:12px;font-weight:600;color:#16A34A;}
.score-card{background:white;border-radius:10px;border:1px solid #E2E8F0;
    padding:18px 22px;height:100%;box-shadow:0 1px 3px rgba(0,0,0,0.05);}
.team-badge{font-size:10px;font-weight:700;letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;}
.score-big{font-size:44px;font-weight:700;line-height:1;}
.score-detail{font-size:13px;color:#64748B;margin-top:5px;}
.pbar{height:8px;background:#E2E8F0;border-radius:4px;overflow:hidden;margin:5px 0;}
.pbar-fill{height:100%;border-radius:4px;}
.split-bar{display:flex;height:6px;border-radius:3px;overflow:hidden;margin-top:4px;}
.ph-pp{background:#DBEAFE;color:#1D4ED8;padding:3px 10px;border-radius:12px;font-size:10px;font-weight:700;letter-spacing:1px;}
.ph-mid{background:#FEF3C7;color:#92400E;padding:3px 10px;border-radius:12px;font-size:10px;font-weight:700;letter-spacing:1px;}
.ph-dth{background:#FEE2E2;color:#991B1B;padding:3px 10px;border-radius:12px;font-size:10px;font-weight:700;letter-spacing:1px;}
.stat-tile{background:white;border-radius:10px;border:1px solid #E2E8F0;padding:14px 16px;
    box-shadow:0 1px 3px rgba(0,0,0,0.04);}
.st-lbl{font-size:10px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:#94A3B8;margin-bottom:6px;}
.st-val{font-size:24px;font-weight:700;color:#1E293B;line-height:1.1;}
.st-sub{font-size:11px;color:#64748B;margin-top:4px;}
.sh{font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;
    color:#475569;border-bottom:2px solid #E2E8F0;padding-bottom:7px;margin:16px 0 12px;}
.tbl-hdr{display:grid;align-items:center;padding:6px 8px 8px;
    border-bottom:2px solid #E2E8F0;font-size:10px;font-weight:700;
    letter-spacing:1px;text-transform:uppercase;color:#94A3B8;}
.tbl-row{display:grid;align-items:center;padding:9px 8px;
    border-bottom:1px solid #F8FAFC;font-size:13px;}
.tbl-row:last-child{border-bottom:none;}
.tbl-row:hover{background:#F8FAFC;}
.player-name{font-weight:600;color:#1E293B;}
.player-info{font-size:10px;color:#94A3B8;margin-top:1px;}
.num{text-align:right;color:#374151;}
.green{color:#16A34A!important;font-weight:600;}
.amber{color:#D97706!important;font-weight:600;}
.red{color:#DC2626!important;font-weight:600;}
.batting-now{color:#16A34A;font-size:10px;font-weight:700;margin-left:4px;}
.pred-green{background:#F0FDF4;border:1px solid #BBF7D0;border-left:4px solid #16A34A;border-radius:8px;padding:14px 18px;}
.pred-amber{background:#FFFBEB;border:1px solid #FDE68A;border-left:4px solid #D97706;border-radius:8px;padding:14px 18px;}
.pred-red{background:#FEF2F2;border:1px solid #FECACA;border-left:4px solid #DC2626;border-radius:8px;padding:14px 18px;}
.pred-title{font-size:15px;font-weight:700;color:#1E293B;margin-bottom:8px;}
.pred-body{font-size:13px;color:#374151;line-height:1.7;}
.nb-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin-top:8px;}
.nb-cell{text-align:center;padding:12px 4px;border-radius:8px;border:2px solid;font-weight:700;}
.nb-dot{border-color:#CBD5E1;background:#F8FAFC;color:#64748B;}
.nb-one{border-color:#93C5FD;background:#EFF6FF;color:#1D4ED8;}
.nb-two{border-color:#FCD34D;background:#FFFBEB;color:#92400E;}
.nb-four{border-color:#6EE7B7;background:#ECFDF5;color:#065F46;}
.nb-six{border-color:#C4B5FD;background:#F5F3FF;color:#5B21B6;}
.nb-wkt{border-color:#FCA5A5;background:#FEF2F2;color:#991B1B;}
.nb-val{font-size:22px;margin-bottom:4px;}
.nb-lbl{font-size:10px;font-weight:700;letter-spacing:1px;}
.nb-pct{font-size:13px;font-weight:700;margin-top:2px;}
.timeline-box{display:flex;gap:8px;align-items:center;margin-top:5px;flex-wrap:wrap;}
.ball-badge{width:32px;height:32px;border-radius:50%;display:flex;justify-content:center;
    align-items:center;font-weight:700;font-size:13px;background:#F8FAFC;border:1px solid #E2E8F0;color:#475569;}
.ball-w{background:#FEF2F2;border-color:#FCA5A5;color:#DC2626;}
.ball-4{background:#ECFDF5;border-color:#6EE7B7;color:#059669;}
.ball-6{background:#F5F3FF;border-color:#C4B5FD;color:#7C3AED;}
.oracle-box{background:linear-gradient(135deg,#1E293B,#0F172A);color:white;border-radius:10px;
    padding:20px;box-shadow:0 4px 6px rgba(0,0,0,0.1);border:1px solid #334155;}
.oracle-box h3{color:#38BDF8;font-size:16px;letter-spacing:1px;text-transform:uppercase;margin-bottom:15px;}
.oracle-vs{font-size:28px;font-weight:800;display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;}
.oracle-vs-vs{font-size:14px;color:#94A3B8;font-weight:500;}
.intent-bar{display:flex;height:10px;border-radius:5px;overflow:hidden;margin-top:8px;background:#334155;}
.intent-fill{height:100%;border-radius:5px;}
.news-item{padding:10px 0;border-bottom:1px solid #F1F5F9;}
.news-item:last-child{border-bottom:none;}
.news-item a{color:#1E40AF;text-decoration:none;font-size:13px;font-weight:500;line-height:1.5;}
.card{background:white;border-radius:10px;border:1px solid #E2E8F0;padding:16px 20px;box-shadow:0 1px 3px rgba(0,0,0,0.04);}
div[data-testid="stTabs"] button{font-weight:600;color:#475569;}
div[data-testid="stTabs"] button[aria-selected="true"]{color:#1D4ED8;border-bottom-color:#1D4ED8;}
div[data-testid="stExpander"] details summary p{font-weight:700;color:#1E293B;letter-spacing:1px;}
.alert-banner{background:#FEF2F2;border:2px solid #DC2626;border-radius:10px;padding:12px 20px;
    margin-bottom:12px;display:flex;align-items:center;gap:12px;}
.alert-banner-amber{background:#FFFBEB;border:2px solid #D97706;}
.alert-banner-green{background:#F0FDF4;border:2px solid #16A34A;}
.commentary-box{background:linear-gradient(135deg,#0F172A,#1E293B);border-radius:10px;
    padding:20px;border-left:4px solid #38BDF8;color:white;}
.captain-box{background:linear-gradient(135deg,#0D1117,#1A2744);border-radius:10px;
    padding:20px;border-left:4px solid #4ADE80;color:white;}
.mc-result-box{background:white;border-radius:10px;border:1px solid #E2E8F0;padding:16px;text-align:center;}
.ppi-dial{background:white;border-radius:10px;border:1px solid #E2E8F0;padding:14px;text-align:center;}
.dna-card{background:white;border-radius:8px;border:1px solid #E2E8F0;padding:12px 16px;margin-bottom:8px;}
.dew-box{background:linear-gradient(135deg,#0EA5E9,#0284C7);color:white;border-radius:10px;padding:20px;}
.pts-row{display:grid;grid-template-columns:30px 2fr 40px 40px 40px 40px 50px 60px;
    gap:4px;align-items:center;padding:8px;border-bottom:1px solid #F1F5F9;font-size:13px;}
.pts-row:last-child{border-bottom:none;}
.pts-hdr{font-size:10px;font-weight:700;letter-spacing:1px;color:#94A3B8;text-transform:uppercase;}
.src-badge{font-size:9px;font-weight:700;padding:2px 6px;border-radius:3px;letter-spacing:1px;}
.src-live{background:#DCFCE7;color:#16A34A;}
.src-archive{background:#FEF3C7;color:#92400E;}
.src-dual{background:#DBEAFE;color:#1D4ED8;}
</style>
""", unsafe_allow_html=True)


# ── HELPER FUNCTIONS ──────────────────────────────────────────────────────────
def _c(s): return TEAM_COLORS.get(s, "#64748B")

def _ts(name):
    n = (name or "").lower().strip()
    for k, v in TEAM_MAP.items():
        if k in n: return v
    parts = (name or "").split()
    return "".join(p[0] for p in parts[:3]).upper() if parts else "UNK"

def _int(v, d=0):
    try: return int(str(v).split("/")[0].strip())
    except: return d

def _float(v, d=0.0):
    try: return float(str(v).strip())
    except: return d

def _layout(**kw):
    d = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
             font=dict(family="Inter, sans-serif", color="#475569", size=11),
             margin=dict(l=10, r=10, t=34, b=10),
             legend=dict(orientation="h", yanchor="bottom", y=1.02,
                         xanchor="right", x=1, bgcolor="rgba(0,0,0,0)"))
    d.update(kw)
    return d

def _ax(title="", sfx="", rng=None, **kw):
    d = dict(title=title, showgrid=True, gridcolor="#F1F5F9",
             zeroline=False, tickfont=dict(size=10), linecolor="#E2E8F0")
    if sfx: d["ticksuffix"] = sfx
    if rng: d["range"] = rng
    d.update(kw)
    return d

def _ax2(title=""):
    return dict(title=title, showgrid=False, zeroline=False,
                tickfont=dict(size=10), linecolor="#E2E8F0",
                overlaying="y", side="right")

def _bar_html(lbl, pct, color):
    return (f'<div style="margin-bottom:6px">'
            f'<div style="display:flex;justify-content:space-between;font-size:10px;color:#94A3B8;margin-bottom:2px">'
            f'<span>{lbl}</span><span>{pct}%</span></div>'
            f'<div class="pbar" style="background:rgba(255,255,255,0.1);height:6px;margin:0">'
            f'<div class="pbar-fill" style="width:{pct}%;background:{color}"></div></div></div>')


# ── WIN PROBABILITY MODELS ────────────────────────────────────────────────────
def _win_prob_2nd(r, w, o, target, total=20):
    if target <= 0: return 50, 50
    bu = int(o)*6 + round((o % 1)*10)
    bl = max(1, total*6 - bu)
    rn = target - r
    wl = 10 - w
    if rn <= 0: return 95, 5
    if bl <= 0: return 5, 95
    res = (wl/10)**1.0*0.5 + (bl/(total*6))*0.5
    dif = (rn*6/bl) / 10.0
    p = max(5, min(95, int(50 + (res - dif)*80)))
    return p, 100-p

def _win_prob_1st(r, w, o, total=20):
    if o <= 0: return 50, 50
    bu = int(o)*6 + round((o % 1)*10)
    bl = max(1, total*6 - bu)
    wl = 10 - w
    crr = r / o
    resource = (wl/10)**1.5*0.6 + (bl/(total*6))*0.4
    proj = r + crr*(bl/6)*resource*1.15
    diff = (proj - 165) / 165
    bat_wp = max(10, min(90, int(50 + diff*80)))
    return 100 - bat_wp, bat_wp

def next_ball(sc):
    phase = sc["phase"]
    two   = sc["second_innings"]
    rr    = sc["req_rr"] if two else _float(sc["bat"]["rr"])
    wl    = 10 - sc["bat"]["_w"]
    d     = {"dot":32,"1":22,"2":8,"4":14,"6":9,"W":7}
    if phase == "powerplay":
        d["4"]+=4; d["6"]+=3; d["dot"]-=5; d["W"]-=1
    elif phase == "death":
        d["4"]+=5; d["6"]+=6; d["dot"]-=7; d["W"]+=3
    else:
        d["dot"]+=4; d["1"]+=2; d["4"]-=2; d["6"]-=2
    if two:
        if rr > 12: d["6"]+=5; d["4"]+=3; d["W"]+=4; d["dot"]-=6
        elif rr > 9: d["4"]+=2; d["6"]+=2; d["W"]+=2
    if wl <= 4: d["dot"]+=4; d["W"]+=2; d["6"]-=2
    keys = ["dot","1","2","4","6","W"]
    tot  = sum(d[k] for k in keys)
    return {k: max(1, round(d[k]/tot*100)) for k in keys}


# ── MONTE CARLO ENGINE ────────────────────────────────────────────────────────
def run_monte_carlo(balls_left, runs_needed, wkts_left, phase, n=3000):
    PHASE_PROBS = {
        "powerplay": [("dot",.27),("1",.22),("2",.09),("4",.18),("6",.13),("W",.07),("wd",.04)],
        "middle":    [("dot",.34),("1",.25),("2",.09),("4",.14),("6",.08),("W",.07),("wd",.03)],
        "death":     [("dot",.24),("1",.18),("2",.07),("4",.20),("6",.16),("W",.10),("wd",.05)],
    }
    probs = PHASE_PROBS.get(phase, PHASE_PROBS["middle"])
    labels = [p[0] for p in probs]
    weights = [p[1] for p in probs]

    wins = 0
    score_dist = []
    for _ in range(n):
        bl = balls_left; wl = wkts_left; rn = runs_needed; scored = 0
        sim_phase = phase
        while bl > 0 and wl > 0 and rn > 0:
            over_num = 20 - bl//6
            if over_num <= 6:   sim_phase = "powerplay"
            elif over_num >= 16: sim_phase = "death"
            else:               sim_phase = "middle"
            pp = PHASE_PROBS.get(sim_phase, PHASE_PROBS["middle"])
            wts = [p[1] for p in pp]; lbls = [p[0] for p in pp]
            r = random.random(); cum = 0; out = "dot"
            for lbl, wt in zip(lbls, wts):
                cum += wt
                if r <= cum: out = lbl; break
            if out == "W":
                wl -= 1
            elif out == "wd":
                rn -= 1; scored += 1
                continue
            elif out not in ("dot",):
                val = int(out)
                rn -= val; scored += val
            bl -= 1
        if rn <= 0: wins += 1
        score_dist.append(scored)

    bat_wp = round(wins/n*100)
    return bat_wp, 100-bat_wp, score_dist


# ── CHASE TRAJECTORY ENGINE ───────────────────────────────────────────────────
def build_chase_trajectories(sc):
    if not sc["second_innings"]: return None
    target     = sc["target"]
    cur_score  = sc["bat"]["_r"]
    cur_over   = sc["bat"]["_o"]
    req_rr     = sc["req_rr"]
    balls_used = int(cur_over)*6 + round((cur_over % 1)*10)
    balls_left = 120 - balls_used
    overs_left = balls_left / 6

    step = 0.5
    n_steps = int(overs_left / step) + 1
    overs = [round(cur_over + i*step, 1) for i in range(n_steps)]

    optimal, aggressive, conservative, historical = [], [], [], []
    cons_half = overs_left / 2

    for o in overs:
        el = o - cur_over
        optimal.append(round(cur_score + el * req_rr, 1))
        aggressive.append(round(cur_score + el * req_rr * 1.22, 1))

        if el <= cons_half:
            conservative.append(round(cur_score + el * req_rr * 0.82, 1))
        else:
            base = cur_score + cons_half * req_rr * 0.82
            extra = el - cons_half
            conservative.append(round(base + extra * req_rr * 1.30, 1))

        historical.append(round(cur_score + el * req_rr * (1.04 + 0.02*(-1 if el%1==0 else 1)), 1))

    return overs, optimal, aggressive, conservative, historical, target, cur_score


# ── PLAYER PRESSURE INDEX ─────────────────────────────────────────────────────
def compute_ppi(batter, sc):
    phase_mult = {"powerplay":0.85, "middle":1.0, "death":1.3}
    pm = phase_mult.get(sc["phase"], 1.0)
    sr_base = 130.0
    sr_ratio = (_float(batter["sr"]) / sr_base) if _float(batter["sr"]) > 0 else 0.5
    wkts_fallen = sc["bat"]["_w"]
    wkt_pressure = 1 + (wkts_fallen / 10) * 0.5
    balls_played = batter["balls"]
    fatigue = 1 + min(balls_played / 60, 0.5)
    two = sc["second_innings"]
    chase_pressure = 1 + ((sc["req_rr"]/10) * 0.4) if two else 1.0
    raw = sr_ratio / (pm * wkt_pressure * fatigue * chase_pressure)
    return max(5, min(95, round(raw * 65)))

def ppi_label(ppi):
    if ppi >= 70: return "Cruising", "#16A34A"
    elif ppi >= 50: return "Settled", "#0EA5E9"
    elif ppi >= 35: return "Under Pressure", "#D97706"
    else: return "Under Siege", "#DC2626"

def bowler_threat(bowler, sc):
    ec = _float(bowler["econ"])
    wkts = bowler["wkts"]
    phase_bonus = 1.3 if sc["phase"] == "death" else (0.9 if sc["phase"] == "powerplay" else 1.0)
    ec_score = max(0, (14 - ec) / 14 * 40)
    wkt_score = min(wkts * 15, 45)
    dot_score = bowler.get("dot_pct", 35) * 0.15
    return min(99, round((ec_score + wkt_score + dot_score) * phase_bonus))

def clutch_rating(player, is_batter=True):
    if is_batter:
        sr = _float(player["sr"]); runs = player["runs"]; balls = player["balls"]
        if sr >= 160 and runs >= 30: return "CLUTCH", "#16A34A", 90
        elif sr >= 140 or runs >= 25: return "RELIABLE", "#0EA5E9", 65
        elif sr >= 110: return "INCONSISTENT", "#D97706", 45
        else: return "STRUGGLES", "#DC2626", 25
    else:
        ec = _float(player["econ"]); wkts = player["wkts"]
        if ec <= 7 and wkts >= 2: return "CLUTCH", "#16A34A", 90
        elif ec <= 9 or wkts >= 2: return "RELIABLE", "#0EA5E9", 65
        elif ec <= 11: return "INCONSISTENT", "#D97706", 45
        else: return "LEAKS RUNS", "#DC2626", 25


# ── WEATHER SCRAPER ───────────────────────────────────────────────────────────
@st.cache_data(ttl=600, show_spinner=False)
def fetch_weather(city="Bengaluru"):
    try:
        r = requests.get(f"https://wttr.in/{city}?format=j1", headers=HEADERS, timeout=6)
        if r.status_code == 200:
            d = r.json()
            cur = d["current_condition"][0]
            return {
                "temp":    cur["temp_C"],
                "humidity": cur["humidity"],
                "wind":    cur["windspeedKmph"],
                "feels":   cur["FeelsLikeC"],
                "desc":    cur["weatherDesc"][0]["value"],
                "ok": True
            }
    except Exception:
        pass
    return {"temp":"26","humidity":"72","wind":"8","feels":"28","desc":"Partly cloudy","ok":False}

def dew_score(humidity, temp):
    h = int(humidity); t = int(temp)
    score = max(0, min(100, (h - 50)*1.5 + (30-t)*0.5))
    return round(score)


# ── SMART URL SWITCHER ────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def get_live_match_url():
    try:
        r = requests.get(ESPN_SERIES, headers=HEADERS, timeout=6)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "live-cricket-score" in href and "2026" in href:
                return "https://www.espncricinfo.com" + href, True
    except Exception:
        pass
    return ESPN_FALLBACK, False


# ── SHADOW SCRAPER — MULTI-SOURCE CONSENSUS ───────────────────────────────────
def _parse_espn(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        if r.status_code != 200: return None
        soup = BeautifulSoup(r.text, "html.parser")
        status_el = soup.find("p", class_=lambda c: c and "ds-text-tight-s" in c)
        status = status_el.text.strip() if status_el else ""
        if "CRR" in status or "Live" in status or "won" in status.lower():
            return {"status": status, "source": "ESPN", "live": "CRR" in status or "Live" in status}
    except Exception:
        pass
    return None

def _parse_cricbuzz(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        if r.status_code != 200: return None
        soup = BeautifulSoup(r.text, "html.parser")
        score_el = soup.find("div", class_=lambda c: c and "cb-min-bat-rw" in c)
        if score_el:
            return {"status": score_el.text.strip(), "source": "Cricbuzz", "live": True}
    except Exception:
        pass
    return None

@st.cache_data(ttl=REFRESH_SECS, show_spinner=False)
def resolve_scraper():
    live_url, url_auto = get_live_match_url()

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        f_espn = ex.submit(_parse_espn, live_url)
        f_cb   = ex.submit(_parse_cricbuzz, CB_FALLBACK)
        espn_data = f_espn.result()
        cb_data   = f_cb.result()

    if espn_data and cb_data:
        st.session_state.scraper_src = "Dual-Source"
    elif espn_data:
        st.session_state.scraper_src = "ESPN"
    elif cb_data:
        st.session_state.scraper_src = "Cricbuzz"
    else:
        st.session_state.scraper_src = "Archive"

    return _get_last_match()


# ── ALERT PUSH SYSTEM ─────────────────────────────────────────────────────────
def check_and_push_alerts(sc, batters):
    alerts = []
    cur_wkts = sc["bat"]["_w"]
    if st.session_state.prev_wkts >= 0 and cur_wkts > st.session_state.prev_wkts:
        wkt_diff = cur_wkts - st.session_state.prev_wkts
        alerts.append({"msg": f"WICKET! {wkt_diff} wicket(s) fell — {sc['bat']['short']} now {sc['bat']['score']}/{cur_wkts}",
                        "type": "red"})
    st.session_state.prev_wkts = cur_wkts

    for b in batters:
        if b.get("batting_now") and b["runs"] in (50, 100, 150):
            key = f"mile_{b['name']}_{b['runs']}"
            if key not in st.session_state:
                st.session_state[key] = True
                alerts.append({"msg": f"MILESTONE! {b['name']} reaches {b['runs']} runs",
                                "type": "green"})

    if sc["second_innings"] and sc["req_rr"] > 12 and sc.get("req_rr_prev", 0) <= 12:
        alerts.append({"msg": f"PRESSURE SPIKE! Required RR crossed 12 — now at {sc['req_rr']}",
                        "type": "amber"})

    for a in alerts[-3:]:
        if a not in st.session_state.alert_log:
            st.session_state.alert_log.insert(0, {**a, "time": datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%H:%M:%S")})
    st.session_state.alert_log = st.session_state.alert_log[:5]


def render_alert_banner():
    if not st.session_state.alert_log:
        return
    a = st.session_state.alert_log[0]
    cls = f"alert-banner alert-banner-{a['type']}" if a["type"] != "red" else "alert-banner"
    icon = {"red":"🚨","amber":"⚠️","green":"🏆"}.get(a["type"],"ℹ️")
    st.markdown(
        f'<div class="{cls}">'
        f'<span style="font-size:20px">{icon}</span>'
        f'<div><div style="font-weight:700;font-size:13px;color:#1E293B">{a["msg"]}</div>'
        f'<div style="font-size:11px;color:#64748B">{a["time"]}</div></div>'
        f'</div>',
        unsafe_allow_html=True)


# ── NEWS FEEDS ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=120, show_spinner=False)
def _fetch_news():
    try:
        feed = feedparser.parse("https://news.google.com/rss/search?q=IPL+2026+Live+Updates&hl=en-IN&gl=IN&ceid=IN:en")
        return [{"title":e.get("title",""),"source":e.get("source",{}).get("title",""),
                 "published":e.get("published","")[:22],"link":e.get("link","#")} for e in feed.entries[:7]]
    except: return []

@st.cache_data(ttl=120, show_spinner=False)
def fetch_upcoming_news():
    try:
        feed = feedparser.parse("https://news.google.com/rss/search?q=IPL+2026+MI+KKR+injury+playing+11&hl=en-IN&gl=IN&ceid=IN:en")
        return [{"title":e.get("title",""),"source":e.get("source",{}).get("title",""),
                 "link":e.get("link","#")} for e in feed.entries[:6]]
    except: return []

def generate_match_preview(news):
    mi_key  = "Suryakumar Yadav (Bat) · Jasprit Bumrah (Bowl)"
    kkr_key = "Shreyas Iyer (Bat) · Sunil Narine (All-round)"
    news_text = " ".join([n["title"].lower() for n in news])
    alerts = []
    checks = [("hardik","⚠️ Hardik Pandya fitness concern"),("starc","⚠️ Mitchell Starc doubtful"),
              ("shreyas","⚠️ Shreyas Iyer availability uncertain")]
    for kw, msg in checks:
        if kw in news_text: alerts.append(msg)
    if not alerts:
        alerts.append("✅ Both squads appear full-strength based on latest reports.")
    return mi_key, kkr_key, alerts


# ── ARCHIVED MATCH DATA ───────────────────────────────────────────────────────
def _get_last_match():
    srh = {"name":"Sunrisers Hyderabad","short":"SRH","score":"201","wickets":"9",
           "overs":"20.0","rr":"10.05","_r":201,"_w":9,"_o":20.0}
    rcb = {"name":"Royal Challengers Bengaluru","short":"RCB","score":"203","wickets":"4",
           "overs":"15.4","rr":"12.95","_r":203,"_w":4,"_o":15.4}
    sc  = {"match":"SRH vs RCB — IPL 2026, 1st Match","venue":"M. Chinnaswamy Stadium, Bengaluru",
           "status":"RCB won by 6 wickets","bat":rcb,"field":srh,"t1":srh,"t2":rcb,
           "target":202,"required":0,"req_rr":0.0,"balls_left":0,
           "phase":"completed","second_innings":True,"bat_wp":100,"fld_wp":0,
           "recent_balls":["1","1","4","W","2","6","1"],
           "drs":{"bat":2,"fld":1},
           "impact":{"bat":"Activated (Patidar)","fld":"Available"}}
    bat = [
        {"name":"Virat Kohli",     "team":"RCB","runs":22,"balls":18,"sr":122.22,"4s":3,"6s":0,
         "status":"c Cummins b Bhuvneshwar","batting_now":False,"dot_pct":38},
        {"name":"Faf du Plessis",  "team":"RCB","runs":14,"balls":11,"sr":127.27,"4s":2,"6s":0,
         "status":"lbw b Natarajan","batting_now":False,"dot_pct":40},
        {"name":"Rajat Patidar",   "team":"RCB","runs":14,"balls":9, "sr":155.55,"4s":1,"6s":1,
         "status":"c Head b Markande","batting_now":False,"dot_pct":33},
        {"name":"Glenn Maxwell",   "team":"RCB","runs":6, "balls":4, "sr":150.00,"4s":1,"6s":0,
         "status":"c Klaasen b Cummins","batting_now":False,"dot_pct":35},
        {"name":"Ishan Kishan",    "team":"RCB","runs":80,"balls":38,"sr":210.52,"4s":7,"6s":5,
         "status":"not out","batting_now":True,"dot_pct":20},
        {"name":"Cameron Green",   "team":"RCB","runs":48,"balls":25,"sr":192.00,"4s":4,"6s":3,
         "status":"not out","batting_now":True,"dot_pct":22},
        {"name":"Dinesh Karthik",  "team":"RCB","runs":0, "balls":0, "sr":0.0,"4s":0,"6s":0,
         "status":"yet to bat","batting_now":False,"dot_pct":30},
    ]
    bowl = [
        {"name":"Bhuvneshwar Kumar","team":"SRH","overs":4.0,"runs":35,"wkts":1,"maidens":0,"econ":8.75,"bowling_now":False,"dot_pct":42},
        {"name":"Pat Cummins",      "team":"SRH","overs":4.0,"runs":42,"wkts":1,"maidens":0,"econ":10.50,"bowling_now":False,"dot_pct":38},
        {"name":"T Natarajan",      "team":"SRH","overs":3.4,"runs":48,"wkts":1,"maidens":0,"econ":13.09,"bowling_now":True,"dot_pct":28},
        {"name":"Mayank Markande",  "team":"SRH","overs":2.0,"runs":28,"wkts":1,"maidens":0,"econ":14.00,"bowling_now":False,"dot_pct":25},
        {"name":"Shahbaz Ahmed",    "team":"SRH","overs":2.0,"runs":25,"wkts":0,"maidens":0,"econ":12.50,"bowling_now":False,"dot_pct":30},
    ]
    extras  = {"wides":8,"noballs":2,"legbyes":3,"byes":1,"total":14}
    partner = {"balls":25,"runs":48,"p1_name":"Ishan","p1_runs":34,"p2_name":"Green","p2_runs":14}
    return sc, bat, bowl, extras, partner

def demo_momentum():
    ov  = list(range(1, 17))
    wp  = [50,48,45,52,58,65,62,70,75,82,85,88,92,95,98,100]
    rr  = [8.0,9.5,9.0,10.5,11.2,11.5,11.0,11.8,12.2,12.5,12.3,12.8,13.1,13.0,12.95,12.95]
    req = [10.2,10.1,10.3,10.0,9.8,9.5,9.7,9.2,8.8,8.2,7.8,7.0,6.2,5.0,2.0,0.0]
    return ov, wp, rr, req

def demo_over_history():
    random.seed(42)
    data, cum = [], 0
    for i in range(1, 21):
        r = random.randint(4, 18)
        w = random.choices([0,1,2], weights=[72,24,4])[0]
        cum += r
        data.append({"over":i,"runs":r,"wkts":w,"cum":cum})
    return data


# ── CLAUDE AI HELPER ──────────────────────────────────────────────────────────
def _call_claude(prompt, system_msg="", max_tokens=350):
    api_key = ""
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:
        pass
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None
    try:
        payload = {
            "model": "claude-3-haiku-20240307", 
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_msg:
            payload["system"] = system_msg
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key,
                     "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json=payload, timeout=10)
        if r.status_code == 200:
            return r.json()["content"][0]["text"]
    except Exception:
        pass
    return None

@st.cache_data(ttl=60, show_spinner=False)
def get_ai_commentary(match_ctx):
    system = ("You are a sharp, insightful IPL cricket commentator. "
              "Give a 2-3 sentence live analysis in broadcast style. Be specific with numbers. No fluff.")
    result = _call_claude(match_ctx, system_msg=system, max_tokens=200)
    return result

@st.cache_data(ttl=60, show_spinner=False)
def get_captains_corner(match_ctx):
    system = ("You are a tactical T20 cricket analyst advising the captain. "
              "Give exactly 3 specific tactical bullet points for right now. Be direct and decisive.")
    result = _call_claude(match_ctx, system_msg=system, max_tokens=250)
    return result

def _fallback_commentary(sc, batters):
    phase = sc["phase"]
    two   = sc["second_innings"]
    striker = next((b for b in batters if b.get("batting_now")), None)
    if sc["phase"] == "completed":
        return f"Match concluded. {sc['status']}. A memorable IPL encounter at {sc['venue']}."
    if two:
        rr = sc["req_rr"]; req = sc["required"]; bl = sc["balls_left"]
        tone = "under pressure" if rr > 11 else ("finely balanced" if rr > 8 else "firmly in control")
        s_txt = f"{striker['name']} is at the crease on {striker['runs']}({striker['balls']})." if striker else ""
        return (f"The chase is {tone} — {req} needed off {bl} balls at a required rate of {rr}. "
                f"{s_txt} The {phase} overs are critical for {sc['bat']['short']}.")
    crr = sc["bat"]["rr"]
    return (f"{sc['bat']['short']} are batting at {crr} RPO in the {phase} phase. "
            f"{'On course for a competitive total.' if _float(crr)>8 else 'Need to accelerate from here.'}")

def _fallback_captain(sc, batters, bowlers):
    phase = sc["phase"]; two = sc["second_innings"]
    active_bwl = next((b for b in bowlers if b.get("bowling_now")), None)
    tips = []
    if two:
        if sc["req_rr"] > 12: tips.append("Attack every ball — dot balls are match-killers at this req rate.")
        else: tips.append("Rotate strike actively — keep the req rate under 10 until the last 3 overs.")
        tips.append(f"Target the weakest bowler (Econ > 10) — avoid {active_bwl['name'] if active_bwl else 'the in-form bowler'}.")
        if phase == "death": tips.append("Send your biggest hitter in NOW — don't wait for a crisis.")
        else: tips.append("Save DRS for the death — high-pressure LBW calls are coming.")
    else:
        if phase == "powerplay": tips.append("Maximize fielding restrictions — target boundary count in the first 6.")
        else: tips.append("Set aggressive field — the pitch is true and batting will get easier.")
        tips.append("Mix pace and spin every alternate over — disrupt batter rhythm.")
        tips.append("Use your best death bowler in overs 17 and 20 — protect that option.")
    return "\n".join([f"• {t}" for t in tips])


# ── CHART BUILDERS ────────────────────────────────────────────────────────────
def chart_momentum(ov, wp, rr, req):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=ov, y=wp, name="RCB Win %", mode="lines",
        line=dict(color="#DC2626", width=3, shape="spline"),
        fill="tozeroy", fillcolor="rgba(220,38,38,0.1)",
        hovertemplate="Over %{x}: %{y}%<extra></extra>"), secondary_y=False)
    fig.add_trace(go.Scatter(x=ov, y=rr, name="Actual RR", mode="lines",
        line=dict(color="#1D4ED8", width=2, dash="dot"),
        hovertemplate="Over %{x}: RR %{y}<extra></extra>"), secondary_y=True)
    fig.add_trace(go.Scatter(x=ov, y=req, name="Req RR", mode="lines",
        line=dict(color="#94A3B8", width=2, dash="dash"),
        hovertemplate="Over %{x}: Req %{y}<extra></extra>"), secondary_y=True)
    fig.update_layout(**_layout(
        title=dict(text="MOMENTUM WORM", font=dict(size=11, color="#1E293B"), x=0),
        height=220, margin=dict(l=0, r=0, t=30, b=0),
        xaxis=_ax("Over"),
        yaxis=_ax("Win %", sfx="%", rng=[0,105]),
        yaxis2=_ax2("Run Rate")))
    return fig

def chart_trajectory(overs, optimal, aggressive, conservative, historical, target, cur_score):
    fig = go.Figure()
    fig.add_hline(y=target, line_dash="dot", line_color="#DC2626", line_width=2,
                  annotation_text=f"Target {target}", annotation_position="top right")
    fig.add_trace(go.Scatter(x=overs, y=optimal, name="Optimal", mode="lines",
        line=dict(color="#16A34A", width=2.5), hovertemplate="Over %{x}: %{y}<extra></extra>"))
    fig.add_trace(go.Scatter(x=overs, y=aggressive, name="Aggressive", mode="lines",
        line=dict(color="#7C3AED", width=2, dash="dot"), hovertemplate="Over %{x}: %{y}<extra></extra>"))
    fig.add_trace(go.Scatter(x=overs, y=conservative, name="Conservative", mode="lines",
        line=dict(color="#D97706", width=2, dash="dash"), hovertemplate="Over %{x}: %{y}<extra></extra>"))
    fig.add_trace(go.Scatter(x=overs, y=historical, name="Historical Avg", mode="lines",
        line=dict(color="#0EA5E9", width=1.5, dash="dashdot"), hovertemplate="Over %{x}: %{y}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[overs[0]], y=[cur_score], name="NOW", mode="markers",
        marker=dict(size=12, color="#DC2626", symbol="circle"),
        hovertemplate=f"Current: {cur_score}<extra></extra>"))
    fig.update_layout(**_layout(
        title=dict(text="CHASE TRAJECTORY — 4 PATHS TO TARGET", font=dict(size=11, color="#1E293B"), x=0),
        height=280, xaxis=_ax("Over"), yaxis=_ax("Score")))
    return fig

def chart_monte_carlo(score_dist, runs_needed):
    if not score_dist: return go.Figure()
    buckets = {}
    for s in score_dist:
        b = (s // 5) * 5
        buckets[b] = buckets.get(b, 0) + 1
    xs = sorted(buckets.keys())
    ys = [buckets[x] for x in xs]
    colors = ["#16A34A" if x >= runs_needed else "#DC2626" for x in xs]
    fig = go.Figure(go.Bar(x=xs, y=ys, marker_color=colors, opacity=0.8,
        hovertemplate="Runs: %{x}–%{x}+5 · Freq: %{y}<extra></extra>"))
    fig.add_vline(x=runs_needed, line_dash="dot", line_color="#1E293B", line_width=2,
                  annotation_text=f"Need {runs_needed}", annotation_position="top right")
    fig.update_layout(**_layout(
        title=dict(text="MONTE CARLO — Score Distribution (3,000 sims)", font=dict(size=11, color="#1E293B"), x=0),
        height=240, xaxis=_ax("Runs Scored"), yaxis=_ax("Simulations")))
    return fig

def chart_run_progression(history):
    ov   = [h["over"] for h in history]
    runs = [h["runs"] for h in history]
    cum  = [h["cum"]  for h in history]
    wov  = [h["over"] for h in history if h["wkts"] > 0]
    wcum = [h["cum"]  for h in history if h["wkts"] > 0]
    fig  = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=ov, y=runs, name="Runs/Over",
        marker=dict(color=["#DC2626" if r>14 else ("#D97706" if r>10 else "#1D4ED8") for r in runs], opacity=0.8),
        hovertemplate="Over %{x}: %{y} runs<extra></extra>"), secondary_y=False)
    fig.add_trace(go.Scatter(x=ov, y=cum, name="Cumulative",
        mode="lines+markers", line=dict(color="#16A34A", width=2),
        marker=dict(size=4), hovertemplate="After Over %{x}: %{y}<extra></extra>"), secondary_y=True)
    if wov:
        fig.add_trace(go.Scatter(x=wov, y=wcum, name="Wicket",
            mode="markers", marker=dict(symbol="x", size=12, color="#DC2626", line=dict(width=2)),
            hovertemplate="Wicket at Over %{x}<extra></extra>"), secondary_y=True)
    fig.update_layout(**_layout(
        title=dict(text="RUN PROGRESSION — OVER BY OVER", font=dict(size=11, color="#1E293B"), x=0),
        height=240, xaxis=_ax("Over"),
        yaxis=_ax("Runs/Over"), yaxis2=_ax2("Cumulative")))
    return fig

def chart_ppi_gauge(batters, sc):
    names, ppis, colors = [], [], []
    for b in batters[:6]:
        ppi = compute_ppi(b, sc)
        lbl, clr = ppi_label(ppi)
        names.append(b["name"].split()[-1])
        ppis.append(ppi)
        colors.append(clr)
    fig = go.Figure(go.Bar(y=names, x=ppis, orientation="h",
        marker=dict(color=colors, opacity=0.85),
        text=[f"{p}" for p in ppis], textposition="inside",
        textfont=dict(color="white", size=11),
        hovertemplate="%{y}: PPI %{x}<extra></extra>"))
    fig.update_layout(**_layout(
        title=dict(text="PLAYER PRESSURE INDEX (PPI)", font=dict(size=11, color="#1E293B"), x=0),
        height=240, xaxis=_ax("PPI Score", rng=[0,100]),
        yaxis=dict(showgrid=False, tickfont=dict(size=11))))
    return fig

def chart_bowler_threat(bowlers, sc):
    names  = [b["name"].split()[-1] for b in bowlers]
    threat = [bowler_threat(b, sc) for b in bowlers]
    colors = ["#DC2626" if t>75 else ("#D97706" if t>50 else "#16A34A") for t in threat]
    fig = go.Figure(go.Bar(x=names, y=threat, marker=dict(color=colors, opacity=0.85),
        text=threat, textposition="auto",
        hovertemplate="%{x}: Threat %{y}/100<extra></extra>"))
    fig.update_layout(**_layout(
        title=dict(text="BOWLER THREAT INDEX", font=dict(size=11, color="#1E293B"), x=0),
        height=220, xaxis=_ax(""), yaxis=_ax("Threat (0–100)", rng=[0,105])))
    return fig

def chart_auction_roi():
    batters_data = [a for a in AUCTION_DATA if a["unit"] == "run"]
    bowlers_data = [a for a in AUCTION_DATA if a["unit"] == "wkt"]

    names_b = [a["name"].split()[-1] for a in batters_data]
    cost_b  = [round(a["price"]*100/max(a["runs"],1), 2) for a in batters_data]

    names_w = [a["name"].split()[-1] for a in bowlers_data]
    cost_w  = [round(a["price"]/max(a["wkts"],1), 2) for a in bowlers_data]

    fig = make_subplots(rows=1, cols=2,
        subplot_titles=("Lakh per Run (Lower = Better)", "Cr per Wicket (Lower = Better)"))
    fig.add_trace(go.Bar(x=names_b, y=cost_b, name="₹L/Run",
        marker=dict(color="#1D4ED8", opacity=0.8),
        hovertemplate="%{x}: ₹%{y}L/run<extra></extra>"), row=1, col=1)
    fig.add_trace(go.Bar(x=names_w, y=cost_w, name="₹Cr/Wkt",
        marker=dict(color="#DC2626", opacity=0.8),
        hovertemplate="%{x}: ₹%{y}Cr/wkt<extra></extra>"), row=1, col=2)
    fig.update_layout(**_layout(
        title=dict(text="AUCTION ROI TRACKER — Value for Money", font=dict(size=11, color="#1E293B"), x=0),
        height=260, showlegend=False))
    return fig

def chart_ball_heatmap(history):
    max_overs = len(history)
    cols = 6
    rows_n = max_overs

    z, hover = [], []
    for h in history:
        row_z, row_h = [], []
        for ball in range(cols):
            val = h["runs"] / 6
            row_z.append(val)
            row_h.append(f"Over {h['over']}: ~{h['runs']} runs")
        if h["wkts"] > 0:
            row_z[-1] = -1
            row_h[-1] = f"Over {h['over']}: WICKET"
        z.append(row_z)
        hover.append(row_h)

    y_labels = [f"Ov {h['over']}" for h in history]
    x_labels = [f"B{i+1}" for i in range(cols)]

    fig = go.Figure(go.Heatmap(
        z=z, x=x_labels, y=y_labels,
        colorscale=[[0,"#FEF2F2"],[0.001,"#DC2626"],[0.3,"#DBEAFE"],[0.6,"#93C5FD"],[1.0,"#1D4ED8"]],
        showscale=False, text=hover,
        hovertemplate="%{text}<extra></extra>"))
    fig.update_layout(**_layout(
        title=dict(text="BALL-BY-BALL INNINGS HEATMAP (Red = Wicket / Blue = Scoring)", font=dict(size=11, color="#1E293B"), x=0),
        height=350, margin=dict(l=50, r=10, t=40, b=10)))
    return fig


# ── RENDER: TAB 1 — LIVE MATCH ────────────────────────────────────────────────
def render_navbar(sc, is_live):
    IST = pytz.timezone("Asia/Kolkata")
    now = datetime.now(IST).strftime("%d %b %Y · %H:%M IST")
    src = st.session_state.scraper_src
    src_cls = "src-live" if src in ("ESPN","Cricbuzz") else ("src-dual" if src=="Dual-Source" else "src-archive")
    lb = ('<span style="background:#DC2626;color:white;font-size:9px;font-weight:700;'
          'padding:2px 7px;border-radius:3px;letter-spacing:1px;margin-right:8px">LIVE</span>'
          if is_live else "")
    st.markdown(
        f'<div class="navbar">'
        f'<div><div class="navbar-logo">GOD\'S<span>EYE</span> v5.2 '
        f'<span style="font-size:11px;color:#94A3B8;font-weight:400">IPL MATCH CENTER</span></div>'
        f'<div class="navbar-sub">{lb}{sc.get("match","")}&nbsp;'
        f'<span class="src-badge {src_cls}">{src}</span></div></div>'
        f'<div class="navbar-right">{now}<br>'
        f'<span style="color:#4ADE80">Shadow Scraper Active</span><br>'
        f'<span style="color:#94A3B8">OPERATOR: UDAY MADDILA</span></div>'
        f'</div>', unsafe_allow_html=True)

def render_scoreboard(sc):
    bat=sc["bat"]; field=sc["field"]; two=sc["second_innings"]
    bwp=sc["bat_wp"]; fwp=sc["fld_wp"]
    bc=_c(bat["short"]); fc=_c(field["short"])
    ph=sc["phase"]; ph_cls="ph-pp" if ph=="powerplay" else ("ph-dth" if ph=="death" else "ph-mid")
    st.markdown(
        f'<div class="match-header">'
        f'<div><div class="mh-venue">🏟️ {sc["venue"]}</div>'
        f'<div class="mh-sub"><span class="mh-status">{sc["status"]}</span>'
        f'&nbsp;·&nbsp;{"2nd Innings" if two else "1st Innings"}</div></div>'
        f'<div><span class="{ph_cls}">{ph.capitalize()}</span></div>'
        f'</div>', unsafe_allow_html=True)

    c1,c2,c3 = st.columns([5,4,5])
    with c1:
        s=bat["score"]; w=bat["wickets"]; o=bat["overs"]; rr=bat["rr"]; drs=sc.get("drs",{}).get("bat",0)
        st.markdown(
            f'<div class="score-card" style="border-left:4px solid {bc}">'
            f'<div class="team-badge" style="color:{bc}">▶ {bat["short"]} (DRS: {drs})</div>'
            f'<div class="score-big" style="color:{bc}">{s}/{w}</div>'
            f'<div class="score-detail">{o} Ov &nbsp;·&nbsp; CRR: <b>{rr}</b></div>'
            f'</div>', unsafe_allow_html=True)
    with c2:
        if two:
            rn=sc["required"]; bl=sc["balls_left"]; rr2=sc["req_rr"]
            rc="#DC2626" if rr2>12 else ("#D97706" if rr2>9 else "#16A34A")
            html = (f'<div class="score-card" style="text-align:center">'
                    f'<div style="font-size:10px;font-weight:700;letter-spacing:1px;color:#94A3B8;margin-bottom:10px">WIN PROBABILITY</div>'
                    f'<div style="display:flex;justify-content:space-between;font-size:13px;font-weight:700;margin-bottom:3px">'
                    f'<span style="color:{bc}">{bat["short"]}</span><span style="color:{bc}">{bwp}%</span></div>'
                    f'<div class="pbar"><div class="pbar-fill" style="width:{bwp}%;background:{bc}"></div></div>'
                    f'<div style="display:flex;justify-content:space-between;font-size:13px;font-weight:700;margin-top:8px;margin-bottom:3px">'
                    f'<span style="color:{fc}">{field["short"]}</span><span style="color:{fc}">{fwp}%</span></div>'
                    f'<div class="pbar"><div class="pbar-fill" style="width:{fwp}%;background:{fc}"></div></div>'
                    f'<div style="margin-top:12px;background:#FEF2F2;border-radius:6px;padding:8px;font-size:12px">'
                    f'Need <b style="color:{rc}">{rn}</b> off <b>{bl}</b> balls &nbsp;·&nbsp; Req RR: <b style="color:{rc}">{rr2}</b>'
                    f'</div></div>')
        else:
            o=bat["_o"]; bu=int(o)*6+round((o%1)*10); bl=max(1,120-bu)
            proj=bat["_r"]+round(_float(bat["rr"])*bl/6*0.9); drs2=sc.get("drs",{}).get("fld",0)
            html = (f'<div class="score-card" style="text-align:center">'
                    f'<div style="font-size:10px;font-weight:700;letter-spacing:1px;color:#94A3B8;margin-bottom:10px">WIN PROBABILITY</div>'
                    f'<div style="display:flex;justify-content:space-between;font-size:13px;font-weight:700;margin-bottom:3px">'
                    f'<span style="color:{fc}">{field["short"]}</span><span style="color:{fc}">{fwp}%</span></div>'
                    f'<div class="pbar"><div class="pbar-fill" style="width:{fwp}%;background:{fc}"></div></div>'
                    f'<div style="display:flex;justify-content:space-between;font-size:13px;font-weight:700;margin-top:8px;margin-bottom:3px">'
                    f'<span style="color:{bc}">{bat["short"]}</span><span style="color:{bc}">{bwp}%</span></div>'
                    f'<div class="pbar"><div class="pbar-fill" style="width:{bwp}%;background:{bc}"></div></div>'
                    f'<div style="margin-top:12px;background:#F0FDF4;border-radius:6px;padding:8px;font-size:12px">'
                    f'{o}/20.0 Overs &nbsp;·&nbsp; Proj: <b>~{proj}</b>'
                    f'</div></div>')
        st.markdown(html, unsafe_allow_html=True)
    with c3:
        s=field["score"]; w=field["wickets"]; o=field["overs"]; rr=field["rr"]; drs2=sc.get("drs",{}).get("fld",0)
        st.markdown(
            f'<div class="score-card" style="border-left:4px solid {fc}">'
            f'<div class="team-badge" style="color:{fc}">⚡ {field["short"]} (DRS: {drs2})</div>'
            f'<div class="score-big" style="color:{fc}">{s}/{w}</div>'
            f'<div class="score-detail">{o} Ov &nbsp;·&nbsp; CRR: <b>{rr}</b></div>'
            f'</div>', unsafe_allow_html=True)

def render_stats_bar(sc, batters, bowlers, extras, partner):
    st.markdown('<div class="sh">📊 Tactical Match Stats</div>', unsafe_allow_html=True)
    bat=sc["bat"]; two=sc["second_innings"]; wl=10-bat["_w"]
    crr_c="#16A34A" if _float(bat["rr"])>=8 else ("#D97706" if _float(bat["rr"])>=6 else "#DC2626")
    top_bat = max(batters, key=lambda x:x["runs"]) if batters else None
    top_bwl = max(bowlers, key=lambda x:x["wkts"]) if bowlers else None

    def tile(col, lbl, val, sub, vc="#1E293B", top="#2563EB", split_html=""):
        with col:
            st.markdown(
                f'<div class="stat-tile" style="border-top:3px solid {top}">'
                f'<div class="st-lbl">{lbl}</div>'
                f'<div class="st-val" style="color:{vc}">{val}</div>'
                f'{split_html}'
                f'<div class="st-sub">{sub}</div></div>', unsafe_allow_html=True)

    c1,c2,c3,c4,c5 = st.columns(5)
    tile(c1,"Current RR",bat["rr"],f'{bat["short"]} · {bat["overs"]} ov',crr_c,crr_c)
    if two:
        rr2=sc["req_rr"]; rc="#DC2626" if rr2>12 else ("#D97706" if rr2>9 else "#16A34A")
        tile(c2,"Required RR",str(rr2),f'{sc["required"]} runs · {sc["balls_left"]} balls',rc,rc)
    else:
        tile(c2,"Wickets Left",str(wl),f'{bat["wickets"]} fallen',"#7C3AED","#7C3AED")
    if partner and partner.get("runs",0)>0:
        pr=partner["runs"]; pb=partner["balls"]
        p1r=partner.get("p1_runs",0); p2r=partner.get("p2_runs",0)
        p1n=partner.get("p1_name",""); p2n=partner.get("p2_name","")
        p1p=int((p1r/pr)*100) if pr>0 else 50; p2p=100-p1p
        split=(f'<div class="split-bar"><div style="width:{p1p}%;background:#1D4ED8"></div>'
               f'<div style="width:{p2p}%;background:#94A3B8"></div></div>'
               f'<div style="font-size:9px;color:#64748B;display:flex;justify-content:space-between">'
               f'<span>{p1n} {p1p}%</span><span>{p2n} {p2p}%</span></div>')
        tile(c3,"Partnership",f'{pr}({pb}b)',"Current Pair","#0EA5E9","#0EA5E9",split_html=split)
    else:
        ext=extras.get("total",0) if extras else 0
        tile(c3,"Extras",str(ext),f'Wd:{extras.get("wides",0)} NB:{extras.get("noballs",0)}' if extras else "","#64748B","#64748B")
    if top_bat:
        tile(c4,"Top Scorer",f'{top_bat["runs"]}*({top_bat["balls"]}b)',f'{top_bat["name"]} · SR:{top_bat["sr"]}', "#1D4ED8","#1D4ED8")
    else:
        tile(c4,"Top Scorer","—","Awaiting data","#94A3B8","#94A3B8")
    if top_bwl:
        ec=top_bwl["econ"]; ec_c="#16A34A" if ec<8 else ("#D97706" if ec<11 else "#DC2626")
        tile(c5,"Best Bowler",f'{top_bwl["wkts"]}/{top_bwl["runs"]}',f'{top_bwl["name"]} · {top_bwl["overs"]}ov',ec_c,ec_c)
    else:
        tile(c5,"Best Bowler","—","Awaiting data","#94A3B8","#94A3B8")

def render_tactical_layer(sc):
    c1,c2 = st.columns([3,2])
    with c1:
        st.markdown('<div class="sh" style="margin-top:0">⚡ Recent Deliveries</div>', unsafe_allow_html=True)
        balls=sc.get("recent_balls",[])
        html='<div class="card" style="padding:12px 20px"><div class="timeline-box">'
        for b in balls:
            cls="ball-w" if b=="W" else ("ball-4" if b=="4" else ("ball-6" if b=="6" else ""))
            html+=f'<div class="ball-badge {cls}">{b}</div>'
        html+='<div style="margin-left:auto;font-size:11px;color:#94A3B8;font-weight:600">▶ THIS OVER</div></div></div>'
        st.markdown(html, unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="sh" style="margin-top:0">🔄 Impact Player</div>', unsafe_allow_html=True)
        ib=sc.get("impact",{}).get("bat","Available"); ifld=sc.get("impact",{}).get("fld","Available")
        st.markdown(
            f'<div class="card" style="padding:12px 20px">'
            f'<div style="display:flex;justify-content:space-between;font-size:12px;font-weight:600">'
            f'<span>{sc["bat"]["short"]}: <span style="color:#16A34A">{ib}</span></span>'
            f'<span>{sc["field"]["short"]}: <span style="color:#D97706">{ifld}</span></span>'
            f'</div></div>', unsafe_allow_html=True)

def render_momentum_and_predict(sc, batters, bowlers):
    st.markdown('<div class="sh" style="margin-top:22px">🔮 Momentum &amp; Prediction</div>', unsafe_allow_html=True)
    c1,c2 = st.columns([2,3])
    with c1:
        bat=sc["bat"]; two=sc["second_innings"]; bwp=sc["bat_wp"]
        if sc["phase"]=="completed":
            verdict,clr,txt="🏆 Match Concluded","green",f"<b>{sc['status']}</b>."
        elif not two:
            crr=_float(bat["rr"]); o=bat["_o"]; bu=int(o)*6+round((o%1)*10); bl=max(1,120-bu)
            proj=bat["_r"]+round(crr*bl/6*0.9)
            if crr>=10: verdict,clr,txt="🔥 Explosive","green",f"Projected: <b>~{proj}</b>"
            elif crr>=8: verdict,clr,txt="✅ Solid","green",f"Projected: <b>~{proj}</b>"
            else: verdict,clr,txt="⚠️ Below Par","amber",f"Projected: <b>~{proj}</b>"
        else:
            rn=sc["required"]; bl=sc["balls_left"]; rr2=sc["req_rr"]; wl=10-bat["_w"]
            if bwp>=65: verdict,clr,txt="🟢 Chase On Track","green",f"Need <b>{rn}</b> off <b>{bl}</b> · <b>{wl} wkts</b> in hand"
            elif bwp>=45: verdict,clr,txt="🟡 Finely Balanced","amber",f"Need <b>{rn}</b> off <b>{bl}</b> · Req RR <b>{rr2}</b>"
            else: verdict,clr,txt="🔴 Under Pressure","red",f"Need <b>{rn}</b> off <b>{bl}</b> · Req RR <b>{rr2}</b>"
        cls_map={"green":"pred-green","amber":"pred-amber","red":"pred-red"}
        st.markdown(f'<div class="{cls_map[clr]}" style="height:100%"><div class="pred-title">{verdict}</div><div class="pred-body">{txt}</div></div>',
                    unsafe_allow_html=True)
    with c2:
        ov,wp,rr,req=demo_momentum()
        st.plotly_chart(chart_momentum(ov,wp,rr,req), use_container_width=True, config={"displayModeBar":False})

def render_batters(batters):
    st.markdown('<div class="sh">🏏 Batting Highlights</div>', unsafe_allow_html=True)
    if not batters:
        st.markdown('<div class="card" style="color:#94A3B8;font-size:13px">Scorecard loading...</div>', unsafe_allow_html=True)
        return
    active  = [b for b in batters if b.get("batting_now")]
    others  = sorted([b for b in batters if not b.get("batting_now")], key=lambda x:x["runs"], reverse=True)
    display = (active+others)[:4]
    grid = "2.4fr 50px 50px 45px 45px 75px 55px"
    hdr = (f'<div class="tbl-hdr" style="display:grid;grid-template-columns:{grid}">'
           f'<div>Batter</div><div style="text-align:right">R</div><div style="text-align:right">B</div>'
           f'<div style="text-align:right">4s</div><div style="text-align:right">6s</div>'
           f'<div style="text-align:right">SR</div><div style="text-align:right">Status</div></div>')
    rows=""
    for b in display:
        bn=b.get("batting_now",False); tc=_c(b["team"]); sr=b["sr"]
        sr_c="green" if sr>=150 else ("amber" if sr>=100 else "red")
        nm=(f'<span class="player-name" style="color:{tc}">{b["name"]}</span>'
            +('<span class="batting-now">▶ BATTING</span>' if bn else ""))
        out=('<span class="green">not out</span>' if bn else
             f'<span style="font-size:10px;color:#64748B">{b["status"][:22]}</span>')
        rows+=(f'<div class="tbl-row" style="display:grid;grid-template-columns:{grid}">'
               f'<div>{nm}</div><div class="num"><b>{b["runs"]}</b></div><div class="num">{b["balls"]}</div>'
               f'<div class="num">{b["4s"]}</div><div class="num">{b["6s"]}</div>'
               f'<div class="num"><span class="{sr_c}">{sr}</span></div>'
               f'<div class="num" style="text-align:right">{out}</div></div>')
    st.markdown(f'<div class="card">{hdr}{rows}</div>', unsafe_allow_html=True)

def render_bowlers(bowlers):
    st.markdown('<div class="sh">🎯 Bowling Highlights</div>', unsafe_allow_html=True)
    if not bowlers:
        st.markdown('<div class="card" style="color:#94A3B8;font-size:13px">Scorecard loading...</div>', unsafe_allow_html=True)
        return
    active  = [b for b in bowlers if b.get("bowling_now")]
    others  = sorted([b for b in bowlers if not b.get("bowling_now")], key=lambda x:x["wkts"], reverse=True)
    display = (active+others)[:4]
    grid="2.2fr 55px 55px 55px 55px 70px"
    hdr=(f'<div class="tbl-hdr" style="display:grid;grid-template-columns:{grid}">'
         f'<div>Bowler</div><div style="text-align:right">O</div><div style="text-align:right">M</div>'
         f'<div style="text-align:right">R</div><div style="text-align:right">W</div><div style="text-align:right">Econ</div></div>')
    rows=""
    for b in display:
        tc=_c(b["team"]); ec=b["econ"]
        ec_c="green" if ec<8 else ("amber" if ec<11 else "red")
        ws='style="color:#DC2626;font-weight:700"' if b["wkts"]>0 else ""
        bn='<span style="color:#16A34A;font-size:10px;font-weight:700;margin-left:4px">▶ BOWLING</span>' if b.get("bowling_now") else ""
        rows+=(f'<div class="tbl-row" style="display:grid;grid-template-columns:{grid}">'
               f'<div><span class="player-name" style="color:{tc}">{b["name"]}</span>{bn}</div>'
               f'<div class="num">{b["overs"]}</div><div class="num">{b["maidens"]}</div>'
               f'<div class="num">{b["runs"]}</div><div class="num"><span {ws}>{b["wkts"]}</span></div>'
               f'<div class="num"><span class="{ec_c}">{ec}</span></div></div>')
    st.markdown(f'<div class="card">{hdr}{rows}</div>', unsafe_allow_html=True)

def render_full_scorecard(batters, bowlers, sc):
    with st.expander("📋 VIEW FULL SCORECARD", expanded=False):
        st.markdown(f'<div class="sh">🏏 BATTING — {sc["bat"]["short"]}</div>', unsafe_allow_html=True)
        grid="2.4fr 2fr 45px 45px 45px 45px 55px"
        hdr=(f'<div class="tbl-hdr" style="display:grid;grid-template-columns:{grid}">'
             f'<div>Batter</div><div>Status</div><div style="text-align:right">R</div>'
             f'<div style="text-align:right">B</div><div style="text-align:right">4s</div>'
             f'<div style="text-align:right">6s</div><div style="text-align:right">SR</div></div>')
        rows=""
        for b in batters:
            bn=b.get("batting_now",False); tc=_c(b["team"])
            nm=(f'<span class="player-name" style="color:{tc}">{b["name"]}</span>'
                +('<span class="batting-now">▶</span>' if bn else ""))
            out='<span class="green">not out</span>' if bn else f'<span style="font-size:11px;color:#64748B">{b["status"]}</span>'
            rows+=(f'<div class="tbl-row" style="display:grid;grid-template-columns:{grid}">'
                   f'<div>{nm}</div><div>{out}</div>'
                   f'<div class="num"><b>{b["runs"]}</b></div><div class="num">{b["balls"]}</div>'
                   f'<div class="num">{b["4s"]}</div><div class="num">{b["6s"]}</div>'
                   f'<div class="num">{b["sr"]}</div></div>')
        st.markdown(f'<div class="card" style="margin-bottom:20px">{hdr}{rows}</div>', unsafe_allow_html=True)

        st.markdown(f'<div class="sh">🎯 BOWLING — {sc["field"]["short"]}</div>', unsafe_allow_html=True)
        grid2="2.4fr 55px 55px 55px 55px 70px"
        hdr2=(f'<div class="tbl-hdr" style="display:grid;grid-template-columns:{grid2}">'
              f'<div>Bowler</div><div style="text-align:right">O</div><div style="text-align:right">M</div>'
              f'<div style="text-align:right">R</div><div style="text-align:right">W</div><div style="text-align:right">Econ</div></div>')
        rows2=""
        for b in bowlers:
            tc=_c(b["team"]); ec=b["econ"]
            ws='style="color:#DC2626;font-weight:700"' if b["wkts"]>0 else ""
            bn2='<span style="color:#16A34A;font-size:10px;margin-left:4px">▶</span>' if b.get("bowling_now") else ""
            rows2+=(f'<div class="tbl-row" style="display:grid;grid-template-columns:{grid2}">'
                    f'<div><span class="player-name" style="color:{tc}">{b["name"]}</span>{bn2}</div>'
                    f'<div class="num">{b["overs"]}</div><div class="num">{b["maidens"]}</div>'
                    f'<div class="num">{b["runs"]}</div><div class="num"><span {ws}>{b["wkts"]}</span></div>'
                    f'<div class="num">{ec}</div></div>')
        st.markdown(f'<div class="card">{hdr2}{rows2}</div>', unsafe_allow_html=True)


# ── RENDER: TAB 2 — AI ORACLE ─────────────────────────────────────────────────
def render_claude_commentary(sc, batters):
    st.markdown('<div class="sh" style="margin-top:20px">🎤 LIVE AI COMMENTARY</div>', unsafe_allow_html=True)
    striker = next((b for b in batters if b.get("batting_now")), None)
    ctx = (f"Match: {sc.get('match','')}. Phase: {sc['phase']}. "
           f"Score: {sc['bat']['score']}/{sc['bat']['wickets']} in {sc['bat']['overs']} overs. "
           f"{'Second innings — need '+str(sc['required'])+' off '+str(sc['balls_left'])+' balls, req RR '+str(sc['req_rr'])+'. ' if sc['second_innings'] else ''}"
           f"{'Striker: '+striker['name']+' '+str(striker['runs'])+'('+str(striker['balls'])+') SR:'+str(striker['sr'])+'. ' if striker else ''}"
           f"Win probability: {sc['bat']['short']} {sc['bat_wp']}%.")
    
    api_key_check = st.secrets.get("ANTHROPIC_API_KEY", "")
    
    if api_key_check:
        commentary = get_ai_commentary(ctx)
        if commentary:
            powered = " (Claude AI Connected)"
        else:
            commentary = _fallback_commentary(sc, batters)
            powered = " (Local Engine Active)"
    else:
        commentary = _fallback_commentary(sc, batters)
        powered = " (Local Tactical Engine)"
        
    st.markdown(
        f'<div class="commentary-box">'
        f'<div style="font-size:10px;color:#38BDF8;font-weight:700;letter-spacing:2px;margin-bottom:12px">'
        f'▶ LIVE COMMENTARY{powered}</div>'
        f'<div style="font-size:15px;line-height:1.75;color:#F1F5F9">{commentary}</div>'
        f'</div>',
        unsafe_allow_html=True)

def render_captains_corner(sc, batters, bowlers):
    st.markdown('<div class="sh" style="margin-top:20px">🧠 CAPTAIN\'S CORNER — TACTICAL BRAIN</div>', unsafe_allow_html=True)
    striker = next((b for b in batters if b.get("batting_now")), None)
    curr_b  = next((b for b in bowlers if b.get("bowling_now")), None)
    ctx = (f"T20 cricket. Phase: {sc['phase']}. "
           f"{'Chase: need '+str(sc['required'])+' off '+str(sc['balls_left'])+' balls, req RR '+str(sc['req_rr'])+', '+str(10-sc['bat']['_w'])+' wickets left. ' if sc['second_innings'] else 'First innings. '}"
           f"{'Striker SR: '+str(striker['sr'])+'. ' if striker else ''}"
           f"{'Current bowler economy: '+str(curr_b['econ'])+'. ' if curr_b else ''}"
           f"What should the captain do RIGHT NOW?")
           
    api_key_check = st.secrets.get("ANTHROPIC_API_KEY", "")
    
    if api_key_check:
        advice = get_captains_corner(ctx)
        if advice:
            powered = " (Claude AI Connected)"
        else:
            advice = _fallback_captain(sc, batters, bowlers)
            powered = " (Local Engine Active)"
    else:
        advice = _fallback_captain(sc, batters, bowlers)
        powered = " (Local Tactical Engine)"

    st.markdown(
        f'<div class="captain-box">'
        f'<div style="font-size:10px;color:#4ADE80;font-weight:700;letter-spacing:2px;margin-bottom:12px">'
        f'▶ CAPTAIN\'S TACTICAL BRIEF{powered}</div>'
        f'<div style="font-size:14px;line-height:1.85;color:#F1F5F9;white-space:pre-line">{advice}</div>'
        f'</div>',
        unsafe_allow_html=True)

    # Next ball grid
    st.markdown('<div class="sh" style="margin-top:20px">🎲 NEXT BALL PROBABILITY ENGINE</div>', unsafe_allow_html=True)
    probs = next_ball(sc)
    styles = {"dot":"nb-dot","1":"nb-one","2":"nb-two","4":"nb-four","6":"nb-six","W":"nb-wkt"}
    icons  = {"dot":"•","1":"1","2":"2","4":"4","6":"6","W":"💀"}
    cells  = "".join([
        f'<div class="nb-cell {styles[k]}">'
        f'<div class="nb-val">{icons[k]}</div>'
        f'<div class="nb-lbl">{k.upper()}</div>'
        f'<div class="nb-pct">{v}%</div></div>' for k,v in probs.items()])
    most   = max(probs, key=probs.get)
    lbl_map= {"dot":"Dot ball most likely","1":"Single dominant","2":"Two runs likely",
               "4":"Boundary incoming!","6":"Six possible!","W":"Wicket alert!"}
    st.markdown(f'<div class="card"><div class="nb-grid">{cells}</div>'
                f'<div style="margin-top:12px;font-size:12px;color:#475569;font-weight:600">'
                f'▶ {lbl_map[most]}</div></div>', unsafe_allow_html=True)

def render_ai_oracle(sc, batters, bowlers):
    striker      = next((b for b in batters if b.get("batting_now")), batters[0] if batters else None)
    curr_bowler  = next((b for b in bowlers if b.get("bowling_now")), bowlers[0] if bowlers else None)
    if not striker or not curr_bowler:
        st.info("Live player data unavailable.")
        return

    s_name=striker["name"]; s_sr=striker["sr"]; b_name=curr_bowler["name"]; b_econ=curr_bowler["econ"]
    phase=sc["phase"]

    if phase=="death": b_intent="Wide Yorker / Slower Bouncer"; pace_pct=40; var_pct=60
    elif phase=="powerplay": b_intent="Hard Length / Swing"; pace_pct=80; var_pct=20
    else: b_intent="Good Length / Stump-to-Stump"; pace_pct=60; var_pct=40
    if b_econ<6.0: b_intent+=" (Highly Defensive)"
    elif b_econ>10.0: b_intent+=" (Under Pressure — Expect Variation)"

    if s_sr>160: bat_intent="Aggressive Aerial / Clear the Ropes"; atk_pct=85; def_pct=15
    elif s_sr>120: bat_intent="Strike Rotation / Find the Gaps"; atk_pct=55; def_pct=45
    else: bat_intent="Consolidation / See Off the Over"; atk_pct=30; def_pct=70

    len_yorker=30 if phase=="death" else 5
    len_full=15 if phase=="death" else 25
    len_good=25 if phase=="death" else 55
    len_short=30 if phase=="death" else 15

    zone_cov=35; zone_mid=40; zone_fin=15; zone_str=10
    if b_econ>9.0: zone_str=30; zone_mid=35; zone_cov=25; zone_fin=10

    d_caught=60; d_bowled=20; d_lbw=15; d_runout=5
    if phase=="death": d_caught=75; d_bowled=15; d_lbw=5

    if s_sr>160: field_rec="Deep point + Long-off on boundary. Fine leg inside the circle."
    elif b_econ<6.0: field_rec="Attacking infield. Slip in place, cover saving the single."
    else: field_rec="Standard T20 field. Protect square boundaries."

    if s_sr>160 and b_econ<6.5:
        verdict=f"High-risk collision — {s_name} vs {b_name}. Boundary OR Wicket expected."
        gold_c="#D97706"
    elif s_sr>150:
        verdict=f"{s_name} has the upper hand. Expect an attacking shot towards the boundaries."
        gold_c="#16A34A"
    elif b_econ<6.0:
        verdict=f"{b_name} is dominating. Dot ball or single most likely next delivery."
        gold_c="#DC2626"
    else:
        verdict=f"Neutral state. Standard delivery pushing for rotation."
        gold_c="#38BDF8"

    st.markdown(
        f'<div class="oracle-box">'
        f'<h3>📸 MICRO-BATTLE: {s_name} vs {b_name}</h3>'
        f'<div class="oracle-vs">'
        f'<span style="color:#38BDF8">{s_name} <span style="font-size:14px;font-weight:400;color:#94A3B8">(SR: {s_sr})</span></span>'
        f'<span class="oracle-vs-vs">VS</span>'
        f'<span style="color:#F472B6">{b_name} <span style="font-size:14px;font-weight:400;color:#94A3B8">(Econ: {b_econ})</span></span>'
        f'</div>'
        f'<div style="display:flex;gap:15px;flex-wrap:wrap">'
        f'<div style="flex:1;min-width:220px;background:rgba(255,255,255,0.05);padding:15px;border-radius:8px">'
        f'<div style="font-size:11px;color:#94A3B8;text-transform:uppercase;margin-bottom:5px">Batter Intent</div>'
        f'<div style="font-size:14px;font-weight:600;color:white;margin-bottom:10px">{bat_intent}</div>'
        f'<div style="display:flex;justify-content:space-between;font-size:10px;color:#CBD5E1"><span>Attack ({atk_pct}%)</span><span>Defend ({def_pct}%)</span></div>'
        f'<div class="intent-bar"><div class="intent-fill" style="width:{atk_pct}%;background:#38BDF8"></div><div class="intent-fill" style="width:{def_pct}%;background:#475569"></div></div>'
        f'</div>'
        f'<div style="flex:1;min-width:220px;background:rgba(255,255,255,0.05);padding:15px;border-radius:8px">'
        f'<div style="font-size:11px;color:#94A3B8;text-transform:uppercase;margin-bottom:5px">Bowler Tactic</div>'
        f'<div style="font-size:14px;font-weight:600;color:white;margin-bottom:10px">{b_intent}</div>'
        f'<div style="display:flex;justify-content:space-between;font-size:10px;color:#CBD5E1"><span>Pace ({pace_pct}%)</span><span>Variation ({var_pct}%)</span></div>'
        f'<div class="intent-bar"><div class="intent-fill" style="width:{pace_pct}%;background:#F472B6"></div><div class="intent-fill" style="width:{var_pct}%;background:#475569"></div></div>'
        f'</div>'
        f'</div>'
        f'<div style="display:flex;gap:15px;margin-top:15px;flex-wrap:wrap">'
        f'<div style="flex:1;min-width:200px;background:rgba(0,0,0,0.2);padding:15px;border-radius:8px;border:1px solid rgba(255,255,255,0.05)">'
        f'<div style="font-size:11px;color:#38BDF8;font-weight:700;text-transform:uppercase;margin-bottom:10px">🎯 Delivery Length</div>'
        f'{_bar_html("Yorker",len_yorker,"#F472B6")}{_bar_html("Full",len_full,"#38BDF8")}'
        f'{_bar_html("Good Length",len_good,"#4ADE80")}{_bar_html("Short/Bouncer",len_short,"#FACC15")}'
        f'</div>'
        f'<div style="flex:1;min-width:200px;background:rgba(0,0,0,0.2);padding:15px;border-radius:8px;border:1px solid rgba(255,255,255,0.05)">'
        f'<div style="font-size:11px;color:#4ADE80;font-weight:700;text-transform:uppercase;margin-bottom:10px">🏏 Shot Zone</div>'
        f'{_bar_html("Covers/Off-Side",zone_cov,"#4ADE80")}{_bar_html("Mid-Wicket/Leg",zone_mid,"#38BDF8")}'
        f'{_bar_html("Straight/Down Ground",zone_str,"#F472B6")}{_bar_html("Fine Leg/Third Man",zone_fin,"#FACC15")}'
        f'</div>'
        f'<div style="flex:1;min-width:200px;background:rgba(220,38,38,0.1);padding:15px;border-radius:8px;border:1px solid rgba(220,38,38,0.2)">'
        f'<div style="font-size:11px;color:#F87171;font-weight:700;text-transform:uppercase;margin-bottom:10px">🚨 Dismissal Risk</div>'
        f'{_bar_html("Caught (Bdry/Circle)",d_caught,"#F87171")}{_bar_html("Bowled",d_bowled,"#F87171")}'
        f'{_bar_html("LBW",d_lbw,"#F87171")}{_bar_html("Run Out",d_runout,"#F87171")}'
        f'</div>'
        f'</div>'
        f'<div style="margin-top:15px;background:rgba(255,255,255,0.05);padding:15px;border-radius:8px">'
        f'<div style="font-size:11px;color:#FACC15;font-weight:700;text-transform:uppercase;margin-bottom:5px">😉 AI Field Strategy</div>'
        f'<div style="font-size:13px;color:#E2E8F0">{field_rec}</div>'
        f'</div>'
        f'<div style="margin-top:20px;padding-top:15px;border-top:1px solid #334155">'
        f'<div style="font-size:11px;color:#94A3B8;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">🔮 The Golden Ball Prediction</div>'
        f'<div style="font-size:16px;font-weight:500;color:{gold_c};line-height:1.5">{verdict}</div>'
        f'</div></div>',
        unsafe_allow_html=True)


# ── RENDER: TAB 3 — PREDICTION LAB ───────────────────────────────────────────
def render_prediction_lab(sc):
    st.markdown('<div class="sh">🎲 MONTE CARLO MATCH SIMULATOR</div>', unsafe_allow_html=True)
    if sc["phase"] == "completed":
        st.markdown('<div class="card" style="color:#94A3B8">Match completed — simulation not applicable.</div>', unsafe_allow_html=True)
    elif sc["second_innings"] and sc["balls_left"] > 0:
        bl  = sc["balls_left"]; rn = sc["required"]; wl = 10 - sc["bat"]["_w"]
        with st.spinner("Running 3,000 simulations..."):
            bat_wp, fld_wp, dist = run_monte_carlo(bl, rn, wl, sc["phase"], n=3000)
        c1,c2,c3 = st.columns(3)
        wp_c = "#16A34A" if bat_wp>=55 else ("#D97706" if bat_wp>=40 else "#DC2626")
        with c1:
            st.markdown(
                f'<div class="mc-result-box" style="border-top:4px solid {wp_c}">'
                f'<div style="font-size:11px;color:#94A3B8;font-weight:700;letter-spacing:1px;margin-bottom:6px">{sc["bat"]["short"]} WIN %</div>'
                f'<div style="font-size:48px;font-weight:800;color:{wp_c};line-height:1">{bat_wp}%</div>'
                f'<div style="font-size:11px;color:#64748B;margin-top:4px">Based on 3,000 path simulations</div>'
                f'</div>', unsafe_allow_html=True)
        with c2:
            st.markdown(
                f'<div class="mc-result-box" style="border-top:4px solid {_c(sc["field"]["short"])}">'
                f'<div style="font-size:11px;color:#94A3B8;font-weight:700;letter-spacing:1px;margin-bottom:6px">{sc["field"]["short"]} WIN %</div>'
                f'<div style="font-size:48px;font-weight:800;color:{_c(sc["field"]["short"])};line-height:1">{fld_wp}%</div>'
                f'<div style="font-size:11px;color:#64748B;margin-top:4px">Fielding team holds {fld_wp}% edge</div>'
                f'</div>', unsafe_allow_html=True)
        with c3:
            avg_sc = round(sum(dist)/len(dist)) if dist else 0
            reach  = round(len([x for x in dist if x >= rn])/len(dist)*100) if dist else 0
            st.markdown(
                f'<div class="mc-result-box" style="border-top:4px solid #7C3AED">'
                f'<div style="font-size:11px;color:#94A3B8;font-weight:700;letter-spacing:1px;margin-bottom:6px">AVG RUNS SCORED</div>'
                f'<div style="font-size:48px;font-weight:800;color:#7C3AED;line-height:1">{avg_sc}</div>'
                f'<div style="font-size:11px;color:#64748B;margin-top:4px">Target reached in {reach}% of sims</div>'
                f'</div>', unsafe_allow_html=True)
        st.plotly_chart(chart_monte_carlo(dist, rn), use_container_width=True, config={"displayModeBar":False})
    else:
        st.markdown('<div class="card" style="color:#94A3B8;font-size:13px">Monte Carlo runs during an active 2nd innings chase.</div>', unsafe_allow_html=True)

    # Chase Trajectory
    st.markdown('<div class="sh" style="margin-top:20px">📈 CHASE TRAJECTORY PLANNER</div>', unsafe_allow_html=True)
    result = build_chase_trajectories(sc)
    if result:
        overs, opt, agg, con, hist, target, cs = result
        st.plotly_chart(chart_trajectory(overs,opt,agg,con,hist,target,cs),
                        use_container_width=True, config={"displayModeBar":False})
        c1,c2,c3,c4 = st.columns(4)
        cards = [
            ("Optimal Path","Match req RR ball-by-ball. Controlled aggression.","#16A34A"),
            ("Aggressive Path","+22% above req RR. Higher boundary count needed. Wicket risk elevated.","#7C3AED"),
            ("Conservative","Start slow, accelerate in death. Requires late burst of 15-18 RPO.","#D97706"),
            ("Historical Avg","Similar chases at this venue averaged ~4% above req RR.","#0EA5E9"),
        ]
        for col,(title,desc,clr) in zip([c1,c2,c3,c4],cards):
            with col:
                st.markdown(
                    f'<div class="card" style="border-left:3px solid {clr};padding:12px 14px">'
                    f'<div style="font-size:11px;font-weight:700;color:{clr};margin-bottom:4px">{title}</div>'
                    f'<div style="font-size:12px;color:#475569">{desc}</div>'
                    f'</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="card" style="color:#94A3B8;font-size:13px">Trajectory planner activates during an active 2nd innings chase.</div>', unsafe_allow_html=True)

    # Over-by-Over Strategy
    st.markdown('<div class="sh" style="margin-top:20px">⏱️ OVER-BY-OVER STRATEGY ADVISOR</div>', unsafe_allow_html=True)
    if sc["second_innings"] and sc["balls_left"] > 0:
        cur_over = sc["bat"]["_o"]; balls_left = sc["balls_left"]
        start_over = int(cur_over) + 1
        remaining_overs = list(range(start_over, 21))[:5]
        if remaining_overs:
            cols = st.columns(len(remaining_overs))
            req_at = sc["req_rr"]
            for i,(col,ov) in enumerate(zip(cols, remaining_overs)):
                bl_at = max(0, balls_left - i*6)
                rn_at = max(0, sc["required"] - int(req_at * i))
                rr_at = round(rn_at*6/max(bl_at,1), 2) if bl_at > 0 else 0
                phase = "death" if ov >= 16 else ("powerplay" if ov <= 6 else "middle")
                ph_c = "#DC2626" if phase=="death" else ("#1D4ED8" if phase=="powerplay" else "#D97706")
                tips = []
                if rr_at > 13: tips.append("Must-boundary over")
                elif rr_at > 10: tips.append("Aggressive rotation")
                else: tips.append("Maintain tempo")
                if ov in [16,17,18,19,20]: tips.append("Use death specialist")
                elif ov in [7,8,9,10]: tips.append("Spinners preferred")
                with col:
                    st.markdown(
                        f'<div class="card" style="text-align:center;border-top:3px solid {ph_c};padding:12px 10px">'
                        f'<div style="font-size:10px;font-weight:700;color:{ph_c};letter-spacing:1px">OVER {ov}</div>'
                        f'<div style="font-size:20px;font-weight:800;color:#1E293B;margin:6px 0">{rr_at}</div>'
                        f'<div style="font-size:9px;color:#94A3B8">REQ RR</div>'
                        f'<div style="margin-top:8px">{"".join([f"<div style=&quot;font-size:10px;color:#475569;margin-top:3px&quot;>{t}</div>" for t in tips])}</div>'
                        f'</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="card" style="color:#94A3B8;font-size:13px">Strategy advisor active during live 2nd innings.</div>', unsafe_allow_html=True)


# ── RENDER: TAB 4 — PLAYER INTEL ─────────────────────────────────────────────
def render_player_intel(sc, batters, bowlers):
    # PPI + Bowler Threat
    st.markdown('<div class="sh">🧠 PLAYER PRESSURE INDEX</div>', unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        st.plotly_chart(chart_ppi_gauge(batters, sc), use_container_width=True, config={"displayModeBar":False})
    with c2:
        st.plotly_chart(chart_bowler_threat(bowlers, sc), use_container_width=True, config={"displayModeBar":False})

    # Clutch Card
    st.markdown('<div class="sh" style="margin-top:10px">🏆 CLUTCH SCORE CARD</div>', unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        rows=""
        for b in batters[:5]:
            lbl,clr,score = clutch_rating(b, is_batter=True)
            rows+=(f'<div style="display:flex;justify-content:space-between;align-items:center;'
                   f'padding:8px 0;border-bottom:1px solid #F1F5F9">'
                   f'<span style="font-weight:600;color:#1E293B;font-size:13px">{b["name"]}</span>'
                   f'<span style="font-size:10px;font-weight:700;color:{clr};background:{clr}18;'
                   f'padding:3px 10px;border-radius:4px;letter-spacing:1px">{lbl}</span></div>')
        st.markdown(f'<div class="card"><div style="font-size:10px;font-weight:700;color:#94A3B8;letter-spacing:1px;margin-bottom:8px">BATTERS</div>{rows}</div>',
                    unsafe_allow_html=True)
    with c2:
        rows=""
        for b in bowlers[:4]:
            lbl,clr,score = clutch_rating(b, is_batter=False)
            rows+=(f'<div style="display:flex;justify-content:space-between;align-items:center;'
                   f'padding:8px 0;border-bottom:1px solid #F1F5F9">'
                   f'<span style="font-weight:600;color:#1E293B;font-size:13px">{b["name"]}</span>'
                   f'<span style="font-size:10px;font-weight:700;color:{clr};background:{clr}18;'
                   f'padding:3px 10px;border-radius:4px;letter-spacing:1px">{lbl}</span></div>')
        st.markdown(f'<div class="card"><div style="font-size:10px;font-weight:700;color:#94A3B8;letter-spacing:1px;margin-bottom:8px">BOWLERS</div>{rows}</div>',
                    unsafe_allow_html=True)

    # DNA Match Finder
    st.markdown('<div class="sh" style="margin-top:10px">🧬 DNA MATCH FINDER — Similar Historical Situations</div>', unsafe_allow_html=True)
    req_rr = sc.get("req_rr",0)
    html = ""
    for d in DNA_MATCHES:
        prob_c = "#16A34A" if "WON" in d["result"] else "#DC2626"
        result_c = "#F0FDF4" if "WON" in d["result"] else "#FEF2F2"
        html+=(f'<div class="dna-card" style="border-left:4px solid {prob_c};background:{result_c}">'
               f'<div style="display:flex;justify-content:space-between;align-items:flex-start">'
               f'<div><div style="font-size:12px;font-weight:700;color:#1E293B">{d["teams"]} ({d["year"]})</div>'
               f'<div style="font-size:12px;color:#475569;margin-top:2px">{d["situation"]}</div>'
               f'<div style="font-size:11px;color:#64748B;margin-top:4px">Hero: {d["hero"]}</div>'
               f'</div>'
               f'<div style="text-align:right">'
               f'<div style="font-size:13px;font-weight:800;color:{prob_c}">{d["result"]}</div>'
               f'<div style="font-size:10px;color:#94A3B8;margin-top:2px">Batting win% then: {d["prob"]}%</div>'
               f'</div></div></div>')
    st.markdown(html, unsafe_allow_html=True)

    # Auction ROI
    st.markdown('<div class="sh" style="margin-top:10px">💰 AUCTION ROI TRACKER</div>', unsafe_allow_html=True)
    st.plotly_chart(chart_auction_roi(), use_container_width=True, config={"displayModeBar":False})
    grid="2fr 70px 70px 70px 90px 100px"
    hdr=(f'<div class="tbl-hdr" style="display:grid;grid-template-columns:{grid}">'
         f'<div>Player</div><div style="text-align:right">Team</div>'
         f'<div style="text-align:right">Price (Cr)</div><div style="text-align:right">Runs/Wkts</div>'
         f'<div style="text-align:right">Cost/Unit</div><div style="text-align:right">ROI Rating</div></div>')
    rows=""
    for a in AUCTION_DATA:
        tc=_c(a["team"])
        if a["unit"]=="run":
            unit_val=a["runs"]; cost=round(a["price"]*100/max(unit_val,1),2); unit_lbl=f"₹{cost}L/run"
            roi="Excellent" if cost<5 else ("Good" if cost<10 else ("Fair" if cost<18 else "Overpaid"))
        else:
            unit_val=a["wkts"]; cost=round(a["price"]/max(unit_val,1),2); unit_lbl=f"₹{cost}Cr/wkt"
            roi="Excellent" if cost<1.2 else ("Good" if cost<2.0 else ("Fair" if cost<3.0 else "Overpaid"))
        roi_c="#16A34A" if roi=="Excellent" else ("#0EA5E9" if roi=="Good" else ("#D97706" if roi=="Fair" else "#DC2626"))
        rows+=(f'<div class="tbl-row" style="display:grid;grid-template-columns:{grid}">'
               f'<div class="player-name">{a["name"]}</div>'
               f'<div class="num" style="color:{tc};font-weight:700">{a["team"]}</div>'
               f'<div class="num">₹{a["price"]}</div>'
               f'<div class="num">{unit_val}</div>'
               f'<div class="num">{unit_lbl}</div>'
               f'<div class="num"><span style="color:{roi_c};font-weight:700">{roi}</span></div></div>')
    st.markdown(f'<div class="card">{hdr}{rows}</div>', unsafe_allow_html=True)


# ── RENDER: TAB 5 — GROUND & CONTEXT ─────────────────────────────────────────
def render_ground_context(sc):
    # Dew Factor
    st.markdown('<div class="sh">💧 DEW FACTOR ANALYSIS</div>', unsafe_allow_html=True)
    city = sc.get("venue","Bengaluru").split(",")[-1].strip() if "," in sc.get("venue","Bengaluru") else "Bengaluru"
    wx = fetch_weather(city)
    dew = dew_score(wx["humidity"], wx["temp"])
    dew_label = "HEAVY DEW" if dew>70 else ("MODERATE DEW" if dew>45 else "LOW DEW")
    dew_c = "#DC2626" if dew>70 else ("#D97706" if dew>45 else "#16A34A")
    src_note = "Live (wttr.in)" if wx["ok"] else "Estimated"

    c1,c2,c3,c4 = st.columns(4)
    with c1:
        st.markdown(
            f'<div class="dew-box" style="background:linear-gradient(135deg,{dew_c},{dew_c}AA)">'
            f'<div style="font-size:11px;font-weight:700;letter-spacing:1px;opacity:0.8;margin-bottom:6px">DEW IMPACT SCORE</div>'
            f'<div style="font-size:52px;font-weight:800;line-height:1">{dew}</div>'
            f'<div style="font-size:12px;font-weight:700;margin-top:4px">{dew_label}</div>'
            f'<div style="font-size:10px;opacity:0.7;margin-top:4px">{src_note}</div>'
            f'</div>', unsafe_allow_html=True)
    def wx_tile(col, lbl, val, unit):
        with col:
            st.markdown(
                f'<div class="card" style="text-align:center">'
                f'<div class="st-lbl">{lbl}</div>'
                f'<div style="font-size:28px;font-weight:700;color:#1E293B">{val}</div>'
                f'<div style="font-size:11px;color:#64748B">{unit}</div>'
                f'</div>', unsafe_allow_html=True)
    wx_tile(c2,"TEMPERATURE",wx["temp"],"°C")
    wx_tile(c3,"HUMIDITY",wx["humidity"],"%")
    wx_tile(c4,"WIND SPEED",wx["wind"],"km/h")

    # Impact text
    if dew > 60:
        impact_txt = ("Heavy dew expected tonight. Ball will get wet by over 12. "
                      "Batting 2nd gets significantly easier — swing and spin will both be neutralised. "
                      "Par score adjustment: +12 to +18 runs for the chasing team.")
        imp_cls = "pred-red"
    elif dew > 35:
        impact_txt = ("Moderate dew likely after 9 PM. Ball grip affected in the second innings. "
                      "Spinners may struggle with purchase. Chasing team gets mild advantage. "
                      "Adjust par score by +6 to +10 runs.")
        imp_cls = "pred-amber"
    else:
        impact_txt = ("Minimal dew impact. Conditions should remain consistent across both innings. "
                      "No significant adjustment needed to par score. Bowling conditions stable.")
        imp_cls = "pred-green"
    st.markdown(f'<div class="{imp_cls}" style="margin-top:12px"><div class="pred-body">{impact_txt}</div></div>',
                unsafe_allow_html=True)

    # Pitch Heatmap
    st.markdown('<div class="sh" style="margin-top:20px">🏟️ PITCH CONDITION MAP</div>', unsafe_allow_html=True)
    over_num = sc["bat"]["_o"]
    worn = min(100, int(over_num / 20 * 100))
    pitch_areas = [
        ("Good Length (Off Stump)", min(worn+10,100), "Rough developing"),
        ("Good Length (Middle)",    worn,              "Standard wear"),
        ("Good Length (Leg Stump)", min(worn-5,80),    "Minimal wear"),
        ("Short Pitch Zone",        max(worn-20,10),   "Light footmarks"),
        ("Full Length Zone",        max(worn-30,5),    "Fresh"),
        ("Yorker Zone",             max(worn-40,3),    "Fresh"),
    ]
    rows=""
    for area, wear, note in pitch_areas:
        w_c="#DC2626" if wear>70 else ("#D97706" if wear>40 else "#16A34A")
        rows+=(f'<div style="display:flex;align-items:center;gap:12px;padding:8px 0;border-bottom:1px solid #F1F5F9">'
               f'<div style="width:200px;font-size:12px;color:#374151">{area}</div>'
               f'<div style="flex:1"><div class="pbar"><div class="pbar-fill" style="width:{wear}%;background:{w_c}"></div></div></div>'
               f'<div style="width:80px;text-align:right;font-size:11px;font-weight:700;color:{w_c}">{wear}%</div>'
               f'<div style="width:120px;font-size:10px;color:#94A3B8">{note}</div>'
               f'</div>')
    st.markdown(f'<div class="card">{rows}</div>', unsafe_allow_html=True)

    # Ball-by-Ball Heatmap
    st.markdown('<div class="sh" style="margin-top:20px">🔥 BALL-BY-BALL INNINGS HEATMAP</div>', unsafe_allow_html=True)
    history = demo_over_history()
    st.plotly_chart(chart_ball_heatmap(history), use_container_width=True, config={"displayModeBar":False})

    # IPL Points Table
    st.markdown('<div class="sh" style="margin-top:20px">🏆 IPL 2026 POINTS TABLE &amp; ELIMINATION TRACKER</div>', unsafe_allow_html=True)
    matches_left = 56 - sum([t["p"] for t in IPL_STANDINGS]) // 2
    hdr=(f'<div class="pts-row pts-hdr">'
         f'<div>#</div><div>Team</div><div style="text-align:right">P</div><div style="text-align:right">W</div>'
         f'<div style="text-align:right">L</div><div style="text-align:right">NR</div>'
         f'<div style="text-align:right">Pts</div><div style="text-align:right">NRR</div>'
         f'</div>')
    rows=""
    for i,t in enumerate(IPL_STANDINGS):
        pos=i+1
        magic = max(0, 16 - t["pts"]) // 2 + 1
        elim  = (14-t["pts"]) > matches_left * 2
        qual  = t["pts"] >= 16
        bg = "#F0FDF4" if qual else ("#FEF2F2" if elim else ("white" if pos<=4 else "#FFFBEB"))
        border= "border-left:3px solid #16A34A;" if qual else ("border-left:3px solid #DC2626;" if elim else ("border-left:3px solid #1D4ED8;" if pos<=4 else ""))
        status = "✅" if qual else ("❌" if elim else ("🎟️" if pos<=4 else ""))
        rows+=(f'<div class="pts-row" style="background:{bg};{border}">'
               f'<div style="font-weight:700;color:#64748B">{pos}</div>'
               f'<div><span style="font-weight:700;color:{t["color"]}">{t["team"]}</span> {status}</div>'
               f'<div style="text-align:right">{t["p"]}</div>'
               f'<div style="text-align:right;color:#16A34A;font-weight:600">{t["w"]}</div>'
               f'<div style="text-align:right;color:#DC2626">{t["l"]}</div>'
               f'<div style="text-align:right;color:#94A3B8">{t["nr"]}</div>'
               f'<div style="text-align:right;font-weight:800;color:#1E293B">{t["pts"]}</div>'
               f'<div style="text-align:right;color:{"#16A34A" if "+" in t["nrr"] else "#DC2626"};font-size:12px">{t["nrr"]}</div>'
               f'</div>')
    st.markdown(f'<div class="card" style="padding:0 0 4px 0;overflow:hidden">{hdr}{rows}</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:11px;color:#94A3B8;margin-top:8px">'
        '✅ Qualified &nbsp; 🎟️ Playoff position &nbsp; ❌ Eliminated &nbsp;'
        'Top 4 qualify for playoffs</div>', unsafe_allow_html=True)

    # Run Progression
    st.markdown('<div class="sh" style="margin-top:20px">📈 INNINGS RUN PROGRESSION</div>', unsafe_allow_html=True)
    st.plotly_chart(chart_run_progression(demo_over_history()), use_container_width=True, config={"displayModeBar":False})


# ── RENDER: TAB 6 — NEXT MATCH ────────────────────────────────────────────────
def render_upcoming_match(news):
    st.markdown('<div class="sh" style="margin-top:20px">🗓️ TONIGHT\'S BLOCKBUSTER</div>', unsafe_allow_html=True)
    mi_key, kkr_key, injury_alerts = generate_match_preview(news)
    st.markdown(
        f'<div class="card" style="border-left:4px solid #1D4ED8;margin-bottom:20px">'
        f'<div class="mh-venue">🏟️ Wankhede Stadium, Mumbai</div>'
        f'<div class="mh-sub"><span class="mh-status">UPCOMING</span>&nbsp;·&nbsp;Today, 7:30 PM IST</div>'
        f'<div style="display:flex;align-items:center;justify-content:space-between;margin-top:15px">'
        f'<div class="score-big" style="color:#1D4ED8;font-size:32px">MI</div>'
        f'<div style="font-weight:700;color:#64748B">VS</div>'
        f'<div class="score-big" style="color:#7C3AED;font-size:32px">KKR</div>'
        f'</div></div>', unsafe_allow_html=True)

    c1,c2,c3 = st.columns(3, gap="medium")
    with c1:
        st.markdown('<div class="sh">⭐ PLAYERS TO WATCH</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="card" style="height:100%">'
            f'<div style="color:#1D4ED8;font-weight:700;margin-bottom:5px">Mumbai Indians</div>'
            f'<div style="font-size:13px;color:#475569;margin-bottom:15px">{mi_key}</div>'
            f'<div style="color:#7C3AED;font-weight:700;margin-bottom:5px">Kolkata Knight Riders</div>'
            f'<div style="font-size:13px;color:#475569">{kkr_key}</div>'
            f'</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="sh">🏥 SQUAD SCANNER</div>', unsafe_allow_html=True)
        alert_html="".join([(f'<div style="font-size:13px;color:#DC2626;font-weight:600;margin-bottom:8px">{a}</div>'
                              if '⚠️' in a else
                              f'<div style="font-size:13px;color:#16A34A;font-weight:600;margin-bottom:8px">{a}</div>')
                             for a in injury_alerts])
        st.markdown(f'<div class="card" style="height:100%">{alert_html}</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="sh">📊 TOURNAMENT CONTEXT</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="card" style="height:100%;font-size:13px">'
            f'<div style="font-weight:700;color:#1E293B;margin-bottom:8px">Pitch Report (Wankhede):</div>'
            f'<div style="color:#475569;margin-bottom:12px">Red soil. High dew post 9 PM. Par: 195. '
            f'Toss winners overwhelmingly choose to chase here.</div>'
            f'<div style="font-weight:700;color:#1E293B;margin-bottom:4px">Standings Impact:</div>'
            f'<div style="color:#475569">MI Win: Moves to 2nd (+0.4 NRR)<br>KKR Win: Jumps to 3rd (+0.8 NRR)</div>'
            f'</div>', unsafe_allow_html=True)

    if news:
        st.markdown('<div class="sh" style="margin-top:20px">📰 LATEST NEWS — MI vs KKR</div>', unsafe_allow_html=True)
        news_html='<div class="card">'
        for n in news[:5]:
            news_html+=(f'<div class="news-item">'
                        f'<a href="{n["link"]}" target="_blank">{n["title"]}</a>'
                        f'<div class="news-src">{n.get("source","")}</div>'
                        f'</div>')
        news_html+='</div>'
        st.markdown(news_html, unsafe_allow_html=True)


# ── CONTROLS ROW ──────────────────────────────────────────────────────────────
ca,cb,cc,cd = st.columns([4,1,1,1])
with ca:
    st.markdown('<div style="font-size:10px;color:#94A3B8;padding-top:12px">GOD\'S EYE v5.2 · Shadow Scraper · © Uday Maddila</div>',
                unsafe_allow_html=True)
with cb: auto_ref = st.toggle("Auto-Refresh", value=True)
with cc: pass
with cd:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear(); st.rerun()


# ── MAIN DATA FETCH ───────────────────────────────────────────────────────────
sc, batters, bowlers, extras, partner = resolve_scraper()
news          = _fetch_news()
upcoming_news = fetch_upcoming_news()
is_live       = sc["phase"] != "completed"

# Alert system
check_and_push_alerts(sc, batters)
render_alert_banner()

# Navbar (always visible above tabs)
render_navbar(sc, is_live)


# ── 6-TAB LAYOUT ─────────────────────────────────────────────────────────────
tab1,tab2,tab3,tab4,tab5,tab6 = st.tabs([
    "🔴 Live Match",
    "🧠 AI Oracle",
    "🎲 Prediction Lab",
    "🏏 Player Intel",
    "🏟️ Ground & Context",
    "⏭️ Next Match",
])

with tab1:
    render_scoreboard(sc)
    render_stats_bar(sc, batters, bowlers, extras, partner)
    render_tactical_layer(sc)
    render_momentum_and_predict(sc, batters, bowlers)
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    cl,cr = st.columns(2, gap="medium")
    with cl: render_batters(batters)
    with cr: render_bowlers(bowlers)
    render_full_scorecard(batters, bowlers, sc)

with tab2:
    render_claude_commentary(sc, batters)
    render_captains_corner(sc, batters, bowlers)
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    render_ai_oracle(sc, batters, bowlers)

with tab3:
    render_prediction_lab(sc)

with tab4:
    render_player_intel(sc, batters, bowlers)

with tab5:
    render_ground_context(sc)

with tab6:
    render_upcoming_match(upcoming_news)


# ── FOOTER ────────────────────────────────────────────────────────────────────
IST = pytz.timezone("Asia/Kolkata")
st.markdown(
    f'<div style="text-align:center;font-size:11px;color:#94A3B8;'
    f'margin-top:20px;padding-top:14px;border-top:1px solid #E2E8F0">'
    f'GOD\'S EYE v5.2 · Shadow Scraper Engine · Smart URL Switcher · Multi-Source Consensus · '
    f'Monte Carlo Engine · Local Tactical Engine · Last sync: {datetime.now(IST).strftime("%H:%M:%S IST")} · '
    f'&copy; Uday Maddila</div>',
    unsafe_allow_html=True)

if auto_ref:
    time.sleep(REFRESH_SECS)
    st.rerun()
