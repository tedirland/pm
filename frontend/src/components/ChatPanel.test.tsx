import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, beforeEach } from "vitest";
import { ChatPanel } from "@/components/ChatPanel";

vi.mock("@/lib/api", () => ({
  sendChat: vi.fn(),
}));

import * as api from "@/lib/api";

const mockSendChat = vi.mocked(api.sendChat);

beforeEach(() => {
  vi.clearAllMocks();
});

describe("ChatPanel", () => {
  const defaultProps = {
    onClose: vi.fn(),
    onBoardUpdated: vi.fn(),
  };

  it("renders the header and input", () => {
    render(<ChatPanel {...defaultProps} />);
    expect(screen.getAllByText("AI Assistant").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByPlaceholderText("Message AI Assistant...")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Send" })).toBeInTheDocument();
  });

  it("shows empty state", () => {
    render(<ChatPanel {...defaultProps} />);
    expect(screen.getByText(/I can create, move, edit, and delete cards/i)).toBeInTheDocument();
  });

  it("sends a message and displays the response", async () => {
    mockSendChat.mockResolvedValue({ message: "Done! Card created.", board_updated: true });

    render(<ChatPanel {...defaultProps} />);
    const input = screen.getByPlaceholderText("Message AI Assistant...");
    await userEvent.type(input, "Create a card");
    await userEvent.click(screen.getByRole("button", { name: "Send" }));

    expect(screen.getByText("Create a card")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Done! Card created.")).toBeInTheDocument();
    });

    expect(mockSendChat).toHaveBeenCalledWith("Create a card", [], undefined);
    expect(defaultProps.onBoardUpdated).toHaveBeenCalled();
  });

  it("sends message on Enter key", async () => {
    mockSendChat.mockResolvedValue({ message: "Hi!", board_updated: false });

    render(<ChatPanel {...defaultProps} />);
    const input = screen.getByPlaceholderText("Message AI Assistant...");
    await userEvent.type(input, "Hello{Enter}");

    await waitFor(() => {
      expect(screen.getByText("Hi!")).toBeInTheDocument();
    });
  });

  it("maintains conversation history", async () => {
    mockSendChat
      .mockResolvedValueOnce({ message: "First.", board_updated: false })
      .mockResolvedValueOnce({ message: "Second.", board_updated: false });

    render(<ChatPanel {...defaultProps} />);
    const input = screen.getByPlaceholderText("Message AI Assistant...");

    await userEvent.type(input, "Hello{Enter}");
    await waitFor(() => expect(screen.getByText("First.")).toBeInTheDocument());

    await userEvent.type(input, "Again{Enter}");
    await waitFor(() => expect(screen.getByText("Second.")).toBeInTheDocument());

    expect(mockSendChat).toHaveBeenLastCalledWith("Again", [
      { role: "user", content: "Hello" },
      { role: "assistant", content: "First." },
    ], undefined);
  });

  it("calls onClose when close button is clicked", async () => {
    render(<ChatPanel {...defaultProps} />);
    await userEvent.click(screen.getByRole("button", { name: "Close chat" }));
    expect(defaultProps.onClose).toHaveBeenCalled();
  });

  it("shows error message on API failure", async () => {
    mockSendChat.mockRejectedValue(new Error("fail"));

    render(<ChatPanel {...defaultProps} />);
    const input = screen.getByPlaceholderText("Message AI Assistant...");
    await userEvent.type(input, "Test{Enter}");

    await waitFor(() => {
      expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
    });
  });

  it("passes boardId to sendChat", async () => {
    mockSendChat.mockResolvedValue({ message: "Ok", board_updated: false });

    render(<ChatPanel {...defaultProps} boardId={42} />);
    const input = screen.getByPlaceholderText("Message AI Assistant...");
    await userEvent.type(input, "Test{Enter}");

    await waitFor(() => {
      expect(mockSendChat).toHaveBeenCalledWith("Test", [], 42);
    });
  });
});
