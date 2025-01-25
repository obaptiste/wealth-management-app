import { analyseText } from "../../app/services/api";

// Mock global fetch
global.fetch = jest.fn() as jest.Mock;

describe("analyseText API Test", () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  test("analyseText should return analysis result", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ sentiment: "positive" }),
    });
    const data = await analyseText("Great stock performance!");
    expect(data.sentiment).toBe("positive");
  });
});
