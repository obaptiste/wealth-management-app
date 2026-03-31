"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import dynamic from "next/dynamic";
import axios from "axios";
import apiClient from "@/lib/api";
import type { PortfolioWithSummary } from "@/types/";
import type { DataPoint } from "@/types/chart";
import type { PortfolioSnapshotHistoryResponse } from "@/types/domain";

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

export default function PortfolioDetailPage() {
  const params = useParams();
  const [portfolio, setPortfolio] = useState<PortfolioWithSummary | null>(null);
  const [historyPoints, setHistoryPoints] = useState<DataPoint[]>([]);
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

    fetchPortfolio();
    fetchHistory();
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
