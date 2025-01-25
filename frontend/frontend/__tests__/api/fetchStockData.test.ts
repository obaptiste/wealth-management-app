import { fetchStockData } from "../../app/services/api";

// Mock global fetch
global.fetch = jest.fn() as jest.Mock;

describe("fetchStockData API Test", () => {
  afterEach(() => {
    jest.clearAllMocks();
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
});
