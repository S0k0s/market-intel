"""lexicon.py — Κοινό deterministic, lexicon-based ανάλυση κειμένου (sentiment,
χρονικός ορίζοντας swing/long-term, ticker-matching) και RSS/XML parsing
helpers, χρησιμοποιούνται από aggregate.py και radar.py."""
import re
import time
import xml.etree.ElementTree as ET
from urllib.request import Request

from net import HEADERS, urlopen_safe

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


# --- Lexicon-based χρονικός ορίζοντας (swing vs long-term) ---
SWING_WORDS = {
    "breakout", "breakdown", "rally", "rallies", "surge", "surges", "plunge",
    "plunges", "spike", "spikes", "correction", "rebound", "selloff", "sell-off",
    "volatility", "volatile", "momentum", "technical", "intraday", "session",
    "shortsqueeze", "squeeze", "earnings", "quarterly", "quarter", "guidance",
    "beat", "beats", "misses", "premarket", "afterhours", "trading", "swing",
    "target price", "price target", "downgrade", "downgrades", "upgrade",
    "upgrades", "short-term", "week", "today", "tumble", "tumbles", "jump", "jumps",
}
LONGTERM_WORDS = {
    "dividend", "dividends", "buyback", "buybacks", "strategy", "strategic",
    "expansion", "expands", "acquisition", "acquires", "merger", "long-term",
    "restructuring", "ipo", "partnership", "joint venture", "pipeline", "patent",
    "sustainability", "market share", "annual", "decade", "years", "growth plan",
    "investment", "invests", "capex", "infrastructure", "roadmap", "outlook",
    "diversify", "diversification", "turnaround", "compound", "portfolio",
}
_SWING_MULTI = [w for w in SWING_WORDS if " " in w or "-" in w]
_LONGTERM_MULTI = [w for w in LONGTERM_WORDS if " " in w or "-" in w]


def horizon_of(text):
    """Ταξινομεί ένα άρθρο ως 'swing', 'long_term' ή None (χωρίς σαφές σήμα),
    βάσει πλήθους λέξεων-κλειδιών κάθε κατηγορίας στο κείμενο."""
    lower = (text or "").lower()
    words = set(WORD_RE.findall(lower))
    swing = sum(1 for w in words if w in SWING_WORDS)
    swing += sum(1 for phrase in _SWING_MULTI if phrase in lower)
    longterm = sum(1 for w in words if w in LONGTERM_WORDS)
    longterm += sum(1 for phrase in _LONGTERM_MULTI if phrase in lower)
    if swing == 0 and longterm == 0:
        return None
    if swing > longterm:
        return "swing"
    if longterm > swing:
        return "long_term"
    return None


# --- Ticker matching: name/override + word-boundary ticker match στον τίτλο/summary ---
# Bare-symbol matching αγνοείται για σύμβολα μήκους < 3 (π.χ. "T", "K", "L", "H")
# — με 1000+ tickers στο universe, τέτοια μονο/δι-γράμματα σύμβολα θα ταίριαζαν
# σχεδόν σε κάθε άρθρο (false positives). Σε αυτές τις περιπτώσεις χρησιμοποιείται
# μόνο το πλήρες όνομα εταιρείας (ή το "match" override).
def build_patterns(universe, bare_denylist, name_overrides, allow_bare=True):
    """allow_bare=False απενεργοποιεί εντελώς το bare-ticker matching (μόνο πλήρες
    όνομα εταιρείας) — χρήσιμο για corpora με πολλά ακρωνύμια (SEC/FDA κείμενα),
    όπου π.χ. "NWS" (News Corp) ταιριάζει λάθος σε "New World Screwworm (NWS)"."""
    patterns = {}
    for tk, meta in universe.items():
        bare = tk.split(".")[0]
        match_phrase = meta.get("match") or name_overrides.get(tk) or meta["name"]
        alts = [re.escape(match_phrase)]
        if allow_bare and len(bare) >= 3 and bare.upper() not in bare_denylist:
            alts.append(re.escape(bare))
        patterns[tk] = re.compile(rf"\b({'|'.join(alts)})\b", re.IGNORECASE)
    return patterns


def match_tickers(text, patterns):
    hits = []
    for tk, pat in patterns.items():
        if pat.search(text or ""):
            hits.append(tk)
    return hits


def strip_html(s):
    return re.sub(r"<[^>]+>", " ", s or "").strip()


def parse_rss_date(s):
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


def fetch_rss_items(url, headers=None):
    """Γενικό RSS/RDF/Atom parsing: επιστρέφει λίστα από {title, summary, url, epoch}.
    Υποστηρίζει RSS <item> και Atom <entry> (π.χ. SEC EDGAR), όπου το link είναι
    attribute (href) αντί για text-content."""
    req = Request(url, headers=headers or HEADERS)
    with urlopen_safe(req) as resp:
        raw = resp.read()
    root = ET.fromstring(raw)
    items = [el for el in root.iter() if _local(el.tag) in ("item", "entry")]
    out = []
    for it in items:
        title = strip_html(_child_text(it, "title"))
        if not title:
            continue
        desc = strip_html(
            _child_text(it, "description") or _child_text(it, "encoded")
            or _child_text(it, "summary") or _child_text(it, "content")
        )
        link = _child_text(it, "link") or it.attrib.get(
            "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about", ""
        )
        if not link:
            for child in it:
                if _local(child.tag) == "link":
                    link = child.attrib.get("href", "")
                    break
        pub = (
            _child_text(it, "pubDate") or _child_text(it, "date")
            or _child_text(it, "updated") or _child_text(it, "published")
        )
        epoch = parse_rss_date(pub) or int(time.time())
        out.append({"title": title, "summary": desc[:280], "url": link, "epoch": epoch})
    return out
