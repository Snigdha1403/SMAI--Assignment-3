import os
import re
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import feedparser
import requests
import streamlit as st
from groq import Groq
import pandas as pd

# ── Page config ─────────────────────────────────────────────
st.set_page_config(
    page_title="StockPulse — Market Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Clear cache to refresh categories
st.cache_data.clear()
st.cache_resource.clear()

# ── DARK TERMINAL CSS (from pro3) ────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;800&display=swap');

:root {
    --bg-deep:    #040d0a;
    --bg-card:    #071510;
    --bg-panel:   #0a1f18;
    --accent:     #00ff88;
    --accent-dim: #00b85c;
    --accent-glow:rgba(0,255,136,0.18);
    --red:        #ff4d6d;
    --yellow:     #ffd166;
    --blue:       #06d6f8;
    --text:       #c8ffe8;
    --muted:      #5a8a72;
    --border:     rgba(0,255,136,0.12);
    --font-mono:  'Space Mono', monospace;
    --font-ui:    'Syne', sans-serif;
}

/* ── Global ── */
html, body, [class*="css"] {
    background-color: var(--bg-deep) !important;
    color: var(--text) !important;
    font-family: var(--font-ui) !important;
}

/* Animated scanline overlay */
body::before {
    content: "";
    position: fixed;
    inset: 0;
    background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 2px,
        rgba(0,255,136,0.015) 2px,
        rgba(0,255,136,0.015) 4px
    );
    pointer-events: none;
    z-index: 9999;
}

/* ── Main container ── */
.main .block-container {
    padding: 2rem 2.5rem 3rem !important;
    max-width: 1400px;
}

/* ── Title banner ── */
.pulse-title {
    font-family: var(--font-ui);
    font-weight: 800;
    font-size: 2.8rem;
    letter-spacing: -0.03em;
    background: linear-gradient(90deg, var(--accent) 0%, var(--blue) 60%, var(--accent) 100%);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shimmer 4s linear infinite;
    margin: 0;
    line-height: 1;
}
@keyframes shimmer {
    0%   { background-position: 0% center; }
    100% { background-position: 200% center; }
}

.pulse-subtitle {
    font-family: var(--font-mono);
    font-size: 0.7rem;
    color: var(--muted);
    letter-spacing: 0.25em;
    text-transform: uppercase;
    margin-top: 0.4rem;
}

.title-bar {
    border-bottom: 1px solid var(--border);
    padding-bottom: 1.5rem;
    margin-bottom: 2rem;
    display: flex;
    align-items: flex-end;
    gap: 2rem;
}

/* Live dot */
.live-dot {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    font-family: var(--font-mono);
    font-size: 0.65rem;
    color: var(--accent);
    letter-spacing: 0.15em;
    margin-left: auto;
    padding-bottom: 0.2rem;
}
.live-dot::before {
    content: "";
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--accent);
    box-shadow: 0 0 8px var(--accent), 0 0 16px var(--accent);
    animation: blink 1.2s ease-in-out infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }

/* ── News Cards ── */
.news-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 6px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1.2rem;
    position: relative;
    transition: border-color 0.2s, box-shadow 0.2s, transform 0.15s;
    overflow: hidden;
}
.news-card::before {
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, var(--accent-glow) 0%, transparent 60%);
    opacity: 0;
    transition: opacity 0.25s;
}
.news-card:hover {
    border-color: var(--accent);
    box-shadow: 0 0 24px var(--accent-glow), 0 4px 20px rgba(0,0,0,0.6);
    transform: translateY(-2px);
}
.news-card:hover::before { opacity: 1; }

/* Bearish variant */
.news-card.bearish  { border-left-color: var(--red); }
.news-card.bearish::before  { background: linear-gradient(135deg, rgba(255,77,109,0.12) 0%, transparent 60%); }
.news-card.bearish:hover  { box-shadow: 0 0 24px rgba(255,77,109,0.2), 0 4px 20px rgba(0,0,0,0.6); }

