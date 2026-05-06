import csv
import os

from sklearn.metrics import accuracy_score, classification_report
from transformers import pipeline

SENTIMENT_LABELS = [
    "Bullish (positive market sentiment)",
    "Bearish (negative market sentiment)",
    "Neutral (no strong sentiment)",
]


TOPIC_LABELS = [
    "Quarterly earnings, financial results, or profit announcements",
    "Government, regulatory, or policy decision",
    "IPO, listing, or public offering",
    "International markets or global economic news",
    "Commodity, metal, oil, or natural resource market",
    "Cryptocurrency or blockchain news",
    "General business or sector news",
]


SENTIMENT_MAP = {
    "Bullish (positive market sentiment)": "Bullish",
    "Bearish (negative market sentiment)": "Bearish",
    "Neutral (no strong sentiment)": "Neutral",
}

TOPIC_MAP = {
    "Quarterly earnings, financial results, or profit announcements": "Results",
    "Government, regulatory, or policy decision": "Policy",
    "IPO, listing, or public offering": "IPO",
    "International markets or global economic news": "Global",
    "Commodity, metal, oil, or natural resource market": "Commodity",
    "Cryptocurrency or blockchain news": "Crypto",
    "General business or sector news": "General",
}


SAMPLE_DATA = [
    ("Sensex rallies 800 points; Nifty crosses 22,500 amid FII buying",              "Bullish"),
    ("Nifty IT index gains 1.5% after strong US earnings",                           "Bullish"),
    ("Zomato eyes ₹8,500 cr fundraise via QIP",                                      "Bullish"),
    ("Bank Nifty hits all-time high of 49,000",                                      "Bullish"),
    ("Auto sector sees 12% volume growth in April",                                  "Bullish"),
    ("Domestic MF SIP inflows cross ₹20,000 cr in March",                           "Bullish"),
    ("Reliance Jio subscriber base crosses 48 crore",                                "Bullish"),
    ("Polycab India achieves ₹20,000 cr revenue milestone",                          "Bullish"),

    ("Markets crash: Nifty falls 2% as inflation data spooks investors",             "Bearish"),
    ("Infosys cuts FY24 revenue guidance citing macro headwinds",                    "Bearish"),
    ("FIIs sell ₹4,200 cr worth of equities in single session",                     "Bearish"),
    ("Pharma stocks drag indices as FDA sends warning letters",                      "Bearish"),
    ("Rupee hits all-time low of 84.20 vs dollar",                                   "Bearish"),
    ("Tata Steel posts ₹6,200 cr loss on UK operations write-off",                  "Bearish"),
    ("IT sector faces headwinds as US tech spending slows",                          "Bearish"),


    ("Rupee stable at 83.45 against dollar in early trade",                          "Neutral"),
    ("Markets flat ahead of US CPI data release tonight",                            "Neutral"),
    ("Bajaj Finance raises ₹3,000 cr via NCD issue",                                "Neutral"),
    ("Nifty consolidates in 22,200-22,600 range; analysts neutral",                  "Neutral"),
    ("Nifty50 ends flat; breadth negative with 35 decliners",                        "Neutral"),

    # Results (6)
    ("TCS Q4 results: Net profit up 9% YoY, beats estimates",                       "Results"),
    ("Adani Ports Q3 PAT jumps 38%; declares dividend of ₹6",                       "Results"),
    ("HDFC Bank Q4 NIM contracts 10 bps; stock falls 2%",                           "Results"),
    ("Wipro misses Q4 estimates; gives muted Q1 guidance",                           "Results"),
    ("IRCTC Q2 profit surges 40% on travel boom",                                    "Results"),
    ("Power Grid Q1 results in line; dividend declared",                             "Results"),

    # Policy (6)
    ("RBI keeps repo rate unchanged at 6.5% in MPC meeting",                        "Policy"),
    ("SEBI tightens F&O norms; lot sizes to increase from October",                 "Policy"),
    ("Government hikes MSP for kharif crops by 5-7%",                               "Policy"),
    ("Retail inflation eases to 4.85% in March",                                    "Policy"),
    ("NSE extends trading hours for commodity derivatives",                          "Policy"),
    ("Domestic natural gas price hiked by 10% effective April",                     "Policy"),
    ("SEBI approves REITs to issue commercial paper",                                "Policy"),

    # IPO (3)
    ("Paytm IPO subscribed 1.89 times on final day",                                "IPO"),
    ("Jio Financial Services lists at 10% premium on BSE",                          "IPO"),
    ("Ola Electric IPO opens; GMP signals strong listing gains",                    "IPO"),

    # Global (4)
    ("US Fed signals two rate cuts in 2024, global markets cheer",                  "Global"),
    ("Asian markets mixed; Japan's Nikkei falls 0.3%",                              "Global"),
    ("China's PMI contracts for 2nd straight month",                                "Global"),
    ("US dollar index slips below 104; EM currencies gain",                         "Global"),
    ("Global growth forecast cut by IMF to 3.1% for 2024",                         "Global"),

    # Commodity (5)
    ("Crude oil climbs to $90/barrel on OPEC+ supply cuts",                         "Commodity"),
    ("Steel prices soften as Chinese demand remains weak",                           "Commodity"),
    ("Silver underperforms gold; spread widens to 3-month high",                    "Commodity"),
    ("Nifty Metal index rises 2% on LME copper strength",                           "Commodity"),
    ("Crude falls to $82 on surprise US inventory build",                           "Commodity"),
    ("Gold prices rise on safe-haven demand amid geopolitical tensions",             "Commodity"),

    # Crypto (3)
    ("Bitcoin surges past $70,000 as ETF inflows accelerate",                       "Crypto"),
    ("Ethereum upgrade goes live; ETH price steady",                                "Crypto"),
    ("Solana transactions hit new daily record of 70 million",                      "Crypto"),
]


