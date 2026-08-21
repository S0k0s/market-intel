import { useMemo, useState } from "react";
import { useJsonData } from "@/hooks/useJsonData";
import { useWatchlist } from "@/hooks/useWatchlist";
import type { ArticlesFile, Horizon } from "@/types/data";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FilterSelect } from "@/components/FilterSelect";
import { Star } from "lucide-react";

const CONTINENT_FILTERS = [
  { id: "all", label: "Όλες οι ήπειροι" },
  { id: "na", label: "🇺🇸 Βόρεια Αμερική" },
  { id: "eu", label: "🇪🇺 Ευρώπη" },
  { id: "as", label: "🌏 Ασία" },
  { id: "oc", label: "🇦🇺 Ωκεανία" },
] as const;

const SENTIMENT_FILTERS = [
  { id: "all", label: "Κάθε sentiment" },
  { id: "positive", label: "Θετικά" },
  { id: "neutral", label: "Ουδέτερα" },
  { id: "negative", label: "Αρνητικά" },
] as const;

const SORT_OPTIONS = [
  { id: "recent", label: "Νεότερα πρώτα" },
  { id: "sentiment_desc", label: "Sentiment: Θετικό → Αρνητικό" },
  { id: "sentiment_asc", label: "Sentiment: Αρνητικό → Θετικό" },
] as const;

const HORIZON_FILTERS = [
  { id: "all", label: "Όλοι οι ορίζοντες" },
  { id: "swing", label: "Swing" },
  { id: "long_term", label: "Long-term" },
] as const;

function sentimentCategory(s: number): "positive" | "neutral" | "negative" {
  if (s > 0.15) return "positive";
  if (s < -0.15) return "negative";
  return "neutral";
}

function horizonBadge(h: Horizon) {
  if (h === "swing") return <Badge variant="outline">Swing</Badge>;
  if (h === "long_term") return <Badge variant="outline">Long-term</Badge>;
  return null;
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
  const [continent, setContinent] = useState<(typeof CONTINENT_FILTERS)[number]["id"]>("all");
  const [sentimentFilter, setSentimentFilter] =
    useState<(typeof SENTIMENT_FILTERS)[number]["id"]>("all");
  const [horizonFilter, setHorizonFilter] = useState<(typeof HORIZON_FILTERS)[number]["id"]>("all");
  const [sort, setSort] = useState<(typeof SORT_OPTIONS)[number]["id"]>("recent");
  const [onlyWithTickers, setOnlyWithTickers] = useState(false);
  const [watchlistOnly, setWatchlistOnly] = useState(false);
  const [search, setSearch] = useState("");

  const articles = useMemo(() => {
    if (!data) return [];
    const q = search.trim().toLowerCase();
    const filtered = data.articles.filter((a) => {
      if (continent !== "all" && a.continent !== continent) return false;
      if (sentimentFilter !== "all" && sentimentCategory(a.sentiment) !== sentimentFilter) return false;
      if (horizonFilter !== "all" && a.horizon !== horizonFilter) return false;
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
  }, [data, continent, sentimentFilter, horizonFilter, sort, onlyWithTickers, watchlistOnly, search, isWatched]);

  if (loading) return <p className="text-muted-foreground text-sm">Φόρτωση ειδήσεων…</p>;
  if (error) return <p className="text-negative text-sm">Σφάλμα φόρτωσης: {error}</p>;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-2 rounded-xl border border-border bg-card p-3">
        <input
          type="text"
          placeholder="Αναζήτηση τίτλου ή ticker…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
        <div className="grid grid-cols-2 gap-2 sm:flex sm:flex-wrap">
          <FilterSelect value={continent} onChange={setContinent} options={CONTINENT_FILTERS} ariaLabel="Ήπειρος" />
          <FilterSelect
            value={sentimentFilter}
            onChange={setSentimentFilter}
            options={SENTIMENT_FILTERS}
            ariaLabel="Sentiment"
          />
          <FilterSelect
            value={horizonFilter}
            onChange={setHorizonFilter}
            options={HORIZON_FILTERS}
            ariaLabel="Χρονικός ορίζοντας"
          />
          <FilterSelect value={sort} onChange={setSort} options={SORT_OPTIONS} ariaLabel="Ταξινόμηση" />
        </div>
        <div className="flex flex-wrap items-center gap-2 border-t border-border pt-2">
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
          <span className="ml-auto text-xs text-muted-foreground">{articles.length} άρθρα</span>
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
                <div className="flex shrink-0 flex-wrap justify-end gap-1">
                  {horizonBadge(a.horizon)}
                  {sentimentBadge(a.sentiment)}
                </div>
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
