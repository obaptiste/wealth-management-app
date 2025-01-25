import { fetchHealth } from "../../app/services/api";

// Mock global fetch
global.fetch = jest.fn() as jest.Mock;

describe("fetchHealth API Test", () => {
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

  test("fetchHealth should throw error on failed request", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({ ok: false });
    await expect(fetchHealth()).rejects.toThrow(
      "Failed to fetch health status"
    );
  });
});
