import { useMemo, useState } from "react";
import { useJsonData } from "@/hooks/useJsonData";
import { useWatchlist } from "@/hooks/useWatchlist";
import type { RadarFile, Archetype } from "@/types/data";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Star, Rocket, TrendingUp, Microscope, Flame } from "lucide-react";

function timeAgo(epoch: number) {
  const diffMin = Math.max(0, Math.round((Date.now() / 1000 - epoch) / 60));
  if (diffMin < 60) return `${diffMin}λ`;
  const diffH = Math.round(diffMin / 60);
  if (diffH < 24) return `${diffH}ω`;
  return `${Math.round(diffH / 24)}μ`;
}

function archetypeBadge(archetype: Archetype, label: string | null) {
  if (!archetype) return null;
  if (archetype === "quality_compounding") return <Badge variant="positive">{label}</Badge>;
  if (archetype === "momentum_breakout") return <Badge variant="positive">{label}</Badge>;
  if (archetype === "speculative") return <Badge variant="negative">{label}</Badge>;
  return null;
}

export function Radar() {
  const { data, error, loading } = useJsonData<RadarFile>(
    `${import.meta.env.BASE_URL}data/radar.json`
  );
  const { isWatched } = useWatchlist();
  const [catalystOnly, setCatalystOnly] = useState(false);

  const breaking = useMemo(() => {
    if (!data) return [];
    return catalystOnly ? data.breaking.filter((a) => a.catalyst) : data.breaking;
  }, [data, catalystOnly]);

  if (loading) return <p className="text-muted-foreground text-sm">Φόρτωση ραντάρ…</p>;
  if (error) return <p className="text-negative text-sm">Σφάλμα φόρτωσης: {error}</p>;
  if (!data) return null;

  return (
    <TooltipProvider>
      <div className="flex flex-col gap-6">
        <div className="rounded-xl border border-border bg-card p-4">
          <div className="flex items-center gap-2">
            <Rocket className="size-4 text-primary" />
            <h2 className="font-semibold">Τι είναι το Ραντάρ</h2>
          </div>
          <p className="mt-2 text-xs text-muted-foreground max-w-3xl">
            <strong>Δεν προβλέπει τίποτα πριν συμβεί</strong> — κάτι τέτοιο θα ήταν είτε
            αδύνατο είτε insider trading. Δύο ξεχωριστά πράγματα εδώ:{" "}
            <strong>
              <Microscope className="inline size-3.5" /> Breaking
            </strong>{" "}
            = ανακοινώσεις από πρωτογενείς πηγές (SEC filings, FDA, δελτία τύπου) τη
            στιγμή που δημοσιεύονται — το μόνο κομμάτι που μπορεί ρεαλιστικά να
            λειτουργήσει σαν <em>πρώιμο σήμα</em>, αν προλάβεις να το διαβάσεις πριν
            αντιδράσει η τιμή. Άρθρα με 🔬 = καταλυτική γλώσσα (κλινικές δοκιμές, FDA
            εγκρίσεις, συμφωνίες) — αυτά συνήθως προηγούνται μεγάλων κινήσεων, όπως το
            +117% της Moderna στις 19-20/8 μετά από νέα για δοκιμές εμβολίου καρκίνου.{" "}
            <strong>
              <TrendingUp className="inline size-3.5" /> Μεγάλες κινήσεις
            </strong>{" "}
            = μετοχές S&amp;P 500 που ήδη κινήθηκαν ≥ +{data.move_threshold_pct}% —{" "}
            <strong>επιβεβαίωση ότι κάτι συνέβη, όχι πρόβλεψη</strong>. Ενημερώνεται κάθε
            ~15 λεπτά.
          </p>
        </div>

        <section className="flex flex-col gap-3">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <Microscope className="size-4 text-primary" />
              <h2 className="font-semibold">Breaking — πρωτογενείς πηγές</h2>
            </div>
            <Button
              size="sm"
              variant={catalystOnly ? "default" : "outline"}
              onClick={() => setCatalystOnly((v) => !v)}
            >
              🔬 Μόνο catalyst
            </Button>
          </div>
          {breaking.length === 0 && (
            <p className="text-sm text-muted-foreground">
              {catalystOnly ? "Καμία καταλυτική ανακοίνωση αυτή τη στιγμή." : "Καμία πρόσφατη ανακοίνωση."}
            </p>
          )}
          <div className="grid gap-3">
            {breaking.map((a, i) => (
              <Card key={i} className={a.catalyst ? "border-primary/50" : undefined}>
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
                    <div className="flex shrink-0 items-center gap-1">
                      {a.small_cap_risk && (
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <span className="text-lg leading-none">⚠️</span>
                          </TooltipTrigger>
                          <TooltipContent>
                            Μικρή κεφαλαιοποίηση εκτός S&amp;P 500/μεγάλων δεικτών —
                            υψηλότερος κίνδυνος thin trading/pump-and-dump
                          </TooltipContent>
                        </Tooltip>
                      )}
                      {a.catalyst && (
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <span className="text-lg leading-none">🔬</span>
                          </TooltipTrigger>
                          <TooltipContent>
                            Καταλυτική γλώσσα (κλινική δοκιμή, FDA, συμφωνία) — πιθανό
                            πρώιμο σήμα
                          </TooltipContent>
                        </Tooltip>
                      )}
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
                    {a.tickers.length === 0 && a.company_name && (
                      <Badge variant="outline">{a.company_name}</Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        <section className="flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <TrendingUp className="size-4 text-positive" />
            <h2 className="font-semibold">Μεγάλες κινήσεις τιμής (S&amp;P 500) — επιβεβαίωση</h2>
          </div>
          {data.concentration_warning && (
            <p className="text-xs text-negative">⚠️ {data.concentration_warning}</p>
          )}
          {data.movers.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Καμία μετοχή S&amp;P 500 δεν έχει ξεπεράσει το +{data.move_threshold_pct}%
              ενδοημερήσια αυτή τη στιγμή.
            </p>
          ) : (
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {data.movers.map((m) => (
                <Card key={m.ticker} className="border-positive/40">
                  <CardContent className="flex flex-col gap-2 p-4">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex flex-col">
                        <span className="font-medium">{m.name}</span>
                        <span className="text-xs text-muted-foreground">{m.ticker}</span>
                      </div>
                      <div className="flex flex-col items-end">
                        <span className="text-lg font-bold text-positive tabular-nums">
                          +{m.change_pct}%
                        </span>
                        <span className="text-xs text-muted-foreground">${m.price}</span>
                      </div>
                    </div>
                    <div className="flex flex-wrap items-center gap-1">
                      {m.sector && <Badge variant="outline">{m.sector}</Badge>}
                      {archetypeBadge(m.archetype, m.archetype_label)}
                      {m.streak_days >= 2 && (
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Badge variant="muted">
                              <Flame className="mr-1 size-3" />
                              {m.streak_days}η μέρα
                            </Badge>
                          </TooltipTrigger>
                          <TooltipContent>
                            Εμφανίζεται ως μεγάλη κίνηση {m.streak_days} συνεχόμενες
                            ημέρες — κίνδυνος "chasing" μιας ήδη παρατεταμένης κίνησης
                          </TooltipContent>
                        </Tooltip>
                      )}
                    </div>
                    {(m.piotroski_f !== null || m.rsi !== null) && (
                      <p className="text-xs text-muted-foreground">
                        {m.piotroski_f !== null && `Piotroski ${m.piotroski_f}/9`}
                        {m.altman_z !== null && ` · Altman Z ${m.altman_z}`}
                        {m.rsi !== null && ` · RSI ${m.rsi}`}
                        {m.peg_ratio !== null && ` · PEG ${m.peg_ratio}`}
                      </p>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </section>
      </div>
    </TooltipProvider>
  );
}
