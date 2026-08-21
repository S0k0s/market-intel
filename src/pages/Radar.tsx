import { useJsonData } from "@/hooks/useJsonData";
import { useWatchlist } from "@/hooks/useWatchlist";
import type { RadarFile } from "@/types/data";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Star, Rocket, TrendingUp } from "lucide-react";

function timeAgo(epoch: number) {
  const diffMin = Math.max(0, Math.round((Date.now() / 1000 - epoch) / 60));
  if (diffMin < 60) return `${diffMin}λ`;
  const diffH = Math.round(diffMin / 60);
  if (diffH < 24) return `${diffH}ω`;
  return `${Math.round(diffH / 24)}μ`;
}

export function Radar() {
  const { data, error, loading } = useJsonData<RadarFile>(
    `${import.meta.env.BASE_URL}data/radar.json`
  );
  const { isWatched } = useWatchlist();

  if (loading) return <p className="text-muted-foreground text-sm">Φόρτωση ραντάρ…</p>;
  if (error) return <p className="text-negative text-sm">Σφάλμα φόρτωσης: {error}</p>;
  if (!data) return null;

  return (
    <div className="flex flex-col gap-6">
      <div className="rounded-xl border border-border bg-card p-4">
        <div className="flex items-center gap-2">
          <Rocket className="size-4 text-primary" />
          <h2 className="font-semibold">Τι είναι το Ραντάρ</h2>
        </div>
        <p className="mt-2 text-xs text-muted-foreground max-w-3xl">
          <strong>Δεν προβλέπει τίποτα πριν συμβεί</strong> — κάτι τέτοιο θα ήταν είτε
          αδύνατο είτε insider trading. Δείχνει δύο πράγματα που ήδη έχουν συμβεί
          δημόσια, όσο πιο γρήγορα γίνεται:{" "}
          <strong>(1) μετοχές S&amp;P 500 με ενδοημερήσια κίνηση ≥ +{data.move_threshold_pct}%</strong>{" "}
          και <strong>(2) ανακοινώσεις από πρωτογενείς πηγές</strong> (SEC filings, FDA,
          δελτία τύπου εταιρειών) — εκεί όπου γεννιέται δημόσια η είδηση, πριν την
          αναδημοσιεύσουν τα μεγάλα sites με καθυστέρηση. Ενημερώνεται κάθε ~15 λεπτά.
        </p>
      </div>

      <section className="flex flex-col gap-3">
        <div className="flex items-center gap-2">
          <TrendingUp className="size-4 text-positive" />
          <h2 className="font-semibold">Μεγάλες κινήσεις τιμής (S&amp;P 500)</h2>
        </div>
        {data.movers.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Καμία μετοχή S&amp;P 500 δεν έχει ξεπεράσει το +{data.move_threshold_pct}%
            ενδοημερήσια αυτή τη στιγμή.
          </p>
        ) : (
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {data.movers.map((m) => (
              <Card key={m.ticker} className="border-positive/40">
                <CardContent className="flex items-center justify-between gap-2 p-4">
                  <div className="flex flex-col">
                    <span className="font-medium">{m.name}</span>
                    <span className="text-xs text-muted-foreground">{m.ticker}</span>
                    {m.sector && (
                      <Badge variant="outline" className="mt-1 w-fit">
                        {m.sector}
                      </Badge>
                    )}
                  </div>
                  <div className="flex flex-col items-end">
                    <span className="text-lg font-bold text-positive tabular-nums">
                      +{m.change_pct}%
                    </span>
                    <span className="text-xs text-muted-foreground">${m.price}</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="font-semibold">Breaking — πρωτογενείς πηγές</h2>
        {data.breaking.length === 0 && (
          <p className="text-sm text-muted-foreground">Καμία πρόσφατη ανακοίνωση.</p>
        )}
        <div className="grid gap-3">
          {data.breaking.map((a, i) => (
            <Card key={i}>
              <CardContent className="flex flex-col gap-2 p-4">
                <a
                  href={a.url}
                  target="_blank"
                  rel="noreferrer"
                  className="font-medium leading-snug hover:underline"
                >
                  {a.title}
                </a>
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
                  {a.tickers.length === 0 && a.company_name && (
                    <Badge variant="outline">{a.company_name}</Badge>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
