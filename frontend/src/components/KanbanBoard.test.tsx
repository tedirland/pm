import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KanbanBoard } from "@/components/KanbanBoard";

const getFirstColumn = () => screen.getAllByTestId(/column-/i)[0];

describe("KanbanBoard", () => {
  it("renders five columns", () => {
    render(<KanbanBoard />);
    expect(screen.getAllByTestId(/column-/i)).toHaveLength(5);
  });

  it("renames a column", async () => {
    render(<KanbanBoard />);
    const column = getFirstColumn();
    const input = within(column).getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.type(input, "New Name");
    expect(input).toHaveValue("New Name");
  });

  it("adds and removes a card via modal", async () => {
    render(<KanbanBoard />);
    const column = getFirstColumn();
    const addButton = within(column).getByRole("button", {
      name: /add a card/i,
    });
    await userEvent.click(addButton);

    const modal = screen.getByText("New card", { selector: "h2" }).closest("div")!.parentElement!;
    const titleInput = within(modal).getByLabelText("Title");
    await userEvent.type(titleInput, "Test card");
    const detailsInput = within(modal).getByLabelText("Details");
    await userEvent.type(detailsInput, "Notes");

    await userEvent.click(within(modal).getByRole("button", { name: /add card/i }));

    expect(within(column).getByText("Test card")).toBeInTheDocument();

    const deleteButton = within(column).getByRole("button", {
      name: /delete test card/i,
    });
    await userEvent.click(deleteButton);

    expect(within(column).queryByText("Test card")).not.toBeInTheDocument();
  });

  it("edits a card via modal", async () => {
    render(<KanbanBoard />);
    const column = getFirstColumn();
    const editButton = within(column).getByRole("button", {
      name: /^edit align roadmap/i,
    });
    await userEvent.click(editButton);

    const titleInput = screen.getByLabelText("Title");
    await userEvent.clear(titleInput);
    await userEvent.type(titleInput, "Updated title");

    await userEvent.click(screen.getByRole("button", { name: /save/i }));

    expect(within(column).getByText("Updated title")).toBeInTheDocument();
  });
});
