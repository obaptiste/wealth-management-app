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

export interface PortfolioSnapshotHolding {
  asset_id?: number | null;
  symbol: string;
  quantity: number;
  price: number;
  current_value: number;
  allocation_percent: number;
  total_cost: number;
  profit_loss: number;
  profit_loss_percent: number;
}

export interface PortfolioSnapshot {
  portfolio_id: number;
  as_of: string;
  summary: PortfolioSummary;
  holdings: PortfolioSnapshotHolding[];
}

export interface HistoricalSnapshotPoint {
  as_of: string;
  portfolio_value: number;
  sentiment_score?: number;
}

/** Matches backend PortfolioSnapshotHistoryResponse */
export interface PortfolioSnapshotHistoryResponse {
  portfolio_id: number;
  from_date: string;
  to_date: string;
  points: HistoricalSnapshotPoint[];
}

export type SnapshotHoldingDeltaStatus =
  | "added"
  | "removed"
  | "changed"
  | "unchanged";

export interface PortfolioSnapshotComparisonSummary {
  current_value: number;
  previous_value: number;
  value_change: number;
  value_change_percent: number;
  current_cost: number;
  previous_cost: number;
  cost_change: number;
  current_profit_loss: number;
  previous_profit_loss: number;
  profit_loss_change: number;
  current_profit_loss_percent: number;
  previous_profit_loss_percent: number;
  profit_loss_percent_change: number;
}

export interface PortfolioSnapshotHoldingDelta {
  asset_id?: number | null;
  symbol: string;
  status: SnapshotHoldingDeltaStatus;
  current_quantity: number;
  previous_quantity: number;
  quantity_change: number;
  current_price: number;
  previous_price: number;
  price_change: number;
  current_value: number;
  previous_value: number;
  value_change: number;
  current_allocation_percent: number;
  previous_allocation_percent: number;
  allocation_percent_change: number;
  current_profit_loss: number;
  previous_profit_loss: number;
  profit_loss_change: number;
}

export interface PortfolioSnapshotComparison {
  portfolio_id: number;
  current_as_of: string;
  previous_as_of: string;
  summary: PortfolioSnapshotComparisonSummary;
  holdings: PortfolioSnapshotHoldingDelta[];
}
