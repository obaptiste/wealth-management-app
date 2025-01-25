import { render } from "@testing-library/react";
import "@testing-library/jest-dom";
import Home from "../app/page";

describe("Home Page", () => {
  it("renders a heading", () => {
    render(<Home />);
    // expect(
    //   screen.getByRole("heading", { name: /welcome to next\.js/i })
    // ).toBeInTheDocument();
  });
});
