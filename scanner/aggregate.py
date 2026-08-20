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
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from universe import build_universe, CONTINENT_LABELS, BARE_MATCH_DENYLIST, NAME_OVERRIDES  # noqa: E402

DATA_DIR = ROOT / "public" / "data"
ARTICLES_JSON = DATA_DIR / "articles.json"
RANKINGS_JSON = DATA_DIR / "rankings.json"
HISTORY_JSON = DATA_DIR / "history.json"
HISTORY_MAX_DAYS = 30

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; market-intel-bot/1.0)"}
TIMEOUT = 15

# Σε κάποια τοπικά Python (π.χ. python.org στο macOS) το urllib δεν βρίσκει CA
# certificates — αν υπάρχει το certifi, χρησιμοποίησε το bundle του (ίδιο μοτίβο
# με trading-copilot/scanner/scan.py:199).
_SSL_CTX = None
try:
    import ssl
    import certifi
    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    pass


def _urlopen(req, timeout=TIMEOUT):
    if _SSL_CTX is not None:
        return urlopen(req, timeout=timeout, context=_SSL_CTX)
    return urlopen(req, timeout=timeout)

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

# --- Lexicon-based sentiment (ίδιο μοτίβο με trading-copilot/scanner/scan.py:605) ---
POSITIVE_WORDS = {
    "beat", "beats", "tops", "top", "record", "surge", "surges", "soar", "soars",
    "jump", "jumps", "rally", "rallies", "upgrade", "upgrades", "upgraded",
    "raises", "raised", "boost", "boosts", "outperform", "strong", "stronger",
    "growth", "gain", "gains", "wins", "win", "deal", "partnership", "partnering",
    "expands", "expansion", "bullish", "upside", "breakthrough", "approval",
    "approves", "buyback", "dividend", "profit", "profitable", "success",
    "milestone", "launches", "launch", "unveils", "accelerates", "momentum",
}
NEGATIVE_WORDS = {
    "miss", "misses", "missed", "falls", "fall", "drop", "drops", "plunge",
    "plunges", "slump", "slumps", "cut", "cuts", "downgrade", "downgrades",
    "downgraded", "underperform", "weak", "weaker", "lawsuit", "sues", "sued",
    "probe", "investigation", "recall", "layoffs", "bearish", "downside",
    "risk", "risks", "fears", "fear", "warning", "warns", "warn", "delay",
    "delays", "delayed", "ban", "bans", "fine", "fined", "decline", "declines",
    "tumble", "tumbles", "crash", "crashes", "loss", "losses", "danger",
    "concern", "concerns", "selloff", "sell-off", "halt", "halts",
}
WORD_RE = re.compile(r"[a-z']+")


def sentiment_of(text):
    """Lexicon score ενός άρθρου: -1.0 .. +1.0 (0 = ουδέτερο)."""
    words = WORD_RE.findall((text or "").lower())
    pos = sum(1 for w in words if w in POSITIVE_WORDS)
    neg = sum(1 for w in words if w in NEGATIVE_WORDS)
    raw = max(-3, min(3, pos - neg))
    return round(raw / 3, 2)


# --- Ticker matching: name/override + word-boundary ticker match στον τίτλο/summary ---
# Bare-symbol matching αγνοείται για σύμβολα μήκους < 3 (π.χ. "T", "K", "L", "H")
# — με 1000+ tickers στο universe, τέτοια μονο/δι-γράμματα σύμβολα θα ταίριαζαν
# σχεδόν σε κάθε άρθρο (false positives). Σε αυτές τις περιπτώσεις χρησιμοποιείται
# μόνο το πλήρες όνομα εταιρείας (ή το "match" override).
def build_patterns(universe):
    patterns = {}
    for tk, meta in universe.items():
        bare = tk.split(".")[0]
        match_phrase = meta.get("match") or NAME_OVERRIDES.get(tk) or meta["name"]
        alts = [re.escape(match_phrase)]
        if len(bare) >= 3 and bare.upper() not in BARE_MATCH_DENYLIST:
            alts.append(re.escape(bare))
        patterns[tk] = re.compile(rf"\b({'|'.join(alts)})\b", re.IGNORECASE)
    return patterns


def match_tickers(text, patterns):
    hits = []
    for tk, pat in patterns.items():
        if pat.search(text or ""):
            hits.append(tk)
    return hits


def _strip_html(s):
    return re.sub(r"<[^>]+>", " ", s or "").strip()


def _parse_rss_date(s):
    """RFC-822 (π.χ. 'Mon, 20 Jan 2026 10:00:00 GMT') ή ISO-8601 (dc:date) -> epoch, αλλιώς None."""
    if not s:
        return None
    s = s.strip()
    for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S %z"):
        try:
            return int(time.mktime(time.strptime(s, fmt)))
        except (ValueError, OverflowError):
            continue
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})", s)
    if m:
        import calendar
        y, mo, d, h, mi, se = map(int, m.groups())
        return calendar.timegm((y, mo, d, h, mi, se, 0, 0, 0))
    return None


def _local(tag):
    """'{ns}item' -> 'item' — namespace-agnostic tag matching (χρειάζεται για
    RSS 1.0/RDF feeds όπως το Nikkei, όπου το namespace δεν είναι κενό)."""
    return tag.rsplit("}", 1)[-1]


def _child_text(el, name):
    for child in el:
        if _local(child.tag) == name:
            return (child.text or "").strip()
    return ""


def fetch_feed(feed, patterns):
    req = Request(feed["url"], headers=HEADERS)
    with _urlopen(req) as resp:
        raw = resp.read()
    root = ET.fromstring(raw)
    items = [el for el in root.iter() if _local(el.tag) == "item"]
    out = []
    for it in items:
        title = _strip_html(_child_text(it, "title"))
        if not title:
            continue
        desc = _strip_html(_child_text(it, "description") or _child_text(it, "encoded"))
        link = _child_text(it, "link") or it.attrib.get(
            "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about", ""
        )
        pub = _child_text(it, "pubDate") or _child_text(it, "date")
        epoch = _parse_rss_date(pub) or int(time.time())
        tickers = match_tickers(title + " " + desc, patterns)
        out.append({
            "title": title,
            "summary": desc[:280],
            "url": link,
            "source": feed["label"],
            "source_id": feed["id"],
            "continent": feed["continent"],
            "published_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch)),
            "epoch": epoch,
            "sentiment": sentiment_of(title + " " + desc),
            "tickers": tickers,
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
    patterns = build_patterns(universe)

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