/* Neutral/General variant */
.news-card.neutral,
.news-card.general  { border-left-color: var(--yellow); }
.news-card.neutral::before,
.news-card.general::before  { background: linear-gradient(135deg, rgba(255,209,102,0.10) 0%, transparent 60%); }
.news-card.neutral:hover,
.news-card.general:hover  { box-shadow: 0 0 24px rgba(255,209,102,0.15), 0 4px 20px rgba(0,0,0,0.6); }

.card-header {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 0.9rem;
}

/* Ticker badge */
.ticker-badge {
    font-family: var(--font-mono);
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    background: rgba(0,255,136,0.1);
    color: var(--accent);
    border: 1px solid rgba(0,255,136,0.3);
    border-radius: 3px;
    padding: 2px 8px;
    white-space: nowrap;
    flex-shrink: 0;
    margin-top: 2px;
}
.ticker-badge.na {
    color: var(--muted);
    background: rgba(90,138,114,0.08);
    border-color: rgba(90,138,114,0.2);
}

.card-title {
    font-family: var(--font-ui);
    font-weight: 600;
    font-size: 1rem;
    color: #e8fff4;
    line-height: 1.45;
    margin: 0;
}

/* Category pill */
.cat-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    font-family: var(--font-mono);
    font-size: 0.58rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 100px;
    margin-bottom: 0.85rem;
}
.cat-pill.bullish  { background:rgba(0,255,136,0.12); color:var(--accent);  border:1px solid rgba(0,255,136,0.25); }
.cat-pill.bearish  { background:rgba(255,77,109,0.12); color:var(--red);    border:1px solid rgba(255,77,109,0.25); }
.cat-pill.neutral  { background:rgba(255,209,102,0.10); color:var(--yellow); border:1px solid rgba(255,209,102,0.2); }

/* Summary block */
.summary-block {
    font-family: var(--font-mono);
    font-size: 0.72rem;
    line-height: 1.8;
    color: #8abfa0;
    border-left: 2px solid rgba(0,255,136,0.15);
    padding-left: 1rem;
    margin: 0.6rem 0 1rem;
    white-space: pre-line;
}

.card-footer {
    display: flex;
    align-items: center;
    gap: 1rem;
    border-top: 1px solid var(--border);
    padding-top: 0.75rem;
    margin-top: 0.5rem;
}

.source-tag {
    font-family: var(--font-mono);
    font-size: 0.6rem;
    color: var(--muted);
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

.read-link {
    font-family: var(--font-mono);
    font-size: 0.6rem;
    color: var(--accent-dim);
    letter-spacing: 0.08em;
    text-decoration: none;
    margin-left: auto;
    transition: color 0.15s;
}
.read-link:hover { color: var(--accent); }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--bg-panel) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * {
    color: var(--text) !important;
    font-family: var(--font-ui) !important;
}

.sidebar-logo {
    font-family: var(--font-ui);
    font-weight: 800;
    font-size: 1.3rem;
    color: var(--accent) !important;
    letter-spacing: -0.02em;
    border-bottom: 1px solid var(--border);
    padding-bottom: 1rem;
    margin-bottom: 1.2rem;
}

.sidebar-section {
    font-family: var(--font-mono);
    font-size: 0.6rem;
    color: var(--muted) !important;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin: 1.4rem 0 0.5rem;
}

/* Stats row */
.stats-row {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.8rem;
}
.stat-box {
    flex: 1;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.9rem 1rem;
    text-align: center;
}
.stat-val {
    font-family: var(--font-mono);
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--accent);
    display: block;
    line-height: 1;
    margin-bottom: 0.25rem;
}
.stat-val.red  { color: var(--red); }
.stat-val.blue { color: var(--blue); }
.stat-lbl {
    font-family: var(--font-mono);
    font-size: 0.58rem;
    color: var(--muted);
    letter-spacing: 0.12em;
    text-transform: uppercase;
}

