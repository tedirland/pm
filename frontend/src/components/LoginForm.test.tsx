import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LoginForm } from "@/components/LoginForm";

const mockOnLogin = vi.fn();

beforeEach(() => {
  mockOnLogin.mockClear();
  vi.restoreAllMocks();
});

describe("LoginForm", () => {
  it("renders username and password fields", () => {
    render(<LoginForm onLogin={mockOnLogin} />);
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
  });

  it("calls onLogin on successful submit", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => ({ username: "user" }),
    } as Response);

    render(<LoginForm onLogin={mockOnLogin} />);
    await userEvent.type(screen.getByLabelText(/username/i), "user");
    await userEvent.type(screen.getByLabelText(/password/i), "password");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    expect(globalThis.fetch).toHaveBeenCalledWith("/api/login", expect.objectContaining({
      method: "POST",
    }));
    expect(mockOnLogin).toHaveBeenCalledWith("user");
  });

  it("shows error on failed login", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: false,
      json: async () => ({ detail: "Invalid credentials" }),
    } as Response);

    render(<LoginForm onLogin={mockOnLogin} />);
    await userEvent.type(screen.getByLabelText(/username/i), "user");
    await userEvent.type(screen.getByLabelText(/password/i), "wrong");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid credentials");
    expect(mockOnLogin).not.toHaveBeenCalled();
  });

  it("switches to registration mode", async () => {
    render(<LoginForm onLogin={mockOnLogin} />);
    await userEvent.click(screen.getByText(/need an account/i));
    expect(screen.getByRole("button", { name: /create account/i })).toBeInTheDocument();
    expect(screen.getByText(/create account/i, { selector: "p" })).toBeInTheDocument();
  });

  it("registers a new user", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => ({ username: "newuser" }),
    } as Response);

    render(<LoginForm onLogin={mockOnLogin} />);
    await userEvent.click(screen.getByText(/need an account/i));
    await userEvent.type(screen.getByLabelText(/username/i), "newuser");
    await userEvent.type(screen.getByLabelText(/password/i), "password123");
    await userEvent.click(screen.getByRole("button", { name: /create account/i }));

    expect(globalThis.fetch).toHaveBeenCalledWith("/api/register", expect.objectContaining({
      method: "POST",
    }));
    expect(mockOnLogin).toHaveBeenCalledWith("newuser");
  });

  it("shows error on failed registration", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: false,
      json: async () => ({ detail: "Username already taken" }),
    } as Response);

    render(<LoginForm onLogin={mockOnLogin} />);
    await userEvent.click(screen.getByText(/need an account/i));
    await userEvent.type(screen.getByLabelText(/username/i), "taken");
    await userEvent.type(screen.getByLabelText(/password/i), "password123");
    await userEvent.click(screen.getByRole("button", { name: /create account/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Username already taken");
    expect(mockOnLogin).not.toHaveBeenCalled();
  });

  it("switches back to login mode", async () => {
    render(<LoginForm onLogin={mockOnLogin} />);
    await userEvent.click(screen.getByText(/need an account/i));
    expect(screen.getByRole("button", { name: /create account/i })).toBeInTheDocument();
    await userEvent.click(screen.getByText(/already have an account/i));
    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
  });
});
