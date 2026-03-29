import apiClient from "@/lib/api";
import { mapSentimentScoreToLabel } from "@/services/sentiment";
import { summarizePortfolio } from "@/services/portfolio-summary";
import {
  buildSentimentTrendPoints,
  type RawSentimentHistory,
} from "@/services/sentiment-trend";
import {
  buildWatchlistSignalItems,
  type RawWatchlistItem,
} from "@/services/watchlist-signals";
import type { AssetWithPerformance } from "@/types/assets";
import type { SentimentChartPoint } from "@/types/chart";
import type {
  PortfolioAllocationSlice,
  PortfolioSummaryResult,
  SentimentResult,
  WatchlistSignalItem,
} from "@/types/domain";
import type { Portfolio, PortfolioWithSummary } from "@/types/portfolios";

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
  watchlist:
    | { status: "available"; items: WatchlistSignalItem[] }
    | { status: "unavailable"; items: [] };
}

const WATCHLIST_SIGNAL_LIMIT = 4;

// Net sentiment score in [-1, 1] derived from percentage breakdown.
function toNetSentimentScore(positive: number, negative: number): number {
  return (positive - negative) / 100;
}

// Fetches sentiment history once so both primary signal and trend can be derived
// from a single API call. Returns null on failure so callers can degrade gracefully.
async function loadSentimentHistory(
  symbol: string,
): Promise<RawSentimentHistory | null> {
  try {
    return (await apiClient.getSentimentHistory(symbol, 7)) as RawSentimentHistory;
  } catch (error) {
    console.warn(`Dashboard sentiment history unavailable for ${symbol}`, error);
    return null;
  }
}

// Derives the primary sentiment signal from the most recent trend entry. Constructs
// a SentimentResult directly so the already-normalized net score is not re-processed
// by normalizeSentimentScore (which assumes [0,1] raw model probabilities as input).
function derivePrimarySentiment(
  history: RawSentimentHistory | null,
): SentimentResult | null {
  if (!history) {
    return null;
  }

  const rawPoints = history.sentiment_trends ?? [];
  const latestTrend = rawPoints.at(-1);

  if (!latestTrend || !latestTrend.date) {
    return null;
  }

  const score = toNetSentimentScore(
    latestTrend.positive ?? 0,
    latestTrend.negative ?? 0,
  );

  return {
    symbol: (history.symbol ?? "UNKNOWN").toUpperCase(),
    score,
    label: mapSentimentScoreToLabel(score),
    confidence: null,
    source: "sentiment_history",
    analyzed_at: new Date(`${latestTrend.date}T00:00:00Z`).toISOString(),
  };
}

function deriveSentimentTrend(
  history: RawSentimentHistory | null,
): SentimentChartPoint[] {
  if (!history) {
    return [];
  }

  return buildSentimentTrendPoints(history);
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

function isFeatureUnavailable(error: unknown): boolean {
  if (
    typeof error === "object" &&
    error !== null &&
    "response" in error &&
    typeof error.response === "object" &&
    error.response !== null &&
    "status" in error.response
  ) {
    const status = error.response.status;

    return status === 404 || status === 405 || status === 501;
  }

  return false;
}

async function loadRawWatchlistItems(): Promise<
  | { status: "available"; items: RawWatchlistItem[] }
  | { status: "unavailable"; items: [] }
> {
  try {
    const items = (await apiClient.getWatchlist()) as RawWatchlistItem[];

    return {
      status: "available",
      items,
    };
  } catch (error) {
    if (isFeatureUnavailable(error)) {
      console.warn("Dashboard watchlist endpoint unavailable", error);
    } else {
      console.warn("Dashboard watchlist request failed", error);
    }

    return {
      status: "unavailable",
      items: [],
    };
  }
}

async function loadWatchlistHistories(
  items: RawWatchlistItem[],
): Promise<Record<string, RawSentimentHistory | null>> {
  const uniqueSymbols = Array.from(
    new Set(
      items
        .map((item) => item.symbol?.trim().toUpperCase())
        .filter((symbol): symbol is string => Boolean(symbol)),
    ),
  ).slice(0, WATCHLIST_SIGNAL_LIMIT);

  const histories = await Promise.all(
    uniqueSymbols.map(async (symbol) => {
      try {
        return [symbol, await loadSentimentHistory(symbol)] as const;
      } catch (error) {
        console.warn(`Dashboard watchlist sentiment unavailable for ${symbol}`, error);
        return [symbol, null] as const;
      }
    }),
  );

  return Object.fromEntries(histories);
}

async function loadWatchlistPanelData(): Promise<DashboardData["watchlist"]> {
  const watchlist = await loadRawWatchlistItems();

  if (watchlist.status === "unavailable") {
    return watchlist;
  }

  const selectedItems = watchlist.items.slice(0, WATCHLIST_SIGNAL_LIMIT);
  const historyBySymbol = await loadWatchlistHistories(selectedItems);

  return {
    status: "available",
    items: buildWatchlistSignalItems(selectedItems, historyBySymbol).slice(
      0,
      WATCHLIST_SIGNAL_LIMIT,
    ),
  };
}

export async function loadDashboardData(): Promise<DashboardData> {
  const portfolios = await loadPortfolioDetails();
  const allAssets = flattenPortfolioAssets(portfolios);
  const summaryResult = summarizePortfolio(allAssets);
  const primarySymbol = summaryResult.allocations[0]?.symbol;

  const [sentimentHistory, watchlist] = await Promise.all([
    primarySymbol ? loadSentimentHistory(primarySymbol) : Promise.resolve(null),
    loadWatchlistPanelData(),
  ]);

  return {
    portfolio_count: portfolios.length,
    asset_count: summaryResult.metrics.asset_count,
    summary: summaryResult.summary,
    metrics: summaryResult.metrics,
    top_allocations: summaryResult.allocations.slice(0, 3),
    portfolios: buildPortfolioSnapshots(portfolios),
    primary_sentiment: derivePrimarySentiment(sentimentHistory),
    sentiment_trend: deriveSentimentTrend(sentimentHistory),
    watchlist,
  };
}
