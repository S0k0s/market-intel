import { useMemo } from "react";
import { useJsonData } from "@/hooks/useJsonData";
import { useWatchlist } from "@/hooks/useWatchlist";
import type { RankingsFile, HistoryFile } from "@/types/data";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Sparkline } from "@/components/Sparkline";
import { Star, Flame } from "lucide-react";

type Trend = "rising" | "falling" | "stable" | "unknown";
type SentimentCat = "positive" | "neutral" | "negative";

function sentimentCategory(s: number): SentimentCat {
  if (s > 0.15) return "positive";
  if (s < -0.15) return "negative";
  return "neutral";
}

function trendOf(points: { score: number }[]): Trend {
  if (points.length < 2) return "unknown";
  const window = Math.min(3, Math.floor(points.length / 2)) || 1;
  const recent = points.slice(-window);
  const prior = points.slice(-window * 2, -window);
  if (prior.length === 0) return "unknown";
  const avg = (arr: { score: number }[]) => arr.reduce((s, p) => s + p.score, 0) / arr.length;
  const diff = avg(recent) - avg(prior);
  if (diff > 3) return "rising";
  if (diff < -3) return "falling";
  return "stable";
}

function statusPhrase(cat: SentimentCat, trend: Trend): string {
  const phrases: Record<SentimentCat, Record<Trend, string>> = {
    positive: {
      rising: "Θετική και ενισχυόμενη ροή ειδήσεων",
      falling: "Θετική, αλλά εξασθενεί",
      stable: "Σταθερά θετική ροή ειδήσεων",
      unknown: "Θετική ροή ειδήσεων (ανεπαρκές ιστορικό για τάση)",
    },
    neutral: {
      rising: "Βελτιούμενη τάση, ακόμη ουδέτερη",
      falling: "Επιδεινούμενη τάση",
      stable: "Ουδέτερη ροή ειδήσεων, χωρίς σαφή κατεύθυνση",
      unknown: "Ουδέτερη ροή ειδήσεων (ανεπαρκές ιστορικό για τάση)",
    },
    negative: {
      rising: "Αρνητική, αλλά βελτιώνεται",
      falling: "Αρνητική και επιδεινώνεται",
      stable: "Σταθερά αρνητική ροή ειδήσεων",
      unknown: "Αρνητική ροή ειδήσεων (ανεπαρκές ιστορικό για τάση)",
    },
  };
  return phrases[cat][trend];
}

function statusColor(cat: SentimentCat) {
  if (cat === "positive") return "text-positive";
  if (cat === "negative") return "text-negative";
  return "text-foreground";
}

export function Portfolio() {
  const { data: rankingsData, loading: loadingRankings } = useJsonData<RankingsFile>(
    `${import.meta.env.BASE_URL}data/rankings.json`
  );
  const { data: history, loading: loadingHistory } = useJsonData<HistoryFile>(
    `${import.meta.env.BASE_URL}data/history.json`
  );
  const { watchlist, toggle } = useWatchlist();

  const rows = useMemo(() => {
    return watchlist.map((ticker) => {
      const ranking = rankingsData?.rankings.find((r) => r.ticker === ticker);
      const points = history?.[ticker] ?? [];
      const trend = trendOf(points);
      const cat = ranking ? sentimentCategory(ranking.avg_sentiment) : "neutral";
      return { ticker, ranking, points, trend, cat };
    });
  }, [watchlist, rankingsData, history]);

  if (loadingRankings || loadingHistory)
    return <p className="text-muted-foreground text-sm">Φόρτωση χαρτοφυλακίου…</p>;

  return (
    <div className="flex flex-col gap-4">
      <p className="text-xs text-muted-foreground max-w-2xl">
        Κατάσταση ειδησεογραφικής ροής για τις μετοχές στο watchlist σου — δείχνει{" "}
        <strong>τάση, όχι σύσταση</strong>. Η απόφαση για κράτημα ή πώληση παραμένει
        δική σου, με βάση τη δική σου στρατηγική· εδώ βλέπεις μόνο τι λένε πρόσφατα οι
        ειδήσεις, deterministic και χωρίς AI-based advice.
      </p>

      {rows.length === 0 && (
        <Card>
          <CardContent className="p-6 text-center text-sm text-muted-foreground">
            Δεν έχεις προσθέσει καμία μετοχή στο watchlist ακόμα. Πήγαινε στο tab
            «Rankings» ή «Ειδήσεις» και πάτησε το ⭐ δίπλα σε μια μετοχή για να την
            παρακολουθείς εδώ.
          </CardContent>
        </Card>
      )}

      <div className="grid gap-3">
        {rows.map(({ ticker, ranking, points, trend, cat }) => (
          <Card key={ticker}>
            <CardContent className="flex items-center gap-4 p-4">
              <button
                onClick={() => toggle(ticker)}
                aria-label="Αφαίρεση από watchlist"
                className="text-muted-foreground hover:text-foreground"
              >
                <Star className="size-4" fill="currentColor" />
              </button>

              <div className="flex min-w-0 flex-1 flex-col gap-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{ranking?.name ?? ticker}</span>
                  <span className="text-xs text-muted-foreground">{ticker}</span>
                  {ranking?.sector && (
                    <Badge variant="outline" className="hidden sm:inline-flex">
                      {ranking.sector}
                    </Badge>
                  )}
                  {ranking?.unusual && (
                    <Flame className="size-3.5 text-negative" aria-label="Ασυνήθιστη κάλυψη" />
                  )}
                </div>
                {ranking ? (
                  <p className={`text-sm ${statusColor(cat)}`}>{statusPhrase(cat, trend)}</p>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    Καμία πρόσφατη κάλυψη ειδήσεων στις τελευταίες ώρες
                  </p>
                )}
                {ranking && (
                  <p className="text-xs text-muted-foreground">
                    {ranking.article_count} άρθρα · {ranking.source_count} πηγές · μέσο
                    sentiment {ranking.avg_sentiment >= 0 ? "+" : ""}
                    {ranking.avg_sentiment}
                  </p>
                )}
              </div>

              <div className="flex flex-col items-end gap-1">
                {ranking && (
                  <span className={`text-lg font-semibold tabular-nums ${statusColor(cat)}`}>
                    {ranking.score}
                  </span>
                )}
                <Sparkline points={points} />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
