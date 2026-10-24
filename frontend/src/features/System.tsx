import { useState } from "react";
import {
  Check,
  Cpu,
  Database,
  Download,
  HardDrive,
  ShieldCheck,
} from "lucide-react";
import { api, message, send, size } from "../api";
import { AudioRow, Panel } from "../components/Controls";
import type { AudioItem, Library, Notify, SystemInfo } from "../types";

export function System({
  info,
  library,
  refresh,
  refreshSystem,
  notify,
}: {
  info: SystemInfo | null;
  library: Library;
  refresh: () => Promise<void>;
  refreshSystem: () => Promise<void>;
  notify: Notify;
}) {
  const [busy, setBusy] = useState(false);
  async function setup() {
    setBusy(true);
    try {
      await send("/setup");
      await refresh();
      await refreshSystem();
      notify("Einrichtung eingereiht. Fortschritt unter Ergebnisse.");
    } catch (error) {
      notify(message(error), true);
    } finally {
      setBusy(false);
    }
  }
  async function remove(item: AudioItem) {
    if (
      !window.confirm(
        `„${item.name}“ dauerhaft aus der Audiobibliothek löschen?`,
      )
    )
      return;
    try {
      await api(`/audio/${item.id}`, { method: "DELETE" });
      await refresh();
    } catch (error) {
      notify(message(error), true);
    }
  }
  return (
    <>
      <div className="page-heading compact">
        <div>
          <div className="eyebrow">LOKAL. PRIVAT. DEINS.</div>
          <h1>
            Dein Studio unter der Haube<span className="heading-dot">.</span>
          </h1>
          <p>Hardware, Basisgewichte und deine gespeicherten Audiodateien.</p>
        </div>
      </div>
      <div className="system-grid">
        <Panel title="Rechenleistung" aside={<Cpu size={20} />}>
          <div className="system-value">
            {info?.gpu.name ?? "Wird erkannt …"}
          </div>
          <p className="subtle">
            {info?.gpu.backend ?? "—"}{" "}
            {info?.gpu.memory_gb ? `· ${info.gpu.memory_gb} GB VRAM` : ""}
          </p>
          <span className="badge">PyTorch {info?.gpu.torch ?? "…"}</span>
          {info?.gpu.error && <p className="error-detail">{info.gpu.error}</p>}
          {info?.gpu.note && <p className="info-note">{info.gpu.note}</p>}
          {info?.gpu.device === "cpu" && (
            <p className="info-note">
              CPU-Modus aktiv. Training und Konvertierung sind möglich, dauern
              aber deutlich länger.
            </p>
          )}
        </Panel>
        <Panel title="Dein Speicher" aside={<HardDrive size={20} />}>
          <div className="system-value">
            {info?.disk_free_gb ?? "…"} <small>GB frei</small>
          </div>
          <p className="subtle">
            {library.audio.length} Audiodateien · {library.models.length}{" "}
            Voice-Modelle
          </p>
          <p className="caption left">
            Dateien, Modelle und Checkpoints bleiben im lokalen Datenspeicher
            erhalten, auch nach einem Neustart der App.
          </p>
        </Panel>
      </div>
      <Panel title="Basisgewichte" aside={<Database size={20} />}>
        <p className="panel-intro">
          HuBERT, RMVPE und vortrainierte RVC-v2-Gewichte für 32, 40 und 48 kHz.
          Einmal herunterladen, danach lokal verwenden. Demucs für
          Gesangstrennung wird beim ersten Song-Auftrag ergänzt.
        </p>
        <div className="asset-list">
          {info?.assets.map((asset) => (
            <div key={asset.name}>
              <span className={asset.ready ? "asset-ready" : "subtle"}>
                {asset.ready ? <Check size={16} /> : <Download size={16} />}
              </span>
              <code>{asset.name}</code>
              <span>{size(asset.size)}</span>
              <span className={`badge ${asset.ready ? "green" : ""}`}>
                {asset.ready ? "Bereit" : "Ausstehend"}
              </span>
            </div>
          ))}
        </div>
        <button className="button secondary" onClick={setup} disabled={busy}>
          <Download size={16} />
          {busy ? "Wird eingereiht …" : "Fehlende Dateien einrichten"}
        </button>
      </Panel>
      <div className="privacy-banner">
        <ShieldCheck size={25} />
        <div>
          <h3>Deine Aufnahmen bleiben bei dir.</h3>
          <p>
            Kein Konto, keine Cloud-Verarbeitung, keine externen Trainingsdaten.
            Internet wird für Installation und Basisgewichte benötigt.
          </p>
        </div>
      </div>
      <Panel
        title="Audiobibliothek"
        aside={<span className="badge">{library.audio.length} Dateien</span>}
      >
        <p className="panel-intro">
          Aufnahmen, die du für Konvertierungen oder Trainingsprojekte
          hochgeladen hast.
        </p>
        <div className="file-list">
          {library.audio.map((item) => (
            <AudioRow key={item.id} item={item} onRemove={() => remove(item)} />
          ))}
        </div>
        {!library.audio.length && (
          <p className="subtle">Noch keine Aufnahmen gespeichert.</p>
        )}
      </Panel>
    </>
  );
}