/* Selectbox & multiselect override */
.stMultiSelect [data-baseweb="tag"] {
    background-color: rgba(0,255,136,0.15) !important;
    border: 1px solid rgba(0,255,136,0.3) !important;
    color: var(--accent) !important;
}
.stMultiSelect [data-baseweb="select"] > div,
.stSelectbox > div > div {
    background: var(--bg-deep) !important;
    border-color: var(--border) !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg-deep); }
::-webkit-scrollbar-thumb { background: var(--muted); border-radius: 10px; }

/* Loading spinner color */
.stSpinner > div { border-top-color: var(--accent) !important; }

/* Button */
.stButton > button {
    background: transparent !important;
    border: 1px solid var(--accent) !important;
    color: var(--accent) !important;
    font-family: var(--font-mono) !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.1em !important;
    border-radius: 4px !important;
    transition: background 0.2s !important;
}
.stButton > button:hover {
    background: rgba(0,255,136,0.1) !important;
}

/* ── Ticker Tape ── */
.ticker-tape-wrapper {
    position: relative;
    width: 100%;
    background: var(--bg-panel);
    border-top: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
    overflow: hidden;
    height: 42px;
    display: flex;
    align-items: center;
    margin-bottom: 2rem;
}

/* Edge fade masks */
.ticker-tape-wrapper::before,
.ticker-tape-wrapper::after {
    content: "";
    position: absolute;
    top: 0; bottom: 0;
    width: 80px;
    z-index: 2;
    pointer-events: none;
}
.ticker-tape-wrapper::before {
    left: 0;
    background: linear-gradient(to right, var(--bg-panel), transparent);
}
.ticker-tape-wrapper::after {
    right: 0;
    background: linear-gradient(to left, var(--bg-panel), transparent);
}

.ticker-tape-label {
    position: absolute;
    left: 0;
    top: 0; bottom: 0;
    width: 90px;
    background: var(--bg-panel);
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: var(--font-mono);
    font-size: 0.55rem;
    letter-spacing: 0.2em;
    color: var(--accent);
    border-right: 1px solid var(--border);
    z-index: 3;
    flex-shrink: 0;
}

.ticker-tape-track {
    display: flex;
    align-items: center;
    white-space: nowrap;
    animation: ticker-scroll 60s linear infinite;
    padding-left: 100px;
    gap: 0;
}
.ticker-tape-track:hover { animation-play-state: paused; }

@keyframes ticker-scroll {
    0%   { transform: translateX(0); }
    100% { transform: translateX(-50%); }
}

.ticker-item {
    display: inline-flex;
    align-items: center;
    gap: 0.55rem;
    padding: 0 2rem;
    border-right: 1px solid rgba(0,255,136,0.08);
    font-family: var(--font-mono);
    font-size: 0.68rem;
    white-space: nowrap;
}

.ticker-name {
    color: #c8ffe8;
    font-weight: 700;
    letter-spacing: 0.06em;
}

.ticker-price {
    color: var(--muted);
    font-size: 0.65rem;
}

.ticker-change.up   { color: var(--accent); }
.ticker-change.down { color: var(--red); }

.ticker-pct {
    font-size: 0.62rem;
    padding: 1px 6px;
    border-radius: 3px;
}
.ticker-pct.up   { background: rgba(0,255,136,0.12); color: var(--accent); }
.ticker-pct.down { background: rgba(255,77,109,0.12); color: var(--red); }

.ticker-sentiment {
    font-size: 0.5rem;
    letter-spacing: 0.12em;
    padding: 1px 5px;
    border-radius: 2px;
    font-weight: 700;
    text-transform: uppercase;
}
.ticker-sentiment.bull { background: rgba(0,255,136,0.15); color: var(--accent); border: 1px solid rgba(0,255,136,0.3); }
.ticker-sentiment.bear { background: rgba(255,77,109,0.15); color: var(--red);    border: 1px solid rgba(255,77,109,0.3); }

