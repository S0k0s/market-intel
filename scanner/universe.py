"""
universe.py — Σταθερό universe μετοχών (ticker -> όνομα/κλάδος/ήπειρος) που
χρησιμοποιεί το aggregate.py για ticker-matching στα άρθρα ειδήσεων.

Seed data παρμένο/προσαρμοσμένο από το ~/trading-copilot/scanner/scan.py
(TICKERS + MARKET_META) — ίδιο universe concept, μικρότερο υποσύνολο εδώ
γιατί ο στόχος του market-intel δεν είναι πλήρες screening αλλά news-driven
ranking πάνω σε τα πιο likely-to-be-in-the-news ονόματα ανά κλάδο.
"""

# continent: "na" (Βόρεια Αμερική), "eu" (Ευρώπη), "as" (Ασία), "oc" (Ωκεανία)
UNIVERSE = {
    # --- Technology ---
    "NVDA": {"name": "NVIDIA", "sector": "Τεχνολογία", "continent": "na"},
    "AAPL": {"name": "Apple", "sector": "Τεχνολογία", "continent": "na"},
    "MSFT": {"name": "Microsoft", "sector": "Τεχνολογία", "continent": "na"},
    "GOOGL": {"name": "Alphabet", "sector": "Τεχνολογία", "continent": "na"},
    "AMZN": {"name": "Amazon", "sector": "Τεχνολογία", "continent": "na"},
    "META": {"name": "Meta Platforms", "sector": "Τεχνολογία", "continent": "na"},
    "AVGO": {"name": "Broadcom", "sector": "Τεχνολογία", "continent": "na"},
    "AMD": {"name": "Advanced Micro Devices", "sector": "Τεχνολογία", "continent": "na"},
    "ORCL": {"name": "Oracle", "sector": "Τεχνολογία", "continent": "na"},
    "CRM": {"name": "Salesforce", "sector": "Τεχνολογία", "continent": "na"},
    "ADBE": {"name": "Adobe", "sector": "Τεχνολογία", "continent": "na"},
    "PLTR": {"name": "Palantir Technologies", "sector": "Τεχνολογία", "continent": "na"},
    "CSCO": {"name": "Cisco Systems", "sector": "Τεχνολογία", "continent": "na"},
    "INTC": {"name": "Intel", "sector": "Τεχνολογία", "continent": "na"},
    "QCOM": {"name": "Qualcomm", "sector": "Τεχνολογία", "continent": "na"},
    "IBM": {"name": "IBM", "sector": "Τεχνολογία", "continent": "na"},
    "NOW": {"name": "ServiceNow", "sector": "Τεχνολογία", "continent": "na"},
    "PANW": {"name": "Palo Alto Networks", "sector": "Τεχνολογία", "continent": "na"},
    "ANET": {"name": "Arista Networks", "sector": "Τεχνολογία", "continent": "na"},
    "MU": {"name": "Micron Technology", "sector": "Τεχνολογία", "continent": "na"},
    # --- Automotive / Industrials ---
    "TSLA": {"name": "Tesla", "sector": "Αυτοκίνητο", "continent": "na"},
    "GE": {"name": "GE Aerospace", "sector": "Βιομηχανία", "continent": "na"},
    "CAT": {"name": "Caterpillar", "sector": "Βιομηχανία", "continent": "na"},
    "RTX": {"name": "RTX Corporation", "sector": "Άμυνα", "continent": "na"},
    "BA": {"name": "Boeing", "sector": "Αεροδιαστημική", "continent": "na"},
    # --- Financials ---
    "JPM": {"name": "JPMorgan Chase", "sector": "Τράπεζες", "continent": "na"},
    "BAC": {"name": "Bank of America", "sector": "Τράπεζες", "continent": "na"},
    "GS": {"name": "Goldman Sachs", "sector": "Τράπεζες", "continent": "na"},
    "MS": {"name": "Morgan Stanley", "sector": "Τράπεζες", "continent": "na"},
    "V": {"name": "Visa", "sector": "Πληρωμές", "continent": "na"},
    "MA": {"name": "Mastercard", "sector": "Πληρωμές", "continent": "na"},
    "PYPL": {"name": "PayPal", "sector": "Πληρωμές", "continent": "na"},
    "BLK": {"name": "BlackRock", "sector": "Χρηματοοικονομικά", "continent": "na"},
    # --- Energy ---
    "XOM": {"name": "ExxonMobil", "sector": "Ενέργεια", "continent": "na"},
    "CVX": {"name": "Chevron", "sector": "Ενέργεια", "continent": "na"},
    # --- Healthcare ---
    "LLY": {"name": "Eli Lilly", "sector": "Υγεία", "continent": "na"},
    "JNJ": {"name": "Johnson & Johnson", "sector": "Υγεία", "continent": "na"},
    "UNH": {"name": "UnitedHealth Group", "sector": "Υγεία", "continent": "na"},
    "ABBV": {"name": "AbbVie", "sector": "Υγεία", "continent": "na"},
    "MRK": {"name": "Merck & Co.", "sector": "Υγεία", "continent": "na"},
    "VRTX": {"name": "Vertex Pharmaceuticals", "sector": "Υγεία", "continent": "na"},
    # --- Consumer ---
    "WMT": {"name": "Walmart", "sector": "Λιανεμπόριο", "continent": "na"},
    "COST": {"name": "Costco Wholesale", "sector": "Λιανεμπόριο", "continent": "na"},
    "HD": {"name": "Home Depot", "sector": "Λιανεμπόριο", "continent": "na"},
    "NKE": {"name": "Nike", "sector": "Καταναλωτικά", "continent": "na"},
    "SBUX": {"name": "Starbucks", "sector": "Καταναλωτικά", "continent": "na"},
    "MCD": {"name": "McDonald's", "sector": "Καταναλωτικά", "continent": "na"},
    "KO": {"name": "Coca-Cola", "sector": "Καταναλωτικά", "continent": "na"},
    "PEP": {"name": "PepsiCo", "sector": "Καταναλωτικά", "continent": "na"},
    "DIS": {"name": "Walt Disney", "sector": "Μέσα Ενημέρωσης", "continent": "na"},
    "NFLX": {"name": "Netflix", "sector": "Μέσα Ενημέρωσης", "continent": "na"},
    "UBER": {"name": "Uber Technologies", "sector": "Μεταφορές", "continent": "na"},
    # --- Europe ---
    "SAP": {"name": "SAP", "sector": "Τεχνολογία", "continent": "eu"},
    "ASML": {"name": "ASML Holding", "sector": "Τεχνολογία", "continent": "eu"},
    "LVMH": {"name": "LVMH", "sector": "Πολυτέλεια", "continent": "eu"},
    "NESN": {"name": "Nestlé", "sector": "Καταναλωτικά", "continent": "eu"},
    "SHEL": {"name": "Shell", "sector": "Ενέργεια", "continent": "eu"},
    "AZN": {"name": "AstraZeneca", "sector": "Υγεία", "continent": "eu"},
    "NOVN": {"name": "Novartis", "sector": "Υγεία", "continent": "eu"},
    "SIE": {"name": "Siemens", "sector": "Βιομηχανία", "continent": "eu"},
    "HSBA": {"name": "HSBC", "sector": "Τράπεζες", "continent": "eu"},
    "BP": {"name": "BP", "sector": "Ενέργεια", "continent": "eu"},
    # --- Asia ---
    "TSM": {"name": "Taiwan Semiconductor", "sector": "Τεχνολογία", "continent": "as"},
    "BABA": {"name": "Alibaba Group", "sector": "Τεχνολογία", "continent": "as"},
    "TCEHY": {"name": "Tencent Holdings", "sector": "Τεχνολογία", "continent": "as"},
    "SONY": {"name": "Sony Group", "sector": "Τεχνολογία", "continent": "as"},
    "TM": {"name": "Toyota Motor", "sector": "Αυτοκίνητο", "continent": "as"},
    "SSNLF": {"name": "Samsung Electronics", "sector": "Τεχνολογία", "continent": "as"},
    "005930.KS": {"name": "Samsung Electronics (KRX)", "sector": "Τεχνολογία", "continent": "as"},
    # --- Oceania ---
    "BHP": {"name": "BHP Group", "sector": "Ορυκτά", "continent": "oc"},
    "CBA.AX": {"name": "Commonwealth Bank", "sector": "Τράπεζες", "continent": "oc"},
}

CONTINENT_LABELS = {
    "na": {"label": "Βόρεια Αμερική", "flag": "🇺🇸"},
    "eu": {"label": "Ευρώπη", "flag": "🇪🇺"},
    "as": {"label": "Ασία", "flag": "🌏"},
    "oc": {"label": "Ωκεανία", "flag": "🇦🇺"},
}
