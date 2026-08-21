#!/usr/bin/env python3
"""
aggregate.py — Τραβάει δωρεάν RSS feeds από μεγάλα πρακτορεία ΗΠΑ/Ευρώπης/Ασίας,
κάνει ticker-matching στα άρθρα, υπολογίζει sentiment (ίδιο lexicon-based μοτίβο
με το trading-copilot/scanner/scan.py) και γράφει:
  - public/data/articles.json  (feed άρθρων με πηγή/sentiment/tickers)
  - public/data/rankings.json  (ranked λίστα μετοχών ανά κλάδο/ήπειρο, με score
    breakdown: πλήθος άρθρων, μέσο sentiment, βαρύτητα πρόσφατου)

Ανθεκτικό: αν μια πηγή αποτύχει (δίκτυο/parse error), το script συνεχίζει με τις
υπόλοιπες αντί να ρίξει όλο το run.
"""
import json
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.error import URLError, HTTPError

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from universe import build_universe, CONTINENT_LABELS, BARE_MATCH_DENYLIST, NAME_OVERRIDES  # noqa: E402
from lexicon import (  # noqa: E402
    sentiment_of, horizon_of, build_patterns, match_tickers, fetch_rss_items,
)

DATA_DIR = ROOT / "public" / "data"
ARTICLES_JSON = DATA_DIR / "articles.json"
RANKINGS_JSON = DATA_DIR / "rankings.json"
HISTORY_JSON = DATA_DIR / "history.json"
HISTORY_MAX_DAYS = 30

# --- Δωρεάν RSS πηγές, ομαδοποιημένες ανά ήπειρο (Φάση 1) ---
FEEDS = [
    {"id": "yahoo-finance", "label": "Yahoo Finance", "continent": "na",
     "url": "https://finance.yahoo.com/news/rssindex"},
    {"id": "marketwatch-topstories", "label": "MarketWatch", "continent": "na",
     "url": "https://www.marketwatch.com/rss/topstories"},
    {"id": "cnbc-markets", "label": "CNBC Markets", "continent": "na",
     "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=15839135"},
    {"id": "investing-europe", "label": "Investing.com Europe", "continent": "eu",
     "url": "https://www.investing.com/rss/news_301.rss"},
    {"id": "google-news-markets", "label": "Google News — Markets", "continent": "eu",
     "url": "https://news.google.com/rss/search?q=stock%20market%20when:2d&hl=en-US&gl=US&ceid=US:en"},
    {"id": "nikkei-asia", "label": "Nikkei Asia", "continent": "as",
     "url": "https://asia.nikkei.com/rss/feed/nar"},
]


def fetch_feed(feed, patterns):
    out = []
    for it in fetch_rss_items(feed["url"]):
        combined = it["title"] + " " + it["summary"]
        out.append({
            "title": it["title"],
            "summary": it["summary"],
            "url": it["url"],
            "source": feed["label"],
            "source_id": feed["id"],
            "continent": feed["continent"],
            "published_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(it["epoch"])),
            "epoch": it["epoch"],
            "sentiment": sentiment_of(combined),
            "horizon": horizon_of(combined),
            "tickers": match_tickers(combined, patterns),
        })
    return out


