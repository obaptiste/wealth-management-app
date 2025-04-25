import { AssetWithPerformance } from './assets';

export interface DataPoint {
  date: string;
  value: number;
}

export interface PerformanceChartProps {
  data: DataPoint[];
  width?: number;
  height?: number;
}

export interface PortfolioChartProps {
  assets: AssetWithPerformance[];
}
