"""
GOD'S EYE v3.5 — IPL LIVE MATCH CENTER
Operator : Uday Maddila
Rebuild  : Light theme · Cricbuzz-style layout · Real-time only
"""

import streamlit as st
import requests
import feedparser
import time
from datetime import datetime
import pytz

# ─────────────────────────────────────────────────────────────────
# 0. PAGE CONFIG
# ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GOD'S EYE | IPL 2026",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────
# 1. CONSTANTS
# ─────────────────────────────────────────────────────────────────
RAPIDAPI_KEY  = "f26160eb44mshc0a20698180c97dp18f61ejsn98a8e23fdf41"
RAPIDAPI_HOST = "cricbuzz-cricket.p.rapidapi.com"
API_HEADERS   = {"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": RAPIDAPI_HOST}
REFRESH_SECS  = 30

# ─────────────────────────────────────────────────────────────────
# 2. GLOBAL CSS — clean light theme
# ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"], .main {
    background: #F5F7FA !important;
    color: #1a1a2e !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stHeader"], [data-testid="stToolbar"], footer { display:none !important; }
section[data-testid="stSidebar"] { display:none !important; }
div.block-container { padding: 1rem 2rem 2rem !important; max-width: 1400px; }
[data-testid="stHorizontalBlock"] > div { padding: 0 6px; }
[data-testid="stHorizontalBlock"] > div:first-child { padding-left: 0; }
[data-testid="stHorizontalBlock"] > div:last-child  { padding-right: 0; }
.stMarkdown { padding: 0 !important; }

