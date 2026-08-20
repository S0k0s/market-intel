# Market Intel

Δεύτερη εφαρμογή, παράλληλη με το `trading-copilot`: συγκεντρώνει οικονομικές
ειδήσεις από δωρεάν RSS πηγές (ΗΠΑ, Ευρώπη, Ασία), υπολογίζει sentiment ανά
άρθρο, και παράγει ranked λίστα μετοχών βάσει **μετρήσιμου, deterministic
scoring** (όχι AI-generated advice).

## Δομή

- `scanner/aggregate.py` — Python ingestion script: RSS fetch, ticker matching,
  sentiment lexicon, ranking. Γράφει `public/data/{articles,rankings}.json`.
- `scanner/universe.py` — Universe μετοχών (ticker → όνομα/κλάδος/ήπειρος).
- `src/` — React + Vite + Tailwind + shadcn/ui frontend. Tabs «Ειδήσεις» και
  «Rankings».
- `.github/workflows/aggregate.yml` — cron κάθε 3 ώρες, τρέχει το script και
  κάνει commit τα ενημερωμένα JSON.

## Ανάπτυξη

```bash
npm install
npm run dev
```

```bash
pip install -r scanner/requirements.txt
python3 scanner/aggregate.py
```

## Σημείωση

Το score στο Rankings tab **δεν αποτελεί επενδυτική συμβουλή** — είναι
δείκτης κάλυψης/απήχησης ειδήσεων (sentiment + όγκος άρθρων), transparent και
tooltip-explainable. Ίδια φιλοσοφία με το deterministic scoring του
trading-copilot.
