"""
GOD'S EYE v7.0 — IPL LIVE MATCH CENTER
Operator : Uday Maddila
FULL AUTO: Live scrape from Cricbuzz + ESPN + OpenWeather.
All tabs auto-update every 15s. Zero manual edits needed per match.
"""

import streamlit as st
import requests
import time
import random
import re
import json
from datetime import datetime
import pytz
from bs4 import BeautifulSoup
import plotly.graph_objects as go

st.set_page_config(page_title="GOD'S EYE | IPL 2026", page_icon="🏏",
                   layout="wide", initial_sidebar_state="collapsed")

# ── SESSION STATE ──────────────────────────────────────────────────────────────
for k, v in [("alert_log",[]), ("prev_score",{}), ("prev_wkts",-1), ("scraper_src","Initializing...")]:
    if k not in st.session_state: st.session_state[k] = v

# ── CONSTANTS ──────────────────────────────────────────────────────────────────
REFRESH_SECS = 15
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

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
    "rcb":"RCB","srh":"SRH","mi":"MI","csk":"CSK","kkr":"KKR",
    "rr":"RR","dc":"DC","pbks":"PBKS","lsg":"LSG","gt":"GT",
}

VENUES = {
    "MI": "Wankhede Stadium, Mumbai",
    "RCB": "M. Chinnaswamy Stadium, Bengaluru",
    "CSK": "M. A. Chidambaram Stadium, Chennai",
    "KKR": "Eden Gardens, Kolkata",
    "SRH": "Rajiv Gandhi Intl Stadium, Hyderabad",
    "DC": "Arun Jaitley Stadium, Delhi",
    "RR": "Sawai Mansingh Stadium, Jaipur",
    "PBKS": "PCA Stadium, Mohali",
    "GT": "Narendra Modi Stadium, Ahmedabad",
    "LSG": "Ekana Stadium, Lucknow"
}

VENUE_CITY = {
    "Wankhede Stadium, Mumbai": "Mumbai",
    "M. Chinnaswamy Stadium, Bengaluru": "Bangalore",
    "M. A. Chidambaram Stadium, Chennai": "Chennai",
    "Eden Gardens, Kolkata": "Kolkata",
    "Rajiv Gandhi Intl Stadium, Hyderabad": "Hyderabad",
    "Arun Jaitley Stadium, Delhi": "Delhi",
    "Sawai Mansingh Stadium, Jaipur": "Jaipur",
    "PCA Stadium, Mohali": "Chandigarh",
    "Narendra Modi Stadium, Ahmedabad": "Ahmedabad",
    "Ekana Stadium, Lucknow": "Lucknow",
}

PITCH_DNA = {
    "Mumbai":    {"avg_1st":172,"avg_2nd":158,"chase_win_pct":48,"pace_friendly":True, "spin_friendly":False,"dew_factor":"High","notes":"Flat track, good for batting. Dew heavily favors chasing team in 2nd half."},
    "Bangalore": {"avg_1st":185,"avg_2nd":170,"chase_win_pct":52,"pace_friendly":False,"spin_friendly":False,"dew_factor":"Low","notes":"Small ground, high-scoring. Both teams love batting first but chases are common."},
    "Chennai":   {"avg_1st":165,"avg_2nd":148,"chase_win_pct":44,"pace_friendly":False,"spin_friendly":True, "dew_factor":"Moderate","notes":"Slow turning pitch. Teams batting first hold an advantage here."},
    "Kolkata":   {"avg_1st":170,"avg_2nd":155,"chase_win_pct":46,"pace_friendly":True, "spin_friendly":True,"dew_factor":"High","notes":"Two-paced pitch. Dew factor is significant in later overs."},
    "Hyderabad": {"avg_1st":175,"avg_2nd":162,"chase_win_pct":50,"pace_friendly":True, "spin_friendly":False,"dew_factor":"Moderate","notes":"Good batting surface with true bounce. Pace bowlers effective early."},
    "Delhi":     {"avg_1st":168,"avg_2nd":154,"chase_win_pct":47,"pace_friendly":True, "spin_friendly":False,"dew_factor":"Low","notes":"Drop-in pitch, tends to slow down. Pacemakers dominate in first 6 overs."},
    "Jaipur":    {"avg_1st":162,"avg_2nd":150,"chase_win_pct":45,"pace_friendly":False,"spin_friendly":True, "dew_factor":"Low","notes":"Dry, spin-friendly surface. Low dew makes first-innings scores more defendable."},
    "Chandigarh":{"avg_1st":170,"avg_2nd":158,"chase_win_pct":49,"pace_friendly":True, "spin_friendly":False,"dew_factor":"Moderate","notes":"Even contest. Good for both batting and bowling in powerplay."},
    "Ahmedabad": {"avg_1st":178,"avg_2nd":162,"chase_win_pct":48,"pace_friendly":True, "spin_friendly":False,"dew_factor":"Low","notes":"World's largest stadium. Outfield is fast. Pace bowlers get good movement."},
    "Lucknow":   {"avg_1st":166,"avg_2nd":152,"chase_win_pct":46,"pace_friendly":False,"spin_friendly":True, "dew_factor":"High","notes":"Spin-friendly with high dew. Bowling second is tricky late in the innings."},
}

SQUAD_DB = {
    "MI":  ["Rohit Sharma","Suryakumar Yadav","Ishan Kishan","Hardik Pandya","Tilak Varma","Tim David",
            "Jasprit Bumrah","Lasith Malinga","Piyush Chawla","Krunal Pandya","Dewald Brevis"],
    "KKR": ["Ajinkya Rahane","Sunil Narine","Andre Russell","Shreyas Iyer","Nitish Rana",
            "Rinku Singh","Mitchell Starc","Varun Chakravarthy","Harshit Rana","Phil Salt","Angkrish Raghuvanshi"],
    "RCB": ["Virat Kohli","Faf du Plessis","Glenn Maxwell","AB de Villiers","Dinesh Karthik",
            "Mohammed Siraj","Harshal Patel","Wanindu Hasaranga","Josh Hazlewood","Rajat Patidar","Anuj Rawat"],
    "CSK": ["MS Dhoni","Ruturaj Gaikwad","Devon Conway","Shivam Dube","Ravindra Jadeja",
            "Moeen Ali","Deepak Chahar","Tushar Deshpande","Matheesha Pathirana","Ajinkya Rahane","Mitchell Santner"],
    "SRH": ["Pat Cummins","Heinrich Klaasen","Travis Head","Abhishek Sharma","Aiden Markram",
            "Washington Sundar","Bhuvneshwar Kumar","T Natarajan","Mayank Agarwal","Nitish Kumar Reddy","Marco Jansen"],
    "RR": ["Sanju Samson","Jos Buttler","Riyan Parag","Shimron Hetmyer","Dhruv Jurel",
           "Yuzvendra Chahal","Trent Boult","Sandeep Sharma","Ravichandran Ashwin","Tom Kohler-Cadmore","Devdutt Padikkal"],
    "DC": ["David Warner","Prithvi Shaw","Axar Patel","Ricky Bhui","Jake Fraser-McGurk",
           "Anrich Nortje","Kuldeep Yadav","Ishant Sharma","Mitchell Marsh","Rishabh Pant","Tristan Stubbs"],
    "PBKS":["Shikhar Dhawan","Liam Livingstone","Jonny Bairstow","Sam Curran","Arshdeep Singh",
            "Kagiso Rabada","Rahul Chahar","Harpreet Brar","Sikandar Raza","Jitesh Sharma","Rilee Rossouw"],
    "GT": ["Shubman Gill","Hardik Pandya","David Miller","Kane Williamson","Wriddhiman Saha",
           "Mohammed Shami","Rashid Khan","Alzarri Joseph","Vijay Shankar","Abhinav Manohar","Yash Dayal"],
    "LSG": ["KL Rahul","Quinton de Kock","Nicholas Pooran","Deepak Hooda","Krunal Pandya",
            "Mark Wood","Ravi Bishnoi","Avesh Khan","Jason Holder","Prerak Mankad","Kyle Mayers"],
}