/* Cards */
.card {
    background: #ffffff;
    border-radius: 10px;
    padding: 16px 20px;
    border: 1px solid #E2E8F0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    height: 100%;
}
.card-blue  { border-top: 3px solid #2563EB; }
.card-red   { border-top: 3px solid #DC2626; }
.card-green { border-top: 3px solid #16A34A; }
.card-amber { border-top: 3px solid #D97706; }
.card-purple{ border-top: 3px solid #7C3AED; }

/* Section headers */
.sec-hdr {
    font-size: 11px; font-weight: 700; letter-spacing: 2px;
    text-transform: uppercase; color: #64748B;
    border-bottom: 2px solid #E2E8F0;
    padding-bottom: 8px; margin-bottom: 14px; margin-top: 20px;
}

/* Score display */
.score-big   { font-size: 42px; font-weight: 700; color: #1E293B; line-height: 1; }
.score-sub   { font-size: 13px; color: #64748B; margin-top: 4px; }
.team-label  { font-size: 11px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; color: #64748B; margin-bottom: 6px; }
.live-dot    { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #DC2626; margin-right: 6px; animation: blink 1.2s ease-in-out infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }

/* Stat value */
.stat-val  { font-size: 22px; font-weight: 700; color: #1E293B; line-height: 1.1; }
.stat-lbl  { font-size: 11px; color: #94A3B8; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 4px; }
.stat-sub  { font-size: 12px; color: #64748B; margin-top: 3px; }

/* Progress bar */
.pbar-wrap { height: 8px; background: #E2E8F0; border-radius: 4px; overflow: hidden; margin: 6px 0; }
.pbar-fill { height: 100%; border-radius: 4px; }

/* Phase badge */
.badge {
    display: inline-block; font-size: 10px; font-weight: 700;
    letter-spacing: 1.5px; text-transform: uppercase;
    padding: 3px 10px; border-radius: 20px;
}
.badge-pp  { background: #DBEAFE; color: #1D4ED8; }
.badge-mid { background: #FEF3C7; color: #92400E; }
.badge-dth { background: #FEE2E2; color: #991B1B; }
.badge-live{ background: #DCFCE7; color: #166534; }

/* Table rows */
.trow {
    display: grid; align-items: center;
    padding: 9px 0; border-bottom: 1px solid #F1F5F9;
    font-size: 13px;
}
.trow:last-child { border-bottom: none; }
.trow-hdr {
    font-size: 10px; font-weight: 600; letter-spacing: 1px;
    text-transform: uppercase; color: #94A3B8;
    padding-bottom: 8px; border-bottom: 2px solid #E2E8F0; margin-bottom: 4px;
}

/* Win prob bar */
.wp-team { font-size: 12px; font-weight: 600; color: #374151; }
.wp-pct  { font-size: 14px; font-weight: 700; }

/* Predict box */
.predict-box {
    background: #F0FDF4; border: 1px solid #BBF7D0;
    border-left: 4px solid #16A34A;
    border-radius: 8px; padding: 14px 18px;
}
.predict-box.warn {
    background: #FFFBEB; border-color: #FDE68A;
    border-left-color: #D97706;
}
.predict-box.danger {
    background: #FEF2F2; border-color: #FECACA;
    border-left-color: #DC2626;
}

/* News */
.news-item { padding: 10px 0; border-bottom: 1px solid #F1F5F9; }
.news-item:last-child { border-bottom: none; }
.news-item a { color: #1E40AF; text-decoration: none; font-size: 13px; font-weight: 500; line-height: 1.5; }
.news-item a:hover { text-decoration: underline; }
.news-src  { font-size: 11px; color: #94A3B8; margin-top: 3px; }

/* Controls bar */
.ctrl-bar {
    background: #1E293B; color: white;
    padding: 8px 20px; border-radius: 10px;
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 16px;
}
.ctrl-logo { font-size: 16px; font-weight: 700; letter-spacing: 1px; color: white; }
.ctrl-logo span { color: #38BDF8; }
.ctrl-time { font-size: 11px; color: #94A3B8; }

/* Stacked mini stat */
.mini-stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.mini-stat { background: #F8FAFC; border-radius: 8px; padding: 10px 12px; border: 1px solid #E2E8F0; }
.mini-stat .val { font-size: 18px; font-weight: 700; color: #1E293B; }
.mini-stat .lbl { font-size: 10px; color: #94A3B8; text-transform: uppercase; letter-spacing: 1px; }
.mini-stat .sub { font-size: 11px; color: #64748B; margin-top: 2px; }

/* Scoreboard match header */
.match-hdr {
    background: #1E293B; color: white;
    border-radius: 10px; padding: 14px 20px;
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 2px;
}
.match-name { font-size: 13px; font-weight: 600; color: #F1F5F9; }
.match-venue{ font-size: 11px; color: #94A3B8; margin-top: 2px; }
.match-status { font-size: 12px; font-weight: 600; color: #4ADE80; }

/* Player rows */
.bat-row { display: grid; grid-template-columns: 2fr 60px 60px 60px 60px 80px; gap: 4px; align-items:center; padding: 8px 4px; border-bottom: 1px solid #F1F5F9; font-size:13px; }
.bowl-row { display: grid; grid-template-columns: 2fr 60px 60px 70px 70px 70px; gap: 4px; align-items:center; padding: 8px 4px; border-bottom: 1px solid #F1F5F9; font-size:13px; }
.row-hdr  { font-size:10px; font-weight:700; letter-spacing:1px; color:#94A3B8; text-transform:uppercase; padding: 4px 4px 8px; border-bottom: 2px solid #E2E8F0; }
.player-name { font-weight:600; color:#1E293B; }
.player-team { font-size:10px; color:#94A3B8; }
.num-cell { text-align:right; color:#374151; font-weight:500; }
.highlight { color:#DC2626; font-weight:700; }
.good { color:#16A34A; font-weight:600; }
.warn { color:#D97706; font-weight:600; }
.bad  { color:#DC2626; font-weight:600; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# 3. DATA LAYER
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

TEAM_COLORS = {
    "RCB": "#DC2626", "SRH": "#D97706", "MI": "#1D4ED8",
    "CSK": "#F59E0B", "KKR": "#7C3AED", "RR": "#EC4899",
    "DC": "#2563EB", "PBKS": "#DC2626", "LSG": "#0EA5E9", "GT": "#0D9488",
}

def _c(short): return TEAM_COLORS.get(short, "#64748B")

def _ts(name):
    n = (name or "").lower().strip()
    for full, short in TEAM_MAP.items():
        if full in n: return short
    parts = (name or "").split()
    return "".join(p[0] for p in parts[:3]).upper() if parts else "UNK"

def _int(v, d=0):
    try: return int(str(v).split("/")[0].strip())
    except: return d

def _float(v, d=0.0):
    try: return float(str(v).strip())
    except: return d

def _win_prob(r, w, o, target, total=20):
    if target <= 0: return 50, 50
    bu = int(o)*6 + round((o%1)*10)
    bl = max(0, total*6 - bu)
    rn = target - r
    wl = 10 - w
    if rn <= 0: return 95, 5
    if bl <= 0: return 5, 95
    res = wl/10*0.5 + bl/(total*6)*0.5
    dif = (rn*6/bl)/10.0
    p = max(5, min(95, int(50 + (res - dif)*80)))
    return p, 100-p


@st.cache_data(ttl=REFRESH_SECS, show_spinner=False)
def _fetch_list():
    try:
        r = requests.get(f"https://{RAPIDAPI_HOST}/matches/v1/live",
                         headers=API_HEADERS, timeout=8)
        if r.status_code == 200: return r.json()
    except: pass
    return None

@st.cache_data(ttl=REFRESH_SECS, show_spinner=False)
def _fetch_scard(mid):
    try:
        r = requests.get(f"https://{RAPIDAPI_HOST}/mcenter/v1/{mid}/hscard",
                         headers=API_HEADERS, timeout=8)
        if r.status_code == 200: return r.json()
    except: pass
    return None

@st.cache_data(ttl=120, show_spinner=False)
def fetch_news():
    try:
        feed = feedparser.parse(
            "https://news.google.com/rss/search?q=IPL+2026&hl=en-IN&gl=IN&ceid=IN:en")
        return [{"title": e.get("title",""), "source": e.get("source",{}).get("title",""),
                 "published": e.get("published","")[:22], "link": e.get("link","#")}
                for e in feed.entries[:7]]
    except: return []


def _parse_list(raw):
    out = []
    try:
        for tm in raw.get("typeMatches", []):
            for sm in tm.get("seriesMatches", []):
                wr = sm.get("seriesAdWrapper", {})
                sname = wr.get("seriesName","")
                for m in wr.get("matches",[]):
                    mi  = m.get("matchInfo",{})
                    ms  = m.get("matchScore",{})
                    vi  = mi.get("venueInfo",{})
                    venue = f"{vi.get('ground','')}, {vi.get('city','')}".strip(", ")
                    out.append({
                        "matchId":    str(mi.get("matchId","")),
                        "team1":      mi.get("team1",{}).get("teamName",""),
                        "team2":      mi.get("team2",{}).get("teamName",""),
                        "seriesName": sname,
                        "status":     mi.get("status",""),
                        "state":      mi.get("state",""),
                        "venue":      venue,
                        "t1s":        ms.get("team1Score",{}),
                        "t2s":        ms.get("team2Score",{}),
                    })
    except: pass
    return out


def _build_sc(m):
    try:
        t1, t2 = m["team1"], m["team2"]
        s1, s2 = _ts(t1), _ts(t2)

        def inn(name, short, sb):
            i = sb.get("inngs1",{})
            r = _int(i.get("runs",0)); w = _int(i.get("wickets",0))
            o = _float(i.get("overs",0))
            rr = round(r/o,2) if o>0 else 0.0
            return {"name":name,"short":short,"score":str(r),"wickets":str(w),
                    "overs":str(o),"rr":str(rr),"_r":r,"_w":w,"_o":o}

        i1 = inn(t1, s1, m["t1s"])
        i2 = inn(t2, s2, m["t2s"]) if m["t2s"] else None

        two = i2 is not None and i2["_r"] > 0
        bat = i2 if two else i1
        fld = i1 if two else {"name":t2,"short":s2,"score":"—","wickets":"—",
                               "overs":"0.0","rr":"0.0","_r":0,"_w":0,"_o":0.0}

        tgt = i1["_r"]+1 if two else 0
        rn  = max(0, tgt - bat["_r"]) if tgt>0 else 0
        bu  = int(bat["_o"])*6 + round((bat["_o"]%1)*10)
        bl  = max(0, 120-bu)
        rr  = round(rn*6/bl,2) if bl>0 and rn>0 else 0.0
        ph  = "powerplay" if bat["_o"]<=6 else ("death" if bat["_o"]>=15 else "middle")
        bwp, fwp = _win_prob(bat["_r"],bat["_w"],bat["_o"],tgt) if tgt>0 else (50,50)

        return {
            "match":     f"{t1} vs {t2}",
            "venue":     m.get("venue",""),
            "status":    m.get("status","LIVE"),
            "bat":       bat,          # currently batting team
            "field":     fld,          # currently fielding / yet to bat
            "t1":        i1,           # team batting first (always t1)
            "t2":        i2 or fld,    # team batting second
            "target":    tgt,
            "required":  rn,
            "req_rr":    rr,
            "balls_left":bl,
            "phase":     ph,
            "second_innings": two,
            "bat_wp":    bwp,
            "fld_wp":    fwp,
        }
    except: return None


def _parse_scard(raw, sc):
    """Extract real-time batters and bowlers from Cricbuzz scorecard."""
    batters, bowlers = [], []
    try:
        cards = raw.get("scoreCard", [])
        if not cards: return [], []

        # Use the latest innings card
        card = cards[-1]
        bat_short = sc["bat"]["short"]
        fld_short = sc["field"]["short"]

        # Batters
        bats = card.get("batTeamDetails",{}).get("batsmenData",{})
        for _, b in bats.items():
            name = b.get("batName","")
            if not name: continue
            r  = _int(b.get("runs",0))
            bl = max(1,_int(b.get("balls",1)))
            f4 = _int(b.get("fours",0))
            f6 = _int(b.get("sixes",0))
            sr = round(_float(b.get("strikeRate",0)) or r/bl*100, 1)
            oot= b.get("outDesc","batting") or "batting"
            batters.append({"name":name,"team":bat_short,"runs":r,"balls":bl,
                            "sr":sr,"4s":f4,"6s":f6,"status":oot})

        # Bowlers
        bwls = card.get("bowlTeamDetails",{}).get("bowlersData",{})
        for _, b in bwls.items():
            name = b.get("bowlName","")
            if not name: continue
            o  = _float(b.get("overs",0))
            r  = _int(b.get("runs",0))
            w  = _int(b.get("wickets",0))
            m  = _int(b.get("maidens",0))
            ec = round(_float(b.get("economy",0)) or (r/o if o>0 else 0),2)
            bowlers.append({"name":name,"team":fld_short,"overs":o,"runs":r,
                            "wkts":w,"maidens":m,"econ":ec})
    except: pass
    return batters, bowlers


def resolve_live(debug=False):
    raw = _fetch_list()
    if debug and raw:
        with st.expander("🔍 RAW — Match List", expanded=True): st.json(raw)
    if not raw: return None, [], []

    for m in _parse_list(raw):
        sn  = m["seriesName"].upper()
        st_ = m["status"].lower()
        if "IPL" not in sn and "INDIAN PREMIER" not in sn: continue
        if not m["matchId"] or "toss" in st_ or "upcom" in st_: continue

        sc = _build_sc(m)
        if not sc: continue

        bat, bowl = [], []
        rscard = _fetch_scard(m["matchId"])
        if debug and rscard:
            with st.expander(f"🔍 RAW — Scorecard ({m['matchId']})", expanded=False):
                st.json(rscard)
        if rscard:
            bat, bowl = _parse_scard(rscard, sc)

        return sc, bat, bowl

    return None, [], []


# ─────────────────────────────────────────────────────────────────
# 4. DEMO DATA (fallback only)
# ─────────────────────────────────────────────────────────────────
def _demo_sc():
    srh = {"name":"Sunrisers Hyderabad","short":"SRH","score":"186","wickets":"5",
           "overs":"20.0","rr":"9.3","_r":186,"_w":5,"_o":20.0}
    rcb = {"name":"Royal Challengers Bengaluru","short":"RCB","score":"142","wickets":"3",
           "overs":"15.3","rr":"9.15","_r":142,"_w":3,"_o":15.3}
    return {"match":"SRH vs RCB — IPL 2026, Match 1","venue":"M.Chinnaswamy Stadium, Bengaluru",
            "status":"Royal Challengers Bengaluru opt to bowl","bat":rcb,"field":srh,
            "t1":srh,"t2":rcb,"target":187,"required":45,"req_rr":6.75,"balls_left":27,
            "phase":"death","second_innings":True,"bat_wp":45,"fld_wp":55}

def _demo_bat():
    return [
        {"name":"Ishan Kishan","team":"SRH","runs":43,"balls":28,"sr":153.6,"4s":4,"6s":3,"status":"batting"},
        {"name":"Travis Head","team":"SRH","runs":68,"balls":41,"sr":165.9,"4s":7,"6s":4,"status":"batting"},
        {"name":"Abhishek Sharma","team":"SRH","runs":12,"balls":9,"sr":133.3,"4s":2,"6s":0,"status":"c Maxwell b Siraj"},
    ]

def _demo_bowl():
    return [
        {"name":"Mohammed Siraj","team":"RCB","overs":3.0,"runs":28,"wkts":2,"maidens":0,"econ":9.33},
        {"name":"Yash Dayal","team":"RCB","overs":3.2,"runs":34,"wkts":1,"maidens":0,"econ":10.2},
        {"name":"Krunal Pandya","team":"RCB","overs":2.0,"runs":18,"wkts":1,"maidens":0,"econ":9.0},
    ]


# ─────────────────────────────────────────────────────────────────
# 5. PREDICTION ENGINE
# ─────────────────────────────────────────────────────────────────
def predict(sc):
    """Generate live match prediction text based on current state."""
    bat  = sc["bat"]
    two  = sc["second_innings"]
    rn   = sc["required"]
    bl   = sc["balls_left"]
    rr   = sc["req_rr"]
    bwp  = sc["bat_wp"]
    ph   = sc["phase"]
    wl   = 10 - bat["_w"]
    crr  = _float(bat["rr"])
    o    = bat["_o"]

    if not two:
        # 1st innings — project final total
        balls_used = int(o)*6 + round((o%1)*10)
        balls_left = max(1, 120 - balls_used)
        proj = bat["_r"] + round(crr * balls_left / 6)
        if crr >= 10:
            verdict = "🔥 Explosive Start"
            clr = "green"
            txt = (f"{bat['name']} are batting at **{crr}** RPO after {o} overs. "
                   f"Projected total: **{proj}** — a challenging target for the chasing side.")
        elif crr >= 8:
            verdict = "✅ Solid Platform"
            clr = "green"
            txt = (f"Good start at **{crr}** RPO. Projected total around **{proj}**. "
                   f"The team needs to accelerate in the {ph} overs.")
        else:
            verdict = "⚠️ Slow Start"
            clr = "warn"
            txt = (f"Below-par rate of **{crr}** RPO. Projected: **{proj}**. "
                   f"Need big hits in the remaining overs to set a competitive total.")
    else:
        # 2nd innings — chase analysis
        balls_per_wkt = round(bl / max(1, wl), 1)
        if bwp >= 65:
            verdict = "🟢 Chase On Track"
            clr = "green"
            txt = (f"Need **{rn}** off **{bl}** balls (Req: **{rr}** RPO). "
                   f"Win probability: **{bwp}%**. With {wl} wickets in hand, "
                   f"~{balls_per_wkt} balls per wicket to spare. Chase well within range.")
        elif bwp >= 45:
            verdict = "🟡 Evenly Poised"
            clr = "warn"
            txt = (f"**{rn}** needed off **{bl}** balls at **{rr}** RPO. "
                   f"Win probability: **{bwp}%**. Pressure building — {wl} wickets left. "
                   f"One partnership can swing this either way.")
        else:
            verdict = "🔴 Under Pressure"
            clr = "danger"
            txt = (f"**{rn}** off **{bl}** balls — required rate **{rr}** is steep. "
                   f"Win probability: **{bwp}%**. Only {wl} wickets left. "
                   f"Need a big over to get back in the game.")
    return verdict, clr, txt


# ─────────────────────────────────────────────────────────────────
# 6. UI COMPONENTS
# ─────────────────────────────────────────────────────────────────

def render_header(sc, is_live):
    IST  = pytz.timezone('Asia/Kolkata')
    now  = datetime.now(IST).strftime("%d %b %Y · %H:%M IST")
    dot  = '<span class="live-dot"></span>' if is_live else ""
    st.markdown(
        f'<div class="ctrl-bar">'
        f'<div><div class="ctrl-logo">GOD\'S<span>EYE</span> v3.5 '
        f'<span style="font-size:11px;color:#94A3B8;font-weight:400">IPL MATCH CENTER</span></div>'
        f'<div style="font-size:11px;color:#94A3B8;margin-top:2px">'
        f'{dot}{"LIVE — " if is_live else ""}{sc.get("match","")}</div></div>'
        f'<div class="ctrl-time">{now}<br>'
        f'<span style="color:#64748B">OPERATOR: UDAY MADDILA</span></div>'
        f'</div>',
        unsafe_allow_html=True)


def render_scoreboard(sc):
    bat   = sc["bat"]
    field = sc["field"]
    two   = sc["second_innings"]
    bwp   = sc["bat_wp"]
    fwp   = sc["fld_wp"]
    bc    = _c(bat["short"])
    fc    = _c(field["short"])
    ph    = sc["phase"]
    ph_b  = ("badge-pp" if ph=="powerplay" else ("badge-dth" if ph=="death" else "badge-mid"))
    ph_t  = ph.capitalize()

    st.markdown('<div class="sec-hdr">📋 Scorecard</div>', unsafe_allow_html=True)

    # Match header bar
    st.markdown(
        f'<div class="match-hdr">'
        f'<div><div class="match-name">🏟️ {sc["venue"]}</div>'
        f'<div class="match-venue">{sc["match"]} &nbsp;·&nbsp; <span class="match-status">{sc["status"]}</span></div></div>'
        f'<div style="text-align:right"><span class="badge {ph_b}">{ph_t}</span>'
        f'<div style="font-size:11px;color:#94A3B8;margin-top:4px">{"2nd Innings" if two else "1st Innings"}</div></div>'
        f'</div>',
        unsafe_allow_html=True)

    # Scores — batting team LEFT, fielding/yet-to-bat RIGHT
    c1, c2, c3 = st.columns([5, 4, 5])

    # LEFT — Batting team (currently batting)
    with c1:
        bat_score = f'{bat["score"]}/{bat["wickets"]}' if bat["score"] not in ("—","0","") else "Yet to Bat"
        bat_sub   = f'{bat["overs"]} Ov  ·  CRR: {bat["rr"]}' if bat["score"] not in ("—","0","") else "Batting 2nd"
        st.markdown(
            f'<div class="card">'
            f'<div class="team-label" style="color:{bc}">▶ {bat["short"]} (Batting)</div>'
            f'<div class="score-big" style="color:{bc}">{bat_score}</div>'
            f'<div class="score-sub">{bat_sub}</div>'
            f'</div>', unsafe_allow_html=True)

    # MIDDLE — Win probability + target
    with c2:
        if two:
            rn = sc["required"]; bl = sc["balls_left"]; rr = sc["req_rr"]
            rc = "#DC2626" if rr>12 else ("#D97706" if rr>9 else "#16A34A")
            mid_html = (
                f'<div class="card" style="text-align:center">'
                f'<div class="stat-lbl">Win Probability</div>'
                f'<div style="margin:10px 0">'
                f'<div style="display:flex;justify-content:space-between;font-size:12px;font-weight:600;margin-bottom:4px">'
                f'<span style="color:{bc}">{bat["short"]}</span><span style="color:{bc}">{bwp}%</span></div>'
                f'<div class="pbar-wrap"><div class="pbar-fill" style="width:{bwp}%;background:{bc}"></div></div>'
                f'<div style="display:flex;justify-content:space-between;font-size:12px;font-weight:600;margin-top:8px;margin-bottom:4px">'
                f'<span style="color:{fc}">{field["short"]}</span><span style="color:{fc}">{fwp}%</span></div>'
                f'<div class="pbar-wrap"><div class="pbar-fill" style="width:{fwp}%;background:{fc}"></div></div>'
                f'</div>'
                f'<div style="margin-top:10px;padding:8px;background:#FEF2F2;border-radius:6px;font-size:12px">'
                f'Need <b style="color:{rc}">{rn}</b> off <b>{bl}</b> balls &nbsp;·&nbsp; Req RR: <b style="color:{rc}">{rr}</b>'
                f'</div></div>'
            )
        else:
            r = bat["_r"]; o = bat["_o"]
            proj = bat["_r"] + round(_float(bat["rr"]) * max(0, (120 - int(o)*6 - round((o%1)*10))) / 6)
            mid_html = (
                f'<div class="card" style="text-align:center">'
                f'<div class="stat-lbl">1st Innings Progress</div>'
                f'<div style="margin:10px 0">'
                f'<div class="pbar-wrap"><div class="pbar-fill" style="width:{min(100,int(o/20*100))}%;background:{bc}"></div></div>'
                f'<div style="font-size:11px;color:#64748B;margin-top:4px">{o} / 20.0 Overs</div>'
                f'</div>'
                f'<div style="margin-top:10px;padding:8px;background:#F0FDF4;border-radius:6px;font-size:12px">'
                f'CRR: <b style="color:#16A34A">{bat["rr"]}</b> &nbsp;·&nbsp; Projected: <b>~{proj}</b>'
                f'</div></div>'
            )
        st.markdown(mid_html, unsafe_allow_html=True)

    # RIGHT — Fielding/yet-to-bat team
    with c3:
        if field["score"] in ("—","") or not two:
            fld_score = f'{field["score"]}/{field["wickets"]}' if field["score"] not in ("—","") else "Yet to Bat"
            fld_sub   = f'{field["overs"]} Ov  ·  CRR: {field["rr"]}' if field["score"] not in ("—","") else "Bats next"
        else:
            fld_score = f'{field["score"]}/{field["wickets"]}'
            fld_sub   = f'{field["overs"]} Ov  ·  CRR: {field["rr"]}'
        fld_label = f'{"Bowled — " if two else "Bats Next — "}{field["short"]}'
        st.markdown(
            f'<div class="card">'
            f'<div class="team-label" style="color:{fc}">⚡ {fld_label}</div>'
            f'<div class="score-big" style="color:{fc}">{fld_score}</div>'
            f'<div class="score-sub">{fld_sub}</div>'
            f'</div>', unsafe_allow_html=True)


def render_key_stats(sc, batters, bowlers):
    st.markdown('<div class="sec-hdr">📊 Key Match Stats</div>', unsafe_allow_html=True)
    bat = sc["bat"]; two = sc["second_innings"]
    wl  = 10 - bat["_w"]
    ph  = sc["phase"]
    ph_b= ("badge-pp" if ph=="powerplay" else ("badge-dth" if ph=="death" else "badge-mid"))

    # Current top scorer from live batters
    live_bat  = [b for b in batters if b.get("status","batting").lower() in ("batting","not out","")]
    top_scorer= max(batters, key=lambda x:x["runs"]) if batters else None
    top_bowler= max(bowlers, key=lambda x:x["wkts"]) if bowlers else None

    c1,c2,c3,c4,c5 = st.columns(5)
    def _card(col, lbl, val, sub, color="#1E293B", top_border="#2563EB"):
        with col:
            st.markdown(
                f'<div class="card" style="border-top:3px solid {top_border}">'
                f'<div class="stat-lbl">{lbl}</div>'
                f'<div class="stat-val" style="color:{color}">{val}</div>'
                f'<div class="stat-sub">{sub}</div></div>',
                unsafe_allow_html=True)

    _card(c1, "Current RR", bat["rr"],
          f'{bat["short"]} batting · {bat["overs"]} ov',
          "#16A34A" if _float(bat["rr"])>=8 else "#DC2626", "#16A34A")

    if two:
        rr = sc["req_rr"]
        col = "#DC2626" if rr>12 else ("#D97706" if rr>9 else "#16A34A")
        _card(c2, "Required RR", str(rr),
              f'{sc["required"]} runs · {sc["balls_left"]} balls', col, col)
    else:
        _card(c2, "Wickets Left", str(wl),
              f'{bat["wickets"]} fallen · {ph} overs', "#1E293B", "#7C3AED")

    _card(c3, "Match Phase", ph.capitalize(),
          f'Over {bat["_o"]} of 20', "#1E293B", "#7C3AED")

    if top_scorer:
        _card(c4, "Top Scorer", f'{top_scorer["runs"]}* ({top_scorer["balls"]}b)',
              f'{top_scorer["name"]} · SR: {top_scorer["sr"]}', "#1D4ED8", "#1D4ED8")
    else:
        _card(c4, "Top Scorer", "—", "Awaiting data", "#94A3B8", "#94A3B8")

    if top_bowler:
        ec = top_bowler["econ"]
        ec_c = "#16A34A" if ec<8 else ("#D97706" if ec<11 else "#DC2626")
        _card(c5, "Best Bowler", f'{top_bowler["wkts"]}/{top_bowler["runs"]}',
              f'{top_bowler["name"]} · {top_bowler["overs"]} ov · Econ {ec}', ec_c, ec_c)
    else:
        _card(c5, "Best Bowler", "—", "Awaiting data", "#94A3B8", "#94A3B8")


def render_prediction(sc):
    st.markdown('<div class="sec-hdr">🔮 Live Match Prediction</div>', unsafe_allow_html=True)
    verdict, clr, txt = predict(sc)
    bwp = sc["bat_wp"]; fwp = sc["fld_wp"]
    bat = sc["bat"]; field = sc["field"]
    bc  = _c(bat["short"]); fc = _c(field["short"])

    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown(
            f'<div class="predict-box {clr if clr != "green" else ""}">'
            f'<div style="font-size:15px;font-weight:700;color:#1E293B;margin-bottom:8px">{verdict}</div>'
            f'<div style="font-size:13px;color:#374151;line-height:1.7">{txt}</div>'
            f'</div>', unsafe_allow_html=True)
    with c2:
        st.markdown(
            f'<div class="card">'
            f'<div class="stat-lbl">Win Probability Model</div>'
            f'<div style="margin-top:10px">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">'
            f'<span style="font-weight:700;color:{bc};font-size:14px">{bat["short"]}</span>'
            f'<span style="font-size:20px;font-weight:700;color:{bc}">{bwp}%</span></div>'
            f'<div class="pbar-wrap" style="height:12px"><div class="pbar-fill" style="width:{bwp}%;background:{bc}"></div></div>'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-top:12px;margin-bottom:6px">'
            f'<span style="font-weight:700;color:{fc};font-size:14px">{field["short"]}</span>'
            f'<span style="font-size:20px;font-weight:700;color:{fc}">{fwp}%</span></div>'
            f'<div class="pbar-wrap" style="height:12px"><div class="pbar-fill" style="width:{fwp}%;background:{fc}"></div></div>'
            f'</div></div>', unsafe_allow_html=True)


def render_batters(batters, sc):
    st.markdown('<div class="sec-hdr">🏏 Batting Scorecard (Current Innings)</div>', unsafe_allow_html=True)
    if not batters:
        st.info("Live batting data loading... (scorecard API enriching)")
        return
    bat_team = sc["bat"]["short"]
    tc = _c(bat_team)
    hdr = ('<div class="bat-row row-hdr">'
           '<div>Batter</div><div style="text-align:right">R</div>'
           '<div style="text-align:right">B</div><div style="text-align:right">4s</div>'
           '<div style="text-align:right">6s</div><div style="text-align:right">SR</div></div>')
    rows = ""
    for b in batters:
        out = b.get("status","")
        is_bat = "batting" in out.lower() or out in ("","not out")
        name_style = f'font-weight:700;color:{tc}' if is_bat else 'color:#374151'
        sr_c = "good" if b["sr"]>=150 else ("warn" if b["sr"]>=100 else "bad")
        rows += (f'<div class="bat-row">'
                 f'<div><span style="{name_style}">{b["name"]}</span>'
                 f'{"&nbsp;🟢" if is_bat else ""}'
                 f'<div style="font-size:10px;color:#94A3B8">{out[:40] if not is_bat else "not out"}</div></div>'
                 f'<div class="num-cell"><b>{b["runs"]}</b></div>'
                 f'<div class="num-cell">{b["balls"]}</div>'
                 f'<div class="num-cell">{b["4s"]}</div>'
                 f'<div class="num-cell">{b["6s"]}</div>'
                 f'<div class="num-cell"><span class="{sr_c}">{b["sr"]}</span></div>'
                 f'</div>')
    st.markdown(f'<div class="card">{hdr}{rows}</div>', unsafe_allow_html=True)


def render_bowlers(bowlers, sc):
    st.markdown('<div class="sec-hdr">🎯 Bowling Figures (Current Innings)</div>', unsafe_allow_html=True)
    if not bowlers:
        st.info("Live bowling data loading... (scorecard API enriching)")
        return
    bowl_team = sc["field"]["short"]
    tc = _c(bowl_team)
    hdr = ('<div class="bowl-row row-hdr">'
           '<div>Bowler</div><div style="text-align:right">O</div>'
           '<div style="text-align:right">R</div><div style="text-align:right">W</div>'
           '<div style="text-align:right">M</div><div style="text-align:right">Econ</div></div>')
    rows = ""
    # Sort by overs bowled descending
    for b in sorted(bowlers, key=lambda x: -x["overs"]):
        ec = b["econ"]
        ec_c = "good" if ec<8 else ("warn" if ec<11 else "bad")
        wkt_style = 'style="color:#DC2626;font-weight:700"' if b["wkts"]>0 else ""
        rows += (f'<div class="bowl-row">'
                 f'<div><span style="font-weight:600;color:{tc}">{b["name"]}</span></div>'
                 f'<div class="num-cell">{b["overs"]}</div>'
                 f'<div class="num-cell">{b["runs"]}</div>'
                 f'<div class="num-cell"><span {wkt_style}>{b["wkts"]}</span></div>'
                 f'<div class="num-cell">{b["maidens"]}</div>'
                 f'<div class="num-cell"><span class="{ec_c}">{ec}</span></div>'
                 f'</div>')
    st.markdown(f'<div class="card">{hdr}{rows}</div>', unsafe_allow_html=True)


def render_news(news):
    st.markdown('<div class="sec-hdr">📰 IPL 2026 News Feed</div>', unsafe_allow_html=True)
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


# ─────────────────────────────────────────────────────────────────
# 7. CONTROLS
# ─────────────────────────────────────────────────────────────────
_c1, _c2, _c3, _c4, _c5 = st.columns([3,1,1,1,1])
with _c1:
    st.markdown(
        '<div style="font-size:11px;color:#94A3B8;padding-top:10px">'
        "GOD'S EYE v3.5 · IPL Match Center · © Uday Maddila</div>",
        unsafe_allow_html=True)
with _c2: auto_refresh = st.toggle("Auto-Refresh", value=True)
with _c3: show_demo    = st.toggle("Demo Mode",    value=False)
with _c4: debug_mode   = st.toggle("Debug API",    value=False)
with _c5:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ─────────────────────────────────────────────────────────────────
# 8. MAIN
# ─────────────────────────────────────────────────────────────────
sc      = None
batters = []
bowlers = []
is_live = False

if not show_demo:
    with st.spinner("Fetching live IPL data..."):
        sc, batters, bowlers = resolve_live(debug=debug_mode)
        is_live = sc is not None

if sc is None:
    st.info("📡 No live IPL match right now — showing demo data.")
    sc      = _demo_sc()
    batters = _demo_bat()
    bowlers = _demo_bowl()

news = fetch_news()

# ─── RENDER ────────────────────────────────────────────────────
render_header(sc, is_live)
render_scoreboard(sc)

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
render_key_stats(sc, batters, bowlers)

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
render_prediction(sc)

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
col_bat, col_bowl = st.columns(2, gap="medium")
with col_bat:  render_batters(batters, sc)
with col_bowl: render_bowlers(bowlers, sc)

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
render_news(news)

st.markdown(
    f'<div style="text-align:center;font-size:11px;color:#94A3B8;margin-top:20px;padding-top:16px;border-top:1px solid #E2E8F0">'
    f'GOD\'S EYE v3.5 · Data: Cricbuzz via RapidAPI · News: Google News RSS · '
    f'Auto-refreshes every {REFRESH_SECS}s · © Uday Maddila</div>',
    unsafe_allow_html=True)

if auto_refresh:
    time.sleep(REFRESH_SECS)
    st.rerun()
