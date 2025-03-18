// types/api.ts
export interface User {
    id: number;
    username: string;
    email: string;
    is_active: boolean;
    created_at: string;
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
  
  export interface PortfolioSummary {
    total_value: number;
    total_cost: number;
    total_profit_loss: number;
    total_profit_loss_percent: number;
    last_updated: string;
  }
  
  export interface Asset {
    id: number;
    symbol: string;
    quantity: number;
    purchase_price: number;
    purchase_date: string;
    notes: string | null;
    portfolio_id: number;
    created_at: string;
    updated_at: string;
  }
  
  export interface AssetWithPerformance extends Asset {
    current_price: number;
    current_value: number;
    profit_loss: number;
    profit_loss_percent: number;
    last_updated: string;
  }