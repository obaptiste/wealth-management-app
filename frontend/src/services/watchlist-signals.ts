import {
  mapSentimentScoreToLabel,
  normalizeSentimentResult,
  type RawSentimentInput,
} from "@/services/sentiment";
import {
  buildSentimentTrendPoints,
  type RawSentimentHistory,
} from "@/services/sentiment-trend";
import type { WatchlistSignalItem } from "@/types/domain";

export interface RawWatchlistItem {
  symbol?: string | null;
  display_name?: string | null;
  notes?: string | null;
  added_at?: string | null;
  created_at?: string | null;
  latest_sentiment?: RawSentimentInput | null;
}

type WatchlistHistoryMap = Record<string, RawSentimentHistory | null>;

const SIGNAL_PRIORITY: Record<WatchlistSignalItem["signal_strength"], number> = {
  high: 3,
  medium: 2,
  low: 1,
  none: 0,
};

function normalizeWatchlistItem(input: RawWatchlistItem): WatchlistSignalItem | null {
  const symbol = input.symbol?.trim().toUpperCase();

  if (!symbol) {
    return null;
  }

  const latestSentiment = input.latest_sentiment
    ? normalizeSentimentResult({
        ...input.latest_sentiment,
        symbol,
      })
    : null;

  return {
    symbol,
    display_name: input.display_name?.trim() || null,
    added_at: input.added_at ?? input.created_at ?? null,
    notes: input.notes?.trim() || null,
    latest_sentiment: latestSentiment,
    last_analyzed_at: latestSentiment?.analyzed_at ?? null,
    trend: "unavailable",
    sentiment_delta: null,
    signal_strength: latestSentiment
      ? classifySignalStrength(Math.abs(latestSentiment.score))
      : "none",
  };
}

function classifySignalStrength(scoreMagnitude: number): WatchlistSignalItem["signal_strength"] {
  if (scoreMagnitude >= 0.55) {
    return "high";
  }

  if (scoreMagnitude >= 0.25) {
    return "medium";
  }

  if (scoreMagnitude > 0) {
    return "low";
  }

  return "none";
}

function deriveSentimentFromHistory(
  symbol: string,
  history: RawSentimentHistory | null,
): Pick<
  WatchlistSignalItem,
  "latest_sentiment" | "last_analyzed_at" | "trend" | "sentiment_delta" | "signal_strength"
> {
  if (!history) {
    return {
      latest_sentiment: null,
      last_analyzed_at: null,
      trend: "unavailable",
      sentiment_delta: null,
      signal_strength: "none",
    };
  }

  const points = buildSentimentTrendPoints(history);
  const latestPoint = points.at(-1);

  if (!latestPoint) {
    return {
      latest_sentiment: null,
      last_analyzed_at: null,
      trend: "unavailable",
      sentiment_delta: null,
      signal_strength: "none",
    };
  }

  const previousPoint = points.at(-2);
  const sentimentDelta = previousPoint
    ? latestPoint.score - previousPoint.score
    : null;

  return {
    latest_sentiment: {
      symbol,
      score: latestPoint.score,
      label: mapSentimentScoreToLabel(latestPoint.score),
      confidence: null,
      source: "sentiment_history",
      analyzed_at: new Date(`${latestPoint.date}T00:00:00Z`).toISOString(),
    },
    last_analyzed_at: new Date(`${latestPoint.date}T00:00:00Z`).toISOString(),
    trend: classifyTrend(sentimentDelta),
    sentiment_delta: sentimentDelta,
    signal_strength: classifySignalStrength(Math.abs(latestPoint.score)),
  };
}

function classifyTrend(sentimentDelta: number | null): WatchlistSignalItem["trend"] {
  if (sentimentDelta === null) {
    return "steady";
  }

  if (sentimentDelta >= 0.15) {
    return "improving";
  }

  if (sentimentDelta <= -0.15) {
    return "worsening";
  }

  return "steady";
}

function sortWatchlistSignals(
  left: WatchlistSignalItem,
  right: WatchlistSignalItem,
): number {
  const strengthDifference =
    SIGNAL_PRIORITY[right.signal_strength] - SIGNAL_PRIORITY[left.signal_strength];

  if (strengthDifference !== 0) {
    return strengthDifference;
  }

  const rightScore = Math.abs(right.latest_sentiment?.score ?? 0);
  const leftScore = Math.abs(left.latest_sentiment?.score ?? 0);

  if (rightScore !== leftScore) {
    return rightScore - leftScore;
  }

  const rightParsed = right.last_analyzed_at ? Date.parse(right.last_analyzed_at) : NaN;
  const leftParsed = left.last_analyzed_at ? Date.parse(left.last_analyzed_at) : NaN;

  // Coerce NaN (invalid/missing timestamps) to 0 so the comparator always
  // returns a stable numeric value and sort ordering is well-defined.
  const rightTimestamp = Number.isNaN(rightParsed) ? 0 : rightParsed;
  const leftTimestamp = Number.isNaN(leftParsed) ? 0 : leftParsed;

  return rightTimestamp - leftTimestamp;
}

export function buildWatchlistSignalItems(
  inputs: RawWatchlistItem[],
  historyBySymbol: WatchlistHistoryMap = {},
): WatchlistSignalItem[] {
  return inputs
    .map((input) => normalizeWatchlistItem(input))
    .filter((item): item is WatchlistSignalItem => item !== null)
    .map((item) => {
      const historySignal = deriveSentimentFromHistory(
        item.symbol,
        historyBySymbol[item.symbol] ?? null,
      );

      return {
        ...item,
        latest_sentiment:
          historySignal.latest_sentiment ?? item.latest_sentiment ?? null,
        last_analyzed_at:
          historySignal.last_analyzed_at ??
          item.latest_sentiment?.analyzed_at ??
          null,
        trend:
          historySignal.latest_sentiment !== null
            ? historySignal.trend
            : item.latest_sentiment
              ? "steady"
              : "unavailable",
        sentiment_delta: historySignal.sentiment_delta,
        signal_strength:
          historySignal.latest_sentiment !== null
            ? historySignal.signal_strength
            : item.signal_strength,
      };
    })
    .sort(sortWatchlistSignals);
}
