import { render, screen } from "@testing-library/react";
import { CardLabels } from "@/components/CardLabels";

describe("CardLabels", () => {
  it("renders preset labels with colors", () => {
    render(<CardLabels labels="bug,feature" />);
    expect(screen.getByText("bug")).toBeInTheDocument();
    expect(screen.getByText("feature")).toBeInTheDocument();
  });

  it("renders custom labels with default style", () => {
    render(<CardLabels labels="custom-tag" />);
    const el = screen.getByText("custom-tag");
    expect(el).toBeInTheDocument();
    expect(el.className).toContain("bg-gray-100");
  });

  it("returns null for empty labels", () => {
    const { container } = render(<CardLabels labels="" />);
    expect(container.innerHTML).toBe("");
  });

  it("handles whitespace in comma-separated labels", () => {
    render(<CardLabels labels="bug , feature" />);
    expect(screen.getByText("bug")).toBeInTheDocument();
    expect(screen.getByText("feature")).toBeInTheDocument();
  });
});
