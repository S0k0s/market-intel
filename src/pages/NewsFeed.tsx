import { useMemo, useState } from "react";
import { useJsonData } from "@/hooks/useJsonData";
import type { ArticlesFile } from "@/types/data";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const CONTINENT_FILTERS: { id: string; label: string }[] = [
  { id: "all", label: "Όλες" },
  { id: "na", label: "🇺🇸 Βόρεια Αμερική" },
  { id: "eu", label: "🇪🇺 Ευρώπη" },
  { id: "as", label: "🌏 Ασία" },
  { id: "oc", label: "🇦🇺 Ωκεανία" },
];

function timeAgo(epoch: number) {
  const diffMin = Math.max(0, Math.round((Date.now() / 1000 - epoch) / 60));
  if (diffMin < 60) return `${diffMin}λ`;
  const diffH = Math.round(diffMin / 60);
  if (diffH < 24) return `${diffH}ω`;
  return `${Math.round(diffH / 24)}μ`;
}

function sentimentBadge(s: number) {
  if (s > 0.15) return <Badge variant="positive">Θετικό</Badge>;
  if (s < -0.15) return <Badge variant="negative">Αρνητικό</Badge>;
  return <Badge variant="muted">Ουδέτερο</Badge>;
}

export function NewsFeed() {
  const { data, error, loading } = useJsonData<ArticlesFile>(
    `${import.meta.env.BASE_URL}data/articles.json`
  );
  const [continent, setContinent] = useState("all");
  const [onlyWithTickers, setOnlyWithTickers] = useState(false);

  const articles = useMemo(() => {
    if (!data) return [];
    return data.articles.filter((a) => {
      if (continent !== "all" && a.continent !== continent) return false;
      if (onlyWithTickers && a.tickers.length === 0) return false;
      return true;
    });
  }, [data, continent, onlyWithTickers]);

  if (loading) return <p className="text-muted-foreground text-sm">Φόρτωση ειδήσεων…</p>;
  if (error) return <p className="text-negative text-sm">Σφάλμα φόρτωσης: {error}</p>;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2">
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
        <Button
          size="sm"
          variant={onlyWithTickers ? "default" : "outline"}
          onClick={() => setOnlyWithTickers((v) => !v)}
          className="ml-auto"
        >
          Μόνο με μετοχές
        </Button>
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
                  <Badge key={t} variant="secondary">
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
