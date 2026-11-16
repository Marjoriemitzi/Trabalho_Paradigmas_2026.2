const { defineConfig } = require("@playwright/test");

module.exports = defineConfig({
  testDir: "./tests",
  fullyParallel: true,

  use: {
    baseURL: "http://127.0.0.1:5174",
    browserName: "chromium",
    trace: "retain-on-failure"
  },

  webServer: {
    command: "npm run build && node scripts/dev.mjs --skip-build",
    url: "http://127.0.0.1:5174",
    timeout: 120000,
    reuseExistingServer: false,
    env: {
      HOST: "127.0.0.1",
      PORT: "5174"
    }
  }
});