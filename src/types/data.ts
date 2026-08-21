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

export interface Mover {
  ticker: string;
  name: string;
  sector: string | null;
  price: string;
  change_pct: number;
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
}

export interface RadarFile {
  generated_at: string;
  move_threshold_pct: number;
  movers: Mover[];
  breaking: BreakingItem[];
}
