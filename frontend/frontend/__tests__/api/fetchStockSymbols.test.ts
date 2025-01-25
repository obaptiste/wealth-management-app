import { fetchStockSymbols } from "../../app/services/api";

// Mock global fetch
global.fetch = jest.fn() as jest.Mock;

describe("fetchStockSymbols API Test", () => {
  afterEach(() => {
    jest.clearAllMocks();
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
});
