import apiClient from '@/lib/api';
import { summarizePortfolio } from '@/services/portfolio-summary';
import { buildSentimentTrendPoints, type RawSentimentHistory } from '@/services/sentiment-trend';
import type { SentimentChartPoint } from '@/types/chart';
import type {
  PortfolioAllocationSlice,
  PortfolioSummaryResult,
  SentimentLabel,
  SentimentResult,
} from '@/types/domain';
import type { Portfolio, PortfolioWithSummary } from '@/types/portfolios';

export interface DashboardPortfolioSnapshot {
  id: number;
  name: string;
  asset_count: number;
  summary: PortfolioSummaryResult['summary'];
}

export interface DashboardData {
  portfolio_count: number;
  asset_count: number;
  summary: PortfolioSummaryResult['summary'];
  metrics: PortfolioSummaryResult['metrics'];
  top_allocations: PortfolioAllocationSlice[];
  portfolios: DashboardPortfolioSnapshot[];
  primary_sentiment: SentimentResult | null;
  sentiment_trend: SentimentChartPoint[];
}

// Maps a net sentiment score in [-1, 1] to a domain label without going through
// normalizeSentimentScore, which assumes [0, 1] inputs are raw model probabilities.
function scoreToSentimentLabel(score: number): SentimentLabel {
  if (score >= 0.5) return 'very_bullish';
  if (score >= 0.1) return 'bullish';
  if (score > -0.1) return 'neutral';
  if (score > -0.5) return 'bearish';
  return 'very_bearish';
}

// Net sentiment score in [-1, 1] derived from percentage breakdown.
function toNetSentimentScore(positive: number, negative: number): number {
  return (positive - negative) / 100;
}

// Fetches sentiment history once so both primary signal and trend can be derived
// from a single API call. Returns null on failure so callers can degrade gracefully.
async function loadSentimentHistory(symbol: string): Promise<RawSentimentHistory | null> {
  try {
    return await apiClient.getSentimentHistory(symbol, 7) as RawSentimentHistory;
  } catch (error) {
    console.warn(`Dashboard sentiment history unavailable for ${symbol}`, error);
    return null;
  }
}

// Derives the primary sentiment signal from the most recent trend entry. Constructs
// a SentimentResult directly so the already-normalized net score is not re-processed
// by normalizeSentimentScore (which assumes [0,1] raw model probabilities as input).
function derivePrimarySentiment(history: RawSentimentHistory | null): SentimentResult | null {
  if (!history) {
    return null;
  }

  const rawPoints = history.sentiment_trends ?? [];
  const latestTrend = rawPoints.at(-1);

  if (!latestTrend || !latestTrend.date) {
    return null;
  }

  const score = toNetSentimentScore(latestTrend.positive ?? 0, latestTrend.negative ?? 0);

  return {
    symbol: (history.symbol ?? 'UNKNOWN').toUpperCase(),
    score,
    label: scoreToSentimentLabel(score),
    confidence: null,
    source: 'sentiment_history',
    analyzed_at: new Date(`${latestTrend.date}T00:00:00Z`).toISOString(),
  };
}

function deriveSentimentTrend(history: RawSentimentHistory | null): SentimentChartPoint[] {
  if (!history) {
    return [];
  }

  return buildSentimentTrendPoints(history);
}

function flattenPortfolioAssets(portfolios: PortfolioWithSummary[]) {
  return portfolios.flatMap((portfolio) => portfolio.assets);
}

function buildPortfolioSnapshots(portfolios: PortfolioWithSummary[]): DashboardPortfolioSnapshot[] {
  return portfolios.map((portfolio) => {
    const result = summarizePortfolio(portfolio.assets);

    return {
      id: portfolio.id,
      name: portfolio.name,
      asset_count: portfolio.assets.length,
      summary: result.summary,
    };
  });
}

async function loadPortfolioDetails(): Promise<PortfolioWithSummary[]> {
  const portfolios = await apiClient.getPortfolios() as Portfolio[];

  if (portfolios.length === 0) {
    return [];
  }

  return Promise.all(
    portfolios.map((portfolio) => apiClient.getPortfolio(String(portfolio.id)) as Promise<PortfolioWithSummary>),
  );
}

export async function loadDashboardData(): Promise<DashboardData> {
  const portfolios = await loadPortfolioDetails();
  const allAssets = flattenPortfolioAssets(portfolios);
  const summaryResult = summarizePortfolio(allAssets);
  const primarySymbol = summaryResult.allocations[0]?.symbol;

  // Fetch sentiment history once; both primary signal and trend series are derived from it.
  const sentimentHistory = primarySymbol
    ? await loadSentimentHistory(primarySymbol)
    : null;

  return {
    portfolio_count: portfolios.length,
    asset_count: summaryResult.metrics.asset_count,
    summary: summaryResult.summary,
    metrics: summaryResult.metrics,
    top_allocations: summaryResult.allocations.slice(0, 3),
    portfolios: buildPortfolioSnapshots(portfolios),
    primary_sentiment: derivePrimarySentiment(sentimentHistory),
    sentiment_trend: deriveSentimentTrend(sentimentHistory),
  };
}
