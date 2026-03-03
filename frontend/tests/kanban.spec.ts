import { expect, test } from "@playwright/test";

// Mock auth endpoints so e2e tests work against the Next.js dev server
test.beforeEach(async ({ page }) => {
  await page.route("**/api/me", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: '{"username":"user"}' })
  );
  await page.route("**/api/logout", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: '{"ok":true}' })
  );
});

test("loads the kanban board", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("adds a card to a column", async ({ page }) => {
  await page.goto("/");
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();

  const modal = page.locator(".fixed");
  await modal.getByLabel("Title").fill("Playwright card");
  await modal.getByLabel("Details").fill("Added via e2e.");
  await modal.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();
});

test("moves a card between columns", async ({ page }) => {
  await page.goto("/");
  const card = page.getByTestId("card-card-1");
  const targetColumn = page.getByTestId("column-col-review");
  const cardBox = await card.boundingBox();
  const columnBox = await targetColumn.boundingBox();
  if (!cardBox || !columnBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  await page.mouse.move(
    cardBox.x + cardBox.width / 2,
    cardBox.y + cardBox.height / 2
  );
  await page.mouse.down();
  await page.mouse.move(
    columnBox.x + columnBox.width / 2,
    columnBox.y + 120,
    { steps: 12 }
  );
  await page.mouse.up();
  await expect(targetColumn.getByTestId("card-card-1")).toBeVisible();
});

test("login flow shows form when not authenticated", async ({ page }) => {
  // Override the /api/me mock to return 401
  await page.route("**/api/me", (route) =>
    route.fulfill({ status: 401, contentType: "application/json", body: '{"error":"Not authenticated"}' })
  );
  await page.route("**/api/login", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: '{"username":"user"}' })
  );

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(page.getByLabel(/username/i)).toBeVisible();
  await expect(page.getByLabel(/password/i)).toBeVisible();

  await page.getByLabel(/username/i).fill("user");
  await page.getByLabel(/password/i).fill("password");
  await page.getByRole("button", { name: /sign in/i }).click();

  // After login, board should appear
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("logout returns to login", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);

  // Override /api/me to return 401 after logout
  await page.route("**/api/me", (route) =>
    route.fulfill({ status: 401, contentType: "application/json", body: '{"error":"Not authenticated"}' })
  );

  await page.getByRole("button", { name: /sign out/i }).click();
  await expect(page.getByLabel(/username/i)).toBeVisible();
});
