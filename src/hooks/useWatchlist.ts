import { useEffect, useState } from "react";

const STORAGE_KEY = "market-intel:watchlist";
// Προεπιλογή: οι θέσεις του demo Trading212 λογαριασμού (βλ. trading-copilot)
const DEFAULT_WATCHLIST = ["MU", "INTC"];

export function useWatchlist() {
  const [watchlist, setWatchlist] = useState<string[]>(() => {
    if (typeof window === "undefined") return DEFAULT_WATCHLIST;
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? (JSON.parse(raw) as string[]) : DEFAULT_WATCHLIST;
    } catch {
      return DEFAULT_WATCHLIST;
    }
  });

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(watchlist));
  }, [watchlist]);

  function toggle(ticker: string) {
    setWatchlist((prev) =>
      prev.includes(ticker) ? prev.filter((t) => t !== ticker) : [...prev, ticker]
    );
  }

  function isWatched(ticker: string) {
    return watchlist.includes(ticker);
  }

  return { watchlist, toggle, isWatched };
}
