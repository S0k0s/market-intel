"""
universe.py — Universe μετοχών (ticker -> όνομα/κλάδος/ήπειρος) που χρησιμοποιεί
το aggregate.py για ticker-matching στα άρθρα ειδήσεων.

Δύο κομμάτια:
  1. STATIC_INTL — επιμελημένες, σταθερές λίστες δεικτών (FTSE 100, DAX 40, Hang
     Seng, S&P/TSX 60) παρμένες από trading-copilot/scanner/scan.py (πηγή:
     Wikipedia, βλ. σχόλια εκεί). Δεν αλλάζουν συχνά, οπότε δεν χρειάζεται live
     fetch — μειώνει και το ρίσκο false-positive matching σε dual-listed
     αμερικανικές εταιρείες που κυριαρχούν στις raw λίστες του stockanalysis.com.
  2. fetch_sp500() — δυναμικό universe ΗΠΑ: όλο το S&P 500 (ticker, name, GICS
     sector) από τον πίνακα της Wikipedia, ένα request. Αν αποτύχει το δίκτυο,
     πέφτουμε σε ένα μικρό στατικό fallback (SP500_FALLBACK) ώστε το app να
     συνεχίζει να δουλεύει με μειωμένο (αλλά όχι μηδενικό) universe.

Το προαιρετικό κλειδί "match" σε μια εγγραφή ορίζει τη λέξη/φράση που ψάχνει
το aggregate.py στον τίτλο/περίληψη άρθρου αντί για το πλήρες "name" — για
tickers με πολύ γενικό όνομα εταιρείας. Το ticker-matching σε bare symbol
αγνοεί σύμβολα μήκους < 3 (π.χ. "T", "K", "L") — πολύ μεγάλο ρίσκο false
positive σε 1000+ tickers.
"""
import html
import re
from urllib.request import Request
from urllib.error import URLError, HTTPError

from net import HEADERS, urlopen_safe as _urlopen


CONTINENT_LABELS = {
    "na": {"label": "Βόρεια Αμερική", "flag": "🇺🇸"},
    "eu": {"label": "Ευρώπη", "flag": "🇪🇺"},
    "as": {"label": "Ασία", "flag": "🌏"},
    "oc": {"label": "Ωκεανία", "flag": "🇦🇺"},
}

GICS_SECTOR_EL = {
    "Information Technology": "Τεχνολογία",
    "Health Care": "Υγεία",
    "Financials": "Χρηματοοικονομικά",
    "Consumer Discretionary": "Καταναλωτικά (Επιλογής)",
    "Consumer Staples": "Καταναλωτικά (Βασικά)",
    "Energy": "Ενέργεια",
    "Industrials": "Βιομηχανία",
    "Utilities": "Ενεργειακές Υπηρεσίες",
    "Real Estate": "Ακίνητα",
    "Materials": "Ορυκτά/Υλικά",
    "Communication Services": "Επικοινωνίες/Μέσα",
}

# --- Βρετανία (FTSE 100) — πηγή Wikipedia, βλ. trading-copilot/scanner/scan.py ---
FTSE_100 = {
    "III": "3i Group", "ABDN": "Aberdeen Group", "ADM": "Admiral Group", "AAF": "Airtel Africa",
    "ALW": "Alliance Witan", "AAL": "Anglo American", "ANTO": "Antofagasta", "ABF": "Associated British Foods",
    "AZN": "AstraZeneca", "AUTO": "Auto Trader Group", "AV": "Aviva", "BAB": "Babcock International",
    "BA": "BAE Systems", "BARC": "Barclays", "BTRW": "Barratt Redrow", "BEZ": "Beazley",
    "BP": "BP", "BATS": "British American Tobacco", "BLND": "British Land", "BT.A": "BT Group",
    "BNZL": "Bunzl", "BRBY": "Burberry", "CNA": "Centrica", "CCEP": "Coca-Cola Europacific Partners",
    "CCH": "Coca-Cola HBC", "CPG": "Compass Group", "CCC": "Computacenter", "CTEC": "Convatec Group",
    "CRDA": "Croda International", "DCC": "DCC", "DGE": "Diageo", "DPLM": "Diploma",
    "EDV": "Endeavour Mining", "ENT": "Entain", "EXPN": "Experian", "FCIT": "F&C Investment Trust",
    "FRES": "Fresnillo", "GAW": "Games Workshop", "GLEN": "Glencore", "GSK": "GSK",
    "HLN": "Haleon", "HLMA": "Halma", "HSX": "Hiscox", "HWDN": "Howdens Joinery",
    "HSBA": "HSBC Holdings", "ICG": "ICG", "IGG": "IG Group", "IHG": "IHG Hotels & Resorts",
    "IMI": "IMI", "IMB": "Imperial Brands", "INF": "Informa", "IAG": "International Airlines Group",
    "ITRK": "Intertek Group", "INVP": "Investec", "JD": "JD Sports Fashion", "BGEO": "Lion Finance Group",
    "KGF": "Kingfisher", "LAND": "Land Securities", "LGEN": "Legal & General", "LLOY": "Lloyds Banking Group",
    "LMP": "LondonMetric Property", "LSEG": "London Stock Exchange Group", "MNG": "M&G", "MKS": "Marks & Spencer",
    "MRO": "Melrose Industries", "MTLN": "Metlen Energy & Metals", "NG": "National Grid", "NWG": "NatWest Group",
    "NXT": "Next", "PSON": "Pearson", "PSH": "Pershing Square Holdings", "PSN": "Persimmon",
    "PCT": "Polar Capital Technology Trust", "PRU": "Prudential", "RKT": "Reckitt Benckiser", "REL": "RELX",
    "RTO": "Rentokil Initial", "RIO": "Rio Tinto", "RR": "Rolls-Royce Holdings", "SGE": "Sage Group",
    "SBRY": "Sainsbury's", "SDR": "Schroders", "SMT": "Scottish Mortgage Investment Trust", "SGRO": "Segro",
    "SVT": "Severn Trent", "SHEL": "Shell", "SMIN": "Smiths Group", "SN": "Smith & Nephew",
    "SPX": "Spirax Group", "SSE": "SSE", "STAN": "Standard Chartered", "SDLF": "Standard Life",
    "STJ": "St. James's Place", "TSCO": "Tesco", "BBOX": "Tritax Big Box REIT", "ULVR": "Unilever",
    "UU": "United Utilities", "VOD": "Vodafone Group", "WEIR": "Weir Group", "WTB": "Whitbread",
}

# --- Γερμανία (DAX 40) ---
DAX_40 = {
    "ADS": "Adidas", "AIR": "Airbus", "ALV": "Allianz", "BAS": "BASF",
    "BAYN": "Bayer", "BEI": "Beiersdorf", "BMW": "BMW", "BNR": "Brenntag",
    "CBK": "Commerzbank", "CON": "Continental", "DTG": "Daimler Truck", "DBK": "Deutsche Bank",
    "DB1": "Deutsche Börse", "DHL": "DHL Group", "DTE": "Deutsche Telekom", "EOAN": "E.ON",
    "FRE": "Fresenius", "FME": "Fresenius Medical Care", "G1A": "GEA Group", "HNR1": "Hannover Re",
    "HEI": "Heidelberg Materials", "HEN3": "Henkel", "IFX": "Infineon Technologies", "MBG": "Mercedes-Benz Group",
    "MRK": "Merck KGaA", "MTX": "MTU Aero Engines", "MUV2": "Munich Re", "PAH3": "Porsche SE",
    "QIA": "Qiagen", "RHM": "Rheinmetall", "RWE": "RWE", "SAP": "SAP",
    "G24": "Scout24", "SIE": "Siemens", "ENR": "Siemens Energy", "SHL": "Siemens Healthineers",
    "SY1": "Symrise", "VOW3": "Volkswagen", "VNA": "Vonovia", "ZAL": "Zalando",
}

