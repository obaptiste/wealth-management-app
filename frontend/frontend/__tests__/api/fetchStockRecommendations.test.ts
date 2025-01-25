import { fetchStockRecommendations } from "../../app/services/api";

// Mock global fetch
global.fetch = jest.fn() as jest.Mock;

describe("fetchStockRecommendations API Test", () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  test("fetchStockRecommendations should return stock recommendations", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ recommendation: "buy" }),
    });
    const data = await fetchStockRecommendations("AAPL");
    expect(data.recommendation).toBe("buy");
  });
});
