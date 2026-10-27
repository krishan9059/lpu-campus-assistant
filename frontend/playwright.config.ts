import { defineConfig, devices } from "@playwright/test";

/**
 * End-to-end smoke tests against a real backend and a real built frontend.
 *
 * Before running:
 *   1. `npx playwright install chromium` (once)
 *   2. From backend/, make sure the demo data can seed: a writable var/ directory and
 *      the .env defaults (EMBEDDING_PROVIDER=hash keeps this fast and offline).
 *
 * Run with: npm run test:e2e
 */
const BACKEND_PORT = 8010;
const FRONTEND_PORT = 4310;
const BACKEND_DIR = "../backend";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: `http://localhost:${FRONTEND_PORT}`,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: "uvicorn app.main:app --port " + BACKEND_PORT,
      cwd: BACKEND_DIR,
      port: BACKEND_PORT,
      timeout: 60_000,
      reuseExistingServer: !process.env.CI,
      env: {
        EMBEDDING_PROVIDER: "hash",
        DATABASE_URL: "sqlite:////tmp/pw-e2e/campus.db",
        VECTOR_DIR: "/tmp/pw-e2e/chroma",
        BCRYPT_ROUNDS: "4",
        LOG_LEVEL: "WARNING",
        CORS_ORIGINS: `http://localhost:${FRONTEND_PORT}`,
      },
    },
    {
      command: `npx vite preview --port ${FRONTEND_PORT} --strictPort`,
      port: FRONTEND_PORT,
      timeout: 60_000,
      reuseExistingServer: !process.env.CI,
      env: { VITE_API_PROXY_TARGET: `http://localhost:${BACKEND_PORT}` },
    },
  ],
});