def predict_label(clf, headline):
    sent_result = clf(
        headline,
        SENTIMENT_LABELS,
        hypothesis_template="This news expresses {}.",
    )
    sent_label = sent_result["labels"][0]
    sent_final = SENTIMENT_MAP[sent_label]
    sent_score = sent_result["scores"][0]

    # STEP 2: TOPIC
    topic_result = clf(
        headline,
        TOPIC_LABELS,
        hypothesis_template="This news is about {}.",
    )
    topic_label = topic_result["labels"][0]
    topic_final = TOPIC_MAP[topic_label]
    topic_score = topic_result["scores"][0]

    if topic_score > 0.35:
        return topic_final
    
    elif sent_final in ["Bullish", "Bearish"] and sent_score > 0.60:
        return sent_final

    elif sent_final == "Neutral" and sent_score > 0.50:
        return "Neutral"
    
    else:
        return topic_final


def run_evaluation():
    print("=" * 65)
    print("T9.5 — TWO-STAGE ZERO-SHOT CLASSIFICATION")
    print("Model  : facebook/bart-large-mnli")
    print("=" * 65)

    print("\nLoading classifier pipeline…")
    clf = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

    headlines = [row[0] for row in SAMPLE_DATA]
    true_labels = [row[1] for row in SAMPLE_DATA]

    pred_labels = []

    print(f"\n{'#':>4}  {'Predicted':<12}  {'Ground Truth':<12}  Headline")
    print("-" * 75)

    for i, headline in enumerate(headlines):
        pred = predict_label(clf, headline)
        pred_labels.append(pred)

        match = "yes" if pred == true_labels[i] else "no"

        print(
            f"[{i+1:02d}] {match}  "
            f"{pred:<12}  GT: {true_labels[i]:<12}  "
            f"{headline[:55]}"
        )

    # ── METRICS ───────────────────────────────────
    print("\n" + "=" * 65)
    print("EVALUATION RESULTS")
    print("=" * 65)

    acc = accuracy_score(true_labels, pred_labels)

    print(f"\nOverall Accuracy : {acc:.4f}  ({acc*100:.1f}%)")
    print(
        "\nExpected improvement over single-stage model.\n"
        "Sentiment and topic separation reduces confusion.\n"
    )

    print(classification_report(true_labels, pred_labels, zero_division=0))


# ── ENTRY POINT ───────────────────────────────────────────────
if __name__ == "__main__":
    run_evaluation()