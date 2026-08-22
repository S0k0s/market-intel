# Early-Alert "Star Tab" Feature — Handoff Doc

Context doc για το υπάρχον trading/code app. Στόχος: προσθήκη ενός ξεχωριστού tab ("το αστέρι του UI") που εντοπίζει όσο το δυνατόν πιο νωρίς μετοχές που κάνουν απότομο άλμα τιμής, πριν/ενώ γίνεται ευρέως γνωστό.

Παράδειγμα-έναυσμα: η μετοχή της Moderna (MRNA) έκλεισε στις 19/8/2026 στα $174.38, +176.97% ($+111.42) σε μία ημέρα, με όγκο ~185.1M μετοχών (~1,819% πάνω από τον μέσο όρο τριμήνου ~9.6M) — το μεγαλύτερο ημερήσιο ποσοστιαίο κέρδος της στην ιστορία της. Ο καταλύτης ήταν η ανακοίνωση θετικών αποτελεσμάτων Φάσης 3 (INTerpath-001, μελάνωμα, mRNA εμβόλιο σε συνδυασμό με Keytruda). Merck +12.6%, BioNTech +21.96% την ίδια ημέρα σε συμπάθεια. Αυτό είναι το prototype pattern: catalyst → gap up πριν το ευρύ κοινό προλάβει να αντιδράσει.

---

## 0. Σχέση με το υπάρχον Claude skill (context, όχι μέρος του app)

Παράλληλα με αυτό το feature υπάρχει ήδη ένα ξεχωριστό, **χειροκίνητο** Claude skill (`catalyst-news-scout`) που κάνει on-demand έρευνα μέσα σε συνομιλία για επερχόμενα catalysts (FDA dates, trial readouts, conference agendas) — **προληπτικό ημερολόγιο, όχι live monitoring**. Δεν αντικαθιστά αυτό το feature και δεν χρειάζεται να ενσωματωθεί στο codebase· είναι ξεχωριστό εργαλείο για ad-hoc research. Αναφέρεται εδώ μόνο για να μην υπάρξει σύγχυση αν εμφανιστεί σε άλλο πλαίσιο.

---

## 1. Απαιτήσεις όπως ορίστηκαν

- **Threshold ενεργοποίησης:** ≥ 20% άμεσο κέρδος τιμής (intraday ή short-window spike)
- **UI:** ξεχωριστό, διακριτό tab μέσα στο υπάρχον app — το "αστέρι" της εφαρμογής
- **Κάλυψη αγοράς:** **παγκόσμια** (όχι μόνο ΗΠΑ)
- **Πηγές δεδομένων:** ξεκινάμε από **δωρεάν/ανοιχτές** πηγές πρώτα, με δυνατότητα προσθήκης **επί πληρωμή** υπηρεσιών αργότερα για ταχύτητα — πάντα με επαλήθευση εγκυρότητας/ενεργότητας κάθε πηγής
- **Κανόνας:** καμία πηγή δεν πρέπει να εμπλέκει μη-δημόσια/insider πληροφορία (MNPI) — μόνο νόμιμα, δημόσια, ταχύτατα διαθέσιμα δεδομένα
- Standing κανόνες του project που ισχύουν και εδώ: καμία εγγύηση αποτελέσματος, καμία αναφορά win-rate από prediction sites ως αξιόπιστη πηγή, κάθε πρόβλεψη αποδίδεται στην πηγή της, ποτέ δεν παρουσιάζεται candidate ως σίγουρο.

---

## 2. Αρχιτεκτονική προσέγγιση (σύνοψη)

Δεν υπάρχει μία πηγή που καλύπτει τα πάντα. Χρειάζονται **δύο παράλληλα επίπεδα**:

1. **Price layer (trigger):** real-time/near-real-time feed τιμών → υπολογισμός `pct = (last - prevClose) / prevClose * 100` → flag όταν `pct >= 20`. Απαιτείται φίλτρο ελάχιστου όγκου/liquidity ώστε να αποφεύγονται false positives σε αραιά διαπραγματεύσιμους τίτλους.
2. **Catalyst layer (το "γιατί", ιδανικά νωρίτερα από το πλήρες 20%):** feeds ειδήσεων/filings που ταιριάζουν το ticker με το flagged price move και δίνουν τον λόγο της κίνησης.

**Push > Poll:** όπου υπάρχει WebSocket/webhook, προτιμάται έναντι polling (δευτερόλεπτα vs λεπτά διαφορά).

**UX πρόταση για το tab:** ranking κατά % κίνηση × πρόσφατο, με επισυναπτόμενο headline/filing ως "λόγος", και badge εμπιστοσύνης/ταχύτητας (π.χ. "catalyst εντοπίστηκε 8s πριν το 20% threshold").

---

## 3. Πηγές — Στάδιο 1: Δωρεάν (ξεκινάμε από εδώ)

### Price / Screener APIs
- **Finnhub** (finnhub.io) — Δωρεάν: 60 calls/min, real-time US quotes, WebSocket trades (`wss://ws.finnhub.io`) περιορισμένο σε **50 σύμβολα**, real-time news feed. Paid tiers ($11.99–$99.99/mo) προσθέτουν διεθνείς μετοχές + unlimited WebSocket symbols.
- **Alpaca** (alpaca.markets) — Δωρεάν "Basic": real-time IEX-based WebSocket (τιμές + trades + bars) `wss://stream.data.alpaca.markets/v2/iex`, ΚΑΙ δωρεάν **news WebSocket** `wss://stream.data.alpaca.markets/v1beta1/news`, plus screener endpoint (top movers). REST είναι 15-min delayed στο δωρεάν. Paid ($99/mo) = full SIP, options, 10,000 req/min.
- **Financial Modeling Prep (FMP)** — έτοιμο endpoint `/api/v3/stock_market/gainers` και `/stable/biggest-gainers` (symbol, price, %change). Φτηνό unlimited tier ~$19/mo. Χρήσιμο: poll κάθε 30–60s, φίλτρο `changesPercentage >= 20`.
- Δευτερεύοντα: **Twelve Data** (800 calls/day δωρεάν, delayed data στο free), **Alpha Vantage** (μόνο 25 req/day δωρεάν — πολύ περιορισμένο για live), **Tiingo**, **EODHD** (φτηνή global ιστορική/EOD κάλυψη).
- **Αποφυγή:** yfinance/scraped Yahoo endpoints — unofficial, ασταθές.
- ⚠️ **IEX Cloud έκλεισε οριστικά τον Αύγουστο 2024** — να μην χρησιμοποιηθεί σε καμία τεκμηρίωση/tutorial που το αναφέρει.

### News / Filings (καταλύτες)
- **SEC EDGAR** (δωρεάν, ΗΠΑ) — "Latest Filings" RSS/Atom feed, φίλτρο σε 8-K. Πλησιέστερο σε real-time (ανεπίσημη μελέτη: median ~24s από αποδοχή filing μέχρι εμφάνιση σε RSS). **Όριο: 10 requests/δευτερόλεπτο**, υποχρεωτικό User-Agent header με email, αλλιώς μπλοκάρισμα IP. Structured/XBRL RSS ενημερώνεται μόνο ανά 10 λεπτά — να ΜΗΝ χρησιμοποιηθεί για ταχύτητα.
- **openFDA** (api.fda.gov, δωρεάν) — εγκρίσεις φαρμάκων. Χωρίς key: 240 req/min, 1,000 req/day. Με δωρεάν key: 240/min, 120,000/day. Καλύπτει biotech καταλύτες τύπου Moderna.
- **ClinicalTrials.gov API** (δωρεάν) — αλλαγές status trials (π.χ. "Completed", αποτελέσματα) — leading indicator για biotech.
- **Press-wire RSS** (Business Wire, PR Newswire, GlobeNewswire) — δωρεάν, αλλά συνήθως λίγα λεπτά πίσω από επί πληρωμή direct feed.
- Το free news WebSocket του Finnhub/Alpaca παραμένει η ταχύτερη δωρεάν push-επιλογή.

---

## 4. Πηγές — Στάδιο 2/3: Επί πληρωμή (όταν χρειαστεί ταχύτητα)

