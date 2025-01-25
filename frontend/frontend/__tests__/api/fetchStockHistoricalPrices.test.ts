import { fetchStockHistoricalPrices } from "../../app/services/api";

// Mock global fetch
global.fetch = jest.fn() as jest.Mock;

describe("fetchStockHistoricalPrices API Test", () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  test("fetchStockHistoricalPrices should return historical prices", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => [{ date: "2024-01-01", price: 150 }],
    });
    const data = await fetchStockHistoricalPrices("AAPL");
    expect(data[0].price).toBe(150);
  });
});
