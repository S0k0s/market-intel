#!/usr/bin/env python3
"""
radar.py — "Ραντάρ": δύο εννοιολογικά ΔΙΑΦΟΡΕΤΙΚΑ πράγματα, μην τα μπερδεύεις:

  1. BREAKING (primary-source wires: PR Newswire, SEC 8-K, FDA) — το μόνο
     κομμάτι που μπορεί ρεαλιστικά να λειτουργήσει ως *πρώιμο σήμα*. Εδώ
     "γεννιέται" δημόσια μια είδηση (π.χ. ανακοίνωση θετικών αποτελεσμάτων
     κλινικής δοκιμής) πριν την αναδημοσιεύσουν τα μεγάλα sites με
     καθυστέρηση λεπτών/ωρών — και πριν αντιδράσει πλήρως η τιμή. Άρθρα με
     καταλυτική γλώσσα (πχ "Phase 3", "breakthrough therapy", "topline data")
     σημαίνονται ρητά ως "catalyst" ώστε να ξεχωρίζουν.
  2. MOVERS (S&P 500, ενδοημερήσια μεταβολή >= +20%) — ΕΠΙΒΕΒΑΙΩΣΗ ότι μια
     κίνηση ήδη συνέβη, ΟΧΙ πρόβλεψη. Χρήσιμο για context/quality-check
     (fundamentals/technicals), όχι για να προλάβεις να μπεις στη θέση νωρίς.

Τρέχει συχνά (π.χ. κάθε 15') από το κύριο aggregate.py (κάθε 3ω) ακριβώς
επειδή η ταχύτητα ανάγνωσης του breaking feed είναι το μόνο ρεαλιστικό
πλεονέκτημα εδώ — καμία δημόσια, νόμιμη πηγή δεν προβλέπει τίποτα πριν
ανακοινωθεί.

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
from quality import fetch_fundamentals, score_from, classify, to_number  # noqa: E402
from urllib.request import Request  # noqa: E402

DATA_DIR = ROOT / "public" / "data"
RADAR_JSON = DATA_DIR / "radar.json"
MOVERS_HISTORY_JSON = DATA_DIR / "movers_history.json"
MOVERS_HISTORY_MAX_DAYS = 30

MOVE_THRESHOLD = 20.0  # % ενδοημερήσια κίνηση για να μπει στο "Μεγάλες κινήσεις"

ARCHETYPE_LABELS = {
    "quality_compounding": "Ποιοτική Ανάπτυξη",
    "momentum_breakout": "Momentum Breakout",
    "speculative": "Κερδοσκοπικό / Χαμηλής Ποιότητας",
}

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
    {"id": "prnewswire-biotech", "label": "PR Newswire — Biotechnology",
     "url": "https://www.prnewswire.com/rss/biotechnology-latest-news/biotechnology-latest-news-list.rss"},
    {"id": "prnewswire-trials-fda", "label": "PR Newswire — Clinical Trials/FDA",
     "url": "https://www.prnewswire.com/rss/clinical-trials-fda-approval-latest-news/clinical-trials-fda-approval-latest-news-list.rss"},
    {"id": "sec-edgar-8k", "label": "SEC EDGAR (8-K filings)",
     "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=8-K&company=&dateb=&owner=include&count=100&output=atom",
     # Το SEC απαιτεί ενημερωτικό User-Agent (πολιτική "fair access") — γενικό
     # browser UA μπλοκάρεται με 403.
     "headers": {"User-Agent": "market-intel (news research tool) contact@example.com"}},
    {"id": "fda-news", "label": "FDA Press Announcements",
     "url": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/press-releases/rss.xml"},
]
# Δοκιμάστηκαν και μπλοκάρουν σταθερά (timeout) από αυτό το περιβάλλον, παρότι
# θα ήταν πολύτιμες πηγές για biotech catalysts: GlobeNewswire, BusinessWire,
# clinicaltrials.gov API. Αν κάποια στιγμή γίνουν προσβάσιμες, προσθέστε τις εδώ.

# --- Pipeline: ΔΙΑΦΟΡΕΤΙΚΟ πράγμα από το BREAKING παραπάνω. Το BREAKING είναι
# ανακοινώσεις ΑΠΟΤΕΛΕΣΜΑΤΩΝ (κάτι μόλις συνέβη/ανακοινώθηκε). Το PIPELINE είναι
# δημοσιογραφία για το τι δουλεύει μια εταιρεία ΠΡΙΝ καν φτάσει σε αποτέλεσμα
# (νέο trial ξεκίνησε, licensing deal, leadership αλλαγή πριν από IND κ.λπ.) —
# δεν λέει "θα ανέβει η μετοχή", απλά σου δείχνει ΤΙ ΥΠΑΡΧΕΙ ΣΕ ΕΞΕΛΙΞΗ ώστε να
# ξέρεις ποιο ticker να παρακολουθείς για το μελλοντικό catalyst. Χωρίς επίσημο
# ημερολόγιο (το ClinicalTrials.gov μπλοκάρει IP-level από αυτό το περιβάλλον,
# 403 σε κάθε δοκιμή) δεν έχουμε ακριβή ημερομηνία readout — μόνο "αυτό υπάρχει
# σε εξέλιξη".
PIPELINE_FEEDS = [
    {"id": "fiercebiotech", "label": "FierceBiotech",
     "url": "https://www.fiercebiotech.com/rss/xml"},
    {"id": "fiercepharma", "label": "FiercePharma",
     "url": "https://www.fiercepharma.com/rss/xml"},
    {"id": "biopharmadive", "label": "BioPharma Dive",
     "url": "https://www.biopharmadive.com/feeds/news/"},
]
# Endpoints News (endpts.com) μπλοκάρει με 403 (πιθανό bot-detection/paywall) —
# θα ήταν η πιο έγκυρη πηγή του κλάδου αν ποτέ γίνει προσβάσιμο.

# --- Καταλυτικές λέξεις: άρθρα με αυτή τη γλώσσα είναι τα πιο πιθανά να
# προηγηθούν μιας μεγάλης κίνησης τιμής (π.χ. ακριβώς ο τύπος είδησης πίσω
# από το +117% της Moderna στις 19-20/8) — σημειώνονται ρητά ως "catalyst"
# στο UI ώστε να ξεχωρίζουν από τον όγκο γενικών εταιρικών ανακοινώσεων.
CATALYST_WORDS = {
    "phase 1", "phase 2", "phase 3", "phase i", "phase ii", "phase iii",
    "topline data", "top-line data", "primary endpoint", "clinical trial",
    "clinical study", "trial results", "data readout", "interim analysis",
    "breakthrough therapy", "orphan drug", "fast track designation",
    "priority review", "fda approval", "fda clearance", "emergency use authorization",
    "positive results", "statistically significant", "met its primary endpoint",
    "accelerated approval", "new drug application", "biologics license application",
    "acquisition agreement", "definitive agreement", "merger agreement",
    "strategic partnership", "licensing agreement", "patent granted",
}


def is_catalyst(text):
    lower = (text or "").lower()
    return any(phrase in lower for phrase in CATALYST_WORDS)


# Δελτία τύπου συχνά αναγράφουν τα ίδια τον ticker τους, π.χ. "(NASDAQ: CAPR)" —
# αυτό πιάνει και εταιρείες εκτός του universe μας (S&P500 + διεθνείς δείκτες),
# π.χ. μικρότερες/biotech εταιρείες που δεν είναι σε κανέναν από τους δείκτες
# που παρακολουθούμε. Πιο αξιόπιστο από το δικό μας name-matching σε αυτές τις
# περιπτώσεις, αφού προέρχεται απευθείας από την ίδια την ανακοίνωση.
EXCHANGE_TICKER_RE = re.compile(
    r"\((?:NASDAQ|NYSE(?:\s+American)?|OTC(?:QB|QX)?|TSX|ASX|LSE)\s*:\s*([A-Z]{1,5}(?:\.[A-Z])?)\)",
    re.IGNORECASE,
)

# SEC EDGAR τίτλοι έχουν πάντα τη μορφή "8-K - COMPANY NAME (CIK) (Filer)" — η
# επωνυμία εδώ είναι πάντα σωστή (προέρχεται απευθείας από το SEC), ακόμα κι αν
# δεν έχουμε αντίστοιχο ticker στο universe μας.
SEC_TITLE_RE = re.compile(r"^\S+\s*-\s*(.+?)\s*\(\d+\)\s*\(Filer\)$")


def extract_exchange_tickers(text):
    return sorted({m.upper() for m in EXCHANGE_TICKER_RE.findall(text or "")})


def extract_sec_company_name(title):
    m = SEC_TITLE_RE.match(title or "")
    return m.group(1).title() if m else None


def fetch_breaking(feed, patterns, known_tickers):
    """known_tickers = σύμβολα του universe μας (S&P500 + μεγάλοι διεθνείς
    δείκτες) — όλα mega/large-cap, εγγενώς ρευστά. Ένα ticker που εξάγεται από
    "(NASDAQ: XYZ)" αλλά ΔΕΝ είναι εκεί μέσα είναι σχεδόν σίγουρα μικρή
    κεφαλαιοποίηση εκτός βασικών δεικτών — ακριβώς ο τύπος τίτλου όπου το
    handoff doc προειδοποιεί για thin-liquidity/pump-and-dump ρίσκο. Δεν
    κάνουμε extra API call για πραγματικό όγκο συναλλαγών (θα πολλαπλασίαζε
    τα requests) — το "εκτός γνωστού universe" είναι ένα δωρεάν, ήδη διαθέσιμο
    proxy γι' αυτό το ρίσκο."""
    out = []
    for it in fetch_rss_items(feed["url"], headers=feed.get("headers")):
        combined = it["title"] + " " + it["summary"]
        matched = set(match_tickers(combined, patterns))
        exchange_tickers = set(extract_exchange_tickers(combined))
        tickers = sorted(matched | exchange_tickers)
        unknown_tickers = sorted(exchange_tickers - known_tickers)
        company_name = None
        if not tickers and feed["id"] == "sec-edgar-8k":
            company_name = extract_sec_company_name(it["title"])
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
            "company_name": company_name,
            "catalyst": is_catalyst(combined),
            "small_cap_risk": bool(unknown_tickers),
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