/* No articles placeholder */
.empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: var(--muted);
    font-family: var(--font-mono);
    font-size: 0.8rem;
    letter-spacing: 0.15em;
    border: 1px dashed var(--border);
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# ── CONSTANTS ────────────────────────────────────────────────
from dotenv import load_dotenv
import os

load_dotenv()

_GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"

# ── FIX 1: Corrected RSS feed URLs ──────────────────────────
RSS_FEEDS = {
    "MoneyControl":      "https://www.moneycontrol.com/rss/latestnews.xml",
    "Economic Times":    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "Business Standard": "https://www.business-standard.com/rss/home_page_top_stories.rss",
}

ALL_CATEGORIES = [
    "Bullish", "Bearish", "Neutral",
]

CATEGORY_ICONS = {
    "Bullish":   "▲",
    "Bearish":   "▼",
    "Neutral":   "◆",
}

# ── MARKET INDICES for ticker tape ───────────────────────────
MARKET_INDICES = {
    "NIFTY 50":     "^NSEI",
    "SENSEX":       "^BSESN",
    "BANK NIFTY":   "^NSEBANK",
    "NIFTY IT":     "^CNXIT",
    "NIFTY MIDCAP": "^NSEMDCP50",
    "NIFTY AUTO":   "^CNXAUTO",
    "NIFTY PHARMA": "^CNXPHARMA",
    "NIFTY METAL":  "^CNXMETAL",
    "INDIA VIX":    "^INDIAVIX",
    "USD/INR":      "USDINR=X",
    "GOLD MCX":     "GC=F",
    "CRUDE OIL":    "CL=F",
}

# ── NSE TICKER MAP ───────────────────────────────────────────
@st.cache_data
def load_ticker_map():
    try:
        df = pd.read_csv("EQUITY_L.csv")
        df.columns = df.columns.str.strip()
        df = df[df["SERIES"] == "EQ"]

        def clean(name):
            name = name.lower()
            name = name.replace("limited", "").replace("ltd", "")
            return name.strip()

        df["CLEAN_NAME"] = df["NAME OF COMPANY"].apply(clean)
        df = df.sort_values("CLEAN_NAME", key=lambda s: s.str.len(), ascending=False)
        return dict(zip(df["CLEAN_NAME"], df["SYMBOL"]))
    except Exception:
        return {}


def extract_ticker(headline, ticker_map):
    text = headline.lower()
    for company, symbol in ticker_map.items():
        company_str = str(company)
        if not company_str or len(company_str) < 4:
            continue
        if re.search(r'\b' + re.escape(company_str) + r'\b', text):
            return symbol
    return None


# ── CLASSIFIER ───────────────────────────────────────────────
@st.cache_resource
def load_classifier():
    from transformers import pipeline
    return pipeline("zero-shot-classification", model="facebook/bart-large-mnli")


def predict_label(clf, text):
    text = "Stock market news: " + text
    
    # ── FIX: Keyword-based pre-classification for strong signals ──
    text_lower = text.lower()
    
    # Strong bearish keywords (must occur as whole words)
    bearish_keywords = [
        "downgrade", "reduce", "reduced", "target down", "sell", "weakness",
        "loss", "losses", "decline", "declined", "drop", "dropped", "fall", "crash", "plunge",
        "bearish", "negative", "concern", "risk", "warning", "caution",
        "downside", "downward", "worse", "deteriorate", "cut", "lower",
    ]
    
    # Strong bullish keywords (must occur as whole words)
    bullish_keywords = [
        "upgrade", "upgraded", "buy", "bullish", "positive", "strength",
        "profit", "profits", "growth", "grew", "rally", "surge", "jump", "soar",
        "outperform", "beat", "upside", "upward", "improve", "improved",
        "record", "momentum",
    ]
    
    bearish_count = sum(1 for kw in bearish_keywords if kw in text_lower)
    bullish_count = sum(1 for kw in bullish_keywords if kw in text_lower)
    
    if bearish_count >= 1:
        return "Bearish"
    
    if bullish_count >= 2:
        return "Bullish"

    labels = ["Bullish", "Bearish", "Neutral"]

    hypothesis_template = {
        "Bullish": "This news will increase the stock price due to positive developments like growth, orders, or strong performance.",
        "Bearish": "This news indicates sustained negative performance such as losses, weak fundamentals, or downgrades that will likely decrease stock price.",
        "Neutral": "This news does not clearly indicate an increase or decrease in stock price.",
    }

    result = clf(
        text,
        labels,
        hypothesis_template="This example is {}."
    )

    scores = dict(zip(result["labels"], result["scores"]))

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_label, top_score = sorted_scores[0]
    second_score = sorted_scores[1][1]

    if top_score - second_score < 0.08:
        return "Neutral"

    return top_label

