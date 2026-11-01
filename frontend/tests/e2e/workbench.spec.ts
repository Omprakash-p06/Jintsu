import { expect, test } from '@playwright/test'

test.describe('Reality Check AI Workbench E2E Journeys', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('CUJ 1: Claim submission, live verification, verdict badge and citation inspection', async ({
    page,
  }) => {
    // 1. Initial Page Load & Composer Inspection
    await expect(page.getByRole('heading', { name: 'Verify a claim', level: 1 })).toBeVisible()
    const textarea = page.getByPlaceholder(/Enter a statement to evaluate/i)
    await expect(textarea).toBeVisible()

    // 2. Claim Submission
    const testClaim = 'Atmospheric CO2 reached 426.9 ppm at Mauna Loa in May 2024'
    await textarea.fill(testClaim)
    const verifyBtn = page.getByRole('button', { name: 'Verify claim' })
    await expect(verifyBtn).toBeEnabled()
    await verifyBtn.click()

    // 3. Verification In-Flight State (Progress Card)
    // Live timer or progress step is displayed
    const progressHeading = page.getByRole('heading', { name: /Verification in progress/i })
    if (await progressHeading.isVisible()) {
      await expect(page.locator('.elapsed')).toBeVisible()
    }

    // 4. Final Verdict Display
    // Wait for the result section to render
    const verdictSection = page.locator('.verdict-card')
    await expect(verdictSection).toBeVisible({ timeout: 15_000 })
    await expect(page.locator('.verdict-badge')).toBeVisible()

    // 5. Dynamic Relationship Graph & Source Evidence Grid
    await expect(page.locator('.graph')).toBeVisible()
    await expect(page.locator('.evidence-section')).toBeVisible()

    const sourceCards = page.locator('.source-card')
    const count = await sourceCards.count()
    if (count > 0) {
      const firstCard = sourceCards.first()
      await expect(firstCard.locator('.stance-badge')).toBeVisible()

      // 6. Copy Quote Interaction
      const copyQuoteBtn = firstCard.getByRole('button', { name: /copy quote/i })
      if (await copyQuoteBtn.isVisible()) {
        await copyQuoteBtn.click()
        await expect(firstCard.getByRole('button', { name: /copied/i })).toBeVisible()
      }
    }

    // 7. Copy Report Interaction
    const copyReportBtn = page.getByRole('button', { name: /copy report/i })
    if (await copyReportBtn.isVisible()) {
      await copyReportBtn.click()
      await expect(page.getByRole('button', { name: /copied/i })).toBeVisible()
    }

    // 8. History Drawer Persistence
    const historySection = page.locator('#history')
    await expect(historySection).toBeVisible()
    await expect(historySection.locator('.history-item')).toBeVisible()
  })

  test('CUJ 3: Abstention on subjective assertion and absent evidence', async ({ page }) => {
    const textarea = page.getByPlaceholder(/Enter a statement to evaluate/i)
    const verifyBtn = page.getByRole('button', { name: 'Verify claim' })

    // 1. Subjective Value Judgment (Gate A Short-Circuit)
    await textarea.fill('The Godfather is the greatest film of all time')
    await verifyBtn.click()

    const verdictCard = page.locator('.verdict-card')
    await expect(verdictCard).toBeVisible({ timeout: 10_000 })
    const badge = page.locator('.verdict-badge')
    await expect(badge).toContainText(/Not Verifiable/i)

    // 2. Limitations Accordion ("What remains unknown")
    const unknownSection = page.locator('.unknown')
    await expect(unknownSection).toBeVisible()
    await expect(page.getByRole('heading', { name: 'What remains unknown' })).toBeVisible()
  })

  test('Settings modal keyboard accessibility and escape dismissal (WCAG 2.2 AA)', async ({
    page,
  }) => {
    // Open settings modal
    const settingsBtn = page.getByRole('button', { name: 'Open settings' })
    await settingsBtn.click()

    const modal = page.getByRole('dialog', { name: 'Settings' })
    await expect(modal).toBeVisible()
    await expect(modal).toHaveAttribute('aria-modal', 'true')

    // Escape dismissal
    await page.keyboard.press('Escape')
    await expect(modal).not.toBeVisible()
  })
})
