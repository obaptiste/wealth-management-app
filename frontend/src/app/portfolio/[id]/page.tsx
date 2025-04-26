'use client';
// Add CSS module imports
import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import * as api from '@/lib/api';
import { PortfolioWithSummary } from '@/types/';
// Removing unused imports

// Helper function to get portfolio data
const getPortfolio = async (id: number): Promise<PortfolioWithSummary> => {
  const { data } = await api.get(`/portfolios/${id}`);
  return data as PortfolioWithSummary;
};

export default function PortfolioDetailPage() {
  const params = useParams();
  const [portfolio, setPortfolio] = useState<PortfolioWithSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPortfolio = async () => {
      try {
        setLoading(true);
        const portfolioId = Number(params.id);
        const data = await getPortfolio(portfolioId);
        setPortfolio(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchPortfolio();
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
        <p>Profit/Loss: ${portfolio.summary.total_profit_loss.toFixed(2)} 
          ({portfolio.summary.total_profit_loss_percent.toFixed(2)}%)
        </p>
      </div>
      
      <div>
        <h2>Assets</h2>
        <ul>
          {portfolio.assets.map(asset => (
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