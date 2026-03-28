import streamlit as st
import requests
import feedparser

# --- TACTICAL CONFIG ---
st.set_page_config(page_title="GOD'S EYE COMMAND", layout="wide")

# CSS Branding (Dark War Room Aesthetic)
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #e0e0e0; }
    .box { background-color: #101010; border: 1px solid #222; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
    .score-large { font-size: 50px; font-weight: bold; color: white; }
    </style>
""", unsafe_allow_html=True)

# --- SENSORS: API CONNECTION ---
def fetch_live_match(api_key):
    url = "https://cricket-api-free-data.p.rapidapi.com/match/live-score"
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "cricket-api-free-data.p.rapidapi.com"
    }
    try:
        response = requests.get(url, headers=headers).json()
        # Grabbing the first live match data
        return response.get('data', [{}])[0]
    except:
        return None

# YOUR PRIVATE KEY (Extracted from your screenshot)
MY_KEY = "f26160eb44mshc0a20698180c97dp18f61ejsn98a8e23fdf41"

# --- MAIN DASHBOARD ---
st.markdown("<h1>👁️ GOD'S EYE <span style='color:#333'>|</span> TACTICAL COMMAND</h1>", unsafe_allow_html=True)

match = fetch_live_match(MY_KEY)

if match and match.get('score'):
    st.markdown("<div class='box'>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.write("LIVE SCORE")
        st.markdown(f"<span class='score-large'>{match.get('score')}</span>", unsafe_allow_html=True)
    with c2:
        st.write("OVERS")
        st.markdown(f"<span class='score-large'>{match.get('overs')}</span>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
else:
    # This will show until the match officially starts at 7:30 PM
    st.warning("📡 Awaiting Live Stream... RCB vs SRH starts tonight at 7:30 PM.")

# --- THE WIRE (LIVE NEWS SCANNER) ---
st.markdown("### 🚨 THE WIRE")
feed = feedparser.parse("https://news.google.com/rss/search?q=IPL+2026+injury&hl=en-IN&gl=IN&ceid=IN:en")
headlines = [e.title for e in feed.entries[:3]]
st.write(" | ".join(headlines) if headlines else "Scanning for intel...")