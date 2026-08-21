#!/usr/bin/env python3
"""
radar.py — "Ραντάρ": γρήγορη ανίχνευση μεγάλων κινήσεων τιμής + breaking
ανακοινώσεις από primary-source wires, τρέχει συχνότερα (π.χ. κάθε 15') από
το κύριο aggregate.py (κάθε 3ω).

ΣΗΜΑΝΤΙΚΟ (βλ. και disclaimer στο UI): αυτό ΔΕΝ προβλέπει τίποτα πριν συμβεί.
Ανιχνεύει δύο πράγματα που ήδη έχουν συμβεί/ανακοινωθεί δημόσια:
  1. Μετοχές S&P 500 με ενδοημερήσια μεταβολή >= +20% (MOVE_THRESHOLD) — η
     ίδια η κίνηση τιμής, μόλις καταγραφεί.
  2. Άρθρα από "πρωτογενείς" πηγές (δελτία τύπου εταιρειών, SEC filings, FDA
     ανακοινώσεις) — εκεί όπου γεννιέται δημόσια η είδηση, πριν την
     αναδημοσιεύσουν τα μεγάλα sites με καθυστέρηση λεπτών/ωρών.

Γράφει: public/data/radar.json
"""
import html
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.error import URLError, HTTPError

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from universe import build_universe, BARE_MATCH_DENYLIST, NAME_OVERRIDES  # noqa: E402
from lexicon import sentiment_of, build_patterns, match_tickers, fetch_rss_items  # noqa: E402
from net import HEADERS, urlopen_safe  # noqa: E402
from urllib.request import Request  # noqa: E402

DATA_DIR = ROOT / "public" / "data"
RADAR_JSON = DATA_DIR / "radar.json"

MOVE_THRESHOLD = 20.0  # % ενδοημερήσια κίνηση για να μπει στο "Μεγάλες κινήσεις"

# --- Primary-source wires: εκεί όπου "γεννιέται" η είδηση, πριν την
# αναδημοσιεύσουν τα μεγάλα sites (Reuters/CNBC κ.λπ.) με καθυστέρηση. Το
# GlobeNewswire/BusinessWire μπλοκάρουν requests χωρίς browser session (δοκιμάστηκε,
# timeout) — μείναμε σε πηγές που πραγματικά απαντάνε.
BREAKING_FEEDS = [
    {"id": "prnewswire-financial", "label": "PR Newswire — Financial",
     "url": "https://www.prnewswire.com/rss/financial-services-latest-news/financial-services-latest-news-list.rss"},
    {"id": "prnewswire-public-co", "label": "PR Newswire — Public Companies",
     "url": "https://www.prnewswire.com/rss/all-public-company-news/all-public-company-news-list.rss"},
    {"id": "prnewswire-health", "label": "PR Newswire — Health",
     "url": "https://www.prnewswire.com/rss/health-latest-news/health-latest-news-list.rss"},
    {"id": "sec-edgar-8k", "label": "SEC EDGAR (8-K filings)",
     "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=8-K&company=&dateb=&owner=include&count=100&output=atom",
     # Το SEC απαιτεί ενημερωτικό User-Agent (πολιτική "fair access") — γενικό
     # browser UA μπλοκάρεται με 403.
     "headers": {"User-Agent": "market-intel (news research tool) contact@example.com"}},
    {"id": "fda-news", "label": "FDA Press Announcements",
     "url": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/press-releases/rss.xml"},
]


def fetch_breaking(feed, patterns):
    out = []
    for it in fetch_rss_items(feed["url"], headers=feed.get("headers")):
        combined = it["title"] + " " + it["summary"]
        tickers = match_tickers(combined, patterns)
        out.append({
            "title": it["title"],
            "summary": it["summary"],
            "url": it["url"],
            "source": feed["label"],
            "source_id": feed["id"],
            "published_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(it["epoch"])),
            "epoch": it["epoch"],
            "sentiment": sentiment_of(combined),
            "tickers": tickers,
        })
    return out


def _cell_text(html_cell):
    text = re.sub(r"<[^>]+>", "", html_cell)
    return html.unescape(re.sub(r"\s+", " ", text).strip())


def fetch_sp500_movers(universe):
    """Ένα request στο stockanalysis.com/list/sp-500-stocks/ δίνει ήδη Symbol,
    Name, Price, %Change για όλο το S&P 500 σε έναν πίνακα — αποφεύγουμε
    per-ticker calls (θα ήταν 500+ requests κάθε 15 λεπτά)."""
    url = "https://stockanalysis.com/list/sp-500-stocks/"
    req = Request(url, headers=HEADERS)
    with urlopen_safe(req, timeout=20) as resp:
        html = resp.read().decode("utf-8", errors="replace")

    m = re.search(r"<tbody>(.*?)</tbody>", html, re.S)
    if not m:
        raise ValueError("Δεν βρέθηκε <tbody> στη λίστα S&P 500")
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", m.group(1), re.S)

    movers = []
    for row in rows:
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
        if len(cells) < 6:
            continue
        ticker_m = re.search(r">([A-Z.\-]+)<", cells[1])
        ticker = ticker_m.group(1) if ticker_m else None
        name = _cell_text(cells[2])
        price = _cell_text(cells[4])
        change_txt = _cell_text(cells[5]).replace("%", "").replace(",", "")
        if not ticker or not change_txt:
            continue
        try:
            change_pct = float(change_txt)
        except ValueError:
            continue
        if change_pct < MOVE_THRESHOLD:
            continue
        meta = universe.get(ticker, {})
        movers.append({
            "ticker": ticker,
            "name": meta.get("name") or name,
            "sector": meta.get("sector"),
            "price": price,
            "change_pct": round(change_pct, 2),
        })
    movers.sort(key=lambda m: m["change_pct"], reverse=True)
    return movers


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("Universe:")
    universe = build_universe()
    patterns = build_patterns(universe, BARE_MATCH_DENYLIST, NAME_OVERRIDES, allow_bare=False)

    print("\nΜεγάλες κινήσεις τιμής (S&P 500, threshold +%.0f%%):" % MOVE_THRESHOLD)
    try:
        movers = fetch_sp500_movers(universe)
        print(f"  Βρέθηκαν {len(movers)} μετοχές πάνω από το threshold")
    except (URLError, HTTPError, TimeoutError, OSError, ValueError) as e:
        print(f"  ! Αποτυχία fetch movers ({e})")
        movers = []

    print("\nBreaking (primary-source wires):")
    breaking = []
    for feed in BREAKING_FEEDS:
        try:
            items = fetch_breaking(feed, patterns)
            print(f"  {feed['label']}: {len(items)} άρθρα")
            breaking.extend(items)
        except (URLError, HTTPError, TimeoutError, OSError, ET.ParseError) as e:
            print(f"  ! {feed['label']}: αποτυχία ({e}) — παραλείπεται")

    breaking.sort(key=lambda a: a["epoch"], reverse=True)
    breaking = breaking[:100]  # μόνο τα πιο πρόσφατα — αυτό είναι ραντάρ, όχι αρχείο

    RADAR_JSON.write_text(
        json.dumps({
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "move_threshold_pct": MOVE_THRESHOLD,
            "movers": movers,
            "breaking": breaking,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nΈγραψα {len(movers)} movers + {len(breaking)} breaking -> {RADAR_JSON}")


if __name__ == "__main__":
    main()
