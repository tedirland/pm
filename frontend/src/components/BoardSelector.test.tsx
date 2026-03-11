import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, beforeEach } from "vitest";
import { BoardSelector } from "@/components/BoardSelector";

vi.mock("@/lib/api", () => ({
  fetchBoards: vi.fn(),
  createBoard: vi.fn(),
  deleteBoard: vi.fn(),
}));

import * as api from "@/lib/api";

const mockFetchBoards = vi.mocked(api.fetchBoards);
const mockCreateBoard = vi.mocked(api.createBoard);
const mockDeleteBoard = vi.mocked(api.deleteBoard);

const defaultProps = {
  onSelectBoard: vi.fn(),
  onLogout: vi.fn(),
  username: "testuser",
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe("BoardSelector", () => {
  it("shows loading then renders boards", async () => {
    mockFetchBoards.mockResolvedValue([
      { id: 1, title: "Board 1", created_at: "2026-01-01T00:00:00" },
      { id: 2, title: "Board 2", created_at: "2026-01-02T00:00:00" },
    ]);

    render(<BoardSelector {...defaultProps} />);
    expect(screen.getByText("Loading boards...")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Board 1")).toBeInTheDocument();
      expect(screen.getByText("Board 2")).toBeInTheDocument();
    });
  });

  it("shows single board without auto-selecting", async () => {
    mockFetchBoards.mockResolvedValue([
      { id: 42, title: "Only Board", created_at: "2026-01-01T00:00:00" },
    ]);

    render(<BoardSelector {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("Only Board")).toBeInTheDocument();
    });
    // Should NOT auto-select - user needs to see the board list to create new ones
    expect(defaultProps.onSelectBoard).not.toHaveBeenCalled();
  });

  it("selects a board on click", async () => {
    mockFetchBoards.mockResolvedValue([
      { id: 1, title: "Board 1", created_at: "2026-01-01T00:00:00" },
      { id: 2, title: "Board 2", created_at: "2026-01-02T00:00:00" },
    ]);

    render(<BoardSelector {...defaultProps} />);
    await waitFor(() => screen.getByText("Board 1"));

    await userEvent.click(screen.getByText("Board 2"));
    expect(defaultProps.onSelectBoard).toHaveBeenCalledWith(2);
  });

  it("creates a new board", async () => {
    mockFetchBoards.mockResolvedValue([
      { id: 1, title: "Board 1", created_at: "2026-01-01T00:00:00" },
      { id: 2, title: "Board 2", created_at: "2026-01-02T00:00:00" },
    ]);
    mockCreateBoard.mockResolvedValue({
      id: 3,
      title: "New Board",
      columns: [],
      cards: {},
    });

    render(<BoardSelector {...defaultProps} />);
    await waitFor(() => screen.getByText("Board 1"));

    const input = screen.getByPlaceholderText("Board name");
    await userEvent.type(input, "New Board");
    await userEvent.click(screen.getByRole("button", { name: /^create$/i }));

    await waitFor(() => {
      expect(mockCreateBoard).toHaveBeenCalledWith("New Board");
    });
    expect(defaultProps.onSelectBoard).toHaveBeenCalledWith(3);
  });

  it("calls onLogout when sign out is clicked", async () => {
    mockFetchBoards.mockResolvedValue([
      { id: 1, title: "Board 1", created_at: "2026-01-01T00:00:00" },
      { id: 2, title: "Board 2", created_at: "2026-01-02T00:00:00" },
    ]);

    render(<BoardSelector {...defaultProps} />);
    await waitFor(() => screen.getByText("Board 1"));

    await userEvent.click(screen.getByRole("button", { name: /sign out/i }));
    expect(defaultProps.onLogout).toHaveBeenCalled();
  });

  it("displays username", async () => {
    mockFetchBoards.mockResolvedValue([
      { id: 1, title: "Board 1", created_at: "2026-01-01T00:00:00" },
      { id: 2, title: "Board 2", created_at: "2026-01-02T00:00:00" },
    ]);

    render(<BoardSelector {...defaultProps} />);
    await waitFor(() => {
      expect(screen.getByText("testuser")).toBeInTheDocument();
    });
  });
});
