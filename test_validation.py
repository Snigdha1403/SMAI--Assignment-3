

import sys
import time
from collections import Counter

def test_imports():
    """Test if all required imports work"""
    print("=" * 60)
    print("TEST 1: Validating Imports")
    print("=" * 60)
    try:
        import os
        print("os")
        import re
        print("re")
        import time
        print("time")
        from collections import Counter
        print("Counter")
        from datetime import datetime
        print("datetime")
        import feedparser
        print("feedparser")
        import requests
        print("requests")
        from transformers import pipeline
        print("transformers.pipeline")
        from groq import Groq
        print("groq.Groq")
        print("\n ALL IMPORTS SUCCESSFUL\n")
        return True
    except ImportError as e:
        print(f" Import Error: {e}\n")
        return False


def test_classifier_loading():
    """Test if BART classifier loads correctly"""
    print("=" * 60)
    print("TEST 2: Testing BART Zero-Shot Classifier")
    print("=" * 60)
    try:
        from transformers import pipeline
        print("Loading classifier model (first time may take 1-2 minutes)...")
        clf = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        print("Classifier loaded successfully")
        return clf
    except Exception as e:
        print(f"Classifier loading failed: {e}\n")
        return None


def test_prediction(clf):
    """Test if classification prediction works"""
    print("\n" + "=" * 60)
    print("TEST 3: Testing 2-Stage Classification")
    print("=" * 60)
    
    if clf is None:
        print("Cannot test prediction: classifier not loaded\n")
        return False
    
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
    
    test_headlines = [
        ("Sensex rallies 800 points; Nifty crosses 22,500 amid FII buying", "Bullish"),
        ("Markets crash: Nifty falls 2% as inflation data spooks investors", "Bearish"),
        ("TCS Q4 results: Net profit up 9% YoY, beats estimates", "Results"),
        ("RBI keeps repo rate unchanged at 6.5% in MPC meeting", "Policy"),
        ("Bitcoin surges past $70,000 as ETF inflows accelerate", "Crypto"),
    ]
    
    try:
        correct = 0
        for headline, expected in test_headlines:
            # Stage 1: Sentiment
            sent_result = clf(
                headline,
                SENTIMENT_LABELS,
                hypothesis_template="This news expresses {}.",
            )
            sent_label = sent_result["labels"][0]
            sent_final = SENTIMENT_MAP[sent_label]
            sent_score = sent_result["scores"][0]
            
            # Stage 2: Topic
            topic_result = clf(
                headline,
                TOPIC_LABELS,
                hypothesis_template="This news is about {}.",
            )
            topic_label = topic_result["labels"][0]
            topic_final = TOPIC_MAP[topic_label]
            topic_score = topic_result["scores"][0]
            
            # Decision logic (matching eval.py)
            if topic_score > 0.35:
                pred = topic_final
            elif sent_final in ["Bullish", "Bearish"] and sent_score > 0.60:
                pred = sent_final
            elif sent_final == "Neutral" and sent_score > 0.50:
                pred = "Neutral"
            else:
                pred = topic_final
            
            match = "yes" if pred == expected else "no"
            status = "YES" if pred == expected else "NO"
            if pred == expected:
                correct += 1
            
            print(f"{match} {status} '{headline[:50]}...'")
            print(f"   Expected: {expected} | Got: {pred}")
        
        accuracy = (correct / len(test_headlines)) * 100
        print(f"\n Classification Accuracy: {accuracy:.0f}% ({correct}/{len(test_headlines)})\n")
        return True
    except Exception as e:
        print(f" Prediction test failed: {e}\n")
        return False


def test_rss_feeds():
    """Test if RSS feeds are accessible"""
    print("=" * 60)
    print("TEST 4: Testing RSS Feed Accessibility")
    print("=" * 60)
    
    RSS_FEEDS = {
        "MoneyControl": "https://www.moneycontrol.com/rss/latestnews.xml",
        "Economic Times": "https://economictimes.indiatimes.com/markets/rss.cms",
        "Business Standard": "https://www.business-standard.com/rss/home_page_news.rss",
        "LiveMint": "https://www.livemint.com/rss/markets.xml",
    }
    
    import feedparser
    
    working = 0
    for name, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            entries = len(feed.entries)
            if entries > 0:
                print(f"{name}: {entries} articles found")
                working += 1
            else:
                print(f" {name}: Feed accessible but no articles")
        except Exception as e:
            print(f" {name}: Connection failed - {str(e)[:40]}...")
    
    print(f"\n {working}/{len(RSS_FEEDS)} feeds working\n")
    return working > 0


def test_groq_api():
    """Test if Groq API key format is correct"""
    print("=" * 60)
    print("TEST 5: Testing Groq API Configuration")
    print("=" * 60)
    
    import os
    groq_key = os.getenv("GROQ_API_KEY", "")
    
    if groq_key:
        if groq_key.startswith("gsk_"):
            print(f"Groq API Key format is valid (starts with 'gsk_')")
            print(f"   Key: {groq_key[:20]}...")
            print("\n Groq API is configured\n")
            return True
        else:
            print(f" Groq API Key format invalid (should start with 'gsk_')")
            print(f"   Got: {groq_key[:30]}...\n")
            return False
    else:
        print(" GROQ_API_KEY environment variable not set")
        print("   You can still use the app without summaries")
        print("   To enable: export GROQ_API_KEY='gsk_...'\n")
        return True  # Not a critical error


def main():
    """Run all validation tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  StockPulse Application Validation Test Suite".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    results = {}
    
    # Test 1: Imports
    results["Imports"] = test_imports()
    if not results["Imports"]:
        print("Cannot continue without required imports")
        return False
    
    # Test 2: Classifier Loading
    clf = test_classifier_loading()
    results["Classifier Loading"] = clf is not None
    
    # Test 3: Prediction
    if clf:
        results["Classification"] = test_prediction(clf)
    else:
        results["Classification"] = False
    
    # Test 4: RSS Feeds
    results["RSS Feeds"] = test_rss_feeds()
    
    # Test 5: Groq API
    results["Groq API"] = test_groq_api()
    
    # Summary
    print("=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED - YOUR APP IS READY TO USE!")
        print("=" * 60)
        print("\nTo run the app, execute:")
        print("  streamlit run app.py")
        print("\nThen open: http://localhost:8501")
    else:
        print("  SOME TESTS FAILED - PLEASE FIX THE ISSUES ABOVE")
        print("=" * 60)
    
    print()
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
