import { fetchStockNews } from "../../app/services/api";

// Mock global fetch
global.fetch = jest.fn() as jest.Mock;

describe("fetchStockNews API Test", () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  test("fetchStockNews should return stock news", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => [{ headline: "Stock rises" }],
    });
    const data = await fetchStockNews("AAPL");
    expect(data[0].headline).toBe("Stock rises");
  });
});