KEY_BATTERS = {
    "MI":  [("Rohit Sharma","+Run Machine. Loves powerplay. Watch for pull shots over square leg."),
            ("Suryakumar Yadav","+360° batter. Dangerous in death overs. Key match-winner."),
            ("Ishan Kishan","+Explosive opener. Fast starter against pace. Watch in PP.")],
    "KKR": [("Ajinkya Rahane","+Technically sound. Anchors the innings. Key against spin."),
            ("Sunil Narine","+Pinch-hitter. Can destroy PP bowling. Key in T20 format."),
            ("Andre Russell","+Death-over destroyer. 150+ SR. Match-winner in last 5 overs.")],
    "RCB": [("Virat Kohli","+Run-machine. Best batter in IPL history. Key anchor."),
            ("Faf du Plessis","+Consistent opener. Good against pace and spin."),
            ("Glenn Maxwell","+Big-hitter. Can score 50 off 20 balls on his day.")],
    "CSK": [("MS Dhoni","+Finisher legend. Watch him in overs 18-20."),
            ("Ruturaj Gaikwad","+Consistent top-order. Excellent against spin."),
            ("Devon Conway","+Solid opener. Good technique against pace.")],
    "SRH": [("Travis Head","+Explosive opener. Can score 40+ in PP alone."),
            ("Heinrich Klaasen","+Power-hitter in middle overs. Very dangerous."),
            ("Abhishek Sharma","+Aggressive opener. Will take on any bowler from ball 1.")],
    "RR":  [("Sanju Samson","+Captain and keeper. Explosive batter on his day."),
            ("Jos Buttler","+Orange cap winner. World-class T20 opener."),
            ("Riyan Parag","+Young finisher. Strong in death overs.")],
    "DC":  [("David Warner","+Consistent opener. IPL legend with 6000+ runs."),
            ("Rishabh Pant","+Dynamic wicket-keeper batter. Can change game in 2 overs."),
            ("Jake Fraser-McGurk","+Explosive young gun. Watch in powerplay.")],
    "PBKS":[("Shikhar Dhawan","+Experienced opener. Strong against pace in PP."),
            ("Jonny Bairstow","+Dangerous T20 batter. Watch against spin."),
            ("Liam Livingstone","+Power-hitter. Can hit 360 degrees.")],
    "GT":  [("Shubman Gill","+Consistent run-scorer. IPL's emerging star."),
            ("David Miller","+Killer Miller. Death-over specialist."),
            ("Kane Williamson","+Technically brilliant. Anchors the innings.")],
    "LSG": [("KL Rahul","+Captain and keeper. Elegant stroke-player."),
            ("Quinton de Kock","+Explosive opener. Big six-hitter."),
            ("Nicholas Pooran","+Middle-order power. High-impact batter.")],
}

KEY_BOWLERS = {
    "MI":  [("Jasprit Bumrah","+Best death bowler in world. Unplayable yorkers."),
            ("Hardik Pandya","+Medium-pace allrounder. Key in death overs."),
            ("Piyush Chawla","+Leg-spin. Effective in middle overs.")],
    "KKR": [("Mitchell Starc","+Left-arm pace. Swings ball in PP. Yorker specialist."),
            ("Varun Chakravarthy","+Mystery spinner. Tough to read. Middle-overs key."),
            ("Sunil Narine","+Off-spin. Bowls powerplay. Economy king.")],
    "RCB": [("Jasprit Bumrah","+Best in business. Wicket-taker in all phases."),
            ("Mohammed Siraj","+Right-arm pace. Good in powerplay."),
            ("Harshal Patel","+Change-up bowler. Death overs specialist.")],
    "CSK": [("Deepak Chahar","+Swing bowler. Key in powerplay."),
            ("Ravindra Jadeja","+Left-arm spin. Miserly. Economy under 7."),
            ("Matheesha Pathirana","+Yorker machine. Death bowling expert.")],
    "SRH": [("Pat Cummins","+Pace and bounce. Wicket-taker in all phases."),
            ("Bhuvneshwar Kumar","+Swing king. Decimates top order in PP."),
            ("T Natarajan","+Left-arm pace. Yorker specialist in death.")],
    "RR":  [("Trent Boult","+Left-arm swing. Powerplay destroyer."),
            ("Yuzvendra Chahal","+Leg-spin. Highest IPL wicket-taker. Key in middle."),
            ("Sandeep Sharma","+Swing bowling. Opening over specialist.")],
    "DC":  [("Anrich Nortje","+Fastest bowler. Unsettles batters with pace."),
            ("Kuldeep Yadav","+Left-arm wrist spin. Takes wickets in clusters."),
            ("Axar Patel","+Left-arm spin. Economical. Effective on slow tracks.")],
    "PBKS":[("Arshdeep Singh","+Left-arm pace. PP and death over specialist."),
            ("Kagiso Rabada","+South African pacer. Wicket-taking machine."),
            ("Sam Curran","+Allrounder. Effective slow cutters in death.")],
    "GT":  [("Mohammed Shami","+Right-arm pace. Inswing PP bowler. Match-changer."),
            ("Rashid Khan","+Afghan leg-spin legend. Economy around 6."),
            ("Alzarri Joseph","+Windies pacer. Hits good areas. Bouncer weapon.")],
    "LSG": [("Mark Wood","+Express pace. 150+ kmph. Unsettles any batter."),
            ("Ravi Bishnoi","+Young leg-spinner. Wicket-taker. Economy bowler."),
            ("Avesh Khan","+Right-arm pace. Death-over specialist.")],
}

HEAD2HEAD = {
    frozenset(["MI","KKR"]): {"MI":{"w":16,"last_result":"MI won by 5 wkts (2024)"},"KKR":{"w":14,"last_result":"KKR won by 24 runs (2024)"}},
    frozenset(["RCB","CSK"]): {"RCB":{"w":14,"last_result":"RCB won by 4 wkts (2024)"},"CSK":{"w":19,"last_result":"CSK won by 6 wkts (2024)"}},
    frozenset(["MI","CSK"]): {"MI":{"w":20,"last_result":"MI won last time (2024)"},"CSK":{"w":16,"last_result":"CSK won (2023)"}},
    frozenset(["SRH","KKR"]): {"SRH":{"w":10,"last_result":"SRH won (2024)"},"KKR":{"w":11,"last_result":"KKR won by 8 wkts (2024)"}},
}


# ── CSS ────────────────────────────────────────────────────────────────────────
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
.score-card{background:white;border-radius:10px;border:1px solid #E2E8F0;
    padding:18px 22px;height:100%;box-shadow:0 1px 3px rgba(0,0,0,0.05);}
