import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  use: {
    reducedMotion: "reduce",
    baseURL: process.env.APP_URL ?? "http://127.0.0.1:8000",
    browserName: "chromium",
  },
  reporter: "list",
});
