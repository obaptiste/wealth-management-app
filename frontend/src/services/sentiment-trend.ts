import type { SentimentChartPoint } from '@/types/chart';

export interface RawSentimentTrendPoint {
  date?: string | null;
  positive?: number | null;
  negative?: number | null;
  neutral?: number | null;
  total_analyzed?: number | null;
}

export interface RawSentimentHistory {
  symbol?: string | null;
  days_analyzed?: number | null;
  sentiment_trends?: RawSentimentTrendPoint[] | null;
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

function clampPercentage(value: unknown): number {
  if (!isFiniteNumber(value)) {
    return 0;
  }

  return Math.min(Math.max(value, 0), 100);
}

function normalizeTotalAnalyzed(value: unknown): number {
  if (!isFiniteNumber(value)) {
    return 0;
  }

  return value > 0 ? Math.round(value) : 0;
}

function normalizeDate(value?: string | null): string | null {
  if (!value) {
    return null;
  }

  const timestamp = Date.parse(value);
  if (!Number.isFinite(timestamp)) {
    return null;
  }

  return new Date(timestamp).toISOString().slice(0, 10);
}

function toSentimentScore(positive: number, negative: number): number {
  return (positive - negative) / 100;
}

export function buildSentimentTrendPoints(history: RawSentimentHistory): SentimentChartPoint[] {
  const rawPoints = history.sentiment_trends ?? [];

  return rawPoints
    .map((point) => {
      const date = normalizeDate(point.date);

      if (!date) {
        return null;
      }

      const positive = clampPercentage(point.positive);
      const negative = clampPercentage(point.negative);
      const neutral = clampPercentage(point.neutral);

      return {
        date,
        score: toSentimentScore(positive, negative),
        positive,
        neutral,
        negative,
        total_analyzed: normalizeTotalAnalyzed(point.total_analyzed),
      };
    })
    .filter((point): point is SentimentChartPoint => point !== null)
    .sort((left, right) => left.date.localeCompare(right.date));
}
