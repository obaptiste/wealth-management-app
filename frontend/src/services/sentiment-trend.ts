import type { SentimentChartPoint } from '@/types/chart';

export interface RawSentimentTrendInput {
  date?: string | null;
  positive?: number | null;
  neutral?: number | null;
  negative?: number | null;
  total_analyzed?: number | null;
}

export interface SentimentTrendHistoryInput {
  sentiment_trends?: RawSentimentTrendInput[] | null;
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

function normalizePercent(value?: number | null): number {
  if (!isFiniteNumber(value)) {
    return 0;
  }

  return clamp(value, 0, 100);
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
  return clamp((positive - negative) / 100, -1, 1);
}

export function mapSentimentTrendPoint(input: RawSentimentTrendInput): SentimentChartPoint | null {
  const date = normalizeDate(input.date);

  if (!date) {
    return null;
  }

  const positive = normalizePercent(input.positive);
  const neutral = normalizePercent(input.neutral);
  const negative = normalizePercent(input.negative);
  const totalAnalyzed = isFiniteNumber(input.total_analyzed)
    ? Math.max(input.total_analyzed, 0)
    : 0;

  return {
    date,
    score: toSentimentScore(positive, negative),
    positive,
    neutral,
    negative,
    total_analyzed: totalAnalyzed,
  };
}

export function mapSentimentTrendHistory(input: SentimentTrendHistoryInput): SentimentChartPoint[] {
  const trends = input.sentiment_trends ?? [];
  const mapped = trends
    .map((trend) => mapSentimentTrendPoint(trend))
    .filter((trend): trend is SentimentChartPoint => trend !== null);

  mapped.sort((left, right) => left.date.localeCompare(right.date));

  return mapped;
}
