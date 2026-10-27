import { expect, test } from "@playwright/test";

// These tests run against the hash embedder (see playwright.config.ts), which does exact
// keyword-style matching rather than real semantic or cross-lingual retrieval. That is
// enough to prove the plumbing end to end; see docs/design-notes.md for why the numbers
// look different once EMBEDDING_PROVIDER=sentence-transformers is used instead.

test("home page lists both assistants", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator(".assistant-card")).toHaveCount(2);
});

test("a grounded question is answered with a citation", async ({ page }) => {
  await page.goto("/chat/university");
  await page
    .getByRole("textbox", { name: "Message" })
    .fill("What attendance do I need to sit the term-end exam?");
  await page.keyboard.press("Enter");
  await expect(page.locator(".bubble-assistant .source-list")).toBeVisible({ timeout: 15_000 });
  await expect(page.locator(".bubble-assistant").last()).toContainText("75");

  await page.locator(".source-toggle").first().click();
  await expect(page.locator(".source-detail")).toBeVisible();
});

test("an off-topic question escalates to a department", async ({ page }) => {
  await page.goto("/chat/university");
  await page.getByRole("textbox", { name: "Message" }).fill("Who won the last cricket world cup?");
  await page.keyboard.press("Enter");
  await expect(page.locator(".escalation-card")).toBeVisible({ timeout: 15_000 });
  await expect(page.locator(".escalation-name").first()).not.toBeEmpty();
});

test("a wellbeing message routes to counselling and Tele-MANAS", async ({ page }) => {
  await page.goto("/chat/university");
  await page.getByRole("textbox", { name: "Message" }).fill("I want to end my life");
  await page.keyboard.press("Enter");
  const card = page.locator(".escalation-card");
  await expect(card).toBeVisible({ timeout: 15_000 });
  await expect(card).toContainText(/counsel/i);
  await expect(card).toContainText(/Tele-MANAS/i);
});

test("signing in shows the student's own placement eligibility", async ({ page }) => {
  await page.goto("/sign-in");
  await page.getByLabel("Registration number").fill("DEMO006");
  await page.getByLabel("Password").fill("campus@123");
  await page.locator(".signin-form").getByRole("button", { name: "Sign in" }).click();
  await page.waitForURL(/\/placement/);

  await expect(page.locator(".student-summary")).toContainText("Ananya Singh");

  // DEMO006 already holds a 6.5 LPA offer, so the one-offer rule (1.5x) requires >= 9.75 LPA.
  await page.getByRole("radio", { name: /Eligible for me/ }).click();
  const eligible = page.locator(".drive-card h3");
  await expect(eligible.filter({ hasText: "Aster Analytics" })).toHaveCount(0); // 7.2 LPA, below threshold
  await expect(eligible.filter({ hasText: "Kestrel Data" })).toBeVisible(); // 18 LPA, above threshold
});

test("admin can see index health and the escalation log", async ({ page }) => {
  await page.goto("/sign-in");
  await page.getByLabel("Registration number").fill("admin");
  await page.getByLabel("Password").fill("campus@123");
  await page.locator(".signin-form").getByRole("button", { name: "Sign in" }).click();
  await page.waitForURL(/\/placement/);

  await page.goto("/admin");
  await expect(page.locator(".admin-health")).toBeVisible();
  await expect(page.locator(".admin-table, .admin-empty")).toBeVisible();
});
