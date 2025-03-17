// src/types/assets.ts
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
  
  export interface CreateAssetData {
    symbol: string;
    quantity: number;
    purchase_price: number;
    purchase_date: string;
    notes?: string;
  }
  
  export interface UpdateAssetData {
    symbol?: string;
    quantity?: number;
    purchase_price?: number;
    purchase_date?: string;
    notes?: string;
  }