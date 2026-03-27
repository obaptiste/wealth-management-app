import apiClient from "@/lib/api";
import { summarizePortfolio } from "@/services/portfolio-summary";
import { normalizeSentimentResult } from "@/services/sentiment";
import { buildSentimentTrendPoints } from "@/services/sentiment-trend";
import type { AssetWithPerformance } from "@/types/assets";
import type { SentimentChartPoint } from "@/types/chart";
import type {
  PortfolioAllocationSlice,
  PortfolioSummaryResult,
  SentimentResult,
} from "@/types/domain";
import type { Portfolio, PortfolioWithSummary } from "@/types/portfolios";

interface SentimentTrendPoint {
  date: string;
  positive: number;
  negative: number;
  neutral: number;
  total_analyzed: number;
}

interface SentimentHistoryResponse {
  symbol: string;
  days_analyzed: number;
  sentiment_trends: SentimentTrendPoint[];
}

export interface DashboardPortfolioSnapshot {
  id: number;
  name: string;
  asset_count: number;
  summary: PortfolioSummaryResult["summary"];
}

export interface DashboardData {
  portfolio_count: number;
  asset_count: number;
  summary: PortfolioSummaryResult["summary"];
  metrics: PortfolioSummaryResult["metrics"];
  top_allocations: PortfolioAllocationSlice[];
  portfolios: DashboardPortfolioSnapshot[];
  primary_sentiment: SentimentResult | null;
  sentiment_trend: SentimentChartPoint[];
}

function flattenPortfolioAssets(
  portfolios: PortfolioWithSummary[],
): AssetWithPerformance[] {
  return portfolios.flatMap((portfolio) => portfolio.assets);
}

function buildPortfolioSnapshots(
  portfolios: PortfolioWithSummary[],
): DashboardPortfolioSnapshot[] {
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

function toSentimentScore(trend: SentimentTrendPoint): number {
  return (trend.positive - trend.negative) / 100;
}

async function loadPrimarySentiment(
  symbol?: string,
): Promise<SentimentResult | null> {
  if (!symbol) {
    return null;
  }

  try {
    const history = (await apiClient.getSentimentHistory(
      symbol,
      7,
    )) as SentimentHistoryResponse;
    const latestTrend = history.sentiment_trends.at(-1);

    if (!latestTrend) {
      return null;
    }

    return normalizeSentimentResult({
      symbol: history.symbol,
      score: toSentimentScore(latestTrend),
      confidence: null,
      source: "sentiment_history",
      analyzed_at: new Date(`${latestTrend.date}T00:00:00Z`).toISOString(),
    });
  } catch (error) {
    console.warn(
      `Dashboard sentiment history unavailable for ${symbol}`,
      error,
    );
    return null;
  }
}

async function loadSentimentTrend(
  symbol?: string,
): Promise<SentimentChartPoint[]> {
  if (!symbol) {
    return [];
  }

  try {
    const history = (await apiClient.getSentimentHistory(
      symbol,
      7,
    )) as SentimentHistoryResponse;
    return buildSentimentTrendPoints(history);
  } catch (error) {
    console.warn(`Dashboard sentiment trend unavailable for ${symbol}`, error);
    return [];
  }
}

async function loadPortfolioDetails(): Promise<PortfolioWithSummary[]> {
  const portfolios = (await apiClient.getPortfolios()) as Portfolio[];

  if (portfolios.length === 0) {
    return [];
  }

  return Promise.all(
    portfolios.map(
      (portfolio) =>
        apiClient.getPortfolio(
          String(portfolio.id),
        ) as Promise<PortfolioWithSummary>,
    ),
  );
}

export async function loadDashboardData(): Promise<DashboardData> {
  const portfolios = await loadPortfolioDetails();
  const allAssets = flattenPortfolioAssets(portfolios);
  const summaryResult = summarizePortfolio(allAssets);
  const primarySymbol = summaryResult.allocations[0]?.symbol;
  const [primarySentiment, sentimentTrend] = await Promise.all([
    loadPrimarySentiment(primarySymbol),
    loadSentimentTrend(primarySymbol),
  ]);

  return {
    portfolio_count: portfolios.length,
    asset_count: summaryResult.metrics.asset_count,
    summary: summaryResult.summary,
    metrics: summaryResult.metrics,
    top_allocations: summaryResult.allocations.slice(0, 3),
    portfolios: buildPortfolioSnapshots(portfolios),
    primary_sentiment: primarySentiment,
    sentiment_trend: sentimentTrend,
  };
}
