import { useRef, useState } from "react";
import {
  ArrowDownToLine,
  AudioLines,
  Link2,
  Search,
  Trash2,
} from "lucide-react";
import { api, message, size, upload, uploadModel } from "../api";
import { Dropzone, Empty } from "../components/Controls";
import type { Library, Notify, VoiceModel } from "../types";

export function Models({
  library,
  refresh,
  notify,
}: {
  library: Library;
  refresh: () => Promise<void>;
  notify: Notify;
}) {
  const [busy, setBusy] = useState("");
  const [search, setSearch] = useState("");
  const indexInput = useRef<HTMLInputElement>(null);
  const [indexModel, setIndexModel] = useState<VoiceModel | null>(null);
  const models = library.models.filter((model) =>
    model.name.toLocaleLowerCase().includes(search.toLocaleLowerCase()),
  );

  async function importModels(files: File[]) {
    try {
      for (const [number, file] of files.entries()) {
        setBusy(`${number + 1}/${files.length} · ${file.name}`);
        await uploadModel(file, (value) =>
          setBusy(`${file.name} · ${value} %`),
        );
      }
      if (files.length)
        notify("Modelle sind in deiner Bibliothek gespeichert.");
    } catch (error) {
      notify(message(error), true);
    } finally {
      setBusy("");
      await refresh();
    }
  }

  async function addIndex(file: File) {
    if (!indexModel) return;
    setBusy("Stimmenindex hinzufügen …");
    try {
      await upload(`/models/${indexModel.id}/index`, file, (value) =>
        setBusy(`Stimmenindex · ${value} %`),
      );
      notify("Stimmenindex verbunden.");
    } catch (error) {
      notify(message(error), true);
    } finally {
      setBusy("");
      setIndexModel(null);
      await refresh();
    }
  }

  async function remove(model: VoiceModel) {
    if (!window.confirm(`„${model.name}“ aus der Bibliothek löschen?`)) return;
    try {
      await api(`/models/${model.id}`, { method: "DELETE" });
      await refresh();
      notify("Modell entfernt.");
    } catch (error) {
      notify(message(error), true);
    }
  }

  return (
    <>
      <div className="page-heading compact">
        <div>
          <div className="eyebrow">DEINE STIMMEN. EIN ZUHAUSE.</div>
          <h1>
            Modellbibliothek<span className="heading-dot">.</span>
          </h1>
          <p>Einmal importieren. Immer wieder neu interpretieren.</p>
        </div>
        <span className="large-count">
          {library.models.length.toString().padStart(2, "0")}
          <small>STIMMEN</small>
        </span>
      </div>
      <Dropzone
        accept=".pth"
        onFiles={importModels}
        busy={busy}
        title="Deine Voice-Modelle hinzufügen"
        subtitle="RVC v1 & v2 · .pth-Dateien · dauerhaft lokal gespeichert"
      />
      <div className="section-title">
        <h2>
          Alle Stimmen <span className="count">{library.models.length}</span>
        </h2>
        <label className="search">
          <Search size={16} />
          <input
            aria-label="Modelle durchsuchen"
            placeholder="Stimme suchen …"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </label>
      </div>
      <input
        ref={indexInput}
        className="visually-hidden"
        type="file"
        accept=".index"
        aria-label="Stimmenindex importieren"
        onChange={(event) => {
          if (event.target.files?.[0]) void addIndex(event.target.files[0]);
          event.target.value = "";
        }}
      />
      {models.length ? (
        <div className="model-grid">
          {models.map((model, index) => (
            <article className="model-card" key={model.id}>
              <div className={`model-cover color-${index % 4}`}>
                <AudioLines size={63} strokeWidth={1.1} />
                <span>
                  {model.origin === "trained"
                    ? "SELBST TRAINIERT"
                    : "DEINE BIBLIOTHEK"}
                </span>
                <span className="badge">RVC {model.version.toUpperCase()}</span>
              </div>
              <div className="model-card-body">
                <h2>{model.name}</h2>
                <p>
                  {model.sample_rate / 1000} kHz <i>·</i> {size(model.size)}{" "}
                  <i>·</i>{" "}
                  {model.pitch_guidance ? "Pitch geführt" : "Ohne Pitch"}
                </p>
                <div className="model-index">
                  <span
                    className={model.index_path ? "tiny-dot" : "tiny-dot muted"}
                  />
                  {model.index_path
                    ? "Stimmenindex verbunden"
                    : "Kein Stimmenindex"}
                </div>
                <div className="model-actions">
                  <button
                    className="text-button"
                    disabled={!!busy}
                    onClick={() => {
                      setIndexModel(model);
                      indexInput.current?.click();
                    }}
                  >
                    <Link2 size={15} />
                    {model.index_path ? "Index ersetzen" : "Index hinzufügen"}
                  </button>
                  <a
                    className="icon-button"
                    href={`/api/models/${model.id}/file`}
                    aria-label={`${model.name} als .pth herunterladen`}
                  >
                    <ArrowDownToLine size={17} />
                  </a>
                  {model.index_path && (
                    <a
                      className="text-button"
                      href={`/api/models/${model.id}/file?index=true`}
                    >
                      .index ↓
                    </a>
                  )}
                  <button
                    className="icon-button danger"
                    onClick={() => remove(model)}
                    aria-label={`${model.name} löschen`}
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <Empty
          title={
            search
              ? "Keine passende Stimme gefunden"
              : "Deine erste Stimme wartet"
          }
        >
          {search
            ? "Probiere einen anderen Suchbegriff."
            : "Importiere ein RVC-Modell oder erstelle im Training dein eigenes."}
        </Empty>
      )}
      <p className="page-footnote">
        Eine optionale .index-Datei verbessert die Ähnlichkeit zur Zielstimme.
        Verwende den zum Modell gehörenden Index.
      </p>
    </>
  );
}
