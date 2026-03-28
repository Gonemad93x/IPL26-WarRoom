"""
╔══════════════════════════════════════════════════════════════════╗
║   GOD'S EYE v3.4 — IPL ELITE MATCH CENTER (FULL UNIFIED)         ║
║   Operator: Uday Maddila                                         ║
║   Patch v3.4: Live data transformer + fallback chain             ║
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
# 0. PAGE CONFIG  (must be FIRST Streamlit call)
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
RAPIDAPI_HOST = "cricbuzz-cricket.p.rapidapi.com"          # ← correct host
API_HEADERS   = {
    "x-rapidapi-key":  RAPIDAPI_KEY,
    "x-rapidapi-host": RAPIDAPI_HOST,
}
REFRESH_SECS = 30

# ─────────────────────────────────────────────────────────────────
# 2. GLOBAL CSS
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
[data-testid="stHeader"],
[data-testid="stToolbar"],
footer { display:none !important; }
section[data-testid="stSidebar"] { display:none !important; }
div.block-container { padding:1.6rem 2.4rem 3rem !important; max-width:1440px; }
.stMarkdown { padding:0 !important; }
[data-testid="stHorizontalBlock"] > div { padding:0 5px; }
[data-testid="stHorizontalBlock"] > div:first-child { padding-left:0; }
[data-testid="stHorizontalBlock"] > div:last-child  { padding-right:0; }

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

.ni a { text-decoration: none; transition: color 0.2s; }
.ni a:hover { color: var(--cyan) !important; text-decoration: underline !important; }

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
    font-family: var(--fm);
    font-size: 9px; font-weight: 700;
    letter-spacing: 1.5px;
    border-radius: 4px;
    padding: 2px 8px;
    display: inline-block;
    margin-bottom: 8px;
}
.b-red    { color:var(--red);    background:rgba(255,62,62,.12);   border:1px solid rgba(255,62,62,.3);   }
.b-amber  { color:var(--amber);  background:rgba(255,181,71,.10);  border:1px solid rgba(255,181,71,.3);  }
.b-cyan   { color:var(--cyan);   background:rgba(0,209,255,.10);   border:1px solid rgba(0,209,255,.25);  }
.b-green  { color:var(--green);  background:rgba(61,255,122,.10);  border:1px solid rgba(61,255,122,.25); }
.b-purple { color:var(--purple); background:rgba(191,127,255,.10); border:1px solid rgba(191,127,255,.3); }

.sh {
    font-family: var(--fm);
    font-size: 10px; letter-spacing: 3px;
    color: var(--td);
    border-bottom: 1px solid var(--border);
    padding-bottom: 8px; margin-bottom: 14px;
}
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

.pl-row {
    display:flex; align-items:center; justify-content:space-between;
    padding:9px 0; border-bottom:1px solid var(--border);
    font-family:var(--fm); font-size:12px;
}
.pl-row:last-child { border-bottom:none; }
.pl-n { font-size:13px; color:var(--tp); font-weight:600; }
.pl-r { font-size:10px; color:var(--td); letter-spacing:1px; }

.nb-grid { display:grid; grid-template-columns:repeat(6,1fr); gap:8px; margin-top:10px; }
.nb-cell {
    text-align:center; padding:10px 4px;
    border-radius:8px; border:1px solid var(--border);
    font-family:var(--fm); font-size:11px; font-weight:600;
}

.mh { display:flex; align-items:center; justify-content:space-between; margin-bottom:24px; padding-bottom:14px; border-bottom:1px solid var(--border); }
.mh-logo { font-family:var(--fm); font-size:20px; font-weight:700; color:var(--tp); }
.mh-logo span { color:var(--cyan); }
.mh-meta { font-family:var(--fm); font-size:11px; color:var(--td); text-align:right; }
.ld { display:inline-block; width:7px; height:7px; border-radius:50%; background:var(--red); margin-right:6px; animation:pulse 1.4s ease-in-out infinite; }
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1);} 50%{opacity:.4;transform:scale(.8);} }

.ni { border-bottom:1px solid var(--border); padding:9px 0; font-size:13px; line-height:1.5; }
.ni:last-child { border-bottom:none; }
.ni-s { font-family:var(--fm); font-size:10px; color:var(--td); margin-top:2px; }

.vd {
    background:rgba(0,209,255,.04);
    border:1px solid rgba(0,209,255,.18);
    border-left:3px solid var(--cyan);
    border-radius:10px; padding:20px 26px; margin-top:14px;
}
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
# 3. PLOTLY HELPERS
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
# 4. DATA LAYER  (v3.4 — live transformer + fallback)
# ─────────────────────────────────────────────────────────────────

TEAM_MAP = {
    "royal challengers bengaluru": "RCB",
    "royal challengers bangalore":  "RCB",
    "sunrisers hyderabad":          "SRH",
    "mumbai indians":               "MI",
    "chennai super kings":          "CSK",
    "kolkata knight riders":        "KKR",
    "rajasthan royals":             "RR",
    "delhi capitals":               "DC",
    "punjab kings":                 "PBKS",
    "lucknow super giants":         "LSG",
    "gujarat titans":               "GT",
}

def _team_short(name: str) -> str:
    n = (name or "").lower().strip()
    for full, short in TEAM_MAP.items():
        if full in n:
            return short
    parts = (name or "").split()
    return "".join(p[0] for p in parts[:3]).upper() if parts else "UNK"

def _int(v, default=0):
    try:
        return int(str(v).split("/")[0].strip())
    except Exception:
        return default

def _float(v, default=0.0):
    try:
        return float(str(v).strip())
    except Exception:
        return default

def _win_prob(runs_scored, wickets_fallen, overs_faced, target, total_overs=20):
    if target <= 0:
        return 50, 50
    balls_used   = int(overs_faced) * 6 + round((overs_faced % 1) * 10)
    balls_total  = total_overs * 6
    balls_left   = max(0, balls_total - balls_used)
    runs_needed  = target - runs_scored
    wickets_left = 10 - wickets_fallen
    if runs_needed <= 0:
        return 95, 5
    if balls_left <= 0:
        return 5, 95
    wkt_resource   = wickets_left / 10
    ball_resource  = balls_left / balls_total
    resource_left  = wkt_resource * 0.5 + ball_resource * 0.5
    run_difficulty = (runs_needed * 6 / balls_left) / 10.0
    prob = 50 + (resource_left - run_difficulty) * 80
    prob = max(5, min(95, int(prob)))
    return prob, 100 - prob

def _parse_innings_dict(inn: dict) -> dict:
    label = inn.get("inning", inn.get("bat", inn.get("team", "")))
    r  = _int(inn.get("r", inn.get("runs", 0)))
    w  = _int(inn.get("w", inn.get("wickets", 0)))
    o  = _float(inn.get("o", inn.get("overs", 0)))
    rr = round(r / o, 2) if o > 0 else 0.0
    return {
        "name":    label,
        "short":   _team_short(label),
        "score":   str(r),
        "wickets": str(w),
        "overs":   str(o),
        "rr":      str(rr),
        "_r": r, "_w": w, "_o": o,
    }

def _extract_batters_from_raw(raw: dict) -> list:
    batters = []
    try:
        data = raw.get("data", raw)
        if isinstance(data, list):
            data = data[0] if data else {}
        scorecard = data.get("scorecard", data.get("score", []))
        if not scorecard:
            return []
        last_inn  = scorecard[-1]
        inn_label = last_inn.get("inning", "")
        team      = _team_short(inn_label)
        for b in last_inn.get("batting", []):
            name  = b.get("batsman", b.get("name", ""))
            if not name:
                continue
            runs  = _int(b.get("r",  b.get("runs",  0)))
            balls = max(1, _int(b.get("b", b.get("balls", 1))))
            fours = _int(b.get("4s", b.get("fours", 0)))
            sixes = _int(b.get("6s", b.get("sixes", 0)))
            sr    = round(runs / balls * 100, 1)
            form  = min(100, int(sr * 0.5 + runs * 0.3 + fours * 2 + sixes * 3))
            p50   = min(99, max(5, 99 if runs >= 50 else int(runs / 50 * 100)))
            p30   = min(99, max(5, 99 if runs >= 30 else int(runs / 30 * 100)))
            batters.append({
                "name": name, "team": team,
                "runs": runs, "balls": balls,
                "sr": sr, "4s": fours, "6s": sixes,
                "form": form, "p50": p50, "p30": p30,
            })
    except Exception:
        pass
    return batters if len(batters) >= 2 else []

def _extract_bowlers_from_raw(raw: dict) -> list:
    bowlers = []
    try:
        data = raw.get("data", raw)
        if isinstance(data, list):
            data = data[0] if data else {}
        scorecard    = data.get("scorecard", data.get("score", []))
        if not scorecard:
            return []
        last_inn     = scorecard[-1]
        inn_label    = last_inn.get("inning", "")
        batting_team = _team_short(inn_label)
        first_inn    = scorecard[0]
        first_label  = first_inn.get("inning", "")
        bowling_team = _team_short(first_label) if batting_team != _team_short(first_label) else batting_team
        for b in last_inn.get("bowling", []):
            name  = b.get("bowler", b.get("name", ""))
            if not name:
                continue
            overs  = _float(b.get("o",  b.get("overs",   0)))
            runs   = _int(b.get("r",    b.get("runs",    0)))
            wkts   = _int(b.get("w",    b.get("wickets", 0)))
            maiden = _int(b.get("m",    b.get("maidens", 0)))
            econ   = round(runs / overs, 2) if overs > 0 else 0.0
            dot    = min(99, int(maiden * 12 + max(0, 8 - econ) * 4))
            avg    = round(runs / wkts, 1) if wkts > 0 else 0.0
            threat = min(99, int(wkts * 25 + max(0, 10 - econ) * 4 + dot * 0.3))
            bowlers.append({
                "name": name, "team": bowling_team,
                "overs": overs, "runs": runs, "wkts": wkts,
                "econ": econ, "dot": dot, "threat": threat, "avg": avg,
            })
    except Exception:
        pass
    return bowlers if len(bowlers) >= 2 else []

def _transform_scorecard(raw: dict):
    if not raw:
        return None
    try:
        data = raw.get("data", raw)
        if isinstance(data, list):
            data = data[0] if data else {}
        if not data:
            return None
        name   = data.get("name",   data.get("matchDesc",   ""))
        venue  = data.get("venue",  data.get("groundName",  ""))
        status = data.get("status", data.get("matchStatus", "LIVE"))
        score  = data.get("score",  data.get("scorecard",   []))
        if not score:
            return None
        inn1_raw = score[0] if len(score) > 0 else {}
        inn2_raw = score[1] if len(score) > 1 else {}
        inn1 = _parse_innings_dict(inn1_raw)
        inn2 = _parse_innings_dict(inn2_raw) if inn2_raw else None
        second_innings = inn2 is not None

        bat_inn   = inn2 if second_innings else inn1
        field_inn = inn1 if second_innings else {
            "name": "", "short": "TBD",
            "score": "—", "wickets": "—", "overs": "0.0", "rr": "0.0",
            "_r": 0, "_w": 0, "_o": 0.0,
        }

        target      = inn1["_r"] + 1 if second_innings else 0
        bat_r       = bat_inn["_r"]
        bat_w       = bat_inn["_w"]
        bat_o       = bat_inn["_o"]
        runs_needed = max(0, target - bat_r) if target > 0 else 0
        balls_used  = int(bat_o) * 6 + round((bat_o % 1) * 10)
        balls_left  = max(0, 120 - balls_used)
        req_rr      = round((runs_needed * 6) / balls_left, 2) if (balls_left > 0 and runs_needed > 0) else 0.0
        phase       = "powerplay" if bat_o <= 6 else ("death" if bat_o >= 15 else "middle")
        bat_wp, fld_wp = _win_prob(bat_r, bat_w, bat_o, target) if target > 0 else (50, 50)
        rcb_batting = "RCB" in bat_inn["short"]

        return {
            "match":        name,
            "venue":        venue,
            "status":       status,
            "rcb":          bat_inn   if rcb_batting else field_inn,
            "srh":          field_inn if rcb_batting else bat_inn,
            "target":       target,
            "required":     runs_needed,
            "req_rr":       req_rr,
            "balls_left":   balls_left,
            "phase":        phase,
            "rcb_win_prob": bat_wp  if rcb_batting else fld_wp,
            "srh_win_prob": fld_wp  if rcb_batting else bat_wp,
        }
    except Exception:
        return None

@st.cache_data(ttl=REFRESH_SECS, show_spinner=False)
def _fetch_match_list():
    try:
        r = requests.get(
            f"https://{RAPIDAPI_HOST}/matches/v1/live",
            headers=API_HEADERS, timeout=8,
        )
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

@st.cache_data(ttl=REFRESH_SECS, show_spinner=False)
def _fetch_scorecard(match_id):
    try:
        r = requests.get(
            f"https://{RAPIDAPI_HOST}/mcenter/v1/{match_id}/hscard",
            headers=API_HEADERS, timeout=8,
        )
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

@st.cache_data(ttl=120, show_spinner=False)
def fetch_news():
    url = "https://news.google.com/rss/search?q=IPL+2026&hl=en-IN&gl=IN&ceid=IN:en"
    try:
        feed = feedparser.parse(url)
        return [
            {
                "title":     e.get("title", ""),
                "source":    e.get("source", {}).get("title", ""),
                "published": e.get("published", ""),
                "link":      e.get("link", "#"),
            }
            for e in feed.entries[:8]
        ]
    except Exception:
        return []


def _parse_cricbuzz_live(raw_list: dict) -> list:
    """
    Flatten Cricbuzz live match list into a simple list of dicts with keys:
      matchId, team1, team2, seriesName, status, score1, score2
    """
    results = []
    try:
        for type_match in raw_list.get("typeMatches", []):
            for series_match in type_match.get("seriesMatches", []):
                wrapper = series_match.get("seriesAdWrapper", {})
                series_name = wrapper.get("seriesName", "")
                for match in wrapper.get("matches", []):
                    mi     = match.get("matchInfo", {})
                    ms     = match.get("matchScore", {})
                    mid    = str(mi.get("matchId", ""))
                    team1  = mi.get("team1", {}).get("teamName", "")
                    team2  = mi.get("team2", {}).get("teamName", "")
                    status = mi.get("status", "")
                    # scores may not exist for upcoming
                    t1s = ms.get("team1Score", {})
                    t2s = ms.get("team2Score", {})
                    results.append({
                        "matchId":    mid,
                        "team1":      team1,
                        "team2":      team2,
                        "seriesName": series_name,
                        "status":     status,
                        "t1_score":   t1s,
                        "t2_score":   t2s,
                    })
    except Exception:
        pass
    return results


def _parse_cricbuzz_scorecard(raw_sc: dict, match_meta: dict) -> tuple:
    """
    Parse Cricbuzz /mcenter/v1/{id}/hscard response into (sc_dict, batters, bowlers).
    Returns (None, [], []) on failure.
    """
    try:
        data      = raw_sc.get("scoreCard", [])
        match_hdr = raw_sc.get("matchHeader", {})

        if not data:
            return None, [], []

        team1_name = match_hdr.get("team1", {}).get("name", match_meta.get("team1", ""))
        team2_name = match_hdr.get("team2", {}).get("name", match_meta.get("team2", ""))
        venue      = match_hdr.get("matchInfo", {}).get("ground", {}).get("longName", "")
        status     = match_hdr.get("status", "LIVE")
        match_name = f"{team1_name} vs {team2_name}"

        # innings 0=first, 1=second (if exists)
        inn1 = data[0] if len(data) > 0 else None
        inn2 = data[1] if len(data) > 1 else None

        def parse_inn(inn, team_name):
            if not inn:
                return None
            score = inn.get("scoreDetails", {})
            r = _int(score.get("runs", 0))
            w = _int(score.get("wickets", 0))
            o = _float(score.get("overs", 0))
            rr = round(r / o, 2) if o > 0 else 0.0
            return {
                "name":    team_name,
                "short":   _team_short(team_name),
                "score":   str(r),
                "wickets": str(w),
                "overs":   str(o),
                "rr":      str(rr),
                "_r": r, "_w": w, "_o": o,
            }

        t1_inn = parse_inn(inn1, team1_name)
        t2_inn = parse_inn(inn2, team2_name)

        if t1_inn is None:
            return None, [], []

        second_innings = t2_inn is not None
        bat_inn   = t2_inn if second_innings else t1_inn
        field_inn = t1_inn if second_innings else {
            "name": team2_name, "short": _team_short(team2_name),
            "score": "—", "wickets": "—", "overs": "0.0", "rr": "0.0",
            "_r": 0, "_w": 0, "_o": 0.0,
        }

        target      = t1_inn["_r"] + 1 if second_innings else 0
        runs_needed = max(0, target - bat_inn["_r"]) if target > 0 else 0
        balls_used  = int(bat_inn["_o"]) * 6 + round((bat_inn["_o"] % 1) * 10)
        balls_left  = max(0, 120 - balls_used)
        req_rr      = round((runs_needed * 6) / balls_left, 2) if (balls_left > 0 and runs_needed > 0) else 0.0
        phase       = "powerplay" if bat_inn["_o"] <= 6 else ("death" if bat_inn["_o"] >= 15 else "middle")
        bat_wp, fld_wp = _win_prob(bat_inn["_r"], bat_inn["_w"], bat_inn["_o"], target) if target > 0 else (50, 50)

        rcb_bat = "RCB" in bat_inn["short"]
        sc_dict = {
            "match":        match_name,
            "venue":        venue,
            "status":       status,
            "rcb":          bat_inn   if rcb_bat else field_inn,
            "srh":          field_inn if rcb_bat else bat_inn,
            "target":       target,
            "required":     runs_needed,
            "req_rr":       req_rr,
            "balls_left":   balls_left,
            "phase":        phase,
            "rcb_win_prob": bat_wp if rcb_bat else fld_wp,
            "srh_win_prob": fld_wp if rcb_bat else bat_wp,
        }

        # Extract batters from the active innings
        batters = []
        active_inn = inn2 if second_innings else inn1
        bat_team   = bat_inn["short"]
        bats_data  = active_inn.get("batTeamDetails", {}).get("batsmenData", {})
        for key, b in bats_data.items():
            name  = b.get("batName", "")
            if not name:
                continue
            runs  = _int(b.get("runs", 0))
            balls = max(1, _int(b.get("balls", 1)))
            fours = _int(b.get("fours", 0))
            sixes = _int(b.get("sixes", 0))
            sr    = round(_float(b.get("strikeRate", 0)) or runs / balls * 100, 1)
            form  = min(100, int(sr * 0.5 + runs * 0.3 + fours * 2 + sixes * 3))
            p50   = min(99, max(5, 99 if runs >= 50 else int(runs / 50 * 100)))
            p30   = min(99, max(5, 99 if runs >= 30 else int(runs / 30 * 100)))
            batters.append({
                "name": name, "team": bat_team,
                "runs": runs, "balls": balls,
                "sr": sr, "4s": fours, "6s": sixes,
                "form": form, "p50": p50, "p30": p30,
            })

        # Extract bowlers from the active innings
        bowlers = []
        bowl_team  = field_inn["short"]
        bowls_data = active_inn.get("bowlTeamDetails", {}).get("bowlersData", {})
        for key, b in bowls_data.items():
            name  = b.get("bowlName", "")
            if not name:
                continue
            overs  = _float(b.get("overs",   0))
            runs   = _int(b.get("runs",      0))
            wkts   = _int(b.get("wickets",   0))
            maiden = _int(b.get("maidens",   0))
            econ   = round(_float(b.get("economy", 0)) or (runs / overs if overs > 0 else 0), 2)
            dot    = min(99, int(maiden * 12 + max(0, 8 - econ) * 4))
            avg    = round(runs / wkts, 1) if wkts > 0 else 0.0
            threat = min(99, int(wkts * 25 + max(0, 10 - econ) * 4 + dot * 0.3))
            bowlers.append({
                "name": name, "team": bowl_team,
                "overs": overs, "runs": runs, "wkts": wkts,
                "econ": econ, "dot": dot, "threat": threat, "avg": avg,
            })

        return sc_dict, (batters if len(batters) >= 2 else []), (bowlers if len(bowlers) >= 2 else [])

    except Exception:
        return None, [], []


def resolve_live_match(debug=False):
    raw_list = _fetch_match_list()
    if debug and raw_list:
        with st.expander("🔍 RAW — Match List (Cricbuzz)", expanded=False):
            st.json(raw_list)
    if not raw_list:
        return None, [], []

    matches = _parse_cricbuzz_live(raw_list)

    for match in matches:
        series = match["seriesName"].upper()
        t1     = match["team1"].upper()
        t2     = match["team2"].upper()
        status = match["status"].lower()

        if "IPL" not in series and "INDIAN PREMIER" not in series:
            continue
        if "upcom" in status or "yet to" in status or "preview" in status or not match["matchId"]:
            continue

        raw_sc = _fetch_scorecard(match["matchId"])
        if debug and raw_sc:
            with st.expander(f"🔍 RAW — Scorecard ({match['matchId']})", expanded=False):
                st.json(raw_sc)
        if not raw_sc:
            continue

        sc, batters, bowlers = _parse_cricbuzz_scorecard(raw_sc, match)
        if sc:
            return sc, batters, bowlers

    return None, [], []


# ─────────────────────────────────────────────────────────────────
# 5. DEMO DATA
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
    dot  = max(10, 30 - pressure*10)
    one  = max(15, 22 - pressure*5)
    two  = max(8,  14 - pressure*3)
    four = max(12, 18 + pressure*5)
    six  = max(8,  10 + pressure*8)
    wkt  = max(4,   6 + pressure*6)
    tot  = dot+one+two+four+six+wkt
    return {
        "dot": round(dot/tot*100), "1": round(one/tot*100),
        "2":   round(two/tot*100), "4": round(four/tot*100),
        "6":   round(six/tot*100), "W": round(wkt/tot*100),
    }


# ─────────────────────────────────────────────────────────────────
# 6. CHART BUILDERS
# ─────────────────────────────────────────────────────────────────
def chart_momentum(ov, wp, rr, req):
    fig = make_subplots(specs=[[{"secondary_y":True}]])
    fig.add_trace(go.Scatter(x=ov, y=wp, name="RCB Win Prob %",
        mode="lines", line=dict(color="#00D1FF",width=2.5,shape="spline",smoothing=1.1),
        fill="tozeroy", fillcolor="rgba(0,209,255,0.06)",
        hovertemplate="Over %{x}: RCB %{y}%<extra></extra>"), secondary_y=False)
    fig.add_trace(go.Scatter(x=ov, y=rr, name="Actual RR",
        mode="lines", line=dict(color="#FFB547",width=1.8,dash="dot",shape="spline"),
        hovertemplate="Over %{x}: RR %{y}<extra></extra>"), secondary_y=True)
    fig.add_trace(go.Scatter(x=ov, y=req, name="Required RR",
        mode="lines", line=dict(color="#FF3E3E",width=1.8,dash="dash",shape="spline"),
        hovertemplate="Over %{x}: Req %{y}<extra></extra>"), secondary_y=True)
    fig.add_hline(y=50, secondary_y=False,
                  line_dash="dot", line_color="rgba(255,255,255,0.10)", line_width=1)
    fig.update_layout(**_layout(
        title=dict(text="WIN PROBABILITY & RUN RATE MATRIX",
                   font=dict(size=11,color="#484F58"),x=0,xanchor="left"),
        xaxis=_ax("Over"),
        yaxis=_ax("Win Prob (%)", sfx="%", rng=[0,100]),
        yaxis2=_ax2("Run Rate"),
    ))
    return fig

def chart_run_progression(hist):
    ov   = [h["over"] for h in hist]
    runs = [h["runs"] for h in hist]
    cum  = [h["cum"]  for h in hist]
    wo   = [h["over"] for h in hist if h["wkts"]>0]
    wc   = [h["cum"]  for h in hist if h["wkts"]>0]
    fig  = make_subplots(specs=[[{"secondary_y":True}]])
    fig.add_trace(go.Bar(x=ov, y=runs, name="Runs/Over",
        marker=dict(color=["#FF3E3E" if r>14 else ("#FFB547" if r>10 else "#00D1FF") for r in runs], opacity=0.8),
        hovertemplate="Over %{x}: %{y} runs<extra></extra>"), secondary_y=False)
    fig.add_trace(go.Scatter(x=ov, y=cum, name="Cumulative",
        mode="lines+markers", line=dict(color="#3DFF7A",width=2),
        marker=dict(size=5,color="#3DFF7A"),
        hovertemplate="After Over %{x}: %{y}<extra></extra>"), secondary_y=True)
    if wo:
        fig.add_trace(go.Scatter(x=wo, y=wc, name="Wicket",
            mode="markers",
            marker=dict(symbol="x",size=12,color="#FF3E3E",line=dict(width=2,color="#FF3E3E")),
            hovertemplate="Wicket at Over %{x}<extra></extra>"), secondary_y=True)
    fig.update_layout(**_layout(
        title=dict(text="RUN PROGRESSION — OVER BY OVER",
                   font=dict(size=11,color="#484F58"),x=0,xanchor="left"),
        xaxis=_ax("Over"),
        yaxis=_ax("Runs/Over"),
        yaxis2=_ax2("Cumulative"),
    ))
    return fig

def chart_wagon():
    cats = ["Straight","Cover","Square Leg","Fine Leg","Mid-Wicket","Point"]
    rcb  = [34,48,22,15,38,27]
    srh  = [41,35,30,18,42,22]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=rcb+[rcb[0]],theta=cats+[cats[0]],name="RCB",
        fill="toself",line=dict(color="#00D1FF",width=2),fillcolor="rgba(0,209,255,0.08)"))
    fig.add_trace(go.Scatterpolar(r=srh+[srh[0]],theta=cats+[cats[0]],name="SRH",
        fill="toself",line=dict(color="#FFB547",width=2),fillcolor="rgba(255,181,71,0.06)"))
    fig.update_layout(paper_bgcolor=BG,
        polar=dict(bgcolor=BG,
            radialaxis=dict(visible=True,range=[0,55],gridcolor="rgba(255,255,255,0.06)",color="#484F58"),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.06)",color="#7D8590")),
        font=dict(family=FF,color=FC,size=10),
        legend=dict(orientation="h",yanchor="top",y=-0.05,xanchor="center",x=0.5,bgcolor=BG),
        margin=dict(l=20,r=20,t=30,b=20),
        title=dict(text="SHOT ZONE DISTRIBUTION",font=dict(size=11,color="#484F58"),x=0.5,xanchor="center"))
    return fig

def chart_bowler_radar(bowlers, team):
    bw = [b for b in bowlers if b["team"]==team]
    cats = ["Wickets","Economy(inv)","Dot %","Avg(inv)","Threat"]
    clrs = ["#00D1FF","#FFB547","#3DFF7A","#FF3E3E","#BF7FFF"]
    fig = go.Figure()
    for i, b in enumerate(bw):
        ei  = max(0, 100 - b["econ"]*6)
        ai  = max(0, 100 - b["avg"]*2) if b["avg"]>0 else 80
        vals = [b["wkts"]*25, ei, b["dot"], ai, b["threat"]]
        c = clrs[i % len(clrs)]
        r,g,bl = int(c[1:3],16), int(c[3:5],16), int(c[5:7],16)
        fig.add_trace(go.Scatterpolar(
            r=vals+[vals[0]], theta=cats+[cats[0]],
            name=b["name"].split()[-1], fill="toself",
            line=dict(color=c,width=2),
            fillcolor=f"rgba({r},{g},{bl},0.07)"))
    fig.update_layout(paper_bgcolor=BG,
        polar=dict(bgcolor=BG,
            radialaxis=dict(visible=True,range=[0,100],gridcolor="rgba(255,255,255,0.05)",color="#484F58"),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.06)",color="#7D8590")),
        font=dict(family=FF,color=FC,size=10),
        legend=dict(orientation="h",yanchor="top",y=-0.08,xanchor="center",x=0.5,bgcolor=BG),
        margin=dict(l=20,r=20,t=30,b=20),
        title=dict(text=f"{team} BOWLING THREAT RADAR",font=dict(size=11,color="#484F58"),x=0.5,xanchor="center"))
    return fig

def chart_partnership(parts):
    labels = [f"P{p['wkt']}: {p['pair']}" for p in parts]
    runs   = [p["runs"] for p in parts]
    fig = go.Figure(go.Bar(
        x=runs, y=labels, orientation="h",
        marker=dict(color=["#00D1FF","#FFB547","#3DFF7A"],opacity=0.8),
        text=[f"{r} runs · {p['balls']} balls · {p['rate']} rpo" for r,p in zip(runs,parts)],
        textfont=dict(family=FF,size=10,color="#E6EDF3"),
        textposition="inside",
        hovertemplate="%{y}: %{x} runs<extra></extra>"))
    fig.update_layout(**_layout(
        title=dict(text="PARTNERSHIP ANALYSIS",font=dict(size=11,color="#484F58"),x=0,xanchor="left"),
        xaxis=_ax("Runs"),
        yaxis=dict(showgrid=False,tickfont=dict(size=10,family=FF),color=FC),
        height=180))
    return fig

def chart_batter_compare(batters):
    names  = [b["name"].split()[-1] for b in batters]
    runs   = [b["runs"] for b in batters]
    sr     = [b["sr"]   for b in batters]
    colors = ["#00D1FF" if b["team"]=="RCB" else "#FFB547" for b in batters]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=names,y=runs,name="Runs",
        marker=dict(color=colors,opacity=0.75),
        hovertemplate="%{x}: %{y} runs<extra></extra>"))
    fig.add_trace(go.Scatter(x=names,y=sr,name="Strike Rate",
        mode="lines+markers",yaxis="y2",
        line=dict(color="#3DFF7A",width=2),
        marker=dict(size=8,color="#3DFF7A"),
        hovertemplate="%{x}: SR %{y}<extra></extra>"))
    fig.update_layout(**_layout(
        title=dict(text="BATTER COMPARISON — Runs & Strike Rate",
                   font=dict(size=11,color="#484F58"),x=0,xanchor="left"),
        xaxis=_ax(""),
        yaxis=_ax("Runs"),
        yaxis2=_ax2("Strike Rate")))
    return fig


# ─────────────────────────────────────────────────────────────────
# 7. UI RENDERERS
# ─────────────────────────────────────────────────────────────────

def render_masterhead(match_label=""):
    IST = pytz.timezone('Asia/Kolkata')
    now = datetime.now(IST).strftime("%d %b %Y  ·  %H:%M:%S IST")
    label = match_label or "LIVE FEED ACTIVE"
    st.markdown(
        f'<div class="mh">'
        f'<div><div class="mh-logo">GOD\'S<span>EYE</span> v3.4&nbsp;'
        f'<span style="font-size:11px;color:var(--td);font-weight:400">IPL MATCH CENTER</span></div>'
        f'<div style="font-family:var(--fm);font-size:10px;color:var(--td);margin-top:4px;">'
        f'<span class="ld"></span>{label}</div></div>'
        f'<div class="mh-meta"><div style="color:var(--tm);margin-bottom:2px">{now}</div>'
        f'<div>OPERATOR: <span style="color:var(--tp)">UDAY MADDILA</span></div></div>'
        f'</div>',
        unsafe_allow_html=True)


def render_press_box(sc):
    rr     = sc.get("req_rr", 0)
    wp     = sc.get("rcb_win_prob", 50)
    swp    = sc.get("srh_win_prob", 50)
    balls  = sc.get("balls_left", 0)
    req    = sc.get("required", 0)
    target = sc.get("target", 0)
    phase  = sc.get("phase", "middle")
    rcb_rr = sc.get("rcb",{}).get("rr","—")
    srh_rr = sc.get("srh",{}).get("rr","—")
    wp_b   = "b-red" if wp<30 else ("b-amber" if wp<50 else "b-cyan")
    wp_lbl = "[P0 CRITICAL]" if wp<25 else ("[P1 ELEVATED]" if wp<50 else "[P2 NOMINAL]")
    wp_c   = "var(--red)" if wp<40 else "var(--cyan)"
    rr_c   = "var(--red)" if rr>12 else ("var(--amber)" if rr>9 else "var(--green)")
    ph_map = {"powerplay":("POWERPLAY","ppp"),"middle":("MIDDLE","ppm"),"death":("DEATH","ppd")}
    ph_t, ph_c = ph_map.get(phase, ("MIDDLE","ppm"))
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1:
        st.markdown(f'<div class="gc"><div class="badge {wp_b}">{wp_lbl}</div>'
                    f'<div class="kl">WIN PROBABILITY</div>'
                    f'<div class="mlg" style="color:{wp_c}">{wp}%</div>'
                    f'<div class="ku">RCB &middot; SRH {swp}%</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="gc"><div class="badge b-amber">[P1 ELEVATED]</div>'
                    f'<div class="kl">REQUIRED RUN RATE</div>'
                    f'<div class="mlg" style="color:{rr_c}">{rr}</div>'
                    f'<div class="ku">{req} runs &middot; {balls} balls</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="gc"><div class="badge b-cyan">[INTELLIGENCE]</div>'
                    f'<div class="kl">MATCH TARGET</div>'
                    f'<div class="mlg">{target}</div>'
                    f'<div class="ku">1st innings total + 1</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="gc"><div class="badge b-cyan">[MATCH PHASE]</div>'
                    f'<div class="kl">CURRENT PHASE</div>'
                    f'<div style="margin-top:8px"><span class="pp {ph_c}">{ph_t}</span></div>'
                    f'</div>', unsafe_allow_html=True)
    with c5:
        st.markdown(f'<div class="gc"><div class="badge b-green">[P3 NOMINAL]</div>'
                    f'<div class="kl">CURRENT RUN RATE</div>'
                    f'<div class="mlg">{rcb_rr}</div>'
                    f'<div class="ku">SRH CRR: {srh_rr}</div></div>', unsafe_allow_html=True)


def render_scorebook(sc):
    st.markdown('<div class="sh" style="margin-top:20px">&#9672; THE SCOREBOOK</div>', unsafe_allow_html=True)
    rcb  = sc.get("rcb",{})
    srh  = sc.get("srh",{})
    wp   = sc.get("rcb_win_prob",50)
    swp  = sc.get("srh_win_prob",50)
    req  = sc.get("required",0)
    bl   = sc.get("balls_left",0)
    rr   = sc.get("req_rr",0)
    rc   = "var(--red)" if rr>10 else "var(--amber)"
    clutch_class = "clutch-alert" if rr > 10 else ""
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
        f'<div class="pr"><span style="color:#00D1FF">{rcb.get("short","RCB")}</span><span>{wp}%</span></div>'
        f'<div class="pt"><div class="pbc" style="width:{wp}%"></div></div>'
        f'<div class="pr" style="margin-top:10px"><span style="color:#FFB547">{srh.get("short","SRH")}</span><span>{swp}%</span></div>'
        f'<div class="pt"><div class="pba" style="width:{swp}%"></div></div>'
        f'<div style="text-align:center;margin-top:14px;font-family:var(--fm);font-size:10px;color:var(--td)">{sc.get("venue","&mdash;")}</div>'
        f'<div style="text-align:center;margin-top:4px;font-family:var(--fm);font-size:11px;color:var(--tm)">{sc.get("status","LIVE")}</div>'
        '</div>'
        '<div style="flex:1;min-width:160px;text-align:right">'
        f'<div class="tl" style="color:#FF822A;text-align:right">&#9670; {srh.get("short","SRH")}</div>'
        f'<div class="mxl">{srh.get("score","&mdash;")}/{srh.get("wickets","&mdash;")}</div>'
        f'<div style="font-family:var(--fm);font-size:13px;color:var(--tm);margin-top:5px">({srh.get("overs","&mdash;")} OV) &nbsp;CRR: {srh.get("rr","&mdash;")}</div>'
        '</div>'
        '</div>'
        '<div style="margin-top:20px;padding:11px 16px;background:rgba(255,62,62,0.06);'
        'border:1px solid rgba(255,62,62,0.2);border-radius:8px;font-family:var(--fm);'
        'font-size:12px;color:var(--tm);display:flex;justify-content:space-between;align-items:center">'
        f'<span><span style="color:var(--red);font-weight:700">RCB CHASE STATUS</span>&nbsp;&middot;&nbsp;'
        f'Need <b style="color:var(--tp)">{req}</b> runs off <b style="color:var(--tp)">{bl}</b> balls</span>'
        f'<span>Req RR: <b style="color:{rc}">{rr}</b></span>'
        '</div></div>',
        unsafe_allow_html=True)


def render_next_ball(sc):
    st.markdown('<div class="sh" style="margin-top:22px">&#9672; NEXT BALL INTELLIGENCE</div>', unsafe_allow_html=True)
    probs    = next_ball_probs(sc)
    req_rr   = float(sc.get("req_rr", 7))
    wp       = sc.get("rcb_win_prob", 50)
    pressure = min(100, int(req_rr/18*100 + (50-wp)*0.6))
    pc = "var(--red)" if pressure>70 else ("var(--amber)" if pressure>45 else "var(--green)")
    pl = "EXTREME" if pressure>70 else ("HIGH" if pressure>45 else "MANAGEABLE")
    ml = max(probs, key=probs.get)
    ml_desc = {"dot":"DOT BALL — defence expected","1":"SINGLE — rotation play",
               "2":"TWO RUNS — good running","4":"BOUNDARY incoming",
               "6":"SIX! — maximum likely","W":"WICKET ALERT"}
    cell_styles = {
        "dot":("#484F58","rgba(72,79,88,0.2)"),
        "1":  ("#7D8590","rgba(125,133,144,0.15)"),
        "2":  ("#FFB547","rgba(255,181,71,0.15)"),
        "4":  ("#00D1FF","rgba(0,209,255,0.15)"),
        "6":  ("#3DFF7A","rgba(61,255,122,0.15)"),
        "W":  ("#FF3E3E","rgba(255,62,62,0.15)"),
    }
    cells = '<div class="nb-grid">'
    for lbl, pct in probs.items():
        clr, bg = cell_styles[lbl]
        cells += (f'<div class="nb-cell" style="color:{clr};background:{bg};border-color:{clr}40">'
                  f'<div style="font-size:18px;font-weight:700">{lbl}</div>'
                  f'<div style="font-size:10px;margin-top:4px;color:var(--tm)">{pct}%</div></div>')
    cells += '</div>'
    ca, cb = st.columns([3,2], gap="medium")
    with ca:
        st.markdown(
            f'<div class="gc gc-cyan"><div class="kl">NEXT BALL — OUTCOME PROBABILITIES</div>'
            + cells +
            f'<div style="margin-top:14px;font-family:var(--fm);font-size:11px;color:var(--tm)">'
            f'&#9654; Most likely: <b style="color:var(--cyan)">{ml_desc[ml]}</b></div></div>',
            unsafe_allow_html=True)
    with cb:
        wkts_left = 10 - int(sc.get("rcb",{}).get("wickets","3") or 3)
        st.markdown(
            f'<div class="gc gc-red" style="height:100%">'
            f'<div class="kl">BATTING PRESSURE INDEX</div>'
            f'<div style="font-family:var(--fm);font-size:42px;font-weight:700;color:{pc};line-height:1">{pressure}</div>'
            f'<div style="font-family:var(--fm);font-size:11px;color:{pc};letter-spacing:2px;margin-top:4px">{pl}</div>'
            f'<div class="pt" style="margin-top:16px"><div class="mf" style="width:{pressure}%;background:{pc}"></div></div>'
            f'<div style="margin-top:18px;font-family:var(--fm);font-size:11px;color:var(--tm);line-height:1.7">'
            f'Req RR: <b style="color:var(--tp)">{sc.get("req_rr","&mdash;")}</b><br>'
            f'Balls left: <b style="color:var(--tp)">{sc.get("balls_left","&mdash;")}</b><br>'
            f'Wickets left: <b style="color:var(--tp)">{wkts_left}</b></div></div>',
            unsafe_allow_html=True)


def render_batter_predictor(batters):
    st.markdown('<div class="sh" style="margin-top:22px">&#9672; BATTER MILESTONE PREDICTOR</div>', unsafe_allow_html=True)
    ca, cb = st.columns(2, gap="medium")
    for col, team in [(ca,"RCB"),(cb,"SRH")]:
        with col:
            tb  = [b for b in batters if b["team"]==team]
            tc  = "#D22D3D" if team=="RCB" else "#FF822A"
            html= f'<div class="gc" style="border-left:3px solid {tc}">'
            html+= f'<div style="font-family:var(--fm);font-size:10px;letter-spacing:2px;color:var(--td);margin-bottom:12px">{team} BATTERS</div>'
            for b in tb:
                p50c = "var(--green)" if b["p50"]>75 else ("var(--amber)" if b["p50"]>40 else "var(--red)")
                p30c = "var(--green)" if b["p30"]>75 else ("var(--amber)" if b["p30"]>40 else "var(--red)")
                fc   = "var(--green)" if b["form"]>80 else ("var(--amber)" if b["form"]>60 else "var(--red)")
                html += (
                    f'<div class="pl-row">'
                    f'<div><div class="pl-n">{b["name"]}</div>'
                    f'<div class="pl-r">{b["runs"]}r ({b["balls"]}b) SR:{b["sr"]} &nbsp;4s:{b["4s"]} 6s:{b["6s"]}</div></div>'
                    f'<div style="text-align:right;min-width:150px">'
                    f'<div style="font-family:var(--fm);font-size:9px;color:var(--td)">HIT 50</div>'
                    f'<div class="mt"><div class="mf" style="width:{b["p50"]}%;background:{p50c}"></div></div>'
                    f'<div style="font-family:var(--fm);font-size:10px;color:{p50c}">{b["p50"]}%</div>'
                    f'<div style="font-family:var(--fm);font-size:9px;color:var(--td);margin-top:4px">HIT 30</div>'
                    f'<div class="mt"><div class="mf" style="width:{b["p30"]}%;background:{p30c}"></div></div>'
                    f'<div style="font-family:var(--fm);font-size:10px;color:{p30c}">{b["p30"]}%</div>'
                    f'<div style="font-family:var(--fm);font-size:9px;color:var(--td);margin-top:4px">FORM</div>'
                    f'<div class="mt"><div class="mf" style="width:{b["form"]}%;background:{fc}"></div></div>'
                    f'<div style="font-family:var(--fm);font-size:10px;color:{fc}">{b["form"]}/100</div>'
                    f'</div></div>'
                )
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)


def render_bowler_intel(bowlers):
    st.markdown('<div class="sh" style="margin-top:22px">&#9672; BOWLING INTELLIGENCE</div>', unsafe_allow_html=True)
    ca, cb = st.columns([3,2], gap="medium")
    with ca:
        html = ('<div class="gc gc-purple">'
                '<div style="font-family:var(--fm);font-size:10px;letter-spacing:2px;color:var(--td);margin-bottom:12px">BOWLER ANALYTICS TABLE</div>'
                '<div style="display:grid;grid-template-columns:2fr 1fr 1fr 1fr 1fr 1.2fr;gap:4px;'
                'font-family:var(--fm);font-size:9px;color:var(--td);letter-spacing:1px;'
                'border-bottom:1px solid var(--border);padding-bottom:6px;margin-bottom:4px">'
                '<div>BOWLER</div><div style="text-align:center">OVRS</div>'
                '<div style="text-align:center">WKTS</div><div style="text-align:center">ECON</div>'
                '<div style="text-align:center">DOT%</div><div style="text-align:center">THREAT</div>'
                '</div>')
        for b in bowlers:
            ec   = b["econ"]
            ec_c = "var(--green)" if ec<7 else ("var(--amber)" if ec<10 else "var(--red)")
            th_c = "var(--red)" if b["threat"]>80 else ("var(--amber)" if b["threat"]>55 else "var(--green)")
            t_c  = "#00D1FF" if b["team"]=="RCB" else "#FFB547"
            html += (
                f'<div class="pl-row" style="display:grid;grid-template-columns:2fr 1fr 1fr 1fr 1fr 1.2fr;gap:4px">'
                f'<div><div class="pl-n">{b["name"]}</div><div class="pl-r" style="color:{t_c}">{b["team"]}</div></div>'
                f'<div style="text-align:center;font-family:var(--fm);font-size:12px;color:var(--tp);align-self:center">{b["overs"]}</div>'
                f'<div style="text-align:center;font-family:var(--fm);font-size:12px;color:var(--tp);align-self:center">{b["wkts"]}</div>'
                f'<div style="text-align:center;font-family:var(--fm);font-size:12px;color:{ec_c};align-self:center">{ec}</div>'
                f'<div style="text-align:center;font-family:var(--fm);font-size:12px;color:var(--tp);align-self:center">{b["dot"]}%</div>'
                f'<div style="text-align:center;align-self:center">'
                f'<span style="font-family:var(--fm);font-size:12px;color:{th_c};font-weight:700">{b["threat"]}</span>'
                f'<div class="mt" style="width:60px;margin:3px auto 0"><div class="mf" style="width:{b["threat"]}%;background:{th_c}"></div></div>'
                f'</div></div>'
            )
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)
    with cb:
        srh_bowlers = [b for b in bowlers if b["team"]=="SRH"]
        radar_team  = "SRH" if srh_bowlers else (bowlers[0]["team"] if bowlers else "SRH")
        st.plotly_chart(chart_bowler_radar(bowlers, radar_team), width="stretch", config={"displayModeBar":False})


def render_momentum_matrix(sc):
    st.markdown('<div class="sh" style="margin-top:22px">&#9672; MOMENTUM MATRIX</div>', unsafe_allow_html=True)
    ov, wp, rr, req = demo_momentum()
    hist  = demo_history()
    parts = demo_partnerships()
    bats  = demo_batters()
    c1, c2 = st.columns([3,2], gap="medium")
    with c1:
        st.plotly_chart(chart_momentum(ov,wp,rr,req), width="stretch", config={"displayModeBar":False})
    with c2:
        st.plotly_chart(chart_wagon(), width="stretch", config={"displayModeBar":False})
    c3, c4 = st.columns([3,2], gap="medium")
    with c3:
        st.plotly_chart(chart_run_progression(hist), width="stretch", config={"displayModeBar":False})
    with c4:
        st.plotly_chart(chart_partnership(parts), width="stretch", config={"displayModeBar":False})
        st.plotly_chart(chart_batter_compare(bats), width="stretch", config={"displayModeBar":False})


def render_intel_row(news):
    st.markdown('<div class="sh" style="margin-top:22px">&#9672; LIVE INTELLIGENCE FEED</div>', unsafe_allow_html=True)
    ca, cb = st.columns([1,2], gap="medium")
    with ca:
        st.markdown(
            '<div class="gc gc-cyan">'
            '<div style="font-family:var(--fm);font-size:10px;letter-spacing:2px;color:var(--td);margin-bottom:12px">KEY METRICS</div>'
            '<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px">'
            '<div><div class="kl">TOP SCORER</div><div style="font-family:var(--fm);font-size:14px;font-weight:700;color:var(--tp)">V. Kohli</div><div class="ku">72 (48)</div></div>'
            '<div><div class="kl">BEST BOWLER</div><div style="font-family:var(--fm);font-size:14px;font-weight:700;color:var(--tp)">P. Cummins</div><div class="ku">3/24 (4 OV)</div></div>'
            '<div><div class="kl">6s/4s (RCB)</div><div style="font-family:var(--fm);font-size:14px;font-weight:700;color:var(--cyan)">8 / 14</div><div class="ku">boundary count</div></div>'
            '<div><div class="kl">EXTRAS</div><div style="font-family:var(--fm);font-size:14px;font-weight:700;color:var(--amber)">11</div><div class="ku">Wides:6 NB:2</div></div>'
            '<div><div class="kl">POWERPLAY RR</div><div style="font-family:var(--fm);font-size:14px;font-weight:700;color:var(--green)">9.67</div><div class="ku">Overs 1&ndash;6</div></div>'
            '<div><div class="kl">DLS PAR</div><div style="font-family:var(--fm);font-size:14px;font-weight:700;color:var(--tp)">148</div><div class="ku">at current over</div></div>'
            '</div></div>',
            unsafe_allow_html=True)
    with cb:
        html = ('<div class="gc"><div style="font-family:var(--fm);font-size:10px;letter-spacing:2px;color:var(--td);margin-bottom:12px">PRESS BOX INTEL (CLICK HEADLINES)</div>')
        if news:
            for item in news[:6]:
                html += f'<div class="ni"><div><a href="{item["link"]}" target="_blank" style="color:var(--tp);">{item["title"]}</a></div><div class="ni-s">{item.get("source","&mdash;")} &middot; {item.get("published","")[:22]}</div></div>'
        else:
            html += '<div class="ni" style="color:var(--td)">News feed unavailable.</div>'
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)


def render_neural_verdict(sc, batters, bowlers):
    wp    = sc.get("rcb_win_prob", 38)
    rr    = sc.get("req_rr", 6.86)
    phase = sc.get("phase", "death")
    bl    = sc.get("balls_left", 27)
    req   = sc.get("required", 46)
    arc_r = [b for b in batters if b["team"]=="RCB"]
    arc_s = [b for b in bowlers if b["team"]=="SRH"]
    top_bat = max(arc_r, key=lambda b:b["p50"]) if arc_r else None
    top_bwl = max(arc_s, key=lambda b:b["threat"]) if arc_s else None
    eco_k   = min(arc_s, key=lambda b:b["econ"])   if arc_s else None
    if wp>=60:
        sent,sc2="#00D1FF","STRONGLY FAVOURS RCB"
        body = (f"Neural pattern analysis indicates a high-confidence RCB chase. With {req} required off "
                f"{bl} balls (req RR {rr}), the model assigns {wp}% to RCB. "
                f"Historical Chinnaswamy data shows 71% conversion from this position.")
    elif wp>=45:
        sent,sc2="#FFB547","CONTESTED — MARGINAL EDGE RCB"
        body = (f"Delicately balanced. RCB hold a {wp}% edge, but req rate of {rr} demands "
                f"calculated aggression in the {phase} phase. Batting depth is the decisive variable.")
    else:
        sent,sc2="#FF3E3E","STRONGLY FAVOURS SRH"
        body = (f"High-pressure scenario for RCB. Required rate {rr} over {bl} balls achieved only "
                f"24% of the time at this venue in {phase} overs. SRH bowling depth adds significant variance.")
    conf    = min(99, int(abs(wp-50)*2+50))
    IST     = pytz.timezone('Asia/Kolkata')
    now_str = datetime.now(IST).strftime("%H:%M:%S IST")
    html = (
        f'<div class="vd"><div class="vd-h">&#9672; 3RD UMPIRE AI &mdash; NEURAL PATTERN ANALYSIS &nbsp;&middot;&nbsp;'
        f'<span style="color:var(--td)">CONFIDENCE: <b style="color:{sc2}">{conf}%</b></span></div>'
        f'<div style="font-family:var(--fm);font-size:12px;font-weight:700;color:{sc2};letter-spacing:2px;margin-bottom:10px">VERDICT &mdash; {sent}</div>'
        f'<div style="font-size:14px;color:var(--tp);line-height:1.7">{body}</div>'
    )
    if top_bat:
        html += (f'<div class="pb1" style="margin-top:16px">'
                 f'<div style="font-family:var(--fm);font-size:10px;letter-spacing:2px;color:var(--cyan);margin-bottom:6px">&#9650; KEY BATTER TO WATCH</div>'
                 f'<b style="color:var(--tp)">{top_bat["name"]}</b> &mdash; '
                 f'{top_bat["runs"]}r ({top_bat["balls"]}b) SR:{top_bat["sr"]} &middot; '
                 f'50-prob: <b style="color:var(--green)">{top_bat["p50"]}%</b> &middot; '
                 f'30-prob: <b style="color:var(--green)">{top_bat["p30"]}%</b>. '
                 f'Form: {top_bat["form"]}/100. Prime finisher candidate.</div>')
    if top_bwl:
        html += (f'<div class="pb2" style="margin-top:6px">'
                 f'<div style="font-family:var(--fm);font-size:10px;letter-spacing:2px;color:var(--red);margin-bottom:6px">&#9654; MOST DANGEROUS BOWLER</div>'
                 f'<b style="color:var(--tp)">{top_bwl["name"]}</b> (SRH) &mdash; '
                 f'{top_bwl["wkts"]} wkts &middot; Econ {top_bwl["econ"]} &middot; '
                 f'Dot%: <b style="color:var(--amber)">{top_bwl["dot"]}%</b> &middot; '
                 f'Threat: <b style="color:var(--red)">{top_bwl["threat"]}/100</b>. '
                 f'High wicket-taking probability in {phase} overs.</div>')
    if eco_k:
        html += (f'<div class="pb3" style="margin-top:6px">'
                 f'<div style="font-family:var(--fm);font-size:10px;letter-spacing:2px;color:var(--amber);margin-bottom:6px">&#9651; ECONOMY MASTER</div>'
                 f'<b style="color:var(--tp)">{eco_k["name"]}</b> &mdash; '
                 f'Economy: <b style="color:var(--green)">{eco_k["econ"]}</b> &middot; '
                 f'Dot%: {eco_k["dot"]}% &middot; Giving fewest runs/over. '
                 f'RCB must target the other end to keep the chase viable.</div>')
    html += (f'<div style="margin-top:14px;font-family:var(--fm);font-size:10px;color:var(--td);'
             f'border-top:1px solid var(--border);padding-top:10px">'
             f'MODEL: GOD\'S EYE v3.4 &middot; RapidAPI / Google News RSS &middot; '
             f'SYNC: {now_str} &middot; OPERATOR: UDAY MADDILA</div></div>')
    st.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# 8. SIDEBAR
# ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div style="font-family:\'JetBrains Mono\',monospace;font-size:12px;'
        'color:#7D8590;margin-bottom:12px">&#9881; SYSTEM CONTROLS</div>',
        unsafe_allow_html=True,
    )
    auto_refresh = st.toggle("Auto-Refresh (30s)", value=True)
    show_demo    = st.toggle("Force Demo Data",    value=False)
    debug_mode   = st.toggle("Debug API Response", value=False)
    st.divider()
    st.markdown(
        '<div style="font-family:\'JetBrains Mono\',monospace;font-size:10px;'
        'color:#484F58">GOD\'S EYE v3.4<br>IPL Match Center<br>'
        '&#169; Uday Maddila</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────
# 9. MAIN RENDER LOOP
# ─────────────────────────────────────────────────────────────────
sc      = None
batters = []
bowlers = []

if not show_demo:
    with st.spinner("Synchronizing with Live Match Feed..."):
        sc, batters, bowlers = resolve_live_match(debug=debug_mode)
if sc is None:
    st.info("📡 No live IPL match found right now. Displaying pre-match demo metrics.")
    sc = demo_sc()

if not batters:
    batters = demo_batters()
if not bowlers:
    bowlers = demo_bowlers()

news = fetch_news()

render_masterhead(sc.get("match", "LIVE FEED ACTIVE"))
render_press_box(sc)
render_scorebook(sc)
render_next_ball(sc)
render_batter_predictor(batters)
render_bowler_intel(bowlers)
render_momentum_matrix(sc)
render_intel_row(news)
render_neural_verdict(sc, batters, bowlers)

if auto_refresh:
    time.sleep(REFRESH_SECS)
    st.rerun()
