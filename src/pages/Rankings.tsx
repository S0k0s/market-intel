import { useMemo, useState } from "react";
import { useJsonData } from "@/hooks/useJsonData";
import { useWatchlist } from "@/hooks/useWatchlist";
import type { RankingsFile, HistoryFile } from "@/types/data";
import { Card } from "@/components/ui/card";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Sparkline } from "@/components/Sparkline";
import { Star, Flame } from "lucide-react";

const CONTINENT_FILTERS: { id: string; label: string }[] = [
  { id: "all", label: "Όλες" },
  { id: "na", label: "🇺🇸 Βόρεια Αμερική" },
  { id: "eu", label: "🇪🇺 Ευρώπη" },
  { id: "as", label: "🌏 Ασία" },
  { id: "oc", label: "🇦🇺 Ωκεανία" },
];

function scoreColor(score: number) {
  if (score >= 60) return "text-positive";
  if (score <= 40) return "text-negative";
  return "text-foreground";
}

export function Rankings() {
  const { data, error, loading } = useJsonData<RankingsFile>(
    `${import.meta.env.BASE_URL}data/rankings.json`
  );
  const { data: history } = useJsonData<HistoryFile>(
    `${import.meta.env.BASE_URL}data/history.json`
  );
  const { toggle, isWatched } = useWatchlist();
  const [continent, setContinent] = useState("all");
  const [sector, setSector] = useState("all");
  const [search, setSearch] = useState("");
  const [watchlistOnly, setWatchlistOnly] = useState(false);

  const sectors = useMemo(() => {
    if (!data) return [];
    const set = new Set(data.rankings.map((r) => r.sector).filter(Boolean) as string[]);
    return [...set].sort();
  }, [data]);

  const rows = useMemo(() => {
    if (!data) return [];
    const q = search.trim().toLowerCase();
    const filtered = data.rankings.filter((r) => {
      if (continent !== "all" && r.continent !== continent) return false;
      if (sector !== "all" && r.sector !== sector) return false;
      if (watchlistOnly && !isWatched(r.ticker)) return false;
      if (q && !r.name.toLowerCase().includes(q) && !r.ticker.toLowerCase().includes(q))
        return false;
      return true;
    });
    return [...filtered].sort((a, b) => {
      const aw = isWatched(a.ticker) ? 1 : 0;
      const bw = isWatched(b.ticker) ? 1 : 0;
      if (aw !== bw) return bw - aw;
      return b.score - a.score;
    });
  }, [data, continent, sector, search, watchlistOnly, isWatched]);

  if (loading) return <p className="text-muted-foreground text-sm">Φόρτωση rankings…</p>;
  if (error) return <p className="text-negative text-sm">Σφάλμα φόρτωσης: {error}</p>;

  return (
    <TooltipProvider>
      <div className="flex flex-col gap-4">
        <div className="flex flex-wrap items-center gap-2">
          <input
            type="text"
            placeholder="Αναζήτηση εταιρείας ή ticker…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-8 w-48 rounded-md border border-input bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
          <select
            value={sector}
            onChange={(e) => setSector(e.target.value)}
            className="h-8 rounded-md border border-input bg-background px-2 text-sm"
          >
            <option value="all">Όλοι οι κλάδοι</option>
            {sectors.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
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
            variant={watchlistOnly ? "default" : "outline"}
            onClick={() => setWatchlistOnly((v) => !v)}
            className="ml-auto"
          >
            <Star className="size-3.5" /> Watchlist
          </Button>
        </div>

        <p className="text-xs text-muted-foreground max-w-2xl">
          Το score προκύπτει αποκλειστικά από deterministic ανάλυση ειδήσεων (μέσο
          sentiment με βάρος πρόσφατου + όγκος/ποικιλομορφία πηγών) —{" "}
          <strong>δεν αποτελεί επενδυτική συμβουλή</strong>, μόνο δείκτη
          κάλυψης/απήχησης ειδήσεων. 🔥 = ασυνήθιστα αυξημένη κάλυψη σε σχέση με το
          ιστορικό της μετοχής.
        </p>

        {rows.length === 0 && (
          <p className="text-muted-foreground text-sm">Δεν βρέθηκαν μετοχές με αυτά τα φίλτρα.</p>
        )}

        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead />
                <TableHead>Μετοχή</TableHead>
                <TableHead>Κλάδος</TableHead>
                <TableHead className="text-right">Score</TableHead>
                <TableHead>Τάση</TableHead>
                <TableHead className="text-right">Άρθρα</TableHead>
                <TableHead className="text-right">Πηγές</TableHead>
                <TableHead className="text-right">Μέσο sentiment</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((r) => (
                <TableRow key={r.ticker}>
                  <TableCell>
                    <button
                      onClick={() => toggle(r.ticker)}
                      aria-label={isWatched(r.ticker) ? "Αφαίρεση από watchlist" : "Προσθήκη στο watchlist"}
                      className="text-muted-foreground hover:text-foreground"
                    >
                      <Star
                        className="size-4"
                        fill={isWatched(r.ticker) ? "currentColor" : "none"}
                      />
                    </button>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className="flex flex-col">
                        <span className="font-medium">{r.name}</span>
                        <span className="text-xs text-muted-foreground">{r.ticker}</span>
                      </div>
                      {r.unusual && (
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Flame className="size-4 text-negative" />
                          </TooltipTrigger>
                          <TooltipContent>
                            Ασυνήθιστα αυξημένη κάλυψη: {r.article_count} άρθρα σήμερα vs
                            {" "}
                            {r.baseline_articles} μέσο όρο τελευταίων ημερών
                          </TooltipContent>
                        </Tooltip>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    {r.sector && <Badge variant="outline">{r.sector}</Badge>}
                  </TableCell>
                  <TableCell className="text-right">
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <span className={`font-semibold tabular-nums ${scoreColor(r.score)}`}>
                          {r.score}
                        </span>
                      </TooltipTrigger>
                      <TooltipContent>
                        50 (ουδέτερο βάση) + sentiment×40 ({r.avg_sentiment >= 0 ? "+" : ""}
                        {(r.avg_sentiment * 40).toFixed(1)}) + μπόνους όγκου (+
                        {r.volume_bonus}) = {r.score}
                      </TooltipContent>
                    </Tooltip>
                  </TableCell>
                  <TableCell>
                    <Sparkline points={history?.[r.ticker] ?? []} />
                  </TableCell>
                  <TableCell className="text-right tabular-nums">{r.article_count}</TableCell>
                  <TableCell className="text-right tabular-nums">{r.source_count}</TableCell>
                  <TableCell className="text-right tabular-nums">
                    {r.avg_sentiment >= 0 ? "+" : ""}
                    {r.avg_sentiment}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      </div>
    </TooltipProvider>
  );
}
