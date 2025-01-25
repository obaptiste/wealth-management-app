import { login } from "../../app/services/api";

// Mock global fetch
global.fetch = jest.fn() as jest.Mock;

describe("login API Test", () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  test("login should return authentication token", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ token: "abc123" }),
    });
    const data = await login("user", "pass");
    expect(data.token).toBe("abc123");
  });
});
