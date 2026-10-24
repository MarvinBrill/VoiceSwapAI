import { expect, test } from "@playwright/test";

for (const separate of [false, true]) {
  test(`voice volume reaches conversion request in ${separate ? "song" : "voice-only"} mode`, async ({
    page,
  }) => {
    const requests: Record<string, unknown>[] = [];
    await page.route("**/api/**", async (route) => {
      const path = new URL(route.request().url()).pathname;
      if (path === "/api/conversions") {
        requests.push(route.request().postDataJSON());
      }
      const fixtures: Record<string, unknown> = {
        "/api/audio": [
          {
            id: "audio",
            name: "Voice.wav",
            duration: 2,
            sample_rate: 44100,
            size: 100,
            channels: 1,
          },
        ],
        "/api/models": [
          {
            id: "model",
            name: "Voice",
            version: "v2",
            sample_rate: 40000,
            speakers: 1,
            size: 100,
            index_path: null,
          },
        ],
        "/api/system": {
          gpu: { name: "CPU", device: "cpu", torch: "test" },
          assets: [],
          disk_free_gb: 10,
          version: "test",
        },
      };
      await route.fulfill({ json: fixtures[path] ?? [] });
    });
    await page.goto("/");
    await page.locator("details.advanced:visible > summary").click();
    const volume = page.getByRole("slider", {
      name: "Stimmenlautstärke",
      exact: true,
    });
    await expect(volume).toHaveValue("0");
    await expect(volume.locator("..").locator("output")).toHaveText("+0 dB");
    await page
      .getByRole("button", { name: /Aus Audiobibliothek wählen/ })
      .click();
    await page.locator('.library-picker input[type="checkbox"]').check();
    await page
      .getByRole("combobox", { name: /Voice-Modell/ })
      .selectOption("model");
    if (!separate)
      await page.getByRole("button", { name: /Stimme pur/ }).click();

    for (const gain of [0, 6.5, -6, 12, -24]) {
      await volume.fill(String(gain));
      await expect(volume.locator("..").locator("output")).toHaveText(
        `${gain >= 0 ? "+" : ""}${gain} dB`,
      );
      await page.getByRole("button", { name: "Stimme verwandeln" }).click();
      await expect.poll(() => requests.at(-1)?.vocal_gain).toBe(gain);
      expect(requests.at(-1)?.separate_vocals).toBe(separate);
      expect(requests.at(-1)?.instrumental_gain).toBe(0);
    }
  });
}