# --- Hong Kong (Hang Seng) ---
HANG_SENG = {
    "0005": "HSBC Holdings", "0388": "HKEX", "0939": "China Construction Bank", "1299": "AIA Group",
    "1398": "ICBC", "2318": "Ping An Insurance", "2388": "BOC Hong Kong", "2628": "China Life Insurance",
    "3968": "China Merchants Bank", "3988": "Bank of China", "0002": "CLP Holdings", "0003": "Hong Kong and China Gas",
    "0006": "Power Assets Holdings", "0836": "China Resources Power", "1038": "CK Infrastructure Holdings", "2688": "ENN Energy",
    "0012": "Henderson Land Development", "0016": "Sun Hung Kai Properties", "0101": "Hang Lung Properties", "0688": "China Overseas Land & Investment",
    "0823": "Link REIT", "0960": "Longfor Group", "1109": "China Resources Land", "1113": "CK Asset Holdings",
    "1209": "China Resources Mixc Lifestyle", "1997": "Wharf REIC", "0001": "CK Hutchison Holdings", "0027": "Galaxy Entertainment Group",
    "0066": "MTR Corporation", "0175": "Geely Auto", "0241": "Alibaba Health", "0267": "CITIC",
    "0285": "BYD Electronic", "0288": "WH Group", "0291": "China Resources Beer", "0300": "Midea Group",
    "0316": "Orient Overseas International", "0322": "Tingyi", "0386": "Sinopec Corp", "0669": "Techtronic Industries",
    "0700": "Tencent Holdings", "0762": "China Unicom Hong Kong", "0857": "PetroChina", "0868": "Xinyi Glass",
    "0881": "Zhongsheng Group", "0883": "CNOOC", "0941": "China Mobile", "0968": "Xinyi Solar",
    "0981": "SMIC", "0992": "Lenovo Group", "1024": "Kuaishou Technology", "1044": "Hengan International",
    "1088": "China Shenhua Energy", "1093": "CSPC Pharmaceutical Group", "1099": "Sinopharm Group", "1177": "Sino Biopharmaceutical",
    "1211": "BYD Company", "1378": "China Hongqiao Group", "1810": "Xiaomi", "1876": "Budweiser APAC",
    "1928": "Sands China", "1929": "Chow Tai Fook Jewellery", "2015": "Li Auto", "2020": "Anta Sports",
    "2057": "ZTO Express", "2269": "WuXi Biologics", "2313": "Shenzhou International", "2319": "China Mengniu Dairy",
    "2331": "Li Ning", "2359": "WuXi AppTec", "2382": "Sunny Optical Technology", "2618": "JD Logistics",
    "2899": "Zijin Mining", "3690": "Meituan", "3692": "Hansoh Pharmaceutical", "6618": "JD Health International",
    "6690": "Haier Smart Home", "6862": "Haidilao International", "9618": "JD.com", "9633": "Nongfu Spring",
    "9888": "Baidu", "9961": "Trip.com Group", "9988": "Alibaba Group", "9992": "Pop Mart",
    "9999": "NetEase",
}

