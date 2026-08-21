export type Horizon = "swing" | "long_term" | null;

export interface Article {
  title: string;
  summary: string;
  url: string;
  source: string;
  source_id: string;
  continent: "na" | "eu" | "as" | "oc";
  published_at: string;
  epoch: number;
  sentiment: number;
  horizon: Horizon;
  tickers: string[];
}

export interface ArticlesFile {
  generated_at: string;
  articles: Article[];
}

export interface ContinentMeta {
  label: string;
  flag: string;
}

export interface Ranking {
  ticker: string;
  name: string;
  sector: string | null;
  continent: "na" | "eu" | "as" | "oc";
  score: number;
  article_count: number;
  avg_sentiment: number;
  volume_bonus: number;
  source_count: number;
  unusual: boolean;
  baseline_articles: number | null;
  horizon: Horizon;
  swing_count: number;
  longterm_count: number;
}

export interface RankingsFile {
  generated_at: string;
  continents: Record<string, ContinentMeta>;
  rankings: Ranking[];
}

export interface HistoryPoint {
  date: string;
  score: number;
  avg_sentiment: number;
  article_count: number;
}

export type HistoryFile = Record<string, HistoryPoint[]>;

export type Archetype = "quality_compounding" | "momentum_breakout" | "speculative" | null;

export interface Mover {
  ticker: string;
  name: string;
  sector: string | null;
  price: string;
  change_pct: number;
  long_term_score: number | null;
  swing_score: number | null;
  archetype: Archetype;
  archetype_label: string | null;
  piotroski_f: number | null;
  altman_z: number | null;
  rsi: number | null;
  peg_ratio: number | null;
  analyst_consensus: string | null;
  streak_days: number;
}

export interface BreakingItem {
  title: string;
  summary: string;
  url: string;
  source: string;
  source_id: string;
  published_at: string;
  epoch: number;
  sentiment: number;
  tickers: string[];
  company_name: string | null;
  catalyst: boolean;
}

export interface RadarFile {
  generated_at: string;
  move_threshold_pct: number;
  movers: Mover[];
  concentration_warning: string | null;
  breaking: BreakingItem[];
}
