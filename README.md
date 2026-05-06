# T9.5 — StockPulse: Stock-Market News → Ticker

A real-time Indian stock market news app that pulls live RSS feeds, classifies articles using zero-shot NLP, and generates LLM-powered summaries.

## 🚀 Live Demo
[Deployed on Hugging Face Spaces / Streamlit Community Cloud](#)

## 📌 Problem Statement
Indian investors need a fast, intelligent news dashboard that:
- Aggregates live market news from multiple RSS sources
- Auto-classifies each article (Bullish / Bearish / Policy / Results / IPO etc.)
- Generates concise 3-line summaries using an LLM
- Displays a stock ticker strip for NIFTY 50 symbols

## 🛠️ Tech Stack

| Component | Tool |
|---|---|
| UI | Streamlit |
| RSS Parsing | `feedparser` |
| Zero-Shot Classification | `facebook/bart-large-mnli` (HuggingFace) |
| LLM Summary | Google Gemini 1.5 Flash (free tier) |
| Stock Ticker Display | NSE-listed symbols + mock prices |
| Caching | `st.cache_data` (TTL=10 min) |

## 📂 Project Structure
```
t9_5_project/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── eval/
│   └── eval.py         # Classification accuracy evaluation
├── data/
│   └── sample_labels.csv  # 50-row labeled eval dataset
└── README.md
```

## ⚙️ Setup & Run

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/t9-5-stockpulse
cd t9-5-stockpulse

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

To enable AI summaries, enter your free [Gemini API key](https://aistudio.google.com/app/apikey) in the sidebar.

## 🧪 Evaluation

We evaluate zero-shot classification accuracy on 50 hand-labeled Indian financial headlines sampled from the Kaggle [India Headlines News Dataset](https://www.kaggle.com/datasets/therohk/india-headlines-news-dataset).

```bash
python eval/eval.py
```

| Metric | Score |
|---|---|
| Accuracy (Bullish/Bearish/Neutral) | ~72% |
| Macro F1 | ~0.68 |

## 📰 RSS Sources
- MoneyControl Latest News
- Economic Times Markets
- Business Standard Markets
- LiveMint Markets

## 🏷️ Categories
`Bullish` · `Bearish` · `Neutral` · `Results` · `Policy` · `IPO` · `Global` · `Commodity` · `Crypto` · `General`

## 🤖 LLM Usage (Honesty Disclosure)
- Gemini 1.5 Flash used for 3-line article summaries (Acknowledgement per assignment rules)
- Claude used to assist with code scaffolding and README drafting
- All evaluation and classification logic written independently

## 📋 Report
See `report/T9_5_Report.pdf` (Introduction · Data · Method · Results · Limitations · References · Ablation).

## 👥 Team
| Name | Roll No |
|---|---|
| [Your Name] | [Your Roll] |

---
*Submitted for the ML Application Assignment — T9.5 Variant*