def classify_all(articles, classifier):
    """Run BART classification in parallel across all articles."""
    results = [None] * len(articles)

    def _classify(idx, art):
        full_text = art["title"] + " " + art.get("summary_raw", "")
        return idx, predict_label(classifier, full_text)

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(_classify, i, a): i for i, a in enumerate(articles)}
        for future in as_completed(futures):
            idx, label = future.result()
            results[idx] = label

    return results


@st.cache_data(ttl=120)
def fetch_market_data():
    results = []
    for name, symbol in MARKET_INDICES.items():
        try:
            url = (
                f"https://query1.finance.yahoo.com/v8/finance/chart/"
                f"{symbol}?interval=1d&range=2d"
            )
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, timeout=6, headers=headers)
            data = resp.json()
            meta   = data["chart"]["result"][0]["meta"]
            price  = meta.get("regularMarketPrice", 0)
            prev   = meta.get("chartPreviousClose", meta.get("previousClose", price))
            change = price - prev
            pct    = (change / prev * 100) if prev else 0
            results.append({
                "name":   name,
                "price":  price,
                "change": change,
                "pct":    pct,
                "up":     change >= 0,
            })
        except Exception:
            pass
    return results


def build_ticker_html(market_data):
    if not market_data:
        return (
            '<div style="font-family:monospace;font-size:0.7rem;'
            'color:#5a8a72;padding:0 2rem;">Market data unavailable</div>'
        )

    def item_html(d):
        direction = "up"   if d["up"] else "down"
        arrow     = "▲"    if d["up"] else "▼"
        sent_cls  = "bull" if d["up"] else "bear"
        sentiment = "BULL" if d["up"] else "BEAR"
        sign      = "+"    if d["up"] else ""
        return (
            f'<span class="ticker-item">'
            f'  <span class="ticker-name">{d["name"]}</span>'
            f'  <span class="ticker-price">{d["price"]:,.2f}</span>'
            f'  <span class="ticker-change {direction}">{arrow} {sign}{d["change"]:,.2f}</span>'
            f'  <span class="ticker-pct {direction}">{sign}{d["pct"]:.2f}%</span>'
            f'  <span class="ticker-sentiment {sent_cls}">{sentiment}</span>'
            f'</span>'
        )

    items_html = "".join(item_html(d) for d in market_data)
    items_html_x2 = items_html + items_html

    return f"""
<div class="ticker-tape-wrapper">
  <div class="ticker-tape-label">◈ LIVE MKT</div>
  <div class="ticker-tape-track">{items_html_x2}</div>
</div>
"""


@st.cache_data(ttl=300)
def fetch_rss(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
    }
    try:
        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(max_retries=2)
        session.mount("https://", adapter)
        resp = session.get(url, timeout=12, headers=headers)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        feed = feedparser.parse(resp.content)
    except Exception:
        feed = feedparser.parse(url)

    articles = []
    for e in feed.entries[:65]:
        description = e.get("summary", "")
        if not description and hasattr(e, "media_description"):
            description = (
                e.media_description[0]
                if isinstance(e.media_description, list)
                else e.media_description
            )
        description = re.sub(r"<[^>]+>", "", description)
        description = description.replace("â‚¹", "₹")

        articles.append({
            "title":       e.get("title", ""),
            "link":        e.get("link", ""),
            "published":   e.get("published", ""),
            "summary_raw": description,
            "source":      feed.feed.get("title", "Unknown"),
        })
    return articles