.team-badge{font-size:10px;font-weight:700;letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;}
.score-big{font-size:44px;font-weight:700;line-height:1;}
.score-detail{font-size:13px;color:#64748B;margin-top:5px;}
.pbar{height:8px;background:#E2E8F0;border-radius:4px;overflow:hidden;margin:5px 0;}
.pbar-fill{height:100%;border-radius:4px;}
.ph-toss{background:#FEF3C7;color:#92400E;padding:3px 10px;border-radius:12px;font-size:10px;font-weight:700;letter-spacing:1px;}
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
.oracle-box{background:linear-gradient(135deg,#1E293B,#0F172A);color:white;border-radius:10px;
    padding:20px;box-shadow:0 4px 6px rgba(0,0,0,0.1);border:1px solid #334155;}
.oracle-box h3{color:#38BDF8;font-size:16px;letter-spacing:1px;text-transform:uppercase;margin-bottom:15px;}
.commentary-box{background:linear-gradient(135deg,#0F172A,#1E293B);border-radius:10px;
    padding:20px;border-left:4px solid #38BDF8;color:white;}
.card{background:white;border-radius:10px;border:1px solid #E2E8F0;padding:16px 20px;box-shadow:0 1px 3px rgba(0,0,0,0.04);}
.mc-result-box{background:white;border-radius:10px;border:1px solid #E2E8F0;padding:16px;text-align:center;}
.dna-card{background:white;border-radius:8px;border:1px solid #E2E8F0;padding:12px 16px;margin-bottom:8px;}
.dew-box{background:linear-gradient(135deg,#0EA5E9,#0284C7);color:white;border-radius:10px;padding:20px;}
.pts-row{display:grid;grid-template-columns:30px 2fr 40px 40px 40px 40px 50px 60px;
    gap:4px;align-items:center;padding:8px;border-bottom:1px solid #F1F5F9;font-size:13px;}
.pts-hdr{font-size:10px;font-weight:700;letter-spacing:1px;color:#94A3B8;text-transform:uppercase;}
.src-badge{font-size:9px;font-weight:700;padding:2px 6px;border-radius:3px;letter-spacing:1px;background:#DCFCE7;color:#16A34A;}
.pre-match-card{background:linear-gradient(135deg, #1E293B, #0F172A); padding: 30px; border-radius: 10px; color: white; text-align: center; border: 1px solid #334155;}
.intel-card{background:white;border-radius:10px;border:1px solid #E2E8F0;padding:16px 20px;margin-bottom:10px;}
.intel-title{font-size:10px;font-weight:700;color:#94A3B8;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:12px;}
.player-row{padding:10px 0;border-bottom:1px solid #F1F5F9;display:flex;align-items:flex-start;gap:8px;}
.player-row:last-child{border-bottom:none;}
.player-dot{width:8px;height:8px;border-radius:50%;background:#38BDF8;margin-top:5px;flex-shrink:0;}
.player-name-big{font-weight:700;font-size:14px;color:#1E293B;}
.player-note{font-size:12px;color:#64748B;margin-top:2px;line-height:1.5;}
.venue-big-card{background:linear-gradient(135deg,#1E293B,#0F172A);color:white;border-radius:12px;padding:20px;margin-bottom:14px;}
.pitch-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-top:10px;}
.pitch-tile{background:rgba(255,255,255,0.08);border-radius:8px;padding:12px;text-align:center;}
.pitch-tile-val{font-size:22px;font-weight:800;color:#38BDF8;}
.pitch-tile-lbl{font-size:10px;color:#94A3B8;font-weight:700;letter-spacing:1px;margin-top:3px;}
.wx-row{display:flex;gap:14px;flex-wrap:wrap;margin-top:10px;}
.wx-tile{background:rgba(255,255,255,0.08);border-radius:8px;padding:12px 16px;text-align:center;flex:1;min-width:80px;}
.live-badge{background:#DC2626;color:white;font-size:9px;font-weight:700;padding:2px 8px;border-radius:3px;letter-spacing:1px;animation:pulse 1.5s infinite;}
@keyframes pulse{0%{opacity:1}50%{opacity:0.6}100%{opacity:1}}
div[data-testid="stTabs"] button{font-weight:600;color:#475569;}
div[data-testid="stTabs"] button[aria-selected="true"]{color:#1D4ED8;border-bottom-color:#1D4ED8;}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SCRAPER ENGINE v2 — Full Live Data from Cricbuzz + ESPN
# ══════════════════════════════════════════════════════════════════════════════

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

def _phase_from_overs(overs_f):
    if overs_f < 6.0: return "powerplay"
    elif overs_f < 15.0: return "middle"
    else: return "death"


@st.cache_data(ttl=REFRESH_SECS, show_spinner=False)
def fetch_weather(city):
    """Fetch live weather for given city via wttr.in (no API key needed)."""
    try:
        r = requests.get(f"https://wttr.in/{city}?format=j1", headers=HEADERS, timeout=6)
        if r.status_code == 200:
            d = r.json()
            cur = d["current_condition"][0]
            temp = cur.get("temp_C","—")
            feels = cur.get("FeelsLikeC","—")
            humidity = cur.get("humidity","—")
            desc = cur.get("weatherDesc",[{}])[0].get("value","—")
            wind_kmph = cur.get("windspeedKmph","—")
            # Dew risk heuristic
            try:
                h = int(humidity)
                dew_risk = "High 🌫️" if h > 75 else ("Moderate" if h > 55 else "Low ✅")
            except: dew_risk = "—"
            return {"temp":temp,"feels":feels,"humidity":humidity,"desc":desc,"wind":wind_kmph,"dew_risk":dew_risk,"ok":True}
    except: pass
    return {"temp":"—","feels":"—","humidity":"—","desc":"N/A","wind":"—","dew_risk":"—","ok":False}


@st.cache_data(ttl=REFRESH_SECS, show_spinner=False)
def scrape_cricbuzz_full():
    """
    Deep scrape Cricbuzz live scores page.
    Returns structured dict with all match info, or None.
    """
    try:
        r = requests.get("https://www.cricbuzz.com/cricket-match/live-scores",
                         headers=HEADERS, timeout=8)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        for block in soup.find_all("div", class_=re.compile("cb-mtch-lst|cb-col-100")):
            txt = block.get_text(" ", strip=True)
            if "Indian Premier League" not in txt and "IPL" not in txt:
                continue
            
            # Look for live tag
            live_el = block.find(string=re.compile(r"LIVE|live", re.I))
            
            # Find match title / teams
            h3 = block.find("h3") or block.find("a", class_=re.compile("cb-mtch-info"))
            if not h3: continue
            title = h3.get_text(" ", strip=True)
            if not any(x in title.lower() for x in ["vs","v/s"]): continue
            
            # Extract teams from title e.g. "Mumbai Indians vs KKR, 2nd Match, ..."
            teams_raw = re.split(r'\s+vs?\s+', title, flags=re.I)
            t1 = _ts(teams_raw[0]) if len(teams_raw) >= 1 else "TBA"
            t2 = _ts(teams_raw[1].split(",")[0]) if len(teams_raw) >= 2 else "TBA"
            
            if t1 == "UNK" or t2 == "UNK" or t1 == "TBA": continue
            
            # Status text
            status_el = block.find("div", class_=re.compile("cb-text-live|cb-text-inprogress|cb-text-preview|cb-text-complete"))
            status = status_el.get_text(strip=True) if status_el else ""
            
            # Score elements - Cricbuzz structure varies; grab all score spans
            score_spans = block.find_all("div", class_=re.compile("cb-scr-wll-chvrn|cb-ovr-num"))
            scores_raw = [s.get_text(strip=True) for s in score_spans if s.get_text(strip=True)]
            
            # Try to find link to match page for deeper scrape
            link = h3.find_parent("a") or block.find("a", href=re.compile(r"/live-cricket-scores/"))
            match_url = ("https://www.cricbuzz.com" + link["href"]) if link and link.get("href") else None
            
            return {
                "t1": t1, "t2": t2,
                "title": title,
                "status": status or f"{t1} vs {t2}",
                "scores_raw": scores_raw,
                "match_url": match_url,
                "is_live": live_el is not None,
            }
    except Exception as e:
        pass
    return None


@st.cache_data(ttl=REFRESH_SECS, show_spinner=False)
def scrape_cricbuzz_match_page(url):
    """Deep-scrape individual Cricbuzz match page for full scorecard."""
    if not url: return {}
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        soup = BeautifulSoup(r.text, 'html.parser')
        result = {}
        
        # Toss info
        toss_el = soup.find("div", class_=re.compile("cb-toss-sts|cb-text-gray"))
        if toss_el: result["toss"] = toss_el.get_text(strip=True)
        
        # Current batting team score
        bat_score_els = soup.find_all("div", class_=re.compile("cb-min-bat-rw"))
        batters = []
        for el in bat_score_els:
            name_el = el.find("a") or el.find("span", class_=re.compile("cb-col-50|cb-col-38"))
            stats_els = el.find_all("div", class_=re.compile("cb-col-8|cb-col-10"))
            if not name_el: continue
            name = name_el.get_text(strip=True)
            if not name or name.lower() in ["batter","batters","r","b","4s","6s","sr"]: continue
            stats = [s.get_text(strip=True) for s in stats_els]
            if len(stats) >= 4:
                batters.append({"name":name,"runs":_int(stats[0]),"balls":_int(stats[1]),
                                "fours":_int(stats[2]),"sixes":_int(stats[3]),
                                "sr":_float(stats[4]) if len(stats)>4 else 0.0})
        result["batters"] = batters[:2]
        
        # Bowlers
        bowl_els = soup.find_all("div", class_=re.compile("cb-min-bwl-rw"))
        bowlers = []
        for el in bowl_els:
            name_el = el.find("a") or el.find("span")
            stats_els = el.find_all("div", class_=re.compile("cb-col-8|cb-col-10"))
            if not name_el: continue
            name = name_el.get_text(strip=True)
            if not name or name.lower() in ["bowler","bowlers","o","m","r","w","econ"]: continue
            stats = [s.get_text(strip=True) for s in stats_els]
            if len(stats) >= 4:
                bowlers.append({"name":name,"overs":_float(stats[0]),"maidens":_int(stats[1]),
                                "runs":_int(stats[2]),"wkts":_int(stats[3]),
                                "econ":_float(stats[4]) if len(stats)>4 else 0.0})
        result["bowlers"] = bowlers[:2]
        
        # Current score line e.g. "44/0 (3.3 Ov)"
        score_el = soup.find("div", class_=re.compile("cb-min-tm"))
        if score_el: result["score_line"] = score_el.get_text(strip=True)
        
        # Recent balls
        recent_el = soup.find("div", class_=re.compile("cb-col cb-col-100 cb-commentary-balls"))
        if recent_el:
            balls = [b.get_text(strip=True) for b in recent_el.find_all("div", class_=re.compile("cb-col-8"))]
            result["recent_balls"] = balls[:6]
        
        return result
    except:
        return {}


@st.cache_data(ttl=REFRESH_SECS, show_spinner=False)
def scrape_espncricinfo_live():
    """
    Scrape ESPN Cricinfo for IPL live match.
    Falls back to check cricket API endpoints.
    """
    try:
        r = requests.get("https://www.espncricinfo.com/live-cricket-score",
                         headers=HEADERS, timeout=8)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Look for IPL match tiles
        for card in soup.find_all(["div","article"], class_=re.compile("match-score-block|ds-p-0")):
            txt = card.get_text(" ", strip=True)
            if "Indian Premier League" not in txt and "IPL" not in txt: continue
            
            # Grab score lines
            score_els = card.find_all(class_=re.compile("score"))
            teams_els = card.find_all(class_=re.compile("team-name|name"))
            
            teams = [t.get_text(strip=True) for t in teams_els if t.get_text(strip=True)]
            scores = [s.get_text(strip=True) for s in score_els if s.get_text(strip=True)]
            
            if len(teams) >= 2:
                t1 = _ts(teams[0])
                t2 = _ts(teams[1])
                if t1 != "UNK" and t2 != "UNK":
                    return {"t1":t1, "t2":t2, "scores":scores, "raw_txt": txt[:300]}
    except: pass
    return None


@st.cache_data(ttl=REFRESH_SECS, show_spinner=False)
def resolve_scraper():
    """
    Master resolver. Tries multiple sources.
    Returns (sc, batters, bowlers, extras, partner).
    sc = full match state dict.
    """
    # ── ATTEMPT 1: Cricbuzz live page ─────────────────────────────────────────
    cb = scrape_cricbuzz_live_v2()
    
    if cb and cb.get("t1") not in ("TBA","UNK","") and cb.get("t2") not in ("TBA","UNK",""):
        st.session_state.scraper_src = "🟢 Cricbuzz Live"
        return _build_sc_from_cricbuzz(cb)
    
    # ── ATTEMPT 2: ESPN fallback ──────────────────────────────────────────────
    espn = scrape_espncricinfo_live()
    if espn and espn.get("t1") not in ("TBA","UNK",""):
        st.session_state.scraper_src = "🟡 ESPN Fallback"
        return _build_sc_simple(espn["t1"], espn["t2"], "Live match in progress", espn.get("scores",[]))
    
    # ── ATTEMPT 3: Last resort - show waiting state ────────────────────────────
    st.session_state.scraper_src = "⚪ No Live IPL Match"
    return _build_sc_waiting()


@st.cache_data(ttl=REFRESH_SECS, show_spinner=False)
def scrape_cricbuzz_live_v2():
    """
    Improved Cricbuzz scraper - tries multiple URL patterns and
    parses score data more deeply.
    """
    urls_to_try = [
        "https://www.cricbuzz.com/cricket-match/live-scores",
        "https://www.cricbuzz.com/api/html/homepage-scag",
    ]
    
    for url in urls_to_try:
        try:
            r = requests.get(url, headers=HEADERS, timeout=8)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # Scan ALL text blocks for IPL match patterns
            all_blocks = soup.find_all(["div","li","article"], 
                                        class_=re.compile(r"cb-mtch|cb-schdl|match-card|cb-series"))
            
            for block in all_blocks:
                txt = block.get_text(" ", strip=True)
                
                # Must be IPL
                if not any(x in txt for x in ["Indian Premier League","IPL 2026","IPL"]):
                    continue
                
                # Must have vs
                vs_match = re.search(r'([A-Za-z ]+)\s+vs?\s+([A-Za-z ]+)', txt, re.I)
                if not vs_match: continue
                
                t1 = _ts(vs_match.group(1).strip())
                t2 = _ts(vs_match.group(2).split(",")[0].strip())
                
                if t1 in ("UNK","TBA") or t2 in ("UNK","TBA"): continue
                
                # Detect if LIVE
                is_live = bool(re.search(r'\bLIVE\b|live score', txt, re.I))
                
                # Status detection
                status = ""
                status_el = block.find(class_=re.compile("cb-text-live|cb-text-inprogress|cb-text-complete|cb-text-preview"))
                if status_el: status = status_el.get_text(strip=True)
                
                # Toss detection
                toss_match = re.search(r'([\w\s]+)\s+won\s+the\s+toss\s+and\s+(?:chose to\s+)?(bat|field|bowl)', txt, re.I)
                toss_info = None
                if toss_match:
                    toss_team_raw = toss_match.group(1).strip()
                    toss_choice = toss_match.group(2).lower()
                    toss_team = _ts(toss_team_raw)
                    toss_info = {"team": toss_team, "choice": toss_choice, "raw": toss_match.group(0)}
                
                # Score detection (e.g. "44/0 (3.3 ov)" or "MI: 120/4 (15.2)")
                score_matches = re.findall(r'(\d{1,3}/\d{1,2})\s*\(?([\d.]+)\s*(?:ov|overs?)?\)?', txt)
                
                # Find match URL
                link = block.find("a", href=re.compile(r"/live-cricket-scores/"))
                match_url = ("https://www.cricbuzz.com" + link["href"]) if link and link.get("href") else None
                
                return {
                    "t1": t1, "t2": t2,
                    "status": status,
                    "is_live": is_live,
                    "toss_info": toss_info,
                    "score_matches": score_matches,  # list of (score, overs) tuples
                    "match_url": match_url,
                    "raw": txt[:400],
                }
        except:
            continue
    return None


def _parse_score_str(score_str):
    """Parse '44/0' or '120/4' into (runs, wickets)."""
    try:
        parts = score_str.split("/")
        return int(parts[0]), int(parts[1]) if len(parts)>1 else 0
    except:
        return 0, 0


def _determine_batting_bowling(t1, t2, toss_info, score_matches, status):
    """
    Determine which team is batting vs bowling.
    Uses toss info first, then tries to infer from score pattern.
    """
    bat_team = t1
    fld_team = t2
    second_innings = False
    
    # Priority 1: Toss info
    if toss_info:
        toss_team = toss_info["team"]
        choice = toss_info["choice"]
        
        if choice in ("bat", "batting"):
            bat_team = toss_team
            fld_team = t2 if toss_team == t1 else t1
        else:  # field / bowl
            fld_team = toss_team
            bat_team = t2 if toss_team == t1 else t1
    
    # Priority 2: Status text
    if status:
        s = status.lower()
        if "chose to field" in s or "elected to field" in s:
            # figure out who chose
            for team in [t1, t2]:
                if team.lower() in s:
                    fld_team = team
                    bat_team = t2 if team == t1 else t1
                    break
        elif "chose to bat" in s or "elected to bat" in s:
            for team in [t1, t2]:
                if team.lower() in s:
                    bat_team = team
                    fld_team = t2 if team == t1 else t1
                    break
    
    # Priority 3: Score pattern - if 2 scores, we're in 2nd innings
    if len(score_matches) >= 2:
        second_innings = True
    
    return bat_team, fld_team, second_innings


def _build_team_dict(short, score_str="0", overs_str="0.0", wickets=0):
    runs, wkts = _parse_score_str(score_str) if "/" in str(score_str) else (int(score_str) if str(score_str).isdigit() else 0, wickets)
    overs = _float(overs_str)
    rr = round(runs / overs, 2) if overs > 0 else 0.0
    return {
        "name": short, "short": short,
        "score": str(runs), "wickets": str(wkts), "overs": overs_str,
        "rr": str(rr),
        "_r": runs, "_w": wkts, "_o": overs
    }


def _build_sc_from_cricbuzz(cb):
    """Build full sc dict from cricbuzz parsed data."""
    t1, t2 = cb["t1"], cb["t2"]
    toss_info = cb.get("toss_info")
    score_matches = cb.get("score_matches", [])
    status = cb.get("status", "")
    is_live = cb.get("is_live", False)
    
    bat_team, fld_team, second_innings = _determine_batting_bowling(t1, t2, toss_info, score_matches, status)
    
    # Determine phase
    if not is_live and not score_matches:
        phase = "pre_match"
    elif toss_info and not score_matches:
        phase = "toss"
    else:
        # Estimate from overs
        overs_f = 0.0
        if score_matches:
            overs_f = _float(score_matches[-1][1]) if score_matches else 0.0
        phase = _phase_from_overs(overs_f)
    
    # Build score strings
    if score_matches:
        if second_innings and len(score_matches) >= 2:
            # First innings complete
            fld_score = score_matches[0][0]  # completed innings
            bat_score = score_matches[1][0]  # current innings
            bat_overs = score_matches[1][1]
            fld_overs = "20.0"
            target_runs, _ = _parse_score_str(fld_score)
            target = target_runs + 1
        else:
            bat_score = score_matches[0][0] if score_matches else "0/0"
            bat_overs = score_matches[0][1] if score_matches else "0.0"
            fld_score = "—"
            fld_overs = "0.0"
            target = 0
    else:
        bat_score = "0/0"
        bat_overs = "0.0"
        fld_score = "—"
        fld_overs = "0.0"
        target = 0
    
    bat = _build_team_dict(bat_team, bat_score, bat_overs)
    fld = _build_team_dict(fld_team, fld_score if fld_score != "—" else "0", fld_overs)
    
    venue = VENUES.get(t1, VENUES.get(t2, "TBD Stadium"))
    
    # Win probability heuristic
    if second_innings and target > 0:
        runs_done = bat["_r"]
        balls_done = int(bat["_o"]) * 6 + round((bat["_o"] % 1) * 10)
        balls_left = max(1, 120 - balls_done)
        runs_needed = target - runs_done
        req_rr = round(runs_needed / (balls_left / 6), 2) if balls_left > 0 else 99
        bat_wp = max(5, min(95, 50 + (target/2 - runs_needed) * 0.8))
        fld_wp = 100 - bat_wp
    else:
        runs_needed = 0
        req_rr = 0.0
        balls_left = 120 - int(_float(bat_overs) * 6)
        bat_wp = 50
        fld_wp = 50
    
    # Status text
    if toss_info:
        toss_txt = toss_info.get("raw", "")
        # Build nice status
        winner = toss_info["team"]
        choice = toss_info["choice"]
        full_name_map = {v:k.title() for k,v in TEAM_MAP.items() if len(k.split())>1}
        status = f"{full_name_map.get(winner, winner)} won the toss and chose to {choice}"
    
    sc = {
        "match": f"{t1} vs {t2}", "venue": venue, "status": status,
        "bat": bat, "field": fld, "t1": bat, "t2": fld,
        "target": target, "required": runs_needed, "req_rr": req_rr,
        "balls_left": balls_left,
        "phase": phase,
        "second_innings": second_innings,
        "bat_wp": round(bat_wp), "fld_wp": round(fld_wp),
        "recent_balls": [], "drs": {"bat": 2, "fld": 2},
        "impact": {"bat": "Available", "fld": "Available"},
        "toss_info": toss_info,
    }
    
    # Try to get deeper match data
    batters, bowlers = [], []
    if cb.get("match_url") and is_live:
        deep = scrape_cricbuzz_match_page(cb["match_url"])
        batters = deep.get("batters", [])
        bowlers = deep.get("bowlers", [])
        if deep.get("recent_balls"):
            sc["recent_balls"] = deep["recent_balls"]
    
    return sc, batters, bowlers, {}, {}


def _build_sc_simple(t1, t2, status, scores):
    """Build minimal sc when only teams and rough status are known."""
    venue = VENUES.get(t1, VENUES.get(t2, "TBD Stadium"))
    bat = _build_team_dict(t1)
    fld = _build_team_dict(t2)
    
    toss_info = None
    if "field" in status.lower() or "bowl" in status.lower():
        # t1 chose to field → t2 batting
        bat, fld = _build_team_dict(t2), _build_team_dict(t1)
        toss_info = {"team": t1, "choice": "field", "raw": status}
    elif "bat" in status.lower():
        toss_info = {"team": t1, "choice": "bat", "raw": status}
    
    sc = {
        "match": f"{t1} vs {t2}", "venue": venue, "status": status,
        "bat": bat, "field": fld, "t1": bat, "t2": fld,
        "target": 0, "required": 0, "req_rr": 0.0, "balls_left": 120,
        "phase": "toss", "second_innings": False, "bat_wp": 50, "fld_wp": 50,
        "recent_balls": [], "drs": {"bat": 2, "fld": 2},
        "impact": {"bat": "Available", "fld": "Available"},
        "toss_info": toss_info,
    }
    return sc, [], [], {}, {}


def _build_sc_waiting():
    """No live IPL match found."""
    sc = {
        "match": "Awaiting IPL Match", "venue": "TBD", "status": "No live IPL match right now",
        "bat": _build_team_dict("TBA"), "field": _build_team_dict("TBA"),
        "t1": _build_team_dict("TBA"), "t2": _build_team_dict("TBA"),
        "target": 0, "required": 0, "req_rr": 0.0, "balls_left": 120,
        "phase": "pre_match", "second_innings": False, "bat_wp": 50, "fld_wp": 50,
        "recent_balls": [], "drs": {"bat": 2, "fld": 2},
        "impact": {"bat": "Available", "fld": "Available"},
        "toss_info": None,
    }
    return sc, [], [], {}, {}


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _c(s): return TEAM_COLORS.get(s, "#64748B")

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


# ══════════════════════════════════════════════════════════════════════════════
# AI / COMMENTARY
# ══════════════════════════════════════════════════════════════════════════════

def _call_claude(prompt, system_msg="", max_tokens=350):
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    if not api_key: return None
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": "claude-3-haiku-20240307", "max_tokens": max_tokens,
                  "messages": [{"role": "user", "content": prompt}], "system": system_msg},
            timeout=8)
        if r.status_code == 200: return r.json()["content"][0]["text"]
    except: pass
    return None

def _fallback_commentary(sc):
    phase = sc["phase"]
    t_info = sc.get("toss_info")
    
    if phase == "pre_match":
        return f"Welcome to GOD'S EYE. No live IPL match detected at the moment. Dashboard will auto-update when a match goes live."
    
    if phase == "toss":
        toss_str = t_info["raw"] if t_info else sc["status"]
        bat = sc["bat"]["short"]
        fld = sc["field"]["short"]
        return (f"📍 We are at {sc['venue']}. {toss_str}. "
                f"{bat} will be opening the batting. {fld} take the field. "
                f"Both camps are finalizing their Playing XI. "
                f"Expect a cracking contest at this venue where the average first innings score is around "
                f"{PITCH_DNA.get(_get_city(sc['venue']),{}).get('avg_1st',170)} runs!")
    
    bat = sc["bat"]
    return (f"{bat['short']} are currently {bat['score']}/{bat['wickets']} in {bat['overs']} overs "
            f"(RR: {bat['rr']}). The match is in the {phase} phase. "
            f"{'The chase is on!' if sc['second_innings'] else 'First innings in progress.'}")


def _build_oracle_prompt(sc, batters, bowlers):
    bat = sc["bat"]
    fld = sc["field"]
    venue = sc["venue"]
    city = _get_city(venue)
    pitch = PITCH_DNA.get(city, {})
    
    phase = sc["phase"]
    if phase == "toss":
        return (f"IPL 2026 match at {venue}. {sc['status']}. "
                f"{bat['short']} batting first vs {fld['short']}. "
                f"Pitch: avg 1st innings score {pitch.get('avg_1st','170')}, "
                f"chase win% {pitch.get('chase_win_pct','50')}%. "
                f"Give a 3-sentence pre-match strategic analysis covering toss decision, key battles to watch, "
                f"and your prediction. Use broadcast style.")
    
    ctx_parts = [
        f"LIVE: {bat['short']} {bat['score']}/{bat['wickets']} ({bat['overs']} ov, RR {bat['rr']})",
        f"Phase: {phase}",
        f"Venue: {venue}",
    ]
    if sc["second_innings"]:
        ctx_parts.append(f"Target: {sc['target']}, Need: {sc['required']} in {sc['balls_left']//6}.{sc['balls_left']%6} ov (Req RR: {sc['req_rr']})")
    if batters:
        bat_str = ', '.join([b["name"] + " " + str(b["runs"]) + "(" + str(b["balls"]) + ")" for b in batters])
        ctx_parts.append("Batters: " + bat_str)
    if bowlers:
        bwl_str = ', '.join([b["name"] + " " + str(b["overs"]) + "ov " + str(b["wkts"]) + "w" for b in bowlers])
        ctx_parts.append("Bowlers: " + bwl_str)
    
    return ". ".join(ctx_parts) + ". Give a 3-sentence broadcast commentary update with tactical insight."


# ══════════════════════════════════════════════════════════════════════════════
# MONTE CARLO
# ══════════════════════════════════════════════════════════════════════════════

def run_monte_carlo(balls_left, runs_needed, wkts_left, phase, n=3000, first_innings=False, curr_score=0):
    if first_innings:
        score_dist = []
        for _ in range(n):
            bl = balls_left; wl = wkts_left; scored = curr_score
            while bl > 0 and wl > 0:
                r = random.random()
                if r < 0.05: wl -= 1
                elif r < 0.20: scored += 4
                elif r < 0.30: scored += 6
                elif r < 0.55: scored += 1
                elif r < 0.65: scored += 2
                bl -= 1
            score_dist.append(scored)
        return 50, 50, score_dist
    else:
        wins = 0; score_dist = []
        for _ in range(n):
            bl = balls_left; wl = wkts_left; rn = runs_needed; scored = 0
            while bl > 0 and wl > 0 and rn > 0:
                r = random.random()
                if r < 0.07: wl -= 1
                elif r < 0.20: rn -= 4; scored += 4
                elif r < 0.30: rn -= 6; scored += 6
                elif r < 0.55: rn -= 1; scored += 1
                elif r < 0.65: rn -= 2; scored += 2
                bl -= 1
            if rn <= 0: wins += 1
            score_dist.append(scored)
        return round(wins/n*100), 100 - round(wins/n*100), score_dist


def chart_monte_carlo(score_dist, runs_needed, first_innings=False):
    if not score_dist: return go.Figure()
    buckets = {}
    for s in score_dist:
        b = (s // 5) * 5
        buckets[b] = buckets.get(b, 0) + 1
    xs = sorted(buckets.keys())
    ys = [buckets[x] for x in xs]
    if first_innings:
        colors = ["#1D4ED8" for _ in xs]
        line_txt = "Avg Projected"
        mark_val = sum(score_dist) // len(score_dist) if score_dist else 165
    else:
        colors = ["#16A34A" if x >= runs_needed else "#DC2626" for x in xs]
        line_txt = f"Target {runs_needed}"
        mark_val = runs_needed
    fig = go.Figure(go.Bar(x=xs, y=ys, marker_color=colors, opacity=0.8))
    fig.add_vline(x=mark_val, line_dash="dot", line_color="#1E293B", line_width=2,
                  annotation_text=line_txt, annotation_position="top right")
    fig.update_layout(**_layout(title=dict(text="MONTE CARLO PROJECTIONS", font=dict(size=11), x=0),
                                height=240, xaxis=_ax("Runs"), yaxis=_ax("Simulations")))
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# VENUE HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _get_city(venue):
    for full_v, city in VENUE_CITY.items():
        if full_v.lower() in venue.lower():
            return city
    # fallback: last part after comma
    if "," in venue:
        return venue.split(",")[-1].strip()
    return venue


# ══════════════════════════════════════════════════════════════════════════════
# TAB RENDERERS
# ══════════════════════════════════════════════════════════════════════════════

def render_live_tab(sc, batters, bowlers):
    c1, c2, c3 = st.columns([5, 4, 5])
    bat = sc["bat"]
    fld = sc["field"]
    bc = _c(bat["short"])
    fc = _c(fld["short"])
    phase = sc["phase"]
    
    # ── SCORE HEADER ──
    with c1:
        batting_label = "▶ BATTING FIRST" if not sc["second_innings"] else "▶ BATTING (2nd INN)"
        score_display = f'{bat["score"]}/{bat["wickets"]}' if bat["score"] != "0" or phase not in ("pre_match","toss") else bat["short"]
        detail = f'{bat["overs"]} ov · RR {bat["rr"]}' if phase not in ("pre_match","toss") else "Yet to bat"
        st.markdown(f'<div class="score-card" style="border-left:4px solid {bc}">'
                    f'<div class="team-badge" style="color:{bc}">{batting_label}</div>'
                    f'<div class="score-big" style="color:{bc}">{score_display}</div>'
                    f'<div class="score-detail">{detail}</div></div>', unsafe_allow_html=True)
    
    with c2:
        # Middle card - toss/status
        toss_txt = ""
        if sc.get("toss_info"):
            ti = sc["toss_info"]
            toss_txt = f'<div style="margin-top:8px"><span class="ph-toss">🪙 TOSS</span> <span style="font-size:12px;color:#374151">{ti.get("raw","")}</span></div>'
        
        if sc["second_innings"] and sc["target"]:
            mid_content = (f'<div style="font-size:14px;font-weight:800;color:#D97706;letter-spacing:1px;margin-bottom:6px">TARGET</div>'
                           f'<div style="font-size:36px;font-weight:800;color:#1E293B;line-height:1">{sc["target"]}</div>'
                           f'<div style="font-size:12px;color:#64748B;margin-top:4px">Need {sc["required"]} in {sc["balls_left"]//6}.{sc["balls_left"]%6} ov</div>'
                           f'<div style="font-size:13px;font-weight:700;color:#DC2626;margin-top:4px">Req RR: {sc["req_rr"]}</div>')
        else:
            mid_content = (f'<div style="font-size:14px;font-weight:800;color:#D97706;letter-spacing:1px;margin-bottom:10px">MATCH STATUS</div>'
                           f'<div style="font-size:14px;font-weight:700;color:#1E293B">{sc["status"]}</div>'
                           f'{toss_txt}')
        
        st.markdown(f'<div class="score-card" style="text-align:center">{mid_content}</div>', unsafe_allow_html=True)
    
    with c3:
        bowling_label = "⚡ BOWLING FIRST" if not sc["second_innings"] else f"⚡ {fld['short']} (1ST INN)"
        fld_score = f'{fld["score"]}/{fld["wickets"]}' if sc["second_innings"] else fld["short"]
        fld_detail = f'{fld["overs"]} ov · RR {fld["rr"]}' if sc["second_innings"] else "Taking the field"
        st.markdown(f'<div class="score-card" style="border-left:4px solid {fc}">'
                    f'<div class="team-badge" style="color:{fc}">{bowling_label}</div>'
                    f'<div class="score-big" style="color:{fc}">{fld_score}</div>'
                    f'<div class="score-detail">{fld_detail}</div></div>', unsafe_allow_html=True)
    
    # ── WIN PROBABILITY BAR ──
    if phase not in ("pre_match",):
        st.markdown('<div style="margin:14px 0 4px;font-size:10px;font-weight:700;letter-spacing:1px;color:#94A3B8;text-transform:uppercase">WIN PROBABILITY</div>', unsafe_allow_html=True)
        bwp = sc.get("bat_wp", 50)
        fwp = sc.get("fld_wp", 50)
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px">'
            f'<span style="font-size:12px;font-weight:700;color:{bc};min-width:60px">{bat["short"]} {bwp}%</span>'
            f'<div style="flex:1;height:10px;border-radius:5px;overflow:hidden;background:#E2E8F0">'
            f'<div style="width:{bwp}%;height:100%;background:{bc};border-radius:5px"></div></div>'
            f'<span style="font-size:12px;font-weight:700;color:{fc};min-width:60px;text-align:right">{fwp}% {fld["short"]}</span>'
            f'</div>', unsafe_allow_html=True)
    
    # ── LIVE SCORECARD (if active) ──
    if phase not in ("pre_match", "toss"):
        if batters:
            st.markdown('<div class="sh" style="margin-top:18px">🏏 AT THE CREASE</div>', unsafe_allow_html=True)
            cols_hdr = st.columns([4,1,1,1,1,2])
            for h, c in zip(["BATTER","R","B","4s","6s","SR"], cols_hdr):
                c.markdown(f'<div style="font-size:10px;font-weight:700;color:#94A3B8;letter-spacing:1px">{h}</div>', unsafe_allow_html=True)
            for b in batters:
                cols = st.columns([4,1,1,1,1,2])
                cols[0].markdown(f'<span class="player-name">{b["name"]}</span>', unsafe_allow_html=True)
                cols[1].markdown(f'<b style="color:#16A34A">{b["runs"]}</b>', unsafe_allow_html=True)
                cols[2].write(b["balls"])
                cols[3].write(b.get("fours",0))
                cols[4].write(b.get("sixes",0))
                cols[5].write(b.get("sr",0.0))
        
        if bowlers:
            st.markdown('<div class="sh">⚡ BOWLING</div>', unsafe_allow_html=True)
            cols_hdr = st.columns([4,1,1,1,1,2])
            for h, c in zip(["BOWLER","O","M","R","W","ECON"], cols_hdr):
                c.markdown(f'<div style="font-size:10px;font-weight:700;color:#94A3B8;letter-spacing:1px">{h}</div>', unsafe_allow_html=True)
            for bw in bowlers:
                cols = st.columns([4,1,1,1,1,2])
                cols[0].markdown(f'<span class="player-name">{bw["name"]}</span>', unsafe_allow_html=True)
                cols[1].write(bw.get("overs",0))
                cols[2].write(bw.get("maidens",0))
                cols[3].write(bw.get("runs",0))
                cols[4].markdown(f'<b style="color:#DC2626">{bw.get("wkts",0)}</b>', unsafe_allow_html=True)
                cols[5].write(bw.get("econ",0.0))
    
    elif phase == "toss":
        # Pre-match rich preview
        st.markdown('<div class="sh" style="margin-top:20px">⏳ PRE-MATCH — SQUAD SNAPSHOT</div>', unsafe_allow_html=True)
        t1_squad = SQUAD_DB.get(bat["short"], [])
        t2_squad = SQUAD_DB.get(fld["short"], [])
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="intel-card"><div class="intel-title">{bat["short"]} — LIKELY XI</div>'
                        + "".join([f'<div class="player-row"><div class="player-dot"></div><div><div class="player-name-big">{p}</div></div></div>' for p in t1_squad[:11]])
                        + '</div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="intel-card"><div class="intel-title">{fld["short"]} — LIKELY XI</div>'
                        + "".join([f'<div class="player-row"><div class="player-dot" style="background:#F59E0B"></div><div><div class="player-name-big">{p}</div></div></div>' for p in t2_squad[:11]])
                        + '</div>', unsafe_allow_html=True)
    
    else:
        # pre_match
        st.markdown('<div class="pre-match-card" style="margin-top:20px"><h2>🔴 Waiting for next IPL match...</h2>'
                    '<p>Dashboard will auto-update the moment toss happens and match goes live.</p></div>', unsafe_allow_html=True)


def render_oracle_tab(sc, batters, bowlers):
    st.markdown('<div class="sh">🎤 LIVE AI COMMENTARY & ANALYSIS</div>', unsafe_allow_html=True)
    
    api_key_check = st.secrets.get("ANTHROPIC_API_KEY", "")
    if api_key_check:
        prompt = _build_oracle_prompt(sc, batters, bowlers)
        com = _call_claude(prompt, "You are an expert IPL cricket commentator and tactician. Be specific, insightful, and use cricket jargon naturally.", 300)
        com = com if com else _fallback_commentary(sc)
        src_label = "Claude AI Active" if com != _fallback_commentary(sc) else "Local Engine"
    else:
        com = _fallback_commentary(sc)
        src_label = "Local Engine Active"
    
    st.markdown(f'<div class="commentary-box"><div style="font-size:10px;color:#38BDF8;font-weight:700;letter-spacing:1px;margin-bottom:12px">▶ AI COMMENTARY ({src_label})</div><div style="font-size:15px;line-height:1.75;color:#F1F5F9">{com}</div></div>', unsafe_allow_html=True)
    
    # Key Battles
    st.markdown('<div class="sh" style="margin-top:20px">⚔️ KEY BATTLES</div>', unsafe_allow_html=True)
    bat_t = sc["bat"]["short"]
    fld_t = sc["field"]["short"]
    
    key_bats = KEY_BATTERS.get(bat_t, [])
    key_bwls = KEY_BOWLERS.get(fld_t, [])
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="oracle-box"><h3>⚡ {bat_t} — BATTING THREATS</h3>'
                    + "".join([f'<div style="padding:8px 0;border-bottom:1px solid #334155"><div style="font-weight:700;font-size:14px">{b[0]}</div><div style="font-size:12px;color:#94A3B8;margin-top:3px">{b[1].lstrip("+")}</div></div>' for b in key_bats[:3]])
                    + '</div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="oracle-box"><h3>🎯 {fld_t} — BOWLING THREATS</h3>'
                    + "".join([f'<div style="padding:8px 0;border-bottom:1px solid #334155"><div style="font-weight:700;font-size:14px">{b[0]}</div><div style="font-size:12px;color:#94A3B8;margin-top:3px">{b[1].lstrip("+")}</div></div>' for b in key_bwls[:3]])
                    + '</div>', unsafe_allow_html=True)
    
    # Head to Head
    h2h_key = frozenset([bat_t, fld_t])
    h2h = HEAD2HEAD.get(h2h_key)
    if h2h:
        st.markdown('<div class="sh" style="margin-top:20px">📊 HEAD-TO-HEAD RECORD</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        for col, team in zip([c1, c2], [bat_t, fld_t]):
            rec = h2h.get(team, {})
            col.markdown(f'<div class="card" style="text-align:center">'
                         f'<div style="font-size:22px;font-weight:800;color:{_c(team)}">{team}</div>'
                         f'<div style="font-size:36px;font-weight:800;color:#1E293B">{rec.get("w","—")}</div>'
                         f'<div style="font-size:10px;color:#94A3B8;letter-spacing:1px">WINS vs OPPONENT</div>'
                         f'<div style="font-size:11px;color:#64748B;margin-top:8px">{rec.get("last_result","—")}</div>'
                         f'</div>', unsafe_allow_html=True)


def render_prediction_lab(sc):
    st.markdown('<div class="sh">🎲 MONTE CARLO MATCH SIMULATOR</div>', unsafe_allow_html=True)
    
    bat = sc["bat"]
    phase = sc["phase"]
    
    if phase == "pre_match":
        st.markdown('<div class="pre-match-card"><h3>Awaiting match data to run simulations...</h3></div>', unsafe_allow_html=True)
        return
    
    if not sc["second_innings"]:
        # First innings projections
        curr_score = bat["_r"]
        balls_bowled = int(bat["_o"]) * 6 + round((bat["_o"] % 1) * 10)
        balls_left = max(1, 120 - balls_bowled)
        wkts_left = 10 - bat["_w"]
        
        with st.spinner("Running 3,000 First Innings Simulations..."):
            _, _, dist = run_monte_carlo(balls_left, 0, wkts_left, phase, n=3000, first_innings=True, curr_score=curr_score)
            avg = sum(dist) // len(dist) if dist else 165
        
        city = _get_city(sc["venue"])
        pitch = PITCH_DNA.get(city, {})
        pitch_avg = pitch.get("avg_1st", 170)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="mc-result-box" style="border-top:4px solid #1D4ED8">'
                        f'<div style="font-size:11px;color:#94A3B8;font-weight:700;letter-spacing:1px;margin-bottom:6px">PROJECTED SCORE</div>'
                        f'<div style="font-size:48px;font-weight:800;color:#1D4ED8;line-height:1">{avg}</div>'
                        f'<div style="font-size:11px;color:#64748B;margin-top:4px">Based on 3,000 simulations</div>'
                        f'</div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="mc-result-box" style="border-top:4px solid #D97706">'
                        f'<div style="font-size:11px;color:#94A3B8;font-weight:700;letter-spacing:1px;margin-bottom:6px">VENUE AVERAGE (1st INN)</div>'
                        f'<div style="font-size:48px;font-weight:800;color:#D97706;line-height:1">{pitch_avg}</div>'
                        f'<div style="font-size:11px;color:#64748B;margin-top:4px">{city} ground average</div>'
                        f'</div>', unsafe_allow_html=True)
        with c3:
            delta = avg - pitch_avg
            color = "#16A34A" if delta > 0 else "#DC2626"
            st.markdown(f'<div class="mc-result-box" style="border-top:4px solid {color}">'
                        f'<div style="font-size:11px;color:#94A3B8;font-weight:700;letter-spacing:1px;margin-bottom:6px">vs VENUE AVERAGE</div>'
                        f'<div style="font-size:48px;font-weight:800;color:{color};line-height:1">{("+" if delta>=0 else "")}{delta}</div>'
                        f'<div style="font-size:11px;color:#64748B;margin-top:4px">{"Above" if delta>=0 else "Below"} par</div>'
                        f'</div>', unsafe_allow_html=True)
        
        st.plotly_chart(chart_monte_carlo(dist, 0, first_innings=True), use_container_width=True, config={"displayModeBar": False})
    
    else:
        # Second innings chase simulation
        runs_needed = sc["required"]
        balls_left = sc["balls_left"]
        wkts_left = max(1, 10 - bat["_w"])
        
        with st.spinner("Running Chase Simulations..."):
            chase_wp, def_wp, dist = run_monte_carlo(balls_left, runs_needed, wkts_left, phase, n=3000)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            color = "#16A34A" if chase_wp > 55 else ("#D97706" if chase_wp > 40 else "#DC2626")
            st.markdown(f'<div class="mc-result-box" style="border-top:4px solid {color}">'
                        f'<div style="font-size:11px;color:#94A3B8;font-weight:700;letter-spacing:1px;margin-bottom:6px">CHASE WIN %</div>'
                        f'<div style="font-size:48px;font-weight:800;color:{color};line-height:1">{chase_wp}%</div>'
                        f'<div style="font-size:11px;color:#64748B;margin-top:4px">{bat["short"]} to win</div>'
                        f'</div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="mc-result-box" style="border-top:4px solid #DC2626">'
                        f'<div style="font-size:11px;color:#94A3B8;font-weight:700;letter-spacing:1px;margin-bottom:6px">RUNS NEEDED</div>'
                        f'<div style="font-size:48px;font-weight:800;color:#DC2626;line-height:1">{runs_needed}</div>'
                        f'<div style="font-size:11px;color:#64748B;margin-top:4px">off {balls_left//6}.{balls_left%6} overs</div>'
                        f'</div>', unsafe_allow_html=True)
        with c3:
            rr_color = "#16A34A" if sc["req_rr"] < 9 else ("#D97706" if sc["req_rr"] < 12 else "#DC2626")
            st.markdown(f'<div class="mc-result-box" style="border-top:4px solid {rr_color}">'
                        f'<div style="font-size:11px;color:#94A3B8;font-weight:700;letter-spacing:1px;margin-bottom:6px">REQUIRED RR</div>'
                        f'<div style="font-size:48px;font-weight:800;color:{rr_color};line-height:1">{sc["req_rr"]}</div>'
                        f'<div style="font-size:11px;color:#64748B;margin-top:4px">{"Achievable" if sc["req_rr"] < 10 else "Stiff ask"}</div>'
                        f'</div>', unsafe_allow_html=True)
        
        st.plotly_chart(chart_monte_carlo(dist, runs_needed, first_innings=False), use_container_width=True, config={"displayModeBar": False})


def render_player_intel(sc):
    st.markdown('<div class="sh">🛡️ MATCH PLAYER INTELLIGENCE</div>', unsafe_allow_html=True)
    
    bat_t = sc["bat"]["short"]
    fld_t = sc["field"]["short"]
    bc = _c(bat_t)
    fc = _c(fld_t)
    
    if bat_t == "TBA":
        st.markdown('<div class="pre-match-card"><h3>Player intel will load when match teams are detected.</h3></div>', unsafe_allow_html=True)
        return
    
    # KEY BATTERS
    st.markdown(f'<div class="sh">🏏 KEY BATTERS — {bat_t}</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    bats = KEY_BATTERS.get(bat_t, [])
    for col, batter in zip([c1,c2,c3], bats[:3]):
        col.markdown(f'<div class="intel-card" style="border-top:3px solid {bc}">'
                     f'<div style="font-size:15px;font-weight:700;color:#1E293B">{batter[0]}</div>'
                     f'<div style="font-size:12px;color:#64748B;margin-top:6px;line-height:1.6">{batter[1].lstrip("+")}</div>'
                     f'</div>', unsafe_allow_html=True)
    
    # KEY BOWLERS
    st.markdown(f'<div class="sh">🎯 KEY BOWLERS — {fld_t}</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    bwls = KEY_BOWLERS.get(fld_t, [])
    for col, bowler in zip([c1,c2,c3], bwls[:3]):
        col.markdown(f'<div class="intel-card" style="border-top:3px solid {fc}">'
                     f'<div style="font-size:15px;font-weight:700;color:#1E293B">{bowler[0]}</div>'
                     f'<div style="font-size:12px;color:#64748B;margin-top:6px;line-height:1.6">{bowler[1].lstrip("+")}</div>'
                     f'</div>', unsafe_allow_html=True)
    
    # KEY MATCHUPS
    st.markdown('<div class="sh" style="margin-top:20px">⚡ CRITICAL MATCHUPS TO WATCH</div>', unsafe_allow_html=True)
    matchups = []
    for bat_p in bats[:2]:
        for bowl_p in bwls[:2]:
            matchups.append((bat_p[0], bowl_p[0]))
    
    c1, c2 = st.columns(2)
    for i, (batter, bowler) in enumerate(matchups[:4]):
        col = c1 if i % 2 == 0 else c2
        col.markdown(f'<div class="dna-card">'
                     f'<div style="display:flex;justify-content:space-between;align-items:center">'
                     f'<span style="font-weight:700;color:{bc}">{batter}</span>'
                     f'<span style="font-size:11px;font-weight:700;color:#94A3B8">vs</span>'
                     f'<span style="font-weight:700;color:{fc}">{bowler}</span>'
                     f'</div>'
                     f'<div style="font-size:11px;color:#64748B;margin-top:5px">Watch this battle — could decide the match</div>'
                     f'</div>', unsafe_allow_html=True)
    
    # Squad list
    st.markdown('<div class="sh" style="margin-top:20px">📋 FULL SQUADS</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        squad = SQUAD_DB.get(bat_t, [])
        st.markdown(f'<div class="intel-card"><div class="intel-title">{bat_t} — SQUAD</div>'
                    + "".join([f'<div class="player-row"><div class="player-dot" style="background:{bc}"></div><div class="player-name-big">{p}</div></div>' for p in squad])
                    + '</div>', unsafe_allow_html=True)
    with c2:
        squad = SQUAD_DB.get(fld_t, [])
        st.markdown(f'<div class="intel-card"><div class="intel-title">{fld_t} — SQUAD</div>'
                    + "".join([f'<div class="player-row"><div class="player-dot" style="background:{fc}"></div><div class="player-name-big">{p}</div></div>' for p in squad])
                    + '</div>', unsafe_allow_html=True)


def render_ground_context(sc):
    st.markdown('<div class="sh">📍 LIVE VENUE INTELLIGENCE</div>', unsafe_allow_html=True)
    
    venue = sc["venue"]
    city = _get_city(venue)
    pitch = PITCH_DNA.get(city, {
        "avg_1st":170,"avg_2nd":155,"chase_win_pct":48,
        "pace_friendly":True,"spin_friendly":False,"dew_factor":"Moderate",
        "notes":"Data being loaded for this venue."
    })
    
    if venue == "TBD":
        st.markdown('<div class="pre-match-card"><h3>Venue info will appear once match teams are detected.</h3></div>', unsafe_allow_html=True)
        return
    
    # Venue header
    st.markdown(f'<div class="venue-big-card">'
                f'<div style="font-size:10px;opacity:0.6;letter-spacing:2px;text-transform:uppercase;margin-bottom:4px">HOST VENUE</div>'
                f'<div style="font-size:22px;font-weight:800">{venue}</div>'
                f'<div style="font-size:12px;opacity:0.7;margin-top:4px">{city}, India</div>'
                f'<div class="pitch-grid" style="margin-top:16px">'
                f'<div class="pitch-tile"><div class="pitch-tile-val">{pitch["avg_1st"]}</div><div class="pitch-tile-lbl">AVG 1ST INN</div></div>'
                f'<div class="pitch-tile"><div class="pitch-tile-val">{pitch["avg_2nd"]}</div><div class="pitch-tile-lbl">AVG 2ND INN</div></div>'
                f'<div class="pitch-tile"><div class="pitch-tile-val">{pitch["chase_win_pct"]}%</div><div class="pitch-tile-lbl">CHASE WIN %</div></div>'
                f'</div>'
                f'<div style="margin-top:14px;font-size:13px;line-height:1.7;opacity:0.85">{pitch["notes"]}</div>'
                f'</div>', unsafe_allow_html=True)
    
    # Weather
    wx = fetch_weather(city)
    st.markdown('<div class="sh">🌤️ LIVE WEATHER CONDITIONS</div>', unsafe_allow_html=True)
    
    if wx["ok"]:
        st.markdown(f'<div class="dew-box">'
                    f'<div style="font-size:11px;opacity:0.7;letter-spacing:1.5px;font-weight:700;margin-bottom:10px">CURRENT CONDITIONS — {city.upper()}</div>'
                    f'<div class="wx-row">'
                    f'<div class="wx-tile"><div style="font-size:28px;font-weight:800">{wx["temp"]}°C</div><div style="font-size:10px;opacity:0.7;letter-spacing:1px">TEMPERATURE</div></div>'
                    f'<div class="wx-tile"><div style="font-size:28px;font-weight:800">{wx["humidity"]}%</div><div style="font-size:10px;opacity:0.7;letter-spacing:1px">HUMIDITY</div></div>'
                    f'<div class="wx-tile"><div style="font-size:28px;font-weight:800">{wx["wind"]}</div><div style="font-size:10px;opacity:0.7;letter-spacing:1px">WIND (kmph)</div></div>'
                    f'<div class="wx-tile"><div style="font-size:20px;font-weight:800">{wx["dew_risk"]}</div><div style="font-size:10px;opacity:0.7;letter-spacing:1px">DEW RISK</div></div>'
                    f'</div>'
                    f'<div style="margin-top:12px;font-size:13px;opacity:0.9">{wx["desc"]} · Feels like {wx["feels"]}°C</div>'
                    f'</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="dew-box"><div style="font-size:14px;opacity:0.8">Weather data unavailable. Venue dew factor: <b>{pitch["dew_factor"]}</b> (historical)</div></div>', unsafe_allow_html=True)
    
    # Pitch analysis
    st.markdown('<div class="sh" style="margin-top:16px">🏏 PITCH ANALYSIS</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        pace_val = "✅ YES" if pitch.get("pace_friendly") else "❌ NO"
        st.markdown(f'<div class="card" style="text-align:center"><div style="font-size:10px;color:#94A3B8;font-weight:700;letter-spacing:1px">PACE FRIENDLY</div><div style="font-size:24px;font-weight:800;margin-top:6px">{pace_val}</div></div>', unsafe_allow_html=True)
    with c2:
        spin_val = "✅ YES" if pitch.get("spin_friendly") else "❌ NO"
        st.markdown(f'<div class="card" style="text-align:center"><div style="font-size:10px;color:#94A3B8;font-weight:700;letter-spacing:1px">SPIN FRIENDLY</div><div style="font-size:24px;font-weight:800;margin-top:6px">{spin_val}</div></div>', unsafe_allow_html=True)
    with c3:
        dew = pitch.get("dew_factor","Moderate")
        dew_color = "#DC2626" if dew=="High 🌫️" or dew=="High" else ("#D97706" if dew=="Moderate" else "#16A34A")
        st.markdown(f'<div class="card" style="text-align:center"><div style="font-size:10px;color:#94A3B8;font-weight:700;letter-spacing:1px">HISTORICAL DEW</div><div style="font-size:20px;font-weight:800;margin-top:6px;color:{dew_color}">{dew}</div></div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

sc, batters, bowlers, extras, partner = resolve_scraper()

# Navbar
now_str = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%d %b %Y · %H:%M IST")
phase_color = "#4ADE80" if sc["phase"] not in ("pre_match",) else "#94A3B8"
phase_label = {"toss":"🪙 TOSS", "powerplay":"⚡ POWERPLAY", "middle":"🎯 MIDDLE OVERS",
               "death":"🔥 DEATH OVERS", "pre_match":"⚪ PRE-MATCH"}.get(sc["phase"], sc["phase"].upper())

st.markdown(
    f'<div class="navbar">'
    f'<div><div class="navbar-logo">GOD\'S<span>EYE</span> v7.0 '
    f'<span style="font-size:11px;color:#94A3B8;font-weight:400">IPL MATCH CENTER</span></div>'
    f'<div class="navbar-sub"><span class="src-badge">{st.session_state.scraper_src}</span> '
    f'&nbsp;{sc.get("match","")} &nbsp; <span style="color:{phase_color};font-weight:700">{phase_label}</span></div>'
    f'</div>'
    f'<div class="navbar-right">{now_str}<br>'
    f'<span style="color:#4ADE80">Auto-Adapting Engine Active</span></div>'
    f'</div>',
    unsafe_allow_html=True
)

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔴 Live Match", "🧠 AI Oracle", "🎲 Prediction Lab",
    "🏏 Player Intel", "🏟️ Ground & Context"
])

with tab1: render_live_tab(sc, batters, bowlers)
with tab2: render_oracle_tab(sc, batters, bowlers)
with tab3: render_prediction_lab(sc)
with tab4: render_player_intel(sc)
with tab5: render_ground_context(sc)

# Auto-refresh
col_refresh, col_src = st.columns([3,1])
with col_refresh:
    auto = st.toggle("🔄 Auto-Refresh (15s)", value=True)
with col_src:
    st.markdown(f'<div style="font-size:10px;color:#94A3B8;margin-top:8px">Source: {st.session_state.scraper_src}</div>', unsafe_allow_html=True)

if auto:
    time.sleep(15)
    st.rerun()
