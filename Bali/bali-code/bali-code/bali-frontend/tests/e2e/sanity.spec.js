import { test, expect } from '@playwright/test';

test.describe('EASY Bali Sanity Tests', () => {

    test('Home page loads correctly', async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState('networkidle');

        // Check if the language switcher exists
        await expect(page.locator('.language')).toBeVisible();

        // Check if the chat input exists
        await expect(page.locator('input[placeholder*="Bot"]')).toBeVisible();
    });

    test('Language switcher updates the UI', async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState('networkidle');

        // Check initial state (default EN)
        const langButton = page.locator('.language');
        await expect(langButton).toContainText('EN');

        // Click to switch to ID
        await langButton.click();
        await expect(langButton).toContainText('ID');

        // Verify translation change (e.g., chat placeholder)
        // ID placeholder: "Obrol dengan Bot AI kami"
        const idInput = page.locator('input[placeholder="Obrol dengan Bot AI kami"]');
        await expect(idInput).toBeVisible();

        // Click again to switch back to EN
        await langButton.click();
        await expect(langButton).toContainText('EN');
        const enInput = page.locator('input[placeholder="Chat with our AI Bot"]');
        await expect(enInput).toBeVisible();
    });

    test('Navigation to chatbot page works', async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState('networkidle');

        // Type something in chat and press enter or click chat button
        const chatInput = page.locator('input[placeholder*="Bot"]');
        await chatInput.fill('Hello Playwright');

        // Click the chat button (orange one)
        const chatBtn = page.locator('img[alt=""][src*="chat-btn.svg"]');
        await chatBtn.click();

        // Should navigate to /chatbot
        await expect(page).toHaveURL(/\/chatbot/);

        // Check if chat container is visible
        await expect(page.locator('.chat')).toBeVisible();
    });

});