### Market data
- **Polygon.io → μετονομάστηκε σε "Massive"** (Οκτ. 2025, ίδιο api.polygon.io surface). Full-market REST+WebSocket+flat files. Paid από ~$199/mo για σοβαρό real-time· ~10ms WebSocket latency (third-party εκτίμηση).
- **Databento** — pay-as-you-go, low-latency. Το "US Equities Mini" προϊόν βασίζεται σε feeds (NYSE Chicago/National, IEX, MIAX Pearl) που είναι **δωρεάν licensable** για διανομή — αποφεύγει τα ακριβά SIP redistribution fees.
- **Trade Ideas**, **Intrinio** — δευτερεύουσες επιλογές, πιο end-user/fundamentals-heavy αντίστοιχα.

### News / Squawk
- **Benzinga** (benzinga.com/apis) — το πιο σημαντικό επί πληρωμή asset. Ιδιόκτητο newsroom, News API (REST+push, παράμετρος `updatedSince` για ελάχιστο latency), σήμα **"WIIM" (Why Is It Moving)** — αυτόματη εξήγηση κίνησης τιμής. Benzinga Pro terminal: Basic $37/mo έως Essential ~$197–199/mo (περιλαμβάνει Real-Time Scanner, Audio Squawk).
- **Newsquawk**, **Trade The News** (~$350/mo), **Livesquawk** (~$350/mo) — real-time audio squawk feeds, ανθρώπινη επιμέλεια, κάλυψη ΗΠΑ/Ευρώπης/Ασίας. Σημείωση από traders: μπορεί να καθυστερούν έως ~1 λεπτό σε σχέση με Bloomberg.
- **RTPR** (rtpr.io) — press-release API με claimed sub-500ms latency (self-reported παραδείγματα 148–341ms). Δωρεάν "Wire" tier + Pro $139/mo.

### Leading indicators / εναλλακτικά δεδομένα
- **Unusual Whales** (unusualwhales.com) — options flow, dark pool prints, insider trades. API πλάνα: Trial $50/wk, Basic $150/mo, Advanced $375/mo (WebSocket μόνο στο Advanced). ⚠️ **Αυστηρά προσωπική χρήση, όχι redistribution.**
- **StockTwits API** — trending symbols endpoint (`/trending/symbols.json`, χωρίς token, μέχρι 30 σύμβολα) — δωρεάν-ish κοινωνικό momentum signal.
- **FlowAlgo, Cheddar Flow** — εναλλακτικά σε Unusual Whales, πιο dashboard-only, λιγότερο developer-friendly.

---

## 5. Global / εκτός ΗΠΑ πηγές

Δεν υπάρχει ενιαία φτηνή global πηγή ειδήσεων/filings — χρειάζεται συνδυασμός εθνικών υπηρεσιών:

- **RNS (UK, LSE/LSEG)** — κύριο κανάλι (~75% των price-sensitive ανακοινώσεων UK). REST Announcement API + real-time WebSocket (`wss://feed.rns-distribution.com`). Απαιτεί LSE license. Δωρεάν restricted view μέσω lse.co.uk για ιδιώτες επενδυτές.
- **EQS News / DGAP (Γερμανία/ΕΕ)** — μεγαλύτερη γερμανική υπηρεσία ρυθμιστικών ειδήσεων, χρησιμοποιείται από >90% εισηγμένων γερμανικών εταιρειών για MAR Article 17 ad-hoc disclosures. App/portal με push notifications + RSS.
- **JPX TDnet (Ιαπωνία)** — υποχρεωτικό δίκτυο έγκαιρης γνωστοποίησης για όλες τις εισηγμένες στο TSE. Paid: TDnet API Service (REST, redistribution επιτρέπεται) ή TDnet Server-Based Service (πιο γρήγορο). Δωρεάν public view περιορισμένο σε 31 ημέρες ιστορικού.
- **HKEX (Χονγκ Κονγκ)** — licensed real-time data products.
- Για **τιμές** παγκοσμίως, ευρύτερη φτηνή κάλυψη δίνουν Twelve Data / EODHD (50+ αγορές)· για **ειδήσεις/filings** δεν υπάρχει συντόμευση — απαιτείται σύνδεση με κάθε εθνική υπηρεσία ξεχωριστά.

---

## 6. Νομικά / Compliance σημεία