# --- Καναδάς (S&P/TSX 60) ---
TSX_60 = {
    "AEM": "Agnico Eagle Mines", "ATD": "Alimentation Couche-Tard", "BMO": "Bank of Montreal", "BNS": "Bank of Nova Scotia",
    "ABX": "Barrick Mining", "BCE": "BCE", "BAM": "Brookfield Asset Management", "BN": "Brookfield Corporation",
    "BIP.UN": "Brookfield Infrastructure Partners", "CAE": "CAE", "CCO": "Cameco", "CM": "Canadian Imperial Bank of Commerce",
    "CNR": "Canadian National Railway", "CNQ": "Canadian Natural Resources", "CP": "Canadian Pacific Kansas City", "CTC.A": "Canadian Tire",
    "CCL.B": "CCL Industries", "CLS": "Celestica", "CVE": "Cenovus Energy", "GIB.A": "CGI",
    "CSU": "Constellation Software", "DOL": "Dollarama", "EMA": "Emera", "ENB": "Enbridge",
    "FFH": "Fairfax Financial Holdings", "FM": "First Quantum Minerals", "FSV": "FirstService", "FTS": "Fortis",
    "FNV": "Franco-Nevada", "WN": "George Weston", "GIL": "Gildan Activewear", "H": "Hydro One",
    "IMO": "Imperial Oil", "IFC": "Intact Financial", "K": "Kinross Gold", "L": "Loblaw Companies",
    "MG": "Magna International", "MFC": "Manulife Financial", "MRU": "Metro", "NA": "National Bank of Canada",
    "NTR": "Nutrien", "OTEX": "Open Text", "PPL": "Pembina Pipeline", "POW": "Power Corporation of Canada",
    "QSR": "Restaurant Brands International", "RCI.B": "Rogers Communications", "RY": "Royal Bank of Canada", "SAP.TO": "Saputo",
    "SHOP": "Shopify", "SLF": "Sun Life Financial", "SU": "Suncor Energy", "TRP": "TC Energy",
    "TECK.B": "Teck Resources", "T": "Telus", "TRI": "Thomson Reuters", "TD": "Toronto-Dominion Bank",
    "TOU": "Tourmaline Oil", "WCN": "Waste Connections", "WPM": "Wheaton Precious Metals", "WSP": "WSP Global",
}

# --- Ασία/Ωκεανία εκτός Hang Seng (επιλεγμένα μεγάλα ονόματα, δεν καλύπτονται
#     από κάποιον απλό δείκτη με ενιαία Wikipedia λίστα) ---
ASIA_OCEANIA_EXTRA = {
    "TSM": {"name": "Taiwan Semiconductor", "sector": "Ημιαγωγοί", "continent": "as", "match": "Taiwan Semiconductor"},
    "SONY": {"name": "Sony Group", "sector": "Τεχνολογία", "continent": "as", "match": "Sony"},
    "TM": {"name": "Toyota Motor", "sector": "Αυτοκίνητο", "continent": "as", "match": "Toyota"},
    "HMC": {"name": "Honda Motor", "sector": "Αυτοκίνητο", "continent": "as", "match": "Honda"},
    "005930.KS": {"name": "Samsung Electronics", "sector": "Τεχνολογία", "continent": "as", "match": "Samsung"},
    "005380.KS": {"name": "Hyundai Motor", "sector": "Αυτοκίνητο", "continent": "as", "match": "Hyundai"},
    "PDD": {"name": "PDD Holdings", "sector": "Τεχνολογία", "continent": "as", "match": "PDD Holdings"},
    "INFY": {"name": "Infosys", "sector": "Τεχνολογία", "continent": "as", "match": "Infosys"},
    "TCS.NS": {"name": "Tata Consultancy Services", "sector": "Τεχνολογία", "continent": "as", "match": "Tata Consultancy"},
    "RELIANCE.NS": {"name": "Reliance Industries", "sector": "Ενέργεια", "continent": "as", "match": "Reliance Industries"},
    "BHP": {"name": "BHP Group", "sector": "Ορυκτά/Υλικά", "continent": "oc", "match": "BHP"},
    "CBA.AX": {"name": "Commonwealth Bank", "sector": "Χρηματοοικονομικά", "continent": "oc", "match": "Commonwealth Bank"},
    "WES.AX": {"name": "Wesfarmers", "sector": "Καταναλωτικά (Επιλογής)", "continent": "oc", "match": "Wesfarmers"},
    "CSL.AX": {"name": "CSL Limited", "sector": "Υγεία", "continent": "oc", "match": "CSL Limited"},
}

