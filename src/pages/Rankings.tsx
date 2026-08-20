import { useMemo, useState } from "react";
import { useJsonData } from "@/hooks/useJsonData";
import type { RankingsFile } from "@/types/data";
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
  const { data, error, loading } = useJsonData<RankingsFile>("/data/rankings.json");
  const [continent, setContinent] = useState("all");

  const rows = useMemo(() => {
    if (!data) return [];
    const filtered = data.rankings.filter(
      (r) => continent === "all" || r.continent === continent
    );
    return [...filtered].sort((a, b) => b.score - a.score);
  }, [data, continent]);

  if (loading) return <p className="text-muted-foreground text-sm">Φόρτωση rankings…</p>;
  if (error) return <p className="text-negative text-sm">Σφάλμα φόρτωσης: {error}</p>;

  return (
    <TooltipProvider>
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
        </div>

        <p className="text-xs text-muted-foreground max-w-2xl">
          Το score προκύπτει αποκλειστικά από deterministic ανάλυση ειδήσεων (μέσο
          sentiment με βάρος πρόσφατου + όγκος κάλυψης) — <strong>δεν αποτελεί
          επενδυτική συμβουλή</strong>, μόνο δείκτη κάλυψης/απήχησης ειδήσεων.
        </p>

        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Μετοχή</TableHead>
                <TableHead>Κλάδος</TableHead>
                <TableHead className="text-right">Score</TableHead>
                <TableHead className="text-right">Άρθρα</TableHead>
                <TableHead className="text-right">Μέσο sentiment</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((r) => (
                <TableRow key={r.ticker}>
                  <TableCell>
                    <div className="flex flex-col">
                      <span className="font-medium">{r.name}</span>
                      <span className="text-xs text-muted-foreground">{r.ticker}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{r.sector}</Badge>
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
                  <TableCell className="text-right tabular-nums">{r.article_count}</TableCell>
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
