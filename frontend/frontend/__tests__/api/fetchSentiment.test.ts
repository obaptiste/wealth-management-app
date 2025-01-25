import { fetchSentiment } from "../../app/services/api";

// Mock global fetch
global.fetch = jest.fn() as jest.Mock;

describe("fetchSentiment API Test", () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  test("fetchSentiment should return sentiment data", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ overall: "neutral" }),
    });
    const data = await fetchSentiment();
    expect(data.overall).toBe("neutral");
  });
});
