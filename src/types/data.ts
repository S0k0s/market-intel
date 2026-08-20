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
  sector: string;
  continent: "na" | "eu" | "as" | "oc";
  score: number;
  article_count: number;
  avg_sentiment: number;
  volume_bonus: number;
}

export interface RankingsFile {
  generated_at: string;
  continents: Record<string, ContinentMeta>;
  rankings: Ranking[];
}
