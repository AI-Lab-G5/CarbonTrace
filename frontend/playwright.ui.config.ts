import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  testMatch: 'ui.spec.ts',
  timeout: 30000,
  workers: 1,
  use: { baseURL: 'http://127.0.0.1:3100', screenshot: 'only-on-failure', trace: 'retain-on-failure' },
  reporter: 'list',
  webServer: { command: 'npm run dev -- --host 127.0.0.1 --port 3100 --strictPort', url: 'http://127.0.0.1:3100', reuseExistingServer: !process.env.CI },
});
