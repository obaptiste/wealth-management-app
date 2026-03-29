import type { SentimentLabel, SentimentResult } from "@/types/domain";

export interface RawSentimentInput {
  symbol?: string | null;
  score?: number | null;
  label?: string | null;
  confidence?: number | null;
  source?: string | null;
  analyzed_at?: string | null;
}

const LABEL_MAP: Record<string, SentimentLabel> = {
  very_bearish: "very_bearish",
  strongly_negative: "very_bearish",
  bearish: "bearish",
  negative: "bearish",
  neutral: "neutral",
  mixed: "neutral",
  bullish: "bullish",
  positive: "bullish",
  very_bullish: "very_bullish",
  strongly_positive: "very_bullish",
};

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

/**
 * Normalize score into [-1, 1].
 *
 * Rules:
 * - values in [-1, 0) are kept as-is
 * - values in [0, 1] from some model outputs are converted into [-1, 1]
 * - values outside expected ranges are clamped to [-1, 1]
 */
export function normalizeSentimentScore(rawScore: number): number {
  if (rawScore >= -1 && rawScore < 0) {
    return rawScore;
  }

  if (rawScore >= 0 && rawScore <= 1) {
    return rawScore * 2 - 1;
  }

  return clamp(rawScore, -1, 1);
}

/**
 * Normalize confidence into [0, 1].
 *
 * Rules:
 * - null/undefined confidence remains null
 * - values in [0, 1] are kept
 * - values in [0, 100] are treated as percentages and converted
 * - any other value is clamped to [0, 1]
 */
export function normalizeSentimentConfidence(
  rawConfidence?: number | null,
): number | null {
  if (rawConfidence === null || rawConfidence === undefined) {
    return null;
  }

  if (rawConfidence >= 0 && rawConfidence <= 1) {
    return rawConfidence;
  }

  if (rawConfidence > 1 && rawConfidence <= 100) {
    return rawConfidence / 100;
  }

  return clamp(rawConfidence, 0, 1);
}

/**
 * Normalize arbitrary external label values into internal domain labels.
 */
export function normalizeSentimentLabel(
  rawLabel?: string | null,
): SentimentLabel {
  if (!rawLabel) {
    return "neutral";
  }

  const normalizedKey = rawLabel
    .trim()
    .toLowerCase()
    .replace(/[\s-]+/g, "_");
  return LABEL_MAP[normalizedKey] ?? "neutral";
}

/**
 * Build a stable SentimentResult from raw sentiment payloads.
 */
export function normalizeSentimentResult(
  input: RawSentimentInput,
): SentimentResult {
  return {
    symbol: (input.symbol ?? "UNKNOWN").toUpperCase(),
    score: normalizeSentimentScore(input.score ?? 0),
    label: normalizeSentimentLabel(input.label),
    confidence: normalizeSentimentConfidence(input.confidence),
    source: (input.source ?? "unknown").trim() || "unknown",
    analyzed_at: input.analyzed_at ?? new Date().toISOString(),
  };
}

/**
 * Normalize a raw list into domain-ready sentiment results.
 */
export function normalizeSentimentBatch(
  inputs: RawSentimentInput[],
): SentimentResult[] {
  return inputs.map((input) => normalizeSentimentResult(input));
}
