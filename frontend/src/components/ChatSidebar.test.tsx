import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, beforeEach } from "vitest";
import { ChatSidebar } from "@/components/ChatSidebar";

vi.mock("@/lib/api", () => ({
  sendChat: vi.fn(),
}));

import * as api from "@/lib/api";

const mockSendChat = vi.mocked(api.sendChat);

beforeEach(() => {
  vi.clearAllMocks();
});

describe("ChatSidebar", () => {
  const defaultProps = {
    open: true,
    onClose: vi.fn(),
    onBoardUpdated: vi.fn(),
  };

  it("renders when open", () => {
    render(<ChatSidebar {...defaultProps} />);
    expect(screen.getByText("AI Assistant")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Ask the AI...")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Send" })).toBeInTheDocument();
  });

  it("shows empty state message", () => {
    render(<ChatSidebar {...defaultProps} />);
    expect(
      screen.getByText(/ask me to create, move, or edit cards/i)
    ).toBeInTheDocument();
  });

  it("sends a message and displays the response", async () => {
    mockSendChat.mockResolvedValue({ message: "You have 5 columns.", board_updated: false });

    render(<ChatSidebar {...defaultProps} />);
    const input = screen.getByPlaceholderText("Ask the AI...");
    await userEvent.type(input, "How many columns?");
    await userEvent.click(screen.getByRole("button", { name: "Send" }));

    // User message appears
    expect(screen.getByText("How many columns?")).toBeInTheDocument();

    // AI response appears
    await waitFor(() => {
      expect(screen.getByText("You have 5 columns.")).toBeInTheDocument();
    });

    expect(mockSendChat).toHaveBeenCalledWith("How many columns?", []);
    expect(defaultProps.onBoardUpdated).not.toHaveBeenCalled();
  });

  it("calls onBoardUpdated when AI modifies the board", async () => {
    mockSendChat.mockResolvedValue({ message: "Created the card.", board_updated: true });

    render(<ChatSidebar {...defaultProps} />);
    const input = screen.getByPlaceholderText("Ask the AI...");
    await userEvent.type(input, "Create a card");
    await userEvent.click(screen.getByRole("button", { name: "Send" }));

    await waitFor(() => {
      expect(screen.getByText("Created the card.")).toBeInTheDocument();
    });

    expect(defaultProps.onBoardUpdated).toHaveBeenCalled();
  });

  it("maintains conversation history across messages", async () => {
    mockSendChat
      .mockResolvedValueOnce({ message: "First reply.", board_updated: false })
      .mockResolvedValueOnce({ message: "Second reply.", board_updated: false });

    render(<ChatSidebar {...defaultProps} />);
    const input = screen.getByPlaceholderText("Ask the AI...");

    // First message
    await userEvent.type(input, "Hello");
    await userEvent.click(screen.getByRole("button", { name: "Send" }));
    await waitFor(() => expect(screen.getByText("First reply.")).toBeInTheDocument());

    // Second message -- history should include the first exchange
    await userEvent.type(input, "Follow up");
    await userEvent.click(screen.getByRole("button", { name: "Send" }));
    await waitFor(() => expect(screen.getByText("Second reply.")).toBeInTheDocument());

    expect(mockSendChat).toHaveBeenLastCalledWith("Follow up", [
      { role: "user", content: "Hello" },
      { role: "assistant", content: "First reply." },
    ]);
  });

  it("calls onClose when close button is clicked", async () => {
    render(<ChatSidebar {...defaultProps} />);
    await userEvent.click(screen.getByRole("button", { name: "Close chat" }));
    expect(defaultProps.onClose).toHaveBeenCalled();
  });

  it("shows error message when API fails", async () => {
    mockSendChat.mockRejectedValue(new Error("fail"));

    render(<ChatSidebar {...defaultProps} />);
    const input = screen.getByPlaceholderText("Ask the AI...");
    await userEvent.type(input, "Test");
    await userEvent.click(screen.getByRole("button", { name: "Send" }));

    await waitFor(() => {
      expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
    });
  });
});
