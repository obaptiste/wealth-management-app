import "@testing-library/jest-dom";

// Mock fetch if needed
global.fetch = require("jest-fetch-mock");

// Mock next/router
jest.mock("next/router", () => ({
  useRouter: () => ({
    route: "/",
    pathname: "",
    query: "",
    asPath: "",
  }),
}));

// Mock next/image