def enrich_mover(mover):
    """Εμπλουτίζει έναν mover με θεμελιώδη/τεχνικά (Piotroski, Altman Z, RSI,
    PEG κ.λπ.) και τον ταξινομεί σε αρχέτυπο ποιότητας — έτσι το Ραντάρ δεν
    επισημαίνει αδιακρίτως κάθε κίνηση >= threshold σαν να είναι ισοδύναμες
    (π.χ. ένα υγιές momentum breakout έναντι ενός κερδοσκοπικού spike με
    αρνητικά κέρδη — βλ. μεθοδολογία στο opportunity_alerts_log.md)."""
    try:
        stats = fetch_fundamentals(mover["ticker"])
        price = to_number(mover["price"])
        long_term_score, swing_score = score_from(stats, price)
        archetype = classify(stats, long_term_score, swing_score)
        mover["long_term_score"] = long_term_score
        mover["swing_score"] = swing_score
        mover["archetype"] = archetype
        mover["archetype_label"] = ARCHETYPE_LABELS.get(archetype)
        mover["piotroski_f"] = stats.get("piotroski_f")
        mover["altman_z"] = stats.get("altman_z")
        mover["rsi"] = stats.get("rsi")
        mover["peg_ratio"] = stats.get("peg_ratio")
        mover["analyst_consensus"] = stats.get("analyst_consensus_text")
    except (URLError, HTTPError, TimeoutError, OSError) as e:
        print(f"    ! {mover['ticker']}: αποτυχία εμπλουτισμού ({e})")
        mover["long_term_score"] = None
        mover["swing_score"] = None
        mover["archetype"] = None
        mover["archetype_label"] = None
    return mover