# --- Ευρώπη εκτός FTSE/DAX (μεγάλα ονόματα Euronext/SIX κ.λπ.) ---
EUROPE_EXTRA = {
    "ASML": {"name": "ASML Holding", "sector": "Ημιαγωγοί", "continent": "eu", "match": "ASML"},
    "MC.PA": {"name": "LVMH", "sector": "Πολυτέλεια", "continent": "eu", "match": "LVMH"},
    "OR.PA": {"name": "L'Oréal", "sector": "Καταναλωτικά (Επιλογής)", "continent": "eu", "match": "L'Oréal"},
    "NESN": {"name": "Nestlé", "sector": "Καταναλωτικά (Βασικά)", "continent": "eu", "match": "Nestlé"},
    "TTE": {"name": "TotalEnergies", "sector": "Ενέργεια", "continent": "eu", "match": "TotalEnergies"},
    "NOVN": {"name": "Novartis", "sector": "Υγεία", "continent": "eu", "match": "Novartis"},
    "ROG": {"name": "Roche Holding", "sector": "Υγεία", "continent": "eu", "match": "Roche"},
    "AIR.PA": {"name": "Airbus (Euronext)", "sector": "Αεροδιαστημική", "continent": "eu", "match": "Airbus"},
    "INGA": {"name": "ING Group", "sector": "Χρηματοοικονομικά", "continent": "eu", "match": "ING Group"},
    "IBE": {"name": "Iberdrola", "sector": "Ενεργειακές Υπηρεσίες", "continent": "eu", "match": "Iberdrola"},
}

# Σύμβολα (bare ticker, χωρίς suffix) που τυχαίνει να είναι κοινές αγγλικές
# λέξεις — σε universe 800+ tickers, το \bLOW\b ή \bARE\b θα ταίριαζε σε σχεδόν
# κάθε άρθρο. Γι' αυτά τα tickers γίνεται matching ΜΟΝΟ βάσει πλήρους ονόματος
# εταιρείας (ή "match" override), ποτέ βάσει bare symbol.
BARE_MATCH_DENYLIST = {
    "ALL", "ARE", "HAS", "TECH", "WELL", "COST", "KEY", "GEN", "FAST", "CAT",
    "PAY", "TAP", "ICE", "HON", "BEN", "DAY", "LOW", "SO", "ON", "GOOD", "WIN",
    "SEE", "OWN", "OUT", "FOR", "ANY", "ARM", "BIG", "TRUE", "REAL", "NOW",
}

# Εταιρείες όπου ακόμα και το πλήρες (καθαρισμένο) όνομα είναι πολύ γενικό /
# διφορούμενο (π.χ. "Target", "Dow") — override σε πιο συγκεκριμένη φράση.
NAME_OVERRIDES = {
    "TGT": "Target Corp",
    "DOW": "Dow Inc",
    "SO": "Southern Company",
    "NDAQ": "Nasdaq, Inc.",
    "XYZ": "Block, Inc.",
    "BALL": "Ball Corporation",
    "FLEX": "Flex Ltd",
    "MRU.TO": "Metro Inc.",
    "GIB.A.TO": "CGI Inc",
    "NXT.L": "Next plc",
    "SSE.L": "SSE plc",
    "0388.HK": "Hong Kong Exchanges and Clearing",
}

# --- ΗΠΑ: μικρό στατικό fallback αν αποτύχει το live fetch του S&P 500 ---
SP500_FALLBACK = {
    "NVDA": "NVIDIA", "AAPL": "Apple", "MSFT": "Microsoft", "GOOGL": "Alphabet",
    "AMZN": "Amazon", "META": "Meta Platforms", "AVGO": "Broadcom", "TSLA": "Tesla",
    "JPM": "JPMorgan Chase", "V": "Visa", "MA": "Mastercard", "WMT": "Walmart",
    "XOM": "ExxonMobil", "UNH": "UnitedHealth Group", "LLY": "Eli Lilly", "PG": "Procter & Gamble",
    "HD": "Home Depot", "COST": "Costco Wholesale", "AMD": "Advanced Micro Devices", "NFLX": "Netflix",
}


