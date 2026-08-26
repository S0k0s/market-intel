import { useEffect, useState } from "react";

const CACHE_TTL_MS = 30 * 60 * 1000; // 30 λεπτά
const REFRESH_EVENT = "market-intel:refresh-data";

/** Καλείται από το κουμπί ανανέωσης στο header — λέει σε όλα τα mounted
 * useJsonData hooks να παρακάμψουν το cache και να ξαναφέρουν φρέσκα δεδομένα,
 * χωρίς reload της σελίδας (κρατάει το ενεργό tab/φίλτρα του χρήστη). */
export function refreshAllData() {
  window.dispatchEvent(new Event(REFRESH_EVENT));
}

export function useJsonData<T>(path: string) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    function onRefresh() {
      setNonce((n) => n + 1);
    }
    window.addEventListener(REFRESH_EVENT, onRefresh);
    return () => window.removeEventListener(REFRESH_EVENT, onRefresh);
  }, []);

  useEffect(() => {
    let cancelled = false;
    const cacheKey = `market-intel:${path}`;
    const bypassCache = nonce > 0;

    async function load() {
      setLoading(true);
      try {
        if (!bypassCache) {
          const cached = localStorage.getItem(cacheKey);
          if (cached) {
            const { ts, payload } = JSON.parse(cached);
            if (Date.now() - ts < CACHE_TTL_MS) {
              if (!cancelled) {
                setData(payload);
                setLoading(false);
              }
              return;
            }
          }
        }
        const res = await fetch(path, bypassCache ? { cache: "no-store" } : undefined);
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        const json = (await res.json()) as T;
        localStorage.setItem(cacheKey, JSON.stringify({ ts: Date.now(), payload: json }));
        if (!cancelled) {
          setData(json);
          setError(null);
          setLoading(false);
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Άγνωστο σφάλμα");
          setLoading(false);
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [path, nonce]);

  return { data, error, loading };
}
