import { useEffect, useState } from "react";

const CACHE_TTL_MS = 30 * 60 * 1000; // 30 λεπτά

export function useJsonData<T>(path: string) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const cacheKey = `market-intel:${path}`;

    async function load() {
      try {
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
        const res = await fetch(path);
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        const json = (await res.json()) as T;
        localStorage.setItem(cacheKey, JSON.stringify({ ts: Date.now(), payload: json }));
        if (!cancelled) {
          setData(json);
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
  }, [path]);

  return { data, error, loading };
}
