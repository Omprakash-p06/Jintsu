import fs from 'node:fs'
import path from 'node:path'
import { defineConfig, devices } from '@playwright/test'

function getBackendCommand(): string {
  if (process.env.BACKEND_COMMAND) {
    return process.env.BACKEND_COMMAND
  }
  const backendDir = path.resolve(__dirname, '../backend')
  const isWin = process.platform === 'win32'
  const venvPaths = [
    path.join(backendDir, '.venv', isWin ? 'Scripts' : 'bin', isWin ? 'python.exe' : 'python'),
    path.join(backendDir, '../.venv', isWin ? 'Scripts' : 'bin', isWin ? 'python.exe' : 'python'),
  ]

  for (const venvPython of venvPaths) {
    if (fs.existsSync(venvPython)) {
      return `"${venvPython}" -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
    }
  }

  const defaultPython = process.env.PYTHON || (isWin ? 'python' : 'python3')
  return `${defaultPython} -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
}

function getFrontendCommand(): string {
  if (process.env.FRONTEND_COMMAND) {
    return process.env.FRONTEND_COMMAND
  }
  if (!fs.existsSync(path.resolve(__dirname, '.next'))) {
    return 'pnpm run build && pnpm run start'
  }
  return 'pnpm run start'
}

/**
 * Playwright E2E configuration for Reality Check AI (jintru) workbench.
 * See https://playwright.dev/docs/test-configuration.
 */
export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'list',
  use: {
    baseURL: process.env.PLAYWRIGHT_TEST_BASE_URL || 'http://127.0.0.1:3000',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
  ],
  webServer: [
    {
      command: getBackendCommand(),
      cwd: '../backend',
      url: 'http://127.0.0.1:8000/api/v1/health',
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        ...process.env,
        USE_MOCK_PROVIDERS: 'true',
      },
    },
    {
      command: getFrontendCommand(),
      url: 'http://127.0.0.1:3000',
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        ...process.env,
        JINTRU_API_URL: 'http://127.0.0.1:8000',
      },
    },
  ],
})


