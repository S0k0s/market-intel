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
import type { BreakingItem, TrendingTicker } from "@/types/data";
import { Star, Rocket, TrendingUp, Microscope, Flame, FlaskConical, BarChart3 } from "lucide-react";

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

function BreakingCard({ a, isWatched }: { a: BreakingItem; isWatched: (t: string) => boolean }) {
  return (
    <Card className={a.catalyst ? "border-primary/50" : undefined}>
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
        {a.summary && <p className="text-sm text-muted-foreground line-clamp-2">{a.summary}</p>}
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
  );
}

function TrendingTickersBar({
  tickers,
  isWatched,
}: {
  tickers: TrendingTicker[];
  isWatched: (t: string) => boolean;
}) {
  if (tickers.length === 0) return null;
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="mb-3 flex items-center gap-2">
        <BarChart3 className="size-4 text-primary" />
        <h2 className="font-semibold">Trending tickers σήμερα</h2>
      </div>
      <div className="flex flex-wrap gap-2">
        {tickers.map((t) => (
          <Tooltip key={t.ticker}>
            <TooltipTrigger asChild>
              <div>
                <Badge variant={isWatched(t.ticker) ? "default" : "secondary"} className="gap-1">
                  {isWatched(t.ticker) && <Star className="size-3" fill="currentColor" />}
                  {t.ticker}
                  <span className="opacity-70">×{t.count}</span>
                  {t.catalyst_count > 0 && <span>🔬{t.catalyst_count}</span>}
                </Badge>
              </div>
            </TooltipTrigger>
            <TooltipContent>
              {t.count} αναφορές σε {t.source_count} διαφορετικές πηγές
              {t.catalyst_count > 0 && `, ${t.catalyst_count} με καταλυτική γλώσσα`}
            </TooltipContent>
          </Tooltip>
        ))}
      </div>
    </div>
  );
}

export function Radar() {
  const { data, error, loading } = useJsonData<RadarFile>(
    `${import.meta.env.BASE_URL}data/radar.json`
  );
  const { isWatched } = useWatchlist();
  const [catalystOnly, setCatalystOnly] = useState(false);
  const [pipelineCatalystOnly, setPipelineCatalystOnly] = useState(false);

  const breaking = useMemo(() => {
    // data.breaking/pipeline μπορεί να λείπουν από ένα παλιότερο cached
    // radar.json στο localStorage του χρήστη (π.χ. πριν προστεθεί το πεδίο
    // "pipeline") — πάντα fallback σε [] αντί να σκάει το .filter/.length.
    const list = data?.breaking ?? [];
    return catalystOnly ? list.filter((a) => a.catalyst) : list;
  }, [data, catalystOnly]);

  const pipeline = useMemo(() => {
    const list = data?.pipeline ?? [];
    return pipelineCatalystOnly ? list.filter((a) => a.catalyst) : list;
  }, [data, pipelineCatalystOnly]);

  const movers = data?.movers ?? [];
  // ίδιο defensive μοτίβο με breaking/pipeline παραπάνω — προστατεύει από
  // stale cached radar.json χωρίς τα νεότερα πεδία summary/trending_tickers
  const summary = data?.summary ?? {
    breaking_count: breaking.length,
    breaking_catalyst_count: 0,
    pipeline_count: pipeline.length,
    pipeline_catalyst_count: 0,
    movers_count: movers.length,
  };
  const trendingTickers = data?.trending_tickers ?? [];

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
              <FlaskConical className="inline size-3.5" /> Pipeline
            </strong>{" "}
            = δημοσιογραφία για το τι δουλεύουν οι εταιρείες πριν καν φτάσουν σε
            αποτέλεσμα (νέα trials, συμφωνίες) — έτσι ξέρεις ΠΟΙΟ ticker να
            παρακολουθείς, όχι πότε ακριβώς θα βγει το catalyst.{" "}
            <strong>
              <TrendingUp className="inline size-3.5" /> Μεγάλες κινήσεις
            </strong>{" "}
            = μετοχές S&amp;P 500 που ήδη κινήθηκαν ≥ +{data.move_threshold_pct}% —{" "}
            <strong>επιβεβαίωση ότι κάτι συνέβη, όχι πρόβλεψη</strong>. Ενημερώνεται κάθε
            ~15 λεπτά.
          </p>
          <p className="mt-3 border-t border-border pt-3 text-sm">
            Σήμερα: <strong>{summary.breaking_count}</strong> breaking άρθρα (
            <strong>{summary.breaking_catalyst_count}</strong> 🔬 catalyst) ·{" "}
            <strong>{summary.pipeline_count}</strong> pipeline αναφορές (
            <strong>{summary.pipeline_catalyst_count}</strong> 🔬 catalyst) ·{" "}
            <strong>{summary.movers_count}</strong> μεγάλες κινήσεις τιμής
          </p>
        </div>

        <TrendingTickersBar tickers={trendingTickers} isWatched={isWatched} />

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
              <BreakingCard key={i} a={a} isWatched={isWatched} />
            ))}
          </div>
        </section>

        <section className="flex flex-col gap-3">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <FlaskConical className="size-4 text-primary" />
              <h2 className="font-semibold">Pipeline — τι δουλεύουν οι εταιρείες</h2>
            </div>
            <Button
              size="sm"
              variant={pipelineCatalystOnly ? "default" : "outline"}
              onClick={() => setPipelineCatalystOnly((v) => !v)}
            >
              🔬 Μόνο catalyst
            </Button>
          </div>
          <p className="text-xs text-muted-foreground max-w-3xl">
            Δημοσιογραφία (FierceBiotech, FiercePharma, BioPharma Dive) για το τι
            βρίσκεται σε εξέλιξη — νέα trials, συμφωνίες, R&amp;D — <strong>πριν</strong>{" "}
            καν φτάσει σε αποτέλεσμα. Δεν λέει "θα ανέβει η μετοχή" — σου δείχνει ποιο
            ticker αξίζει να παρακολουθείς για το επόμενο catalyst. Χωρίς επίσημο
            ημερολόγιο ημερομηνιών (readout dates) προς το παρόν.
          </p>
          {pipeline.length === 0 && (
            <p className="text-sm text-muted-foreground">
              {pipelineCatalystOnly ? "Καμία καταλυτική αναφορά αυτή τη στιγμή." : "Καμία πρόσφατη αναφορά."}
            </p>
          )}
          <div className="grid gap-3">
            {pipeline.map((a, i) => (
              <BreakingCard key={i} a={a} isWatched={isWatched} />
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
          {movers.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Καμία μετοχή S&amp;P 500 δεν έχει ξεπεράσει το +{data.move_threshold_pct}%
              ενδοημερήσια αυτή τη στιγμή.
            </p>
          ) : (
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {movers.map((m) => (
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
