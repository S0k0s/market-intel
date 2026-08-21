"""quality.py — Θεμελιώδη/τεχνικά δεδομένα ανά μετοχή + scoring, ίδια
μεθοδολογία με το trading-copilot (Long-Term Score & Swing Score, βλ.
trading-copilot/scanner/scan.py:448) — χρησιμοποιείται από το radar.py για να
ξεχωρίζει "υγιείς" κινήσεις τιμής (καλά θεμελιώδη/τεχνικά) από κερδοσκοπικά
spikes, αντί να επισημαίνει αδιακρίτως κάθε μετοχή που κινήθηκε >= threshold.
"""
import re
from urllib.request import Request

from net import HEADERS, urlopen_safe

LABELS_MAP = {
    "PE Ratio": "pe_ratio",
    "PEG Ratio": "peg_ratio",
    "Debt / Equity": "debt_equity",
    "Return on Equity (ROE)": "roe",
    "Relative Strength Index (RSI)": "rsi",
    "50-Day Moving Average": "ma50",
    "200-Day Moving Average": "ma200",
    "52-Week Price Change": "week52_change",
    "Beta (5Y)": "beta",
    "Price Target": "price_target",
    "EPS Growth Forecast (3Y)": "eps_growth_forecast_3y",
    "Altman Z-Score": "altman_z",
    "Piotroski F-Score": "piotroski_f",
    "Analyst Consensus": "analyst_consensus",
}


def to_number(txt):
    """'37.16%' -> 37.16, '1.94' -> 1.94, 'n/a' -> None, '5.03B' -> 5030000000.0"""
    if txt is None:
        return None
    t = txt.strip()
    if t in ("", "n/a", "N/A", "—", "-"):
        return None
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()")
    mult = 1
    if t.endswith("%"):
        t = t[:-1]
    elif t and t[-1] in "KMBT":
        mult = {"K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}[t[-1]]
        t = t[:-1]
    t = t.replace(",", "").replace("+", "").strip()
    try:
        val = float(t) * mult
        return -val if neg else val
    except ValueError:
        return None


def _clean(cell_html):
    text = re.sub(r"<[^>]+>", "", cell_html)
    return re.sub(r"\s+", " ", text).strip()


def fetch_fundamentals(ticker):
    """Κατεβάζει τη σελίδα στατιστικών (stockanalysis.com) ενός US ticker και
    επιστρέφει dict με τα βασικά θεμελιώδη/τεχνικά μεγέθη ήδη μετατραμμένα σε
    αριθμούς. Ελαφρύ regex-table parsing (χωρίς bs4/lxml εξάρτηση)."""
    slug = ticker.lower().replace(".", "-")
    url = f"https://stockanalysis.com/stocks/{slug}/statistics/"
    req = Request(url, headers=HEADERS)
    with urlopen_safe(req, timeout=15) as resp:
        html_text = resp.read().decode("utf-8", errors="replace")

    raw = {}
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", html_text, re.S):
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)
        if len(cells) != 2:
            continue
        label = _clean(cells[0])
        value = _clean(cells[1])
        if label and label not in raw:
            raw[label] = value

    stats = {key: to_number(raw.get(label)) for label, key in LABELS_MAP.items()}
    stats["analyst_consensus_text"] = raw.get("Analyst Consensus")
    return stats


def score_from(stats, price):
    """Ίδια μεθοδολογία με trading-copilot's score_from() — long_term_score
    (θεμελιώδη, 0-100) και swing_score (τεχνικά, 0-100)."""

    def clamp(v, lo, hi):
        return max(lo, min(hi, v))

    parts = []
    if stats.get("piotroski_f") is not None:
        parts.append(clamp(stats["piotroski_f"] / 9 * 100, 0, 100))
    if stats.get("altman_z") is not None:
        az = stats["altman_z"]
        parts.append(100 if az >= 3 else 0 if az < 1.8 else (az - 1.8) / 1.2 * 100)
    if stats.get("roe") is not None:
        parts.append(clamp(stats["roe"], 0, 30) / 30 * 100)
    if stats.get("peg_ratio") is not None and stats["peg_ratio"] > 0:
        pg = stats["peg_ratio"]
        parts.append(100 if pg <= 1 else 0 if pg >= 3 else (3 - pg) / 2 * 100)
    if stats.get("debt_equity") is not None:
        de = stats["debt_equity"]
        parts.append(100 if de <= 0 else 0 if de >= 2 else (2 - de) / 2 * 100)
    if stats.get("eps_growth_forecast_3y") is not None:
        parts.append(clamp(stats["eps_growth_forecast_3y"], 0, 50) / 50 * 100)
    long_term_score = round(sum(parts) / len(parts), 1) if parts else None

    sparts = []
    ma50, ma200 = stats.get("ma50"), stats.get("ma200")
    if price is not None and None not in (ma50, ma200):
        if price > ma50 > ma200:
            sparts.append(100)
        elif price < ma50 < ma200:
            sparts.append(0)
        else:
            sparts.append(50)
    if stats.get("rsi") is not None:
        rsi = stats["rsi"]
        if 45 <= rsi <= 65:
            sparts.append(100)
        else:
            edge = 45 if rsi < 45 else 65
            sparts.append(clamp(100 - abs(rsi - edge) * 4, 0, 100))
    if stats.get("week52_change") is not None:
        sparts.append(clamp(stats["week52_change"], 0, 100))
    if stats.get("beta") is not None:
        sparts.append(clamp(stats["beta"], 0, 3) / 3 * 100)
    swing_score = round(sum(sparts) / len(sparts), 1) if sparts else None

    return long_term_score, swing_score


def classify(stats, long_term_score, swing_score):
    """Αρχέτυπο ποιότητας της κίνησης — ίδια λογική με το χειρόγραφο
    opportunity_alerts_log.md: 'Quality Compounding' (ισχυρά θεμελιώδη),
    'Momentum Breakout' (ισχυρά τεχνικά), 'speculative' (αδύναμα θεμελιώδη —
    σημαία προσοχής, όχι αποκλεισμός), ή None όταν δεν υπάρχουν αρκετά
    δεδομένα να αποφασίσουμε."""
    if long_term_score is not None and long_term_score > 90:
        return "quality_compounding"
    if swing_score is not None and swing_score > 90:
        return "momentum_breakout"

    piotroski = stats.get("piotroski_f")
    altman = stats.get("altman_z")
    pe = stats.get("pe_ratio")
    if (piotroski is not None and piotroski < 4) or (altman is not None and altman < 1.8) or pe is None:
        return "speculative"

    return None