def _build_intl_entries():
    out = dict(EUROPE_EXTRA)
    out.update(ASIA_OCEANIA_EXTRA)
    for tk, name in FTSE_100.items():
        out[f"{tk}.L"] = {"name": name, "sector": None, "continent": "eu"}
    for tk, name in DAX_40.items():
        out[f"{tk}.DE"] = {"name": name, "sector": None, "continent": "eu"}
    for tk, name in HANG_SENG.items():
        out[f"{tk}.HK"] = {"name": name, "sector": None, "continent": "as"}
    for tk, name in TSX_60.items():
        # πολλά TSX tickers μοιάζουν με αμερικανικά (T, K, L, H) — πάντα suffix .TO
        base = tk if tk.endswith(".TO") else f"{tk}.TO"
        out[base] = {"name": name, "sector": None, "continent": "na"}
    return out


def _clean_company_name(name):
    name = re.sub(
        r"(?:,?\s+(?:Inc|Corp|Corporation|Co|Company|plc|PLC|Ltd|Limited|Group|Holdings?)\.?"
        r"|\s+S\.?A\.?|\s+N\.?V\.?)$",
        "", name.strip(),
    )
    return name.strip() or name


def fetch_sp500():
    """Δυναμικό universe ΗΠΑ: όλο το S&P 500 (ticker, name, GICS sector) από τον
    πίνακα συστατικών στη Wikipedia. Επιστρέφει dict ticker -> entry, ή None αν
    αποτύχει το fetch."""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    try:
        req = Request(url, headers=HEADERS)
        with _urlopen(req) as resp:
            raw_html = resp.read().decode("utf-8", errors="replace")
    except (URLError, HTTPError, TimeoutError, OSError) as e:
        print(f"  ! Αποτυχία λήψης S&P 500 από Wikipedia ({e}) — χρήση στατικού fallback.")
        return None

    # Ελαφρύ HTML-table parsing χωρίς εξάρτηση σε bs4/lxml: βρίσκουμε την πρώτη
    # <table id="constituents">...</table> και τις γραμμές της.
    m = re.search(r'<table[^>]*id="constituents"[^>]*>(.*?)</table>', raw_html, re.S)
    if not m:
        print("  ! Δεν βρέθηκε ο πίνακας 'constituents' στη σελίδα Wikipedia — fallback.")
        return None
    table_html = m.group(1)
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table_html, re.S)
    out = {}
    for row in rows[1:]:
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
        if len(cells) < 4:
            continue

        def cell_text(html_cell):
            text = re.sub(r"<[^>]+>", "", html_cell)
            return html.unescape(re.sub(r"\s+", " ", text).strip())

        ticker = cell_text(cells[0])
        name = _clean_company_name(cell_text(cells[1]))
        sector_en = cell_text(cells[2])
        if not ticker or not name:
            continue
        out[ticker] = {
            "name": name,
            "sector": GICS_SECTOR_EL.get(sector_en, sector_en or None),
            "continent": "na",
        }
    if len(out) < 400:
        print(f"  ! Πίνακας S&P 500 έδωσε μόνο {len(out)} tickers — fallback.")
        return None
    return out


def build_universe():
    """Τελικό universe: S&P 500 (δυναμικό, με sector fallback στο στατικό
    SP500_FALLBACK αν αποτύχει το δίκτυο) + επιμελημένες διεθνείς λίστες."""
    sp500 = fetch_sp500()
    universe = {}
    if sp500:
        universe.update(sp500)
        print(f"  S&P 500: {len(sp500)} tickers (live, με sector)")
    else:
        universe.update({tk: {"name": n, "sector": None, "continent": "na"} for tk, n in SP500_FALLBACK.items()})
        print(f"  S&P 500: {len(SP500_FALLBACK)} tickers (στατικό fallback)")

    intl = _build_intl_entries()
    for tk, entry in intl.items():
        universe.setdefault(tk, entry)
    print(f"  Διεθνείς λίστες (FTSE/DAX/HangSeng/TSX/λοιπά): {len(intl)} tickers")
    print(f"  Σύνολο universe: {len(universe)} tickers")
    return universe


# Υπολογίζεται μία φορά ανά εκτέλεση του aggregate.py — δες scanner/aggregate.py.
UNIVERSE = None
