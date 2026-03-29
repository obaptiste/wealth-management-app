import type { AssetWithPerformance } from "./assets";
import type { PortfolioSummary } from "./portfolios";

export type SentimentLabel =
  | "very_bearish"
  | "bearish"
  | "neutral"
  | "bullish"
  | "very_bullish";

export interface SentimentResult {
  symbol: string;
  score: number;
  label: SentimentLabel;
  confidence: number | null;
  source: string;
  analyzed_at: string;
}

export interface HoldingSnapshot {
  symbol: string;
  quantity: number;
  current_value: number;
  allocation_percent: number;
}

export interface PortfolioAllocationSlice extends HoldingSnapshot {
  total_cost: number;
  current_price: number;
  profit_loss: number;
  profit_loss_percent: number;
}

export interface PortfolioGainLossMetrics {
  asset_count: number;
  profitable_positions: number;
  losing_positions: number;
  flat_positions: number;
}

export interface PortfolioSummaryResult {
  summary: PortfolioSummary;
  allocations: PortfolioAllocationSlice[];
  metrics: PortfolioGainLossMetrics;
}

export interface WatchlistItem {
  symbol: string;
  display_name?: string | null;
  added_at: string | null;
  notes?: string | null;
  latest_sentiment?: SentimentResult | null;
}

export type WatchlistSignalTrend =
  | "improving"
  | "worsening"
  | "steady"
  | "unavailable";

export type WatchlistSignalStrength = "high" | "medium" | "low" | "none";

export interface WatchlistSignalItem extends WatchlistItem {
  latest_sentiment: SentimentResult | null;
  last_analyzed_at: string | null;
  trend: WatchlistSignalTrend;
  sentiment_delta: number | null;
  signal_strength: WatchlistSignalStrength;
}

export interface PortfolioSnapshot {
  portfolio_id: number;
  as_of: string;
  summary: PortfolioSummary;
  holdings: AssetWithPerformance[];
}

export interface HistoricalSnapshotPoint {
  as_of: string;
  portfolio_value: number;
  sentiment_score?: number;
}