def build_rankings(articles, universe, history):
    """Aggregate score per μετοχή: μέσο sentiment με βάρος πρόσφατου (half-life 3 μέρες)
    + πλήθος άρθρων + ποικιλομορφία πηγών· ίδιο μοτίβο half-life με trading-copilot's
    ticker_news_summary(). Το "unusual" flag συγκρίνει το σημερινό πλήθος άρθρων με τον
    μέσο όρο των τελευταίων 7 ημερών ιστορικού (history.json) — ξαφνική αύξηση κάλυψης
    συχνά σημαίνει ότι μόλις συνέβη κάτι σημαντικό για τη μετοχή."""
    now = time.time()
    HALF_LIFE_SEC = 3 * 86400
    by_ticker = {}
    for a in articles:
        for tk in a["tickers"]:
            by_ticker.setdefault(tk, []).append(a)

    rankings = []
    for tk, arts in by_ticker.items():
        meta = universe[tk]
        weighted_sum = 0.0
        weight_total = 0.0
        for a in arts:
            age = max(0, now - a["epoch"])
            w = 0.5 ** (age / HALF_LIFE_SEC)
            weighted_sum += a["sentiment"] * w
            weight_total += w
        avg_sentiment = weighted_sum / weight_total if weight_total else 0.0
        source_count = len({a["source_id"] for a in arts})
        # score 0-100: 50 = ουδέτερο, κλιμακωμένο με sentiment [-1,1] + μπόνους όγκου/πηγών
        volume_bonus = min(10, len(arts) * 2)
        score = round(max(0, min(100, 50 + avg_sentiment * 40 + volume_bonus)), 1)

        past = [h["article_count"] for h in history.get(tk, [])[-7:]]
        baseline = round(sum(past) / len(past), 1) if past else None
        unusual = bool(baseline and baseline >= 0.5 and len(arts) >= 3 * baseline)

        swing_count = sum(1 for a in arts if a["horizon"] == "swing")
        longterm_count = sum(1 for a in arts if a["horizon"] == "long_term")
        if swing_count > longterm_count:
            horizon = "swing"
        elif longterm_count > swing_count:
            horizon = "long_term"
        else:
            horizon = None

        rankings.append({
            "ticker": tk,
            "name": meta["name"],
            "sector": meta.get("sector"),
            "continent": meta["continent"],
            "score": score,
            "article_count": len(arts),
            "avg_sentiment": round(avg_sentiment, 2),
            "volume_bonus": volume_bonus,
            "source_count": source_count,
            "unusual": unusual,
            "baseline_articles": baseline,
            "horizon": horizon,
            "swing_count": swing_count,
            "longterm_count": longterm_count,
        })

    rankings.sort(key=lambda r: r["score"], reverse=True)
    return rankings


def load_history():
    if HISTORY_JSON.exists():
        try:
            return json.loads(HISTORY_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def update_history(history, rankings, today):
    """Προσθέτει/αντικαθιστά το σημερινό snapshot ανά ticker, κρατώντας τις
    τελευταίες HISTORY_MAX_DAYS ημέρες. Πολλαπλά runs την ίδια μέρα ενημερώνουν
    το ίδιο entry αντί να δημιουργούν διπλότυπα."""
    for r in rankings:
        entries = history.setdefault(r["ticker"], [])
        snapshot = {
            "date": today,
            "score": r["score"],
            "avg_sentiment": r["avg_sentiment"],
            "article_count": r["article_count"],
        }
        if entries and entries[-1]["date"] == today:
            entries[-1] = snapshot
        else:
            entries.append(snapshot)
        history[r["ticker"]] = entries[-HISTORY_MAX_DAYS:]
    for tk in list(history.keys()):
        if not history[tk]:
            del history[tk]
    return history


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("Universe:")
    universe = build_universe()
    patterns = build_patterns(universe, BARE_MATCH_DENYLIST, NAME_OVERRIDES)

    print("\nRSS feeds:")
    all_articles = []
    for feed in FEEDS:
        try:
            items = fetch_feed(feed, patterns)
            print(f"  {feed['label']}: {len(items)} άρθρα")
            all_articles.extend(items)
        except (URLError, HTTPError, TimeoutError, OSError, ET.ParseError) as e:
            print(f"  ! {feed['label']}: αποτυχία ({e}) — παραλείπεται")

    all_articles.sort(key=lambda a: a["epoch"], reverse=True)

    history = load_history()
    rankings = build_rankings(all_articles, universe, history)
    today = time.strftime("%Y-%m-%d", time.gmtime())
    history = update_history(history, rankings, today)

    ARTICLES_JSON.write_text(
        json.dumps({"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "articles": all_articles}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    RANKINGS_JSON.write_text(
        json.dumps({"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "continents": CONTINENT_LABELS, "rankings": rankings},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    HISTORY_JSON.write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nUniverse: {len(universe)} tickers")
    print(f"Έγραψα {len(all_articles)} άρθρα -> {ARTICLES_JSON}")
    print(f"Έγραψα {len(rankings)} rankings -> {RANKINGS_JSON}")
    print(f"Ιστορικό: {len(history)} tickers -> {HISTORY_JSON}")


if __name__ == "__main__":
    main()
