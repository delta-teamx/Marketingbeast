import { expect, test } from "@playwright/test";

test("landing page shows the hero and CTA", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText(/Be everywhere/i)).toBeVisible();
  await expect(page.getByRole("link", { name: /get started/i })).toBeVisible();
});

test("login page renders email and password fields", async ({ page }) => {
  await page.goto("/login");
  await expect(page.getByLabel(/email/i)).toBeVisible();
  await expect(page.getByLabel(/password/i)).toBeVisible();
});