- **Καμία πηγή = insider info.** Όλες οι παραπάνω πηγές είναι νόμιμα δημόσια δεδομένα· η αξία είναι στην ταχύτητα πρόσβασης σε δημόσια πληροφορία, όχι σε προνομιακή.
- **Real-time US equity data (SIP) = ρυθμισμένα exchange fees.** Επαγγελματίες συνδρομητές πληρώνουν εκατοντάδες-χιλιάδες $/μήνα για πλήρες SIP feed. Η κατηγοριοποίηση professional vs non-professional επηρεάζει δραστικά το κόστος.
- **Η "διαφυγή" IEX:** το IEX TOPS real-time feed είναι διαθέσιμο σε τελικούς χρήστες **χωρίς per-user fees** (~$500/mo exchange fee, χωρίς pro/non-pro διάκριση) — γι' αυτό Alpaca/Finnhub free tiers βασίζονται σε αυτό. Το Databento Mini προϊόν ακολουθεί παρόμοια λογική.
- **Redistribution restrictions:** το Unusual Whales API απαγορεύει ρητά redistribution. Benzinga, Polygon/Massive, RNS, TDnet έχουν δικά τους enterprise/redistribution licensing tiers — πρέπει να ελεγχθεί το ToS πριν εμφανιστούν δεδομένα σε χρήστες του app.
- Delayed data (15-min) αρκεί για μη-κρίσιμα features (ιστορικά charts κ.λπ.) — το ακριβό real-time licensing να περιοριστεί μόνο στην οθόνη του νέου tab.

---

## 7. Προτεινόμενα στάδια υλοποίησης

**Στάδιο 1 — Δωρεάν MVP:**
1. Price/trigger: FMP `/gainers` (poll 30–60s, φίλτρο ≥20%, cross-check με "most active" για liquidity) + Finnhub/Alpaca WebSocket για watchlist.
2. Catalyst: SEC EDGAR Latest Filings RSS (8-K, 10 req/s όριο) + Alpaca free news WebSocket + openFDA + ClinicalTrials.gov.
3. Global: RNS δωρεάν view, EQS News, TDnet δημόσιο feed.

**Στάδιο 2 — Paid ταχύτητα (όταν το latency/coverage γίνεται bottleneck):**
1. Price: Polygon/Massive (από $199/mo) ή Databento Mini.
2. News: Benzinga News API (WIIM + `updatedSince` push).
3. PR ταχύτητα: RTPR (~$139/mo) αν το press-release latency είναι ο περιοριστικός παράγοντας.

**Στάδιο 3 — Επαγγελματικό επίπεδο:**
- Newsquawk/Trade The News (audio), Unusual Whales Advanced ($375/mo) για options-flow leading indicators, σωστό SIP/exchange redistribution licensing.

---

## 8. Επιφυλάξεις / πράγματα προς επαλήθευση

- Τα latency νούμερα (Polygon ~10ms, Benzinga ~25ms, RTPR sub-500ms, EDGAR ~24s median) είναι κυρίως από marketing pages ή single-experiment blogs — να επαληθευτούν ανεξάρτητα πριν την παραγωγική χρήση.
- "Δωρεάν real-time" σχεδόν πάντα σημαίνει IEX-only ή delayed· το πλήρες SIP real-time είναι πάντα paid/licensed.
- Social/options-flow signals είναι leading indicators, όχι επιβεβαιώσεις — έχουν false positives, να χρησιμοποιούνται μόνο για πρώιμο εντοπισμό, πάντα με επιβεβαίωση από την πραγματική κίνηση τιμής.
- Πολλοί τίτλοι με 20%+ κίνηση είναι thin small-caps — ανάγκη για volume/liquidity guards ώστε να αποφεύγονται pump-and-dump παγίδες.
- Οι τιμές/APIs αλλάζουν συχνά (IEX Cloud έκλεισε 2024, Polygon→Massive 2025, Unusual Whales αύξησε τιμές 2025) — να επαληθεύονται pricing pages/ToS τη στιγμή της ενσωμάτωσης.
- Το πιο συχνό νομικό λάθος: εμφάνιση δεδομένων περιορισμένης redistribution (Unusual Whales, RNS, TDnet, SIP) σε χρήστες χωρίς το σωστό license tier.

---

*Έκδοση handoff doc: consolidated για χρήση από coding assistant. Καμία αλλαγή περιεχομένου σε σχέση με το αρχικό — μόνο προσθήκη της ενότητας 0 για context.*