def is_stock_market_news(title, description):
    text = (title + " " + description).lower()

    indian_keywords = [
        "india", "indian", "nifty", "sensex", "bse", "nse", "rupee", "inr",
        "stock exchange", "mcx", "bank nifty", "nifty 50", "equity", "demat",
    ]
    indian_companies = [
        "hdfc", "icici", "sbi", "axis", "kotak", "indusind", "tata", "reliance",
        "infosys", "tcs", "wipro", "hul", "airtel", "jio", "heromotocorp",
        "maruti", "mahindra", "adanigreen", "adaniports", "powergrid", "ntpc",
        "tatasteel", "hindalco", "zomato", "paytm", "swiggy",
    ]
    exclude_keywords = [
        "us stock", "us market", "nasdaq", "sp 500", "dow jones", "us dollar",
        "fed", "fomc", "america", "american", "united states", "uk ", "london",
        "ftse", "frankfurt", "dax", "tokyo", "nikkei", "singapore", "hong kong",
        "actor", "actress", "cricket", "bollywood", "sports", "election",
        "politics", "political", "minister", "weather", "climate", "movie", "film",
    ]
    for kw in exclude_keywords:
        if kw in text:
            return False
    if any(k in text for k in indian_keywords):
        return True
    if "stock" in text or "shares" in text or "market" in text:
        return True
    if any(k in text for k in indian_companies):
        return True
    return False


def fetch_all(selected):
    all_articles = []
    for src in selected:
        all_articles.extend(fetch_rss(RSS_FEEDS[src]))

    if len(all_articles) < 10:
        try:
            resp = requests.get("https://feeds.cnbctv18.com/cnbctv18/business/", timeout=5)
            if resp.status_code == 200:
                feed = feedparser.parse(resp.text)
                for entry in feed.entries[:20]:
                    all_articles.append({
                        "title":       entry.get("title", ""),
                        "link":        entry.get("link", ""),
                        "published":   entry.get("published", ""),
                        "summary_raw": entry.get("summary", ""),
                        "source":      "CNBC India",
                    })
        except Exception:
            pass

    seen, unique = set(), []
    for a in all_articles:
        if a["title"] not in seen and is_stock_market_news(a["title"], a["summary_raw"]):
            seen.add(a["title"])
            unique.append(a)
    return unique


@st.cache_data(show_spinner=False)
def groq_summary(title, raw_summary):
    try:
        client = Groq(api_key=_GROQ_API_KEY.strip())
        prompt = f"""You are a financial news analyst. Summarize the following headline and content in EXACTLY 3 short lines:

Line 1: What happened (1 sentence)
Line 2: Market impact (1 sentence)
Line 3: Key takeaway (1 sentence)

Headline: {title}
Content: {raw_summary[:300]}

Provide ONLY the 3 lines, no numbering, no labels."""
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.3,
        )
        lines = response.choices[0].message.content.strip().split("\n")[:3]
        return "\n".join(lines)
    except Exception as e:
        return f"⚠ Summary unavailable ({str(e)[:50]})"



def fetch_summaries_parallel(articles):
    """Fetch all Groq summaries in parallel before the render loop."""
    summaries = [None] * len(articles)

    def _summarize(idx, art):
        return idx, groq_summary(art["title"], art.get("summary_raw", ""))

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(_summarize, i, a): i for i, a in enumerate(articles)}
        for future in as_completed(futures):
            idx, summ = future.result()
            summaries[idx] = summ

    return summaries



with st.sidebar:
    st.markdown('<div class="sidebar-logo">📈 StockPulse</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section">Data Sources</div>', unsafe_allow_html=True)
    sources = st.multiselect(
        "", list(RSS_FEEDS.keys()),
        default=list(RSS_FEEDS.keys()),
        label_visibility="collapsed",
    )
    st.markdown('<div class="sidebar-section">Filter by Category</div>', unsafe_allow_html=True)
    selected_cats = st.multiselect(
        "", ALL_CATEGORIES,
        default=[],
        label_visibility="collapsed",
        placeholder="All categories",
    )
    st.markdown("---")
    st.markdown(
        '<span style="font-family:\'Space Mono\',monospace;font-size:0.6rem;color:#5a8a72;">'
        f'Last refresh: {datetime.now().strftime("%H:%M:%S")}</span>',
        unsafe_allow_html=True,
    )

if not sources:
    st.stop()


st.markdown("""
<div class="title-bar">
  <div>
    <p class="pulse-title">StockPulse</p>
    <p class="pulse-subtitle">Indian Market Intelligence Terminal</p>
  </div>
  <div class="live-dot">LIVE FEED</div>
</div>
""", unsafe_allow_html=True)

# ── TICKER TAPE ──────────────────────────────────────────────
market_data = fetch_market_data()
st.markdown(build_ticker_html(market_data), unsafe_allow_html=True)

# ── LOAD MODELS + DATA ───────────────────────────────────────
with st.spinner("Initialising models…"):
    classifier = load_classifier()
    ticker_map = load_ticker_map()

with st.spinner("Fetching market news…"):
    articles = fetch_all(sources)

# ── FIX 2: Parallel BART classification + ticker extraction ──
with st.spinner("Classifying articles…"):
    labels = classify_all(articles, classifier)

for i, art in enumerate(articles):
    art["category"] = labels[i]
    art["ticker"]   = extract_ticker(
        art["title"] + " " + art.get("summary_raw", ""), ticker_map
    )


if selected_cats:
    articles = [a for a in articles if a["category"] in selected_cats]

cats  = [a["category"] for a in articles]
bull  = cats.count("Bullish")
bear  = cats.count("Bearish")
total = len(articles)

st.markdown(f"""
<div class="stats-row">
  <div class="stat-box">
    <span class="stat-val">{total}</span>
    <span class="stat-lbl">Stories</span>
  </div>
  <div class="stat-box">
    <span class="stat-val">{bull}</span>
    <span class="stat-lbl">Bullish</span>
  </div>
  <div class="stat-box">
    <span class="stat-val red">{bear}</span>
    <span class="stat-lbl">Bearish</span>
  </div>
  <div class="stat-box">
    <span class="stat-val blue">{total - bull - bear}</span>
    <span class="stat-lbl">Mixed/Other</span>
  </div>
</div>
""", unsafe_allow_html=True)

if not articles:
    st.markdown(
        '<div class="empty-state">NO ARTICLES MATCH YOUR FILTERS</div>',
        unsafe_allow_html=True,
    )
else:
    with st.spinner("Generating summaries…"):
        summaries = fetch_summaries_parallel(articles)

    for i, art in enumerate(articles):
        cat         = art["category"]
        css_cat     = cat.lower()
        icon        = CATEGORY_ICONS.get(cat, "◉")
        ticker      = art["ticker"]
        badge_class = "ticker-badge" if ticker else "ticker-badge na"
        badge_label = ticker if ticker else "N/A"

        # Use pre-fetched summary — no Groq call at render time
        summary = summaries[i] or "⚠ Summary unavailable"

        st.markdown(f"""
        <div class="news-card {css_cat}">
          <div class="card-header">
            <span class="{badge_class}">{badge_label}</span>
            <p class="card-title">{art['title']}</p>
          </div>
          <span class="cat-pill {css_cat}">{icon} {cat}</span>
          <div class="summary-block">{summary}</div>
          <div class="card-footer">
            <span class="source-tag">⬡ {art['source']}</span>
          </div>
        </div>
        """, unsafe_allow_html=True)