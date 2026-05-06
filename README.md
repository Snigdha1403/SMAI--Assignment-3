# StockPulse — "Indian Market Intelligence Terminal"

> Real-time Indian stock market news aggregator with zero-shot sentiment classification and LLM-powered summaries.


##  Problem Statement

Indian retail investors face information overload where hundreds of financial articles are published daily across MoneyControl, Economic Times, and Business Standard. **StockPulse** automates the triage:

- Pulls live RSS feeds from major Indian financial publishers
- Filters out non-market content (politics, sports, US markets)
- Classifies each article as **Bullish**, **Bearish**, or **Neutral** using a hybrid NLP pipeline
- Extracts the relevant **NSE ticker symbol** from article text
- Generates a concise **3-line LLM summary** via Groq API
- Displays a live **market indices ticker tape** (Nifty 50, Sensex, Bank Nifty, VIX, USD/INR, etc.)

---

## Tech Stack

| Component | Tool |
|---|---|
| UI Framework | Streamlit |
| RSS Parsing | `feedparser` + `requests` |
| Zero-Shot Classification | `facebook/bart-large-mnli` (HuggingFace Transformers) |
| Keyword Pre-Filter | Custom domain-specific rule layer |
| LLM Summarisation | Groq API — `llama-3.3-70b-versatile` |
| Market Data | Yahoo Finance Chart API |
| Ticker Extraction | NSE `EQUITY_L.csv` + regex word-boundary matching |
| Caching | `st.cache_data` (TTL: 300 s news, 120 s market data) |
| Parallelism | `concurrent.futures.ThreadPoolExecutor` |

---

## Project Structure

```
stockpulse/
├── app3.py              # Main Streamlit application
├── EQUITY_L.csv        # NSE equity list (symbol ↔ company name)
├── .env                # GROQ_API_KEY (not committed)
├── requirements.txt    # Python dependencies
└── README.md
```

---

##  Setup & Run

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/stockpulse
cd stockpulse

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your Groq API key
echo "GROQ_API_KEY=your_key_here" > .env

# 4. Download the NSE equity list
# Get EQUITY_L.csv from: https://www.nseindia.com/market-data/securities-available-for-trading
# Place it in the project root directory

# 5. Run the app
streamlit run app3.py
```

Get a free Groq API key at [console.groq.com](https://console.groq.com).

---

## Pipeline Overview

```
RSS Feeds (3 sources)
        │
        ▼
  News Filter          ← removes politics, sports, US markets
        │
        ▼
Keyword Pre-Filter     ← fast domain-specific rule check
        │
        ├─ Bearish keyword found?  → Bearish
        ├─ 2+ Bullish keywords?    → Bullish
        └─ Inconclusive            → BART Zero-Shot
                                          │
                              margin < 0.08 → Neutral
                              margin ≥ 0.08 → Top label
        │
        ▼
  Ticker Extraction    ← regex match against NSE EQUITY_L.csv
        │
        ▼
  Groq LLM Summary     ← 3-line structured summary (parallel)
        │
        ▼
  Streamlit UI         ← cards + live ticker tape
```

---

## RSS Sources

| Source | Feed |
|---|---|
| MoneyControl | `moneycontrol.com/rss/latestnews.xml` |
| Economic Times | `economictimes.indiatimes.com/markets/rssfeeds/...` |

A fallback to CNBC TV18 Business RSS is attempted if fewer than 10 articles are retrieved.

---

## Sentiment Categories

| Label | Meaning | Left-border colour |
|---|---|---|
| **Bullish** ▲ | Positive outlook — price likely to rise | Green |
| **Bearish** ▼ | Negative outlook — price likely to fall | Red |
| **Neutral** ◆ | No clear directional signal | Yellow |

---

## Live Market Indices

The ticker tape displays real-time data for:

`NIFTY 50` · `SENSEX` · `BANK NIFTY` · `NIFTY IT` · `NIFTY MIDCAP` · `NIFTY AUTO` · `NIFTY PHARMA` · `NIFTY METAL` · `INDIA VIX` · `USD/INR` · `GOLD MCX` · `CRUDE OIL`

---

## ⚡ Performance

| Optimisation | Detail |
|---|---|
| Streamlit caching | RSS: 300 s TTL · Market data: 120 s TTL · Model: session-scoped |
| Parallel classification | `ThreadPoolExecutor(max_workers=4)` across all articles |
| Parallel summarisation | `ThreadPoolExecutor(max_workers=8)` — all Groq calls pre-fetched before render |
| Pre-fetch strategy | Summaries fetched in one batch before the render loop; no per-card blocking |

---

## LLM Usage Disclosure

- **Groq API** (`llama-3.3-70b-versatile`) used for 3-line article summarisation
- **BART MNLI** (`facebook/bart-large-mnli`) used for zero-shot sentiment classification
- Classification logic and keyword rules written independently

---

## Team Name - VS Coders

| Name | Roll No |
|---|---|
| Gandlur Valli | 2023102068 |
| Snigdha Stp | 2023102036 |

---

*Submitted for the ML Application Assignment — T9.5 Variant*
