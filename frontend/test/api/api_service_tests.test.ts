import {
  fetchHealth,
  fetchStockData,
  analyseText,
  fetchSentiment,
  fetchStockSymbols,
  fetchStockSentiment,
  fetchStockNews,
  fetchStockPrice,
  fetchStockHistoricalPrices,
  fetchStockRecommendations,
  login,
} from "@/app/services/api";

// Mock global fetch
global.fetch = jest.fn() as jest.Mock;

describe("API Service Tests", () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  test("fetchHealth should return health status", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: "ok" }),
    });
    const data = await fetchHealth();
    expect(data.status).toBe("ok");
  });

  test("fetchStockData should return stock data for a given symbol", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ symbol: "AAPL", price: 150 }),
    });
    const data = await fetchStockData("AAPL");
    expect(data.symbol).toBe("AAPL");
    expect(data.price).toBe(150);
  });

  test("analyseText should return analysis result", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ sentiment: "positive" }),
    });
    const data = await analyseText("Great stock performance!");
    expect(data.sentiment).toBe("positive");
  });

  test("fetchSentiment should return sentiment data", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ overall: "neutral" }),
    });
    const data = await fetchSentiment();
    expect(data.overall).toBe("neutral");
  });

  test("fetchStockSymbols should return stock symbols list", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ["AAPL", "TSLA"],
    });
    const data = await fetchStockSymbols();
    expect(data).toContain("AAPL");
    expect(data).toContain("TSLA");
  });

  test("fetchStockSentiment should return sentiment for a stock", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ sentiment: "bullish" }),
    });
    const data = await fetchStockSentiment("TSLA");
    expect(data.sentiment).toBe("bullish");
  });

  test("fetchStockNews should return stock news", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => [{ headline: "Stock rises" }],
    });
    const data = await fetchStockNews("AAPL");
    expect(data[0].headline).toBe("Stock rises");
  });

  test("fetchStockPrice should return stock price", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ price: 200 }),
    });
    const data = await fetchStockPrice("AAPL");
    expect(data.price).toBe(200);
  });

  test("fetchStockHistoricalPrices should return historical prices", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => [{ date: "2024-01-01", price: 150 }],
    });
    const data = await fetchStockHistoricalPrices("AAPL");
    expect(data[0].price).toBe(150);
  });

  test("fetchStockRecommendations should return stock recommendations", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ recommendation: "buy" }),
    });
    const data = await fetchStockRecommendations("AAPL");
    expect(data.recommendation).toBe("buy");
  });

  test("login should return authentication token", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ token: "abc123" }),
    });
    const data = await login("user", "pass");
    expect(data.token).toBe("abc123");
  });

  test("fetch functions should throw error on failed request", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({ ok: false });
    await expect(fetchHealth()).rejects.toThrow(
      "Failed to fetch health status"
    );
  });
});
