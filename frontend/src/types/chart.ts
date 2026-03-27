import { AssetWithPerformance } from "./assets";

export interface DataPoint {
  date: string;
  value: number;
}

export interface SentimentChartPoint {
  date: string;
  score: number;
  positive: number;
  neutral: number;
  negative: number;
  total_analyzed: number;
}

export interface PerformanceChartProps {
  data: DataPoint[];
  width?: number;
  height?: number;
}

export interface PortfolioChartProps {
  assets: AssetWithPerformance[];
}
