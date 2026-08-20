import { useMemo, useState } from "react";
import { useJsonData } from "@/hooks/useJsonData";
import { useWatchlist } from "@/hooks/useWatchlist";
import type { RankingsFile, HistoryFile, Horizon } from "@/types/data";
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
import { Star, Flame, ArrowUp, ArrowDown, ArrowUpDown } from "lucide-react";

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

const HORIZON_FILTERS: { id: "all" | "swing" | "long_term"; label: string }[] = [
  { id: "all", label: "Όλοι οι ορίζοντες" },
  { id: "swing", label: "Swing" },
  { id: "long_term", label: "Long-term" },
];

type SortKey = "score" | "article_count" | "source_count" | "avg_sentiment";

const SORT_COLUMNS: { key: SortKey; label: string; align?: "right" }[] = [
  { key: "score", label: "Score", align: "right" },
  { key: "article_count", label: "Άρθρα", align: "right" },
  { key: "source_count", label: "Πηγές", align: "right" },
  { key: "avg_sentiment", label: "Μέσο sentiment", align: "right" },
];

function scoreColor(score: number) {
  if (score >= 60) return "text-positive";
  if (score <= 40) return "text-negative";
  return "text-foreground";
}

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

function SortableHead({
  col,
  sortKey,
  sortDir,
  onSort,
}: {
  col: { key: SortKey; label: string; align?: "right" };
  sortKey: SortKey;
  sortDir: "asc" | "desc";
  onSort: (key: SortKey) => void;
}) {
  return (
    <TableHead className={col.align === "right" ? "text-right" : ""}>
      <button
        onClick={() => onSort(col.key)}
        className="inline-flex items-center gap-1 hover:text-foreground"
      >
        {col.label}
        {sortKey === col.key ? (
          sortDir === "desc" ? (
            <ArrowDown className="size-3" />
          ) : (
            <ArrowUp className="size-3" />
          )
        ) : (
          <ArrowUpDown className="size-3 opacity-40" />
        )}
      </button>
    </TableHead>
  );
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
  const [sentimentFilter, setSentimentFilter] = useState<"all" | "positive" | "neutral" | "negative">("all");
  const [horizonFilter, setHorizonFilter] = useState<"all" | "swing" | "long_term">("all");
  const [search, setSearch] = useState("");
  const [watchlistOnly, setWatchlistOnly] = useState(false);
  const [sortKey, setSortKey] = useState<SortKey>("score");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  function handleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDir((d) => (d === "desc" ? "asc" : "desc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

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
      if (sentimentFilter !== "all" && sentimentCategory(r.avg_sentiment) !== sentimentFilter) return false;
      if (horizonFilter !== "all" && r.horizon !== horizonFilter) return false;
      if (watchlistOnly && !isWatched(r.ticker)) return false;
      if (q && !r.name.toLowerCase().includes(q) && !r.ticker.toLowerCase().includes(q))
        return false;
      return true;
    });
    return [...filtered].sort((a, b) => {
      const aw = isWatched(a.ticker) ? 1 : 0;
      const bw = isWatched(b.ticker) ? 1 : 0;
      if (aw !== bw) return bw - aw;
      const diff = a[sortKey] - b[sortKey];
      return sortDir === "desc" ? -diff : diff;
    });
  }, [data, continent, sector, sentimentFilter, horizonFilter, search, watchlistOnly, isWatched, sortKey, sortDir]);

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
            value={horizonFilter}
            onChange={(e) => setHorizonFilter(e.target.value as typeof horizonFilter)}
            className="h-8 rounded-md border border-input bg-background px-2 text-sm"
          >
            {HORIZON_FILTERS.map((o) => (
              <option key={o.id} value={o.id}>
                {o.label}
              </option>
            ))}
          </select>
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
          ιστορικό της μετοχής. Οι ετικέτες <strong>Swing/Long-term</strong> προκύπτουν
          από τη γλώσσα των άρθρων (π.χ. "earnings"/"breakout" → swing,
          "dividend"/"στρατηγική" → long-term) — δεν βασίζονται σε τεχνικά ή
          θεμελιώδη δεδομένα.
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
                <SortableHead col={SORT_COLUMNS[0]} sortKey={sortKey} sortDir={sortDir} onSort={handleSort} />
                <TableHead>Τάση</TableHead>
                <SortableHead col={SORT_COLUMNS[1]} sortKey={sortKey} sortDir={sortDir} onSort={handleSort} />
                <SortableHead col={SORT_COLUMNS[2]} sortKey={sortKey} sortDir={sortDir} onSort={handleSort} />
                <SortableHead col={SORT_COLUMNS[3]} sortKey={sortKey} sortDir={sortDir} onSort={handleSort} />
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
                      {horizonBadge(r.horizon)}
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