def load_movers_history():
    if MOVERS_HISTORY_JSON.exists():
        try:
            return json.loads(MOVERS_HISTORY_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def update_movers_history(history, movers, today):
    """Καταγράφει ποια ημερομηνία εμφανίστηκε κάθε ticker ως mover — για να
    υπολογίσουμε 'streak' (πόσες συνεχόμενες μέρες) και να επισημάνουμε κίνδυνο
    'chasing' μιας ήδη παρατεταμένης κίνησης, όπως κάνει το
    opportunity_alerts_log.md χειροκίνητα."""
    for m in movers:
        dates = history.setdefault(m["ticker"], [])
        if not dates or dates[-1] != today:
            dates.append(today)
        history[m["ticker"]] = dates[-MOVERS_HISTORY_MAX_DAYS:]
    return history


def compute_streak(history, ticker, today):
    """Πόσες συνεχόμενες ημέρες (μέχρι και σήμερα) εμφανίστηκε το ticker ως mover."""
    dates = history.get(ticker, [])
    if not dates or dates[-1] != today:
        return 0
    streak = 0
    cursor = time.strptime(today, "%Y-%m-%d")
    cursor_epoch = time.mktime(cursor)
    date_set = set(dates)
    while time.strftime("%Y-%m-%d", time.localtime(cursor_epoch)) in date_set:
        streak += 1
        cursor_epoch -= 86400
    return streak


def sector_concentration_warning(movers):
    """Αν 2+ movers μοιράζονται τον ίδιο κλάδο, το επισημαίνουμε ρητά — ίδιο
    μοτίβο με τις σημειώσεις 'συγκέντρωση κλάδου' στο opportunity_alerts_log.md."""
    counts = {}
    for m in movers:
        if m.get("sector"):
            counts[m["sector"]] = counts.get(m["sector"], 0) + 1
    concentrated = {sector: n for sector, n in counts.items() if n >= 2}
    if not concentrated:
        return None
    parts = [f"{sector} ({n} μετοχές)" for sector, n in concentrated.items()]
    return "Συγκέντρωση κλάδου σήμερα: " + ", ".join(parts)


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    today = time.strftime("%Y-%m-%d", time.gmtime())

    print("Universe:")
    universe = build_universe()
    patterns = build_patterns(universe, BARE_MATCH_DENYLIST, NAME_OVERRIDES, allow_bare=False)
    known_tickers = set(universe.keys())

    print("\nBreaking (primary-source wires — πιθανά πρώιμα σήματα):")
    breaking = []
    for feed in BREAKING_FEEDS:
        try:
            items = fetch_breaking(feed, patterns, known_tickers)
            n_catalyst = sum(1 for it in items if it["catalyst"])
            n_small_cap = sum(1 for it in items if it["small_cap_risk"])
            print(f"  {feed['label']}: {len(items)} άρθρα ({n_catalyst} catalyst, {n_small_cap} small-cap risk)")
            breaking.extend(items)
        except (URLError, HTTPError, TimeoutError, OSError, ET.ParseError) as e:
            print(f"  ! {feed['label']}: αποτυχία ({e}) — παραλείπεται")

    # catalyst πρώτα, μετά πιο πρόσφατα — τα πιο αξιοπρόσεκτα άρθρα στην κορυφή
    breaking.sort(key=lambda a: (a["catalyst"], a["epoch"]), reverse=True)
    breaking = breaking[:150]  # μόνο τα πιο πρόσφατα — αυτό είναι ραντάρ, όχι αρχείο

    print("\nPipeline (τι δουλεύουν οι εταιρείες πριν φτάσουν σε αποτέλεσμα):")
    pipeline = []
    for feed in PIPELINE_FEEDS:
        try:
            items = fetch_breaking(feed, patterns, known_tickers)
            n_catalyst = sum(1 for it in items if it["catalyst"])
            print(f"  {feed['label']}: {len(items)} άρθρα ({n_catalyst} catalyst)")
            pipeline.extend(items)
        except (URLError, HTTPError, TimeoutError, OSError, ET.ParseError) as e:
            print(f"  ! {feed['label']}: αποτυχία ({e}) — παραλείπεται")
    pipeline.sort(key=lambda a: (a["catalyst"], a["epoch"]), reverse=True)
    pipeline = pipeline[:100]

    print("\nΜεγάλες κινήσεις τιμής (S&P 500, threshold +%.0f%% — ΕΠΙΒΕΒΑΙΩΣΗ, όχι πρόβλεψη):" % MOVE_THRESHOLD)
    try:
        movers = fetch_sp500_movers(universe)
        print(f"  Βρέθηκαν {len(movers)} μετοχές πάνω από το threshold")
    except (URLError, HTTPError, TimeoutError, OSError, ValueError) as e:
        print(f"  ! Αποτυχία fetch movers ({e})")
        movers = []

    if movers:
        print("  Εμπλουτισμός με θεμελιώδη/τεχνικά (Piotroski/Altman/RSI/PEG):")
        for m in movers:
            enrich_mover(m)
            print(f"    {m['ticker']}: archetype={m['archetype']} "
                  f"long_term={m['long_term_score']} swing={m['swing_score']}")

    movers_history = load_movers_history()
    movers_history = update_movers_history(movers_history, movers, today)
    for m in movers:
        m["streak_days"] = compute_streak(movers_history, m["ticker"], today)
    concentration_warning = sector_concentration_warning(movers)
    if concentration_warning:
        print(f"  ⚠️ {concentration_warning}")

    RADAR_JSON.write_text(
        json.dumps({
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "move_threshold_pct": MOVE_THRESHOLD,
            "movers": movers,
            "concentration_warning": concentration_warning,
            "breaking": breaking,
            "pipeline": pipeline,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    MOVERS_HISTORY_JSON.write_text(
        json.dumps(movers_history, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    n_catalyst_total = sum(1 for a in breaking if a["catalyst"])
    print(f"\nΈγραψα {len(movers)} movers + {len(breaking)} breaking "
          f"({n_catalyst_total} catalyst) + {len(pipeline)} pipeline -> {RADAR_JSON}")


if __name__ == "__main__":
    main()
