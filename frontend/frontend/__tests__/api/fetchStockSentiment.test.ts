import { fetchStockSentiment } from "../../app/services/api";

// Mock global fetch
global.fetch = jest.fn() as jest.Mock;

describe("fetchStockSentiment API Test", () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  test("fetchStockSentiment should return sentiment for a stock", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ sentiment: "bullish" }),
    });
    const data = await fetchStockSentiment("TSLA");
    expect(data.sentiment).toBe("bullish");
  });
});
