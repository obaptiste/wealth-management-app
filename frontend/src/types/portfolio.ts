// frontend/src/types/portfolio.ts
import { AssetWithPerformance } from './assets';

export interface PortfolioSummary {
  total_value: number;
  total_cost: number;
  total_profit_loss: number;
  total_profit_loss_percent: number;
  last_updated?: string;
}

export interface Portfolio {
  id: number;
  name: string;
  description: string | null;
  owner_id: number;
  created_at: string;
  updated_at: string;
}

export interface PortfolioWithSummary extends Portfolio {
  assets: AssetWithPerformance[];
  summary: PortfolioSummary;
}

export interface CreatePortfolioData {
  name: string;
  description?: string;
}

export interface UpdatePortfolioData {
  name?: string;
  description?: string;
}