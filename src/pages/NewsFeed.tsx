import { useMemo, useState } from "react";
import { useJsonData } from "@/hooks/useJsonData";
import { useWatchlist } from "@/hooks/useWatchlist";
import type { ArticlesFile } from "@/types/data";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Star } from "lucide-react";

const CONTINENT_FILTERS: { id: string; label: string }[] = [
  { id: "all", label: "Όλες" },
  { id: "na", label: "🇺🇸 Βόρεια Αμερική" },
  { id: "eu", label: "🇪🇺 Ευρώπη" },
  { id: "as", label: "🌏 Ασία" },
  { id: "oc", label: "🇦🇺 Ωκεανία" },
];

const SENTIMENT_FILTERS: { id: "all" | "positive" | "neutral" | "negative"; label: string }[] = [
  { id: "all", label: "Όλα" },
  { id: "positive", label: "Θετικά" },
  { id: "neutral", label: "Ουδέτερα" },
  { id: "negative", label: "Αρνητικά" },
];

const SORT_OPTIONS: { id: "recent" | "sentiment_desc" | "sentiment_asc"; label: string }[] = [
  { id: "recent", label: "Νεότερα πρώτα" },
  { id: "sentiment_desc", label: "Sentiment: Θετικό → Αρνητικό" },
  { id: "sentiment_asc", label: "Sentiment: Αρνητικό → Θετικό" },
];

function sentimentCategory(s: number): "positive" | "neutral" | "negative" {
  if (s > 0.15) return "positive";
  if (s < -0.15) return "negative";
  return "neutral";
}

function timeAgo(epoch: number) {
  const diffMin = Math.max(0, Math.round((Date.now() / 1000 - epoch) / 60));
  if (diffMin < 60) return `${diffMin}λ`;
  const diffH = Math.round(diffMin / 60);
  if (diffH < 24) return `${diffH}ω`;
  return `${Math.round(diffH / 24)}μ`;
}

function sentimentBadge(s: number) {
  const cat = sentimentCategory(s);
  if (cat === "positive") return <Badge variant="positive">Θετικό</Badge>;
  if (cat === "negative") return <Badge variant="negative">Αρνητικό</Badge>;
  return <Badge variant="muted">Ουδέτερο</Badge>;
}

export function NewsFeed() {
  const { data, error, loading } = useJsonData<ArticlesFile>(
    `${import.meta.env.BASE_URL}data/articles.json`
  );
  const { isWatched } = useWatchlist();
  const [continent, setContinent] = useState("all");
  const [sentimentFilter, setSentimentFilter] = useState<"all" | "positive" | "neutral" | "negative">("all");
  const [sort, setSort] = useState<"recent" | "sentiment_desc" | "sentiment_asc">("recent");
  const [onlyWithTickers, setOnlyWithTickers] = useState(false);
  const [watchlistOnly, setWatchlistOnly] = useState(false);
  const [search, setSearch] = useState("");

  const articles = useMemo(() => {
    if (!data) return [];
    const q = search.trim().toLowerCase();
    const filtered = data.articles.filter((a) => {
      if (continent !== "all" && a.continent !== continent) return false;
      if (sentimentFilter !== "all" && sentimentCategory(a.sentiment) !== sentimentFilter) return false;
      if (onlyWithTickers && a.tickers.length === 0) return false;
      if (watchlistOnly && !a.tickers.some((t) => isWatched(t))) return false;
      if (q && !a.title.toLowerCase().includes(q) && !a.tickers.some((t) => t.toLowerCase().includes(q)))
        return false;
      return true;
    });
    return [...filtered].sort((a, b) => {
      if (sort === "sentiment_desc") return b.sentiment - a.sentiment;
      if (sort === "sentiment_asc") return a.sentiment - b.sentiment;
      return b.epoch - a.epoch;
    });
  }, [data, continent, sentimentFilter, sort, onlyWithTickers, watchlistOnly, search, isWatched]);

  if (loading) return <p className="text-muted-foreground text-sm">Φόρτωση ειδήσεων…</p>;
  if (error) return <p className="text-negative text-sm">Σφάλμα φόρτωσης: {error}</p>;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <input
          type="text"
          placeholder="Αναζήτηση τίτλου ή ticker…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="h-8 w-48 rounded-md border border-input bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
        {CONTINENT_FILTERS.map((f) => (
          <Button
            key={f.id}
            size="sm"
            variant={continent === f.id ? "default" : "outline"}
            onClick={() => setContinent(f.id)}
          >
            {f.label}
          </Button>
        ))}
        <span className="text-muted-foreground">·</span>
        {SENTIMENT_FILTERS.map((f) => (
          <Button
            key={f.id}
            size="sm"
            variant={sentimentFilter === f.id ? "default" : "outline"}
            onClick={() => setSentimentFilter(f.id)}
          >
            {f.label}
          </Button>
        ))}
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value as typeof sort)}
          className="h-8 rounded-md border border-input bg-background px-2 text-sm"
        >
          {SORT_OPTIONS.map((o) => (
            <option key={o.id} value={o.id}>
              {o.label}
            </option>
          ))}
        </select>
        <div className="ml-auto flex items-center gap-2">
          <Button
            size="sm"
            variant={watchlistOnly ? "default" : "outline"}
            onClick={() => setWatchlistOnly((v) => !v)}
          >
            <Star className="size-3.5" /> Watchlist
          </Button>
          <Button
            size="sm"
            variant={onlyWithTickers ? "default" : "outline"}
            onClick={() => setOnlyWithTickers((v) => !v)}
          >
            Μόνο με μετοχές
          </Button>
        </div>
      </div>

      {articles.length === 0 && (
        <p className="text-muted-foreground text-sm">Δεν βρέθηκαν άρθρα με αυτά τα φίλτρα.</p>
      )}

      <div className="grid gap-3">
        {articles.map((a, i) => (
          <Card key={i}>
            <CardContent className="flex flex-col gap-2 p-4">
              <div className="flex items-start justify-between gap-3">
                <a
                  href={a.url}
                  target="_blank"
                  rel="noreferrer"
                  className="font-medium leading-snug hover:underline"
                >
                  {a.title}
                </a>
                {sentimentBadge(a.sentiment)}
              </div>
              {a.summary && (
                <p className="text-sm text-muted-foreground line-clamp-2">{a.summary}</p>
              )}
              <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                <span>{a.source}</span>
                <span>·</span>
                <span>{timeAgo(a.epoch)} πριν</span>
                {a.tickers.map((t) => (
                  <Badge key={t} variant={isWatched(t) ? "default" : "secondary"}>
                    {isWatched(t) && <Star className="mr-1 size-3" fill="currentColor" />}
                    {t}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
