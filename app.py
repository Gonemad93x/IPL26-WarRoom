"""
GOD'S EYE v3.5 — IPL LIVE MATCH CENTER
Operator : Uday Maddila
"""

import streamlit as st
import requests
import feedparser
import time
from datetime import datetime
import pytz

st.set_page_config(page_title="GOD'S EYE | IPL 2026", page_icon="🏏",
                   layout="wide", initial_sidebar_state="collapsed")

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
RAPIDAPI_KEY  = "f26160eb44mshc0a20698180c97dp18f61ejsn98a8e23fdf41"
# PRIMARY: unofficial-cricbuzz (subscribe free at rapidapi.com/naeimsalib/api/unofficial-cricbuzz)
RAPIDAPI_HOST = "unofficial-cricbuzz.p.rapidapi.com"
API_HEADERS   = {"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": RAPIDAPI_HOST}
# BACKUP host (switch if quota hit): "cricbuzz-cricket.p.rapidapi.com"
BACKUP_HOST   = "cricbuzz-cricket.p.rapidapi.com"
REFRESH_SECS  = 15

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[data-testid="stAppViewContainer"],[data-testid="stApp"],.main{
    background:#F0F2F5!important;color:#1a1a2e!important;font-family:'Inter',sans-serif!important;}
[data-testid="stHeader"],[data-testid="stToolbar"],footer{display:none!important;}
section[data-testid="stSidebar"]{display:none!important;}
div.block-container{padding:0.8rem 1.8rem 2rem!important;max-width:1400px;}
[data-testid="stHorizontalBlock"]>div{padding:0 5px;}
[data-testid="stHorizontalBlock"]>div:first-child{padding-left:0;}
[data-testid="stHorizontalBlock"]>div:last-child{padding-right:0;}
.stMarkdown{padding:0!important;}

/* Top navbar */
.navbar{background:#1B2A4A;color:white;padding:10px 20px;border-radius:10px;
    display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;}
.navbar-logo{font-size:17px;font-weight:700;letter-spacing:1px;}
.navbar-logo span{color:#38BDF8;}
.navbar-sub{font-size:11px;color:#94A3B8;margin-top:2px;}
.navbar-right{text-align:right;font-size:11px;color:#94A3B8;}
.live-badge{display:inline-block;background:#DC2626;color:white;font-size:10px;
    font-weight:700;padding:2px 8px;border-radius:4px;letter-spacing:1px;margin-right:8px;}

/* Match header */
.match-header{background:white;border-radius:10px;border:1px solid #E2E8F0;
    padding:14px 20px;margin-bottom:10px;display:flex;align-items:center;justify-content:space-between;}
.mh-venue{font-size:13px;font-weight:600;color:#1E293B;}
.mh-sub{font-size:11px;color:#64748B;margin-top:2px;}
.mh-status{font-size:12px;font-weight:600;color:#16A34A;}

/* Scorecard boxes */
.score-card{background:white;border-radius:10px;border:1px solid #E2E8F0;
    padding:18px 22px;height:100%;box-shadow:0 1px 3px rgba(0,0,0,0.05);}
.team-badge{font-size:10px;font-weight:700;letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;}
.score-big{font-size:44px;font-weight:700;line-height:1;}
.score-detail{font-size:13px;color:#64748B;margin-top:5px;}

/* Progress bar */
.pbar{height:8px;background:#E2E8F0;border-radius:4px;overflow:hidden;margin:5px 0;}
.pbar-fill{height:100%;border-radius:4px;}

/* Phase badge */
.ph-pp{background:#DBEAFE;color:#1D4ED8;padding:3px 10px;border-radius:12px;font-size:10px;font-weight:700;letter-spacing:1px;}
.ph-mid{background:#FEF3C7;color:#92400E;padding:3px 10px;border-radius:12px;font-size:10px;font-weight:700;letter-spacing:1px;}
.ph-dth{background:#FEE2E2;color:#991B1B;padding:3px 10px;border-radius:12px;font-size:10px;font-weight:700;letter-spacing:1px;}

/* Stat tile */
.stat-tile{background:white;border-radius:10px;border:1px solid #E2E8F0;padding:14px 16px;
    box-shadow:0 1px 3px rgba(0,0,0,0.04);}
.st-lbl{font-size:10px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:#94A3B8;margin-bottom:6px;}
.st-val{font-size:24px;font-weight:700;color:#1E293B;line-height:1.1;}
.st-sub{font-size:11px;color:#64748B;margin-top:4px;}

/* Section header */
.sh{font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;
    color:#475569;border-bottom:2px solid #E2E8F0;padding-bottom:7px;margin:16px 0 12px;}

/* Table */
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

/* Predict / analysis box */
.pred-green{background:#F0FDF4;border:1px solid #BBF7D0;border-left:4px solid #16A34A;
    border-radius:8px;padding:14px 18px;}
.pred-amber{background:#FFFBEB;border:1px solid #FDE68A;border-left:4px solid #D97706;
    border-radius:8px;padding:14px 18px;}
.pred-red{background:#FEF2F2;border:1px solid #FECACA;border-left:4px solid #DC2626;
    border-radius:8px;padding:14px 18px;}
.pred-title{font-size:15px;font-weight:700;color:#1E293B;margin-bottom:8px;}
.pred-body{font-size:13px;color:#374151;line-height:1.7;}

/* Next ball grid */
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

/* News */
.news-item{padding:10px 0;border-bottom:1px solid #F1F5F9;}
.news-item:last-child{border-bottom:none;}
.news-item a{color:#1E40AF;text-decoration:none;font-size:13px;font-weight:500;line-height:1.5;}
.news-item a:hover{text-decoration:underline;}
.news-src{font-size:11px;color:#94A3B8;margin-top:2px;}

/* White card wrapper */
.card{background:white;border-radius:10px;border:1px solid #E2E8F0;
    padding:16px 20px;box-shadow:0 1px 3px rgba(0,0,0,0.04);}
</style>
""", unsafe_allow_html=True)

# ── HELPERS ───────────────────────────────────────────────────────────────────
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

def _win_prob_2nd(r, w, o, target, total=20):
    """2nd innings win probability for batting team."""
    if target <= 0: return 50, 50
    bu = int(o)*6 + round((o%1)*10)
    bl = max(1, total*6 - bu)
    rn = target - r
    wl = 10 - w
    if rn <= 0: return 95, 5
    if bl <= 0: return 5, 95
    res = (wl/10)**1.0 * 0.5 + (bl/(total*6)) * 0.5
    dif = (rn*6/bl) / 10.0
    p = max(5, min(95, int(50 + (res - dif)*80)))
    return p, 100-p

def _win_prob_1st(r, w, o, total=20):
    """1st innings win probability for FIELDING team (bowling side)."""
    if o <= 0: return 50, 50
    bu = int(o)*6 + round((o%1)*10)
    bl = max(1, total*6 - bu)
    wl = 10 - w
    crr = r / o
    # Resource remaining: wickets matter more than balls
    wkt_factor = (wl/10)**1.5   # non-linear — 3 wkts down weighs heavily
    ball_factor = bl / (total*6)
    resource = wkt_factor*0.6 + ball_factor*0.4
    # Projected total with acceleration factor
    accel = 1.0 + (bl/(total*6))*0.3
    proj = r + crr * (bl/6) * resource * accel
    # Par score for T20 (competitive average)
    par = 165
    diff = (proj - par) / par
    bat_wp = max(10, min(90, int(50 + diff*80)))  # batting team win%
    return 100 - bat_wp, bat_wp  # returns (fielding_wp, batting_wp) — fielding first!

def next_ball(sc):
    """Compute next-ball outcome % based on phase, req_rr, wickets."""
    phase = sc["phase"]
    two   = sc["second_innings"]
    rr    = sc["req_rr"] if two else _float(sc["bat"]["rr"])
    wl    = 10 - sc["bat"]["_w"]

    d = {"dot":32,"1":22,"2":8,"4":14,"6":9,"W":7,"wd":8}
    if phase == "powerplay":
        d["4"]+=4; d["6"]+=3; d["dot"]-=5; d["W"]-=1; d["wd"]+=1
    elif phase == "death":
        d["4"]+=5; d["6"]+=6; d["dot"]-=7; d["W"]+=3; d["wd"]+=1
    else:
        d["dot"]+=4; d["1"]+=2; d["4"]-=2; d["6"]-=2

    if two:
        if rr > 12: d["6"]+=5; d["4"]+=3; d["W"]+=4; d["dot"]-=6
        elif rr > 9: d["4"]+=2; d["6"]+=2; d["W"]+=2
    if wl <= 4: d["dot"]+=4; d["W"]+=2; d["6"]-=2

    keys = ["dot","1","2","4","6","W"]
    tot  = sum(d[k] for k in keys)
    return {k: max(1, round(d[k]/tot*100)) for k in keys}


# ── DATA LAYER ────────────────────────────────────────────────────────────────
def _fetch_list():
    """Returns (data, status_code). Tries primary host, falls back to backup on 429/403."""
    for host in [RAPIDAPI_HOST, BACKUP_HOST]:
        try:
            h = {"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": host}
            r = requests.get(f"https://{host}/matches/v1/live", headers=h, timeout=8)
            if r.status_code == 200: return r.json(), 200
            if r.status_code not in (429, 403): return None, r.status_code
            # 429/403 on this host — try next
        except: pass
    return None, 429  # both hosts exhausted

def _fetch_list_data():
    """Compatibility wrapper — returns just data."""
    data, _ = _fetch_list()
    return data

@st.cache_data(ttl=10, show_spinner=False)
def _fetch_scard(mid):
    for host in [RAPIDAPI_HOST, BACKUP_HOST]:
        try:
            h = {"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": host}
            r = requests.get(f"https://{host}/mcenter/v1/{mid}/hscard", headers=h, timeout=8)
            if r.status_code == 200: return r.json()
        except: pass
    return None

@st.cache_data(ttl=120, show_spinner=False)
def _fetch_news():
    try:
        feed = feedparser.parse(
            "https://news.google.com/rss/search?q=IPL+2026&hl=en-IN&gl=IN&ceid=IN:en")
        return [{"title":e.get("title",""),"source":e.get("source",{}).get("title",""),
                 "published":e.get("published","")[:22],"link":e.get("link","#")}
                for e in feed.entries[:7]]
    except: return []


def _parse_list(raw, source="cricbuzz"):
    """Parse match list from either cricketdata.org or Cricbuzz."""
    out = []
    try:
        if source == "cricdata":
            # cricketdata.org /currentMatches format:
            # { "data": [ { "id", "name", "status", "venue", "teams": [...],
            #               "score": [{"inning","r","w","o"},...] } ] }
            for m in raw.get("data", []):
                name  = m.get("name", "")
                teams = m.get("teams", [])
                t1    = teams[0] if len(teams) > 0 else "Team1"
                t2    = teams[1] if len(teams) > 1 else "Team2"
                score = m.get("score", [])
                s1    = score[0] if len(score) > 0 else {}
                s2    = score[1] if len(score) > 1 else {}
                series= m.get("series", m.get("matchType",""))
                out.append({
                    "matchId":    str(m.get("id","")),
                    "team1":      t1,
                    "team2":      t2,
                    "seriesName": series,
                    "status":     m.get("status",""),
                    "venue":      m.get("venue",""),
                    "t1s": {"inngs1": {"runs": _int(s1.get("r",0)),
                                       "wickets": _int(s1.get("w",0)),
                                       "overs": _float(s1.get("o",0))}},
                    "t2s": {"inngs1": {"runs": _int(s2.get("r",0)),
                                       "wickets": _int(s2.get("w",0)),
                                       "overs": _float(s2.get("o",0))}} if s2 else {},
                })
        else:
            # Cricbuzz format (original)
            for tm in raw.get("typeMatches",[]):
                for sm in tm.get("seriesMatches",[]):
                    wr = sm.get("seriesAdWrapper",{})
                    sn = wr.get("seriesName","")
                    for m in wr.get("matches",[]):
                        mi = m.get("matchInfo",{}); ms = m.get("matchScore",{})
                        vi = mi.get("venueInfo",{})
                        out.append({
                            "matchId":    str(mi.get("matchId","")),
                            "team1":      mi.get("team1",{}).get("teamName",""),
                            "team2":      mi.get("team2",{}).get("teamName",""),
                            "seriesName": sn,
                            "status":     mi.get("status",""),
                            "venue":      f"{vi.get('ground','')}, {vi.get('city','')}".strip(", "),
                            "t1s":        ms.get("team1Score",{}),
                            "t2s":        ms.get("team2Score",{}),
                        })
    except: pass
    return out


def _build_sc(m):
    t1,t2 = m["team1"],m["team2"]
    s1,s2 = _ts(t1),_ts(t2)

    def inn(name, short, sb):
        i = sb.get("inngs1",{})
        r=_int(i.get("runs",0)); w=_int(i.get("wickets",0)); o=_float(i.get("overs",0))
        rr=round(r/o,2) if o>0 else 0.0
        return {"name":name,"short":short,"score":str(r),"wickets":str(w),
                "overs":str(o),"rr":str(rr),"_r":r,"_w":w,"_o":o}

    i1 = inn(t1,s1,m["t1s"])
    i2 = inn(t2,s2,m["t2s"]) if m["t2s"] else None

    two = i2 is not None and i2["_r"] > 0
    bat = i2 if two else i1
    fld = i1 if two else {"name":t2,"short":s2,"score":"—","wickets":"—",
                           "overs":"0.0","rr":"0.0","_r":0,"_w":0,"_o":0.0}

    tgt = i1["_r"]+1 if two else 0
    rn  = max(0,tgt-bat["_r"]) if tgt>0 else 0
    bu  = int(bat["_o"])*6+round((bat["_o"]%1)*10)
    bl  = max(0,120-bu)
    rr  = round(rn*6/bl,2) if bl>0 and rn>0 else 0.0
    ph  = "powerplay" if bat["_o"]<=6 else ("death" if bat["_o"]>=15 else "middle")

    if two:
        bwp, fwp = _win_prob_2nd(bat["_r"],bat["_w"],bat["_o"],tgt)
    else:
        # In 1st innings: _win_prob_1st returns (fielding_wp, batting_wp)
        fwp, bwp = _win_prob_1st(bat["_r"],bat["_w"],bat["_o"])

    return {
        "match": f"{t1} vs {t2}",
        "venue": m.get("venue",""),
        "status": m.get("status","LIVE"),
        "bat": bat, "field": fld,
        "t1": i1, "t2": i2 or fld,
        "target": tgt, "required": rn,
        "req_rr": rr, "balls_left": bl,
        "phase": ph, "second_innings": two,
        "bat_wp": bwp, "fld_wp": fwp,
    }


def _parse_scard(raw, sc):
    """
    cricketdata.org match_scorecard structure:
      raw['data']['scorecard'] = list of innings
      innings: { batting:[{batsman,r,b,4s,6s,sr,dismissal}], bowling:[{bowler,o,m,r,w,eco}] }
    """
    batters, bowlers, extras, partnership = [], [], {}, {}
    try:
        data = raw.get("data", {})
        if not data: return [], [], {}, {}

        cards = data.get("scorecard", [])
        if not cards: return [], [], {}, {}

        card = cards[-1]  # latest innings
        bat_short = sc["bat"]["short"]
        fld_short = sc["field"]["short"]

        extras = data.get("extras", {})
        if isinstance(extras, list) and extras:
            extras = extras[-1]

        # ── Batters ──────────────────────────────────────────────────────
        for b in card.get("batting", []):
            name = b.get("batsman","") or b.get("name","")
            if not name: continue
            r   = _int(b.get("r", b.get("runs", 0)))
            bl  = max(1, _int(b.get("b", b.get("balls", 1))))
            f4  = _int(b.get("4s", b.get("fours", 0)))
            f6  = _int(b.get("6s", b.get("sixes", 0)))
            sr  = round(_float(b.get("sr", b.get("strikeRate",0))) or r/bl*100, 1)
            out = b.get("dismissal", b.get("outdec","")) or ""
            if bl > 0 or "not out" in out.lower() or out == "":
                batters.append({
                    "name": name, "team": bat_short,
                    "runs": r, "balls": bl, "sr": sr,
                    "4s": f4, "6s": f6, "status": out,
                    "batting_now": "not out" in out.lower() or out.strip() == ""
                })

        # ── Bowlers ──────────────────────────────────────────────────────
        for b in card.get("bowling", []):
            name = b.get("bowler","") or b.get("name","")
            if not name: continue
            o  = _float(b.get("o", b.get("overs", 0)))
            r  = _int(b.get("r", b.get("runs", 0)))
            w  = _int(b.get("w", b.get("wickets", 0)))
            m  = _int(b.get("m", b.get("maidens", 0)))
            ec = round(_float(b.get("eco", b.get("economy",0))) or (r/o if o>0 else 0), 2)
            if o > 0 or w > 0:
                bowlers.append({
                    "name": name, "team": fld_short,
                    "overs": o, "runs": r, "wkts": w,
                    "maidens": m, "econ": ec,
                    "bowling_now": False
                })

    except Exception:
        pass
    return batters, bowlers, extras, partnership


def resolve_live(debug=False):
    raw, status, source = _fetch_list()
    if debug and raw:
        with st.expander(f"🔍 RAW — Match List ({source})", expanded=True): st.json(raw)
    if status in (429, 403):
        return None, [], [], {}, {}, status
    if not raw: return None, [], [], {}, {}, status

    for m in _parse_list(raw, source):
        sn  = m["seriesName"].upper()
        st_ = m["status"].lower()
        if "IPL" not in sn and "INDIAN PREMIER" not in sn: continue
        if not m["matchId"] or "toss" in st_ or "upcom" in st_: continue

        sc = _build_sc(m)
        if not sc: continue

        bat, bowl, extras, partner = [], [], {}, {}
        rscard_result = _fetch_scard(m["matchId"])
        rscard = rscard_result[0] if rscard_result and isinstance(rscard_result, tuple) else rscard_result
        if debug and rscard:
            with st.expander(f"🔍 RAW — Scorecard ({m['matchId']})", expanded=False):
                st.json(rscard)
        if rscard:
            bat, bowl, extras, partner = _parse_scard(rscard, sc)

        return sc, bat, bowl, extras, partner, 200

    return None, [], [], {}, {}, 0


# ── DEMO DATA ─────────────────────────────────────────────────────────────────
def _demo():
    srh = {"name":"Sunrisers Hyderabad","short":"SRH","score":"186","wickets":"5",
           "overs":"20.0","rr":"9.3","_r":186,"_w":5,"_o":20.0}
    rcb = {"name":"Royal Challengers Bengaluru","short":"RCB","score":"142","wickets":"3",
           "overs":"15.3","rr":"9.15","_r":142,"_w":3,"_o":15.3}
    sc  = {"match":"SRH vs RCB","venue":"M.Chinnaswamy Stadium, Bengaluru",
           "status":"RCB opt to bowl","bat":rcb,"field":srh,"t1":srh,"t2":rcb,
           "target":187,"required":45,"req_rr":6.75,"balls_left":27,
           "phase":"death","second_innings":True,"bat_wp":45,"fld_wp":55}
    bat = [
        {"name":"Ishan Kishan","team":"RCB","runs":31,"balls":15,"sr":206.7,"4s":2,"6s":3,
         "status":"batting","batting_now":True},
        {"name":"Heinrich Klaasen","team":"RCB","runs":17,"balls":11,"sr":154.5,"4s":1,"6s":1,
         "status":"batting","batting_now":True},
        {"name":"Travis Head","team":"SRH","runs":11,"balls":9,"sr":122.2,"4s":2,"6s":0,
         "status":"c Phil Salt b Jacob Duffy","batting_now":False},
    ]
    bowl = [
        {"name":"Jacob Duffy","team":"RCB","overs":4.0,"runs":22,"wkts":3,"maidens":0,"econ":5.5,"bowling_now":False},
        {"name":"Romario Shepherd","team":"RCB","overs":0.1,"runs":1,"wkts":0,"maidens":0,"econ":6.0,"bowling_now":True},
        {"name":"Bhuvneshwar Kumar","team":"RCB","overs":2.0,"runs":15,"wkts":0,"maidens":0,"econ":7.5,"bowling_now":False},
    ]
    extras = {"wides":3,"noballs":0,"legbyes":1,"byes":0,"total":4}
    partner= {"balls":17,"runs":26}
    return sc, bat, bowl, extras, partner


# ── PREDICTION ────────────────────────────────────────────────────────────────
def build_prediction(sc, batters, bowlers):
    bat  = sc["bat"]
    two  = sc["second_innings"]
    bwp  = sc["bat_wp"]
    fwp  = sc["fld_wp"]

    if not two:
        crr  = _float(bat["rr"])
        o    = bat["_o"]
        bu   = int(o)*6 + round((o%1)*10)
        bl   = max(1, 120-bu)
        proj = bat["_r"] + round(crr * bl/6 * 0.9)  # slight realism factor
        if crr >= 10:
            return "🔥 Explosive Start", "green", (
                f"**{bat['short']}** are on fire at **{crr}** RPO. "
                f"Projected total: **~{proj}** — a difficult target. "
                f"Win probability: **{fwp}%** for the fielding side.")
        elif crr >= 8:
            return "✅ Solid Platform", "green", (
                f"**{bat['short']}** building well at **{crr}** RPO. "
                f"Projected total: **~{proj}**. "
                f"Fielding team holding control — **{fwp}%** win chance.")
        else:
            return "⚠️ Below Par", "amber", (
                f"**{bat['short']}** scoring at **{crr}** RPO — below T20 par. "
                f"Projected total: **~{proj}**. "
                f"Fielding side in command — **{fwp}%** win probability.")
    else:
        rn  = sc["required"]; bl = sc["balls_left"]; rr = sc["req_rr"]
        wl  = 10 - bat["_w"]
        bpw = round(bl/max(1,wl), 1)
        if bwp >= 65:
            return "🟢 Chase On Track", "green", (
                f"Need **{rn}** off **{bl}** balls · Req RR: **{rr}**. "
                f"**{wl} wickets** in hand (~{bpw} balls/wkt). "
                f"**{bat['short']}** win probability: **{bwp}%** — chase well within reach.")
        elif bwp >= 45:
            return "🟡 Finely Balanced", "amber", (
                f"Need **{rn}** off **{bl}** balls · Req RR: **{rr}**. "
                f"**{wl} wickets** remaining. Either team can take control. "
                f"**{bat['short']}** at **{bwp}%** · **{sc['field']['short']}** at **{fwp}%**.")
        else:
            return "🔴 Under Pressure", "red", (
                f"Need **{rn}** off **{bl}** balls · steep req rate of **{rr}**. "
                f"Only **{wl} wickets** left. "
                f"**{sc['field']['short']}** heavily favoured at **{fwp}%**.")


# ── RENDER FUNCTIONS ──────────────────────────────────────────────────────────

def render_navbar(sc, is_live):
    IST = pytz.timezone('Asia/Kolkata')
    now = datetime.now(IST).strftime("%d %b %Y · %H:%M IST")
    lb  = '<span style="background:#DC2626;color:white;font-size:9px;font-weight:700;padding:2px 7px;border-radius:3px;letter-spacing:1px;margin-right:8px">LIVE</span>' if is_live else ""
    st.markdown(
        f'<div class="navbar">'
        f'<div><div class="navbar-logo">GOD\'S<span>EYE</span> v3.5 '
        f'<span style="font-size:11px;color:#64748B;font-weight:400">IPL MATCH CENTER</span></div>'
        f'<div class="navbar-sub">{lb}{sc.get("match","")}</div></div>'
        f'<div class="navbar-right">{now}<br>'
        f'<span style="color:#4ADE80">Updated: {now}</span><br>'
        f'<span style="color:#64748B">OPERATOR: UDAY MADDILA</span></div>'
        f'</div>', unsafe_allow_html=True)


def render_scoreboard(sc):
    bat  = sc["bat"]; field = sc["field"]
    two  = sc["second_innings"]
    bwp  = sc["bat_wp"]; fwp = sc["fld_wp"]
    bc   = _c(bat["short"]); fc = _c(field["short"])
    ph   = sc["phase"]
    ph_cls = "ph-pp" if ph=="powerplay" else ("ph-dth" if ph=="death" else "ph-mid")

    # Match header bar
    st.markdown(
        f'<div class="match-header">'
        f'<div><div class="mh-venue">🏟️ {sc["venue"]}</div>'
        f'<div class="mh-sub">'
        f'<span class="mh-status">{sc["status"]}</span> &nbsp;·&nbsp; '
        f'{"2nd Innings" if two else "1st Innings"}'
        f'</div></div>'
        f'<div><span class="{ph_cls}">{ph.capitalize()}</span></div>'
        f'</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns([5, 4, 5])

    # LEFT — Batting team
    with c1:
        s = bat["score"]; w = bat["wickets"]; o = bat["overs"]; rr = bat["rr"]
        score_txt = f"{s}/{w}" if s not in ("—","0","") else "Yet to Bat"
        sub_txt   = f"{o} Ov &nbsp;·&nbsp; CRR: <b>{rr}</b>" if s not in ("—","0","") else "Bats 2nd"
        st.markdown(
            f'<div class="score-card" style="border-left:4px solid {bc}">'
            f'<div class="team-badge" style="color:{bc}">▶ {bat["short"]} — Batting</div>'
            f'<div class="score-big" style="color:{bc}">{score_txt}</div>'
            f'<div class="score-detail">{sub_txt}</div>'
            f'</div>', unsafe_allow_html=True)

    # CENTRE — Win prob + chase/progress info
    with c2:
        if two:
            rn=sc["required"]; bl=sc["balls_left"]; rr=sc["req_rr"]
            rc="#DC2626" if rr>12 else ("#D97706" if rr>9 else "#16A34A")
            html = (
                f'<div class="score-card" style="text-align:center">'
                f'<div style="font-size:10px;font-weight:700;letter-spacing:1px;color:#94A3B8;margin-bottom:10px">WIN PROBABILITY</div>'
                f'<div style="display:flex;justify-content:space-between;font-size:13px;font-weight:700;margin-bottom:3px">'
                f'<span style="color:{bc}">{bat["short"]}</span><span style="color:{bc}">{bwp}%</span></div>'
                f'<div class="pbar"><div class="pbar-fill" style="width:{bwp}%;background:{bc}"></div></div>'
                f'<div style="display:flex;justify-content:space-between;font-size:13px;font-weight:700;margin-top:8px;margin-bottom:3px">'
                f'<span style="color:{fc}">{field["short"]}</span><span style="color:{fc}">{fwp}%</span></div>'
                f'<div class="pbar"><div class="pbar-fill" style="width:{fwp}%;background:{fc}"></div></div>'
                f'<div style="margin-top:12px;background:#FEF2F2;border-radius:6px;padding:8px;font-size:12px">'
                f'Need <b style="color:{rc}">{rn}</b> off <b>{bl}</b> balls<br>'
                f'Req RR: <b style="color:{rc}">{rr}</b>'
                f'</div></div>'
            )
        else:
            o=bat["_o"]; pct=min(100,int(o/20*100))
            bu=int(o)*6+round((o%1)*10); bl=max(1,120-bu)
            proj=bat["_r"]+round(_float(bat["rr"])*bl/6*0.9)
            html = (
                f'<div class="score-card" style="text-align:center">'
                f'<div style="font-size:10px;font-weight:700;letter-spacing:1px;color:#94A3B8;margin-bottom:10px">WIN PROBABILITY</div>'
                f'<div style="display:flex;justify-content:space-between;font-size:13px;font-weight:700;margin-bottom:3px">'
                f'<span style="color:{fc}">{field["short"]}</span><span style="color:{fc}">{fwp}%</span></div>'
                f'<div class="pbar"><div class="pbar-fill" style="width:{fwp}%;background:{fc}"></div></div>'
                f'<div style="display:flex;justify-content:space-between;font-size:13px;font-weight:700;margin-top:8px;margin-bottom:3px">'
                f'<span style="color:{bc}">{bat["short"]}</span><span style="color:{bc}">{bwp}%</span></div>'
                f'<div class="pbar"><div class="pbar-fill" style="width:{bwp}%;background:{bc}"></div></div>'
                f'<div style="margin-top:12px;background:#F0FDF4;border-radius:6px;padding:8px;font-size:12px">'
                f'{o} / 20.0 Overs &nbsp;·&nbsp; Proj: <b>~{proj}</b>'
                f'</div></div>'
            )
        st.markdown(html, unsafe_allow_html=True)

    # RIGHT — Fielding / yet-to-bat
    with c3:
        s=field["score"]; w=field["wickets"]; o=field["overs"]; rr=field["rr"]
        score_txt = f"{s}/{w}" if s not in ("—","") else "Yet to Bat"
        sub_txt   = f"{o} Ov &nbsp;·&nbsp; CRR: <b>{rr}</b>" if s not in ("—","") else "Bats next"
        lbl = f"{'Bowled — ' if two else 'Bats Next — '}{field['short']}"
        st.markdown(
            f'<div class="score-card" style="border-left:4px solid {fc}">'
            f'<div class="team-badge" style="color:{fc}">⚡ {lbl}</div>'
            f'<div class="score-big" style="color:{fc}">{score_txt}</div>'
            f'<div class="score-detail">{sub_txt}</div>'
            f'</div>', unsafe_allow_html=True)


def render_stats_bar(sc, batters, bowlers, extras, partner):
    st.markdown('<div class="sh">📊 Key Match Stats</div>', unsafe_allow_html=True)
    bat=sc["bat"]; two=sc["second_innings"]; wl=10-bat["_w"]
    crr_c="#16A34A" if _float(bat["rr"])>=8 else ("#D97706" if _float(bat["rr"])>=6 else "#DC2626")

    top_bat = max(batters, key=lambda x:x["runs"]) if batters else None
    top_bwl = max(bowlers, key=lambda x:x["wkts"]) if bowlers else None
    ext_tot = extras.get("total",0) if extras else 0

    c1,c2,c3,c4,c5 = st.columns(5)

    def tile(col, lbl, val, sub, vc="#1E293B", top="#2563EB"):
        with col:
            st.markdown(
                f'<div class="stat-tile" style="border-top:3px solid {top}">'
                f'<div class="st-lbl">{lbl}</div>'
                f'<div class="st-val" style="color:{vc}">{val}</div>'
                f'<div class="st-sub">{sub}</div></div>', unsafe_allow_html=True)

    tile(c1,"Current RR", bat["rr"],
         f'{bat["short"]} · {bat["overs"]} ov', crr_c, crr_c)

    if two:
        rr=sc["req_rr"]; rc="#DC2626" if rr>12 else ("#D97706" if rr>9 else "#16A34A")
        tile(c2,"Required RR",str(rr),
             f'{sc["required"]} runs · {sc["balls_left"]} balls', rc, rc)
    else:
        tile(c2,"Wickets Left",str(wl),
             f'{bat["wickets"]} fallen so far',"#7C3AED","#7C3AED")

    # Partnership
    if partner and isinstance(partner, dict):
        pr = partner.get("runs", partner.get("totalRuns","—"))
        pb = partner.get("balls", partner.get("totalBalls","—"))
        tile(c3,"Partnership",f'{pr}({pb}b)',"Current pair","#0EA5E9","#0EA5E9")
    else:
        tile(c3,"Extras",str(ext_tot),
             f'Wd:{extras.get("wides",0)} NB:{extras.get("noballs",0)}' if extras else "","#64748B","#64748B")

    if top_bat:
        tile(c4,"Top Scorer",f'{top_bat["runs"]}*({top_bat["balls"]}b)',
             f'{top_bat["name"]} · SR:{top_bat["sr"]}', "#1D4ED8","#1D4ED8")
    else:
        tile(c4,"Top Scorer","—","Awaiting scorecard","#94A3B8","#94A3B8")

    if top_bwl:
        ec=top_bwl["econ"]; ec_c="#16A34A" if ec<8 else ("#D97706" if ec<11 else "#DC2626")
        tile(c5,"Best Bowler",f'{top_bwl["wkts"]}/{top_bwl["runs"]}',
             f'{top_bwl["name"]} · {top_bwl["overs"]}ov · Econ {ec}', ec_c, ec_c)
    else:
        tile(c5,"Best Bowler","—","Awaiting scorecard","#94A3B8","#94A3B8")


def render_batters(batters):
    st.markdown('<div class="sh">🏏 Batting — Current Innings</div>', unsafe_allow_html=True)
    if not batters:
        st.markdown('<div class="card" style="color:#94A3B8;font-size:13px">Scorecard loading — data will appear shortly.</div>', unsafe_allow_html=True)
        return
    # Show only batters who have batted (balls > 0)
    active = [b for b in batters if b["balls"] > 0]
    if not active:
        active = batters[:4]

    grid = "2.4fr 50px 50px 45px 45px 75px 55px"
    hdr = (f'<div class="tbl-hdr" style="display:grid;grid-template-columns:{grid}">'
           f'<div>Batter</div><div style="text-align:right">R</div>'
           f'<div style="text-align:right">B</div><div style="text-align:right">4s</div>'
           f'<div style="text-align:right">6s</div><div style="text-align:right">SR</div>'
           f'<div style="text-align:right">Status</div></div>')
    rows = ""
    for b in active:
        bn   = b.get("batting_now", False)
        tc   = _c(b["team"])
        sr   = b["sr"]
        sr_c = "green" if sr>=150 else ("amber" if sr>=100 else "red")
        name_html = (f'<span class="player-name" style="color:{tc}">{b["name"]}</span>'
                     + ('<span class="batting-now">▶ BATTING</span>' if bn else ""))
        out_html  = ('<span class="green">not out</span>' if bn else
                     f'<span style="font-size:10px;color:#64748B">{b["status"][:22]}</span>')
        rows += (f'<div class="tbl-row" style="display:grid;grid-template-columns:{grid}">'
                 f'<div>{name_html}</div>'
                 f'<div class="num"><b>{b["runs"]}</b></div>'
                 f'<div class="num">{b["balls"]}</div>'
                 f'<div class="num">{b["4s"]}</div>'
                 f'<div class="num">{b["6s"]}</div>'
                 f'<div class="num"><span class="{sr_c}">{sr}</span></div>'
                 f'<div class="num" style="text-align:right">{out_html}</div>'
                 f'</div>')
    st.markdown(f'<div class="card">{hdr}{rows}</div>', unsafe_allow_html=True)


def render_bowlers(bowlers):
    st.markdown('<div class="sh">🎯 Bowling — Current Innings</div>', unsafe_allow_html=True)
    if not bowlers:
        st.markdown('<div class="card" style="color:#94A3B8;font-size:13px">Scorecard loading — data will appear shortly.</div>', unsafe_allow_html=True)
        return
    active = [b for b in bowlers if b["overs"] > 0]
    if not active: active = bowlers

    grid = "2.2fr 55px 55px 55px 55px 70px"
    hdr = (f'<div class="tbl-hdr" style="display:grid;grid-template-columns:{grid}">'
           f'<div>Bowler</div><div style="text-align:right">O</div>'
           f'<div style="text-align:right">M</div><div style="text-align:right">R</div>'
           f'<div style="text-align:right">W</div><div style="text-align:right">Econ</div></div>')
    rows = ""
    for b in sorted(active, key=lambda x:-x["overs"]):
        tc   = _c(b["team"])
        ec   = b["econ"]
        ec_c = "green" if ec<8 else ("amber" if ec<11 else "red")
        wkt_style = 'style="color:#DC2626;font-weight:700"' if b["wkts"]>0 else ""
        bn_html = '<span style="color:#16A34A;font-size:10px;font-weight:700;margin-left:4px">▶ BOWLING</span>' if b.get("bowling_now") else ""
        rows += (f'<div class="tbl-row" style="display:grid;grid-template-columns:{grid}">'
                 f'<div><span class="player-name" style="color:{tc}">{b["name"]}</span>{bn_html}</div>'
                 f'<div class="num">{b["overs"]}</div>'
                 f'<div class="num">{b["maidens"]}</div>'
                 f'<div class="num">{b["runs"]}</div>'
                 f'<div class="num"><span {wkt_style}>{b["wkts"]}</span></div>'
                 f'<div class="num"><span class="{ec_c}">{ec}</span></div>'
                 f'</div>')
    st.markdown(f'<div class="card">{hdr}{rows}</div>', unsafe_allow_html=True)


def render_prediction_and_nextball(sc, batters, bowlers):
    st.markdown('<div class="sh">🔮 Match Analysis & Prediction</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([3, 2])

    with c1:
        verdict, clr, txt = build_prediction(sc, batters, bowlers)
        cls_map = {"green":"pred-green","amber":"pred-amber","red":"pred-red"}
        st.markdown(
            f'<div class="{cls_map[clr]}">'
            f'<div class="pred-title">{verdict}</div>'
            f'<div class="pred-body">{txt}</div>'
            f'</div>', unsafe_allow_html=True)

        # Next Ball section
        st.markdown('<div style="margin-top:14px"><div class="sh" style="margin-top:0">⚡ Next Ball Prediction</div></div>', unsafe_allow_html=True)
        probs = next_ball(sc)
        cells_html = '<div class="nb-grid">'
        cfg = {
            "dot": ("nb-dot",  "·",  "DOT"),
            "1":   ("nb-one",  "1",  "SINGLE"),
            "2":   ("nb-two",  "2",  "TWO"),
            "4":   ("nb-four", "4",  "FOUR"),
            "6":   ("nb-six",  "6",  "SIX"),
            "W":   ("nb-wkt",  "🎯", "WICKET"),
        }
        for k, (cls, icon, lbl) in cfg.items():
            pct = probs.get(k, 0)
            cells_html += (
                f'<div class="nb-cell {cls}">'
                f'<div class="nb-val">{icon}</div>'
                f'<div class="nb-lbl">{lbl}</div>'
                f'<div class="nb-pct">{pct}%</div>'
                f'</div>')
        cells_html += '</div>'
        likely = max(probs, key=probs.get)
        likely_desc = {"dot":"Dot ball likely — good bowling spell",
                       "1":"Single expected — steady rotation",
                       "2":"Two runs — good running between wickets",
                       "4":"Boundary incoming — attacking shot",
                       "6":"Maximum likely — big hit expected",
                       "W":"Wicket alert — bowling pressure building"}
        st.markdown(
            f'<div class="card">{cells_html}'
            f'<div style="margin-top:10px;font-size:12px;color:#64748B">'
            f'▶ Most likely: <b style="color:#1E293B">{likely_desc[likely]}</b>'
            f'</div></div>', unsafe_allow_html=True)

    with c2:
        bat=sc["bat"]; fld=sc["field"]
        bc=_c(bat["short"]); fc=_c(fld["short"])
        bwp=sc["bat_wp"]; fwp=sc["fld_wp"]

        # Win probability visual
        st.markdown(
            f'<div class="card">'
            f'<div style="font-size:10px;font-weight:700;letter-spacing:1px;color:#94A3B8;margin-bottom:12px">WIN PROBABILITY MODEL</div>'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px">'
            f'<span style="font-weight:700;color:{bc};font-size:15px">{bat["short"]}</span>'
            f'<span style="font-size:26px;font-weight:700;color:{bc}">{bwp}%</span></div>'
            f'<div class="pbar" style="height:14px"><div class="pbar-fill" style="width:{bwp}%;background:{bc}"></div></div>'
            f'<div style="font-size:11px;color:#64748B;margin-bottom:16px;margin-top:3px">'
            f'{"Batting" if sc["second_innings"] else "Bowling"} · {bat["overs"]} ov · {bat["wickets"]} wkts</div>'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px">'
            f'<span style="font-weight:700;color:{fc};font-size:15px">{fld["short"]}</span>'
            f'<span style="font-size:26px;font-weight:700;color:{fc}">{fwp}%</span></div>'
            f'<div class="pbar" style="height:14px"><div class="pbar-fill" style="width:{fwp}%;background:{fc}"></div></div>'
            f'<div style="font-size:11px;color:#64748B;margin-top:3px">'
            f'{"Bowling" if sc["second_innings"] else "Batting"} · Yet to bat</div>'
            f'</div>', unsafe_allow_html=True)

        # Current over / phase context
        two=sc["second_innings"]; ph=sc["phase"]
        ph_c="#1D4ED8" if ph=="powerplay" else ("#991B1B" if ph=="death" else "#92400E")
        context_lines = []
        if two:
            context_lines.append(f'<b>Req RR:</b> {sc["req_rr"]} &nbsp;·&nbsp; <b>Balls:</b> {sc["balls_left"]}')
            context_lines.append(f'<b>Wickets left:</b> {10 - bat["_w"]}')
        else:
            context_lines.append(f'<b>CRR:</b> {bat["rr"]} &nbsp;·&nbsp; Over {bat["_o"]}')
        st.markdown(
            f'<div class="card" style="margin-top:10px">'
            f'<div style="font-size:10px;font-weight:700;letter-spacing:1px;color:#94A3B8;margin-bottom:10px">MATCH SITUATION</div>'
            f'<div style="font-size:13px;color:#374151;line-height:2">'
            + "<br>".join(context_lines) +
            f'<br><b>Phase:</b> <span style="color:{ph_c};font-weight:700">{ph.capitalize()}</span>'
            f'<br><b>Innings:</b> {"2nd" if two else "1st"}'
            f'</div></div>', unsafe_allow_html=True)


def render_news(news):
    st.markdown('<div class="sh">📰 IPL 2026 News</div>', unsafe_allow_html=True)
    if not news:
        st.info("News feed unavailable.")
        return
    html = '<div class="card">'
    for n in news:
        html += (f'<div class="news-item">'
                 f'<a href="{n["link"]}" target="_blank">{n["title"]}</a>'
                 f'<div class="news-src">{n["source"]} · {n["published"]}</div>'
                 f'</div>')
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


# ── CONTROLS ──────────────────────────────────────────────────────────────────
ca, cb, cc, cd, ce = st.columns([3,1,1,1,1])
with ca:
    st.markdown('<div style="font-size:10px;color:#94A3B8;padding-top:12px">'
                "GOD'S EYE v3.5 · © Uday Maddila</div>", unsafe_allow_html=True)
with cb: auto_ref  = st.toggle("Auto-Refresh", value=True)
with cc: demo_mode = st.toggle("Demo Mode",    value=False)
with cd: debug_api = st.toggle("Debug API",    value=False)
with ce:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear(); st.rerun()

# ── MAIN ──────────────────────────────────────────────────────────────────────
API_INTERVAL = 120  # 2 min intervals = 720 calls/day, well within 100/day free quota


_now = time.time()

# Init session state
for _k, _v in [("last_fetch",0),("cached_sc",None),("cached_bat",[]),
               ("cached_bowl",[]),("cached_ext",{}),("cached_part",{}),
               ("quota_hit",False),("api_status",200)]:
    if _k not in st.session_state: st.session_state[_k] = _v

sc=None; batters=[]; bowlers=[]; extras={}; partner={}; is_live=False
_api_msg = ""

if not demo_mode:
    _due = (_now - st.session_state.last_fetch) >= API_INTERVAL

    if _due:
        _fresh_sc, _b, _bw, _ex, _pt, _code = resolve_live(debug=debug_api)
        st.session_state.api_status = _code

        if _code in (429, 403):
            # Quota hit — back off for 5 minutes, keep showing cached data
            st.session_state.quota_hit  = True
            st.session_state.last_fetch = _now + 270  # skip 4.5 min before retry
            _api_msg = "⚠️ API quota reached — showing last known live data"
        elif _fresh_sc is not None:
            st.session_state.cached_sc   = _fresh_sc
            st.session_state.cached_bat  = _b
            st.session_state.cached_bowl = _bw
            st.session_state.cached_ext  = _ex
            st.session_state.cached_part = _pt
            st.session_state.last_fetch  = _now
            st.session_state.quota_hit   = False
        else:
            # API returned 200 but no IPL match — update timestamp
            st.session_state.last_fetch  = _now
            st.session_state.quota_hit   = False

    # Always serve cached data if available (regardless of whether due)
    if st.session_state.cached_sc is not None:
        sc      = st.session_state.cached_sc
        batters = st.session_state.cached_bat
        bowlers = st.session_state.cached_bowl
        extras  = st.session_state.cached_ext
        partner = st.session_state.cached_part
        is_live = True

if _api_msg:
    st.warning(_api_msg)
elif sc is None and not demo_mode:
    st.info("📡 No live IPL match right now — showing demo data.")

if sc is None:
    sc,batters,bowlers,extras,partner = _demo()

next_fetch_in = max(0, int(API_INTERVAL - (_now - st.session_state.last_fetch)))
news = _fetch_news()

render_navbar(sc, is_live)
render_scoreboard(sc)
render_stats_bar(sc, batters, bowlers, extras, partner)
render_prediction_and_nextball(sc, batters, bowlers)

st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
cl, cr = st.columns(2, gap="medium")
with cl: render_batters(batters)
with cr: render_bowlers(bowlers)

render_news(news)

st.markdown(
    f'<div style="text-align:center;font-size:11px;color:#94A3B8;'
    f'margin-top:20px;padding-top:14px;border-top:1px solid #E2E8F0">'
    f'GOD\'S EYE v3.5 · Data: Cricbuzz API (RapidAPI) · '
    f'Last fetched: {datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%H:%M:%S IST")} · '
    f'Next refresh in: {next_fetch_in}s'
    + (' · ⚠️ Quota hit' if st.session_state.get("quota_hit") else '') +
    f' · © Uday Maddila</div>',
    unsafe_allow_html=True)

if auto_ref:
    time.sleep(REFRESH_SECS)
    st.rerun()
