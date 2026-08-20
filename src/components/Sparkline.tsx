import type { HistoryPoint } from "@/types/data";

export function Sparkline({ points }: { points: HistoryPoint[] }) {
  if (points.length < 2) {
    return <span className="text-xs text-muted-foreground">—</span>;
  }
  const scores = points.map((p) => p.score);
  const min = Math.min(...scores);
  const max = Math.max(...scores);
  const range = max - min || 1;
  const w = 64;
  const h = 20;
  const step = w / (scores.length - 1);
  const coords = scores.map((s, i) => {
    const x = i * step;
    const y = h - ((s - min) / range) * h;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });
  const trendUp = scores[scores.length - 1] >= scores[0];

  return (
    <svg
      width={w}
      height={h}
      viewBox={`0 0 ${w} ${h}`}
      className={trendUp ? "text-positive" : "text-negative"}
    >
      <polyline
        points={coords.join(" ")}
        fill="none"
        stroke="currentColor"
        strokeWidth={1.5}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
