//a service file to interact with the API

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const fetchHealth = async () => {
  const response = await fetch(`${API_URL}/health`);
  if (!response.ok) throw new Error("Failed to fetch health status");
  return response.json();
};

export const fetchStockData = async (symbol: string) => {
  const response = await fetch(`${API_URL}/stock-data/${symbol}`);
  if (!response.ok) throw new Error("Failed to fetch stock data");
  return response.json();
};

export const analyseText = async (text: string) => {
  const response = await fetch(`${API_URL}/analyse-text`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text }),
  });
  if (!response.ok) throw new Error("Failed to analyse text");
  return response.json();
};

export const fetchSentiment = async () => {
  const response = await fetch(`${API_URL}/sentiment`);
  if (!response.ok) throw new Error("Failed to fetch sentiment");
  return response.json();
};

export const fetchStockSymbols = async () => {
  const response = await fetch(`${API_URL}/stock-symbols`);
  if (!response.ok) throw new Error("Failed to fetch stock symbols");
  return response.json();
};

export const fetchStockSentiment = async (symbol: string) => {
  const response = await fetch(`${API_URL}/stock-sentiment/${symbol}`);
  if (!response.ok) throw new Error("Failed to fetch stock sentiment");
  return response.json();
};

export const fetchStockNews = async (symbol: string) => {
  const response = await fetch(`${API_URL}/stock-news/${symbol}`);
  if (!response.ok) throw new Error("Failed to fetch stock news");
  return response.json();
};

export const fetchStockPrice = async (symbol: string) => {
  const response = await fetch(`${API_URL}/stock-price/${symbol}`);
  if (!response.ok) throw new Error("Failed to fetch stock price");
  return response.json();
};

export const fetchStockHistoricalPrices = async (symbol: string) => {
  const response = await fetch(`${API_URL}/stock-historical-prices/${symbol}`);
  if (!response.ok) throw new Error("Failed to fetch stock historical prices");
  return response.json();
};

export const fetchStockRecommendations = async (symbol: string) => {
  const response = await fetch(`${API_URL}/stock-recommendations/${symbol}`);
  if (!response.ok) throw new Error("Failed to fetch stock recommendations");
  return response.json();
};

export const login = async (username: string, password: string) => {
  const response = await fetch(`${API_URL}/token`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: new URLSearchParams({ username, password }),
  });
  if (!response.ok) throw new Error("Invalid username or password");
  return response.json();
};
