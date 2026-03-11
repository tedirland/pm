import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, beforeEach } from "vitest";
import { KanbanBoard } from "@/components/KanbanBoard";
import type { BoardData } from "@/lib/kanban";

const mockBoard: BoardData = {
  id: 1,
  title: "Test Board",
  columns: [
    { id: "col-1", title: "Backlog", cardIds: ["card-10", "card-11"] },
    { id: "col-2", title: "Discovery", cardIds: ["card-12"] },
    { id: "col-3", title: "In Progress", cardIds: [] },
    { id: "col-4", title: "Review", cardIds: [] },
    { id: "col-5", title: "Done", cardIds: [] },
  ],
  cards: {
    "card-10": { id: "card-10", title: "Align roadmap themes", details: "Draft quarterly themes." },
    "card-11": { id: "card-11", title: "Gather customer signals", details: "Review support tags." },
    "card-12": { id: "card-12", title: "Prototype analytics view", details: "Sketch layout." },
  },
};

vi.mock("@/lib/api", () => ({
  fetchBoard: vi.fn(),
  fetchBoardById: vi.fn(),
  updateBoardTitle: vi.fn(),
  addColumn: vi.fn(),
  deleteColumn: vi.fn(),
  renameColumn: vi.fn(),
  createCard: vi.fn(),
  updateCard: vi.fn(),
  deleteCard: vi.fn(),
  moveCardApi: vi.fn(),
  sendChat: vi.fn(),
}));

import * as api from "@/lib/api";

const mockFetchBoard = vi.mocked(api.fetchBoard);
const mockFetchBoardById = vi.mocked(api.fetchBoardById);
const mockRenameColumn = vi.mocked(api.renameColumn);
const mockCreateCard = vi.mocked(api.createCard);
const mockUpdateCard = vi.mocked(api.updateCard);
const mockDeleteCard = vi.mocked(api.deleteCard);

beforeEach(() => {
  vi.clearAllMocks();
  mockFetchBoard.mockResolvedValue(structuredClone(mockBoard));
  mockFetchBoardById.mockResolvedValue(structuredClone(mockBoard));
  mockRenameColumn.mockResolvedValue(undefined);
  mockCreateCard.mockResolvedValue({ id: "card-99", title: "Test card", details: "Notes" });
  mockUpdateCard.mockResolvedValue(undefined);
  mockDeleteCard.mockResolvedValue(undefined);
});

const getFirstColumn = () => screen.getAllByTestId(/column-/i)[0];

describe("KanbanBoard", () => {
  it("shows loading then renders columns from API", async () => {
    render(<KanbanBoard />);
    expect(screen.getByText("Loading board...")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getAllByTestId(/column-/i)).toHaveLength(5);
    });
    expect(mockFetchBoard).toHaveBeenCalledOnce();
  });

  it("uses fetchBoardById when boardId is provided", async () => {
    render(<KanbanBoard boardId={1} />);
    await waitFor(() => {
      expect(screen.getAllByTestId(/column-/i)).toHaveLength(5);
    });
    expect(mockFetchBoardById).toHaveBeenCalledWith(1);
  });

  it("shows error when API fails", async () => {
    mockFetchBoard.mockRejectedValue(new Error("fail"));
    render(<KanbanBoard />);
    await waitFor(() => {
      expect(screen.getByText("Failed to load board")).toBeInTheDocument();
    });
  });

  it("renames a column and calls API", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<KanbanBoard />);
    await waitFor(() => screen.getAllByTestId(/column-/i));
    const column = getFirstColumn();
    const input = within(column).getByLabelText("Column title");
    await user.clear(input);
    await user.type(input, "Todo");
    expect(input).toHaveValue("Todo");
    await vi.advanceTimersByTimeAsync(500);
    expect(mockRenameColumn).toHaveBeenCalled();
    vi.useRealTimers();
  });

  it("adds a card via modal and calls API", async () => {
    render(<KanbanBoard />);
    await waitFor(() => screen.getAllByTestId(/column-/i));
    const column = getFirstColumn();
    await userEvent.click(within(column).getByRole("button", { name: /add a card/i }));

    const modal = screen.getByText("New card", { selector: "h2" }).closest("div")!.parentElement!;
    await userEvent.type(within(modal).getByLabelText("Title"), "Test card");
    await userEvent.type(within(modal).getByLabelText("Details"), "Notes");
    await userEvent.click(within(modal).getByRole("button", { name: /add card/i }));

    await waitFor(() => {
      expect(mockCreateCard).toHaveBeenCalledWith("col-1", "Test card", "Notes", null, undefined);
    });
    expect(within(column).getByText("Test card")).toBeInTheDocument();
  });

  it("deletes a card with confirmation and calls API", async () => {
    render(<KanbanBoard />);
    await waitFor(() => screen.getAllByTestId(/column-/i));
    const column = getFirstColumn();

    const deleteButton = within(column).getByRole("button", {
      name: /delete align roadmap/i,
    });
    await userEvent.click(deleteButton);

    const confirmButton = within(column).getByRole("button", {
      name: /confirm delete align roadmap/i,
    });
    await userEvent.click(confirmButton);

    await waitFor(() => {
      expect(mockDeleteCard).toHaveBeenCalledWith("card-10", undefined);
    });
    expect(within(column).queryByText("Align roadmap themes")).not.toBeInTheDocument();
  });

  it("edits a card via modal and calls API", async () => {
    render(<KanbanBoard />);
    await waitFor(() => screen.getAllByTestId(/column-/i));
    const column = getFirstColumn();
    await userEvent.click(
      within(column).getByRole("button", { name: /^edit align roadmap/i })
    );

    const titleInput = screen.getByLabelText("Title");
    await userEvent.clear(titleInput);
    await userEvent.type(titleInput, "Updated title");
    await userEvent.click(screen.getByRole("button", { name: /save/i }));

    await waitFor(() => {
      expect(mockUpdateCard).toHaveBeenCalledWith("card-10", "Updated title", "Draft quarterly themes.", null, undefined, undefined);
    });
    expect(within(column).getByText("Updated title")).toBeInTheDocument();
  });
});
