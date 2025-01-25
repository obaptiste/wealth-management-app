import { fetchStockPrice } from "../../app/services/api";

// Mock global fetch
global.fetch = jest.fn() as jest.Mock;

describe("fetchStockPrice API Test", () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  test("fetchStockPrice should return stock price", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ price: 200 }),
    });
    const data = await fetchStockPrice("AAPL");
    expect(data.price).toBe(200);
  });
});
