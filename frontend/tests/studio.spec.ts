import { expect, test } from "@playwright/test";

test("navigation, empty states and responsive layout", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Dein Sound. Neue Stimme." }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Stimme verwandeln" }),
  ).toBeDisabled();
  await page.screenshot({
    path: "../test-results/studio-desktop.png",
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Modellbibliothek", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Modellbibliothek." }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Training", exact: true }).click();
  const system = await (await page.request.get("/api/system")).json();
  await expect(page.getByLabel("Batch-Größe", { exact: true })).toHaveValue(
    system.gpu.backend === "DirectML" ? "1" : "4",
  );
  await expect(
    page.getByRole("button", { name: "Training starten", exact: true }),
  ).toBeDisabled();
  await page.getByLabel("Name der Stimme").fill("Mein Testprojekt");
  await page
    .getByRole("button", { name: "Projekt speichern", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText(
    "Trainingsprojekt gespeichert",
  );
  await page.getByRole("button", { name: /^Ergebnisse/ }).click();
  await expect(
    page.getByRole("heading", { name: "Alles, was du erschaffst." }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Voice Studio", exact: true }).click();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({
    path: "../test-results/studio-mobile.png",
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.getByRole("button", { name: "Menü öffnen", exact: true }).click();
  await page
    .getByRole("button", { name: "System & Speicher", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Dein Studio unter der Haube." }),
  ).toBeVisible();
  expect(errors).toEqual([]);
});

test("audio upload survives navigation and generated audio is playable", async ({
  page,
  request,
}) => {
  const buffer = Buffer.alloc(44 + 32000);
  buffer.write("RIFF", 0);
  buffer.writeUInt32LE(buffer.length - 8, 4);
  buffer.write("WAVEfmt ", 8);
  buffer.writeUInt32LE(16, 16);
  buffer.writeUInt16LE(1, 20);
  buffer.writeUInt16LE(1, 22);
  buffer.writeUInt32LE(16000, 24);
  buffer.writeUInt32LE(32000, 28);
  buffer.writeUInt16LE(2, 32);
  buffer.writeUInt16LE(16, 34);
  buffer.write("data", 36);
  buffer.writeUInt32LE(32000, 40);
  for (let i = 0; i < 16000; i++)
    buffer.writeInt16LE(
      Math.round(Math.sin((i * Math.PI) / 40) * 8000),
      44 + i * 2,
    );

  await page.goto("/");
  await page
    .getByLabel("Audio hier ablegen", { exact: true })
    .setInputFiles({ name: "Browser-Test.wav", mimeType: "audio/wav", buffer });
  await expect(
    page
      .locator(".studio-main")
      .first()
      .getByText("Browser-Test.wav", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Modell hinzufügen", exact: true })
    .click();
  await page.getByRole("button", { name: "Voice Studio", exact: true }).click();
  await expect(
    page
      .locator(".studio-main")
      .first()
      .getByText("Browser-Test.wav", { exact: true }),
  ).toBeVisible();

  const response = await request.get("/api/jobs");
  const jobs = await response.json();
  if (!jobs.some((job: { outputs: unknown[] }) => job.outputs.length > 0))
    return;
  await page.getByRole("button", { name: /^Ergebnisse/ }).click();
  const audio = page.locator('audio[src*="/outputs/"]:visible').first();
  const audioDuration = await audio.evaluate(
    (element: HTMLAudioElement) =>
      new Promise<number>((resolve, reject) => {
        element.onloadedmetadata = () => resolve(element.duration);
        element.onerror = () =>
          reject(new Error("Browser could not decode generated audio"));
        element.load();
      }),
  );
  expect(audioDuration).toBeGreaterThan(0);
});
