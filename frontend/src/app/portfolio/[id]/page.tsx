"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import dynamic from "next/dynamic";
import axios from "axios";
import apiClient from "@/lib/api";
import type { PortfolioWithSummary } from "@/types/";
import type { DataPoint } from "@/types/chart";
import type {
  PortfolioSnapshotComparison,
  PortfolioSnapshotHistoryResponse,
} from "@/types/domain";

// PerformanceChart uses d3 and must be client-only
const PerformanceChart = dynamic(
  () => import("@/components/PerformanceChart"),
  { ssr: false },
);

const getPortfolio = async (id: number): Promise<PortfolioWithSummary> => {
  return apiClient.getPortfolio(String(id)) as Promise<PortfolioWithSummary>;
};

/** Map snapshot history points to the DataPoint shape expected by PerformanceChart. */
function toChartPoints(
  history: PortfolioSnapshotHistoryResponse,
): DataPoint[] {
  return history.points.map((point) => ({
    // Backend returns date as "YYYY-MM-DD" — matches the format d3 timeParse expects
    date: point.as_of,
    value: point.portfolio_value,
  }));
}

function formatSignedCurrency(value: number): string {
  const prefix = value > 0 ? "+" : "";
  return `${prefix}$${value.toFixed(2)}`;
}

function formatSignedPercent(value: number): string {
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${value.toFixed(2)}%`;
}

export default function PortfolioDetailPage() {
  const params = useParams();
  const [portfolio, setPortfolio] = useState<PortfolioWithSummary | null>(null);
  const [historyPoints, setHistoryPoints] = useState<DataPoint[]>([]);
  const [comparison, setComparison] =
    useState<PortfolioSnapshotComparison | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const portfolioId = Number(params.id);

    // Load portfolio detail first so the summary and assets render immediately.
    const fetchPortfolio = async () => {
      try {
        setLoading(true);
        const data = await getPortfolio(portfolioId);
        setPortfolio(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "An error occurred");
      } finally {
        setLoading(false);
      }
    };

    // History is non-critical: fetch independently so a slow or failing
    // /snapshots response never delays the summary or asset list.
    const fetchHistory = async () => {
      // Clear immediately so navigating between portfolios never shows
      // a previous portfolio's chart while the new request is in flight.
      setHistoryPoints([]);
      try {
        const data = await apiClient.getPortfolioSnapshotHistory(portfolioId, 30);
        setHistoryPoints(toChartPoints(data));
      } catch (err) {
        if (axios.isAxiosError(err) && err.response?.status === 404) {
          // Expected: no snapshots exist yet — show empty state silently
          return;
        }
        // Unexpected failure (5xx, network error, schema mismatch) — surface
        // in dev tools without blocking the portfolio summary or asset list.
        console.error("Portfolio snapshot history failed unexpectedly:", err);
        throw err;
      }
    };

    // Comparison is also non-critical: default to the latest two snapshots when
    // available so the page has a clear hook for future drift/comparison views.
    const fetchComparison = async () => {
      setComparison(null);
      try {
        const data = await apiClient.getPortfolioSnapshotComparison(portfolioId);
        setComparison(data);
      } catch (err) {
        if (axios.isAxiosError(err) && err.response?.status === 404) {
          return;
        }
        console.error("Portfolio snapshot comparison failed unexpectedly:", err);
      }
    };

    fetchPortfolio();
    fetchHistory();
    fetchComparison();
  }, [params.id]);

  if (loading) return <div>Loading portfolio details...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!portfolio) return <div>Portfolio not found</div>;

  return (
    <div>
      <h1>{portfolio.name}</h1>
      <p>{portfolio.description}</p>

      <div>
        <h2>Portfolio Summary</h2>
        <p>Total Value: ${portfolio.summary.total_value.toFixed(2)}</p>
        <p>Total Cost: ${portfolio.summary.total_cost.toFixed(2)}</p>
        <p>
          Profit/Loss: ${portfolio.summary.total_profit_loss.toFixed(2)}(
          {portfolio.summary.total_profit_loss_percent.toFixed(2)}%)
        </p>
      </div>

      <div>
        <h2>Value History (30 days)</h2>
        {historyPoints.length > 0 ? (
          <PerformanceChart data={historyPoints} />
        ) : (
          <p>No snapshot history yet. History is captured daily once assets are added.</p>
        )}
      </div>

      <div>
        <h2>Snapshot Comparison</h2>
        {comparison ? (
          <>
            <p>
              Comparing {comparison.current_as_of} against {comparison.previous_as_of}
            </p>
            <p>
              Value change:{" "}
              {formatSignedCurrency(comparison.summary.value_change)} (
              {formatSignedPercent(comparison.summary.value_change_percent)})
            </p>
            <p>
              Profit/Loss change:{" "}
              {formatSignedCurrency(comparison.summary.profit_loss_change)}
            </p>
            <p>
              Cost change: {formatSignedCurrency(comparison.summary.cost_change)}
            </p>

            {comparison.holdings.length > 0 ? (
              <ul>
                {comparison.holdings
                  .filter((holding) => holding.status !== "unchanged")
                  .slice(0, 5)
                  .map((holding) => (
                    <li key={holding.symbol}>
                      {holding.symbol}: {holding.status}, value{" "}
                      {formatSignedCurrency(holding.value_change)}, allocation{" "}
                      {formatSignedPercent(holding.allocation_percent_change)}
                    </li>
                  ))}
              </ul>
            ) : null}
          </>
        ) : (
          <p>
            No comparison yet. Comparison becomes available once two daily snapshots
            exist for this portfolio.
          </p>
        )}
      </div>

      <div>
        <h2>Assets</h2>
        <ul>
          {portfolio.assets.map((asset) => (
            <li key={asset.id}>
              {asset.symbol}: {asset.quantity} shares @ ${asset.purchase_price}
              (Current: ${asset.current_price})
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
