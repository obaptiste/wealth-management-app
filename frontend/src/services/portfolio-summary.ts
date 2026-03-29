import type {
  PortfolioAllocationSlice,
  PortfolioGainLossMetrics,
  PortfolioSummaryResult,
} from "@/types/domain";
import type { PortfolioSummary } from "@/types/portfolios";

export interface PortfolioAssetInput {
  symbol?: string | null;
  quantity?: number | null;
  purchase_price?: number | null;
  current_price?: number | null;
  current_value?: number | null;
  profit_loss?: number | null;
  profit_loss_percent?: number | null;
  last_updated?: string | null;
}

interface NormalizedAssetPosition {
  symbol: string;
  quantity: number;
  total_cost: number;
  current_price: number;
  current_value: number;
  profit_loss: number;
  profit_loss_percent: number;
  last_updated: string | null;
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function toNonNegativeNumber(value: unknown): number {
  if (!isFiniteNumber(value)) {
    return 0;
  }

  return value < 0 ? 0 : value;
}

function toTimestamp(value?: string | null): number | null {
  if (!value) {
    return null;
  }

  const parsed = Date.parse(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function buildSummary(
  totalValue: number,
  totalCost: number,
  lastUpdated: string,
): PortfolioSummary {
  const totalProfitLoss = totalValue - totalCost;

  return {
    total_value: totalValue,
    total_cost: totalCost,
    total_profit_loss: totalProfitLoss,
    total_profit_loss_percent:
      totalCost > 0 ? (totalProfitLoss / totalCost) * 100 : 0,
    last_updated: lastUpdated,
  };
}

function normalizeAssetPosition(
  input: PortfolioAssetInput,
): NormalizedAssetPosition {
  const quantity = toNonNegativeNumber(input.quantity);
  const purchasePrice = toNonNegativeNumber(input.purchase_price);
  const derivedCost = quantity * purchasePrice;
  const totalCost =
    isFiniteNumber(input.profit_loss) && isFiniteNumber(input.current_value)
      ? Math.max(input.current_value - input.profit_loss, 0)
      : derivedCost;

  const fallbackCurrentPrice =
    quantity > 0 ? totalCost / quantity : purchasePrice;
  const currentPrice = isFiniteNumber(input.current_price)
    ? toNonNegativeNumber(input.current_price)
    : fallbackCurrentPrice;
  const currentValue = isFiniteNumber(input.current_value)
    ? toNonNegativeNumber(input.current_value)
    : quantity * currentPrice;
  const profitLoss = isFiniteNumber(input.profit_loss)
    ? input.profit_loss
    : currentValue - totalCost;
  const profitLossPercent = isFiniteNumber(input.profit_loss_percent)
    ? input.profit_loss_percent
    : totalCost > 0
      ? (profitLoss / totalCost) * 100
      : 0;

  return {
    symbol: (input.symbol ?? "UNKNOWN").trim().toUpperCase() || "UNKNOWN",
    quantity,
    total_cost: totalCost,
    current_price: currentPrice,
    current_value: currentValue,
    profit_loss: profitLoss,
    profit_loss_percent: profitLossPercent,
    last_updated: input.last_updated ?? null,
  };
}

function mergeAssetPositions(
  positions: NormalizedAssetPosition[],
): NormalizedAssetPosition[] {
  const mergedBySymbol = new Map<string, NormalizedAssetPosition>();

  for (const position of positions) {
    const existing = mergedBySymbol.get(position.symbol);

    if (!existing) {
      mergedBySymbol.set(position.symbol, { ...position });
      continue;
    }

    const totalQuantity = existing.quantity + position.quantity;
    const totalCost = existing.total_cost + position.total_cost;
    const totalValue = existing.current_value + position.current_value;
    const totalProfitLoss = totalValue - totalCost;
    const latestTimestamp = Math.max(
      toTimestamp(existing.last_updated) ?? 0,
      toTimestamp(position.last_updated) ?? 0,
    );

    mergedBySymbol.set(position.symbol, {
      symbol: position.symbol,
      quantity: totalQuantity,
      total_cost: totalCost,
      current_price: totalQuantity > 0 ? totalValue / totalQuantity : 0,
      current_value: totalValue,
      profit_loss: totalProfitLoss,
      profit_loss_percent:
        totalCost > 0 ? (totalProfitLoss / totalCost) * 100 : 0,
      last_updated:
        latestTimestamp > 0 ? new Date(latestTimestamp).toISOString() : null,
    });
  }

  return Array.from(mergedBySymbol.values());
}

function buildAllocationSlices(
  positions: NormalizedAssetPosition[],
  totalValue: number,
): PortfolioAllocationSlice[] {
  return positions
    .map((position) => ({
      symbol: position.symbol,
      quantity: position.quantity,
      current_value: position.current_value,
      allocation_percent:
        totalValue > 0 ? (position.current_value / totalValue) * 100 : 0,
      total_cost: position.total_cost,
      current_price: position.current_price,
      profit_loss: position.profit_loss,
      profit_loss_percent: position.profit_loss_percent,
    }))
    .sort((left, right) => right.current_value - left.current_value);
}

function buildGainLossMetrics(
  allocations: PortfolioAllocationSlice[],
): PortfolioGainLossMetrics {
  let profitablePositions = 0;
  let losingPositions = 0;
  let flatPositions = 0;

  for (const allocation of allocations) {
    if (allocation.profit_loss > 0) {
      profitablePositions += 1;
      continue;
    }

    if (allocation.profit_loss < 0) {
      losingPositions += 1;
      continue;
    }

    flatPositions += 1;
  }

  return {
    asset_count: allocations.length,
    profitable_positions: profitablePositions,
    losing_positions: losingPositions,
    flat_positions: flatPositions,
  };
}

export function summarizePortfolio(
  assets: PortfolioAssetInput[],
): PortfolioSummaryResult {
  const mergedPositions = mergeAssetPositions(
    assets.map(normalizeAssetPosition),
  );
  const totalValue = mergedPositions.reduce(
    (sum, position) => sum + position.current_value,
    0,
  );
  const totalCost = mergedPositions.reduce(
    (sum, position) => sum + position.total_cost,
    0,
  );
  const latestTimestamp = mergedPositions.reduce((latest, position) => {
    const current = toTimestamp(position.last_updated) ?? 0;
    return current > latest ? current : latest;
  }, 0);
  const summary = buildSummary(
    totalValue,
    totalCost,
    latestTimestamp > 0
      ? new Date(latestTimestamp).toISOString()
      : new Date().toISOString(),
  );
  const allocations = buildAllocationSlices(
    mergedPositions,
    summary.total_value,
  );
  const metrics = buildGainLossMetrics(allocations);

  return {
    summary,
    allocations,
    metrics,
  };
}
