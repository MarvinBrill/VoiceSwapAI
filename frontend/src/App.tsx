import { useCallback, useEffect, useState } from "react";
import {
  AudioLines,
  Check,
  ChevronRight,
  CircleHelp,
  Cpu,
  Disc3,
  FlaskConical,
  FolderHeart,
  Menu,
  Radio,
  Settings2,
  TriangleAlert,
  X,
} from "lucide-react";
import { api, message } from "./api";
import { Models } from "./features/Models";
import { Results } from "./features/Results";
import { Studio } from "./features/Studio";
import { System } from "./features/System";
import { Training } from "./features/Training";
import type { Job, Library, Page, SystemInfo } from "./types";

const navigation = [
  { page: "studio", label: "Voice Studio", icon: AudioLines },
  { page: "models", label: "Modellbibliothek", icon: FolderHeart },
  { page: "training", label: "Training", icon: FlaskConical },
  { page: "results", label: "Ergebnisse", icon: Disc3 },
] as const;

export default function App() {
  const [page, setPage] = useState<Page>("studio");
  const [mobileOpen, setMobileOpen] = useState(false);
  const [library, setLibrary] = useState<Library>({
    audio: [],
    models: [],
    projects: [],
    jobs: [],
  });
  const [system, setSystem] = useState<SystemInfo | null>(null);
  const [connectionError, setConnectionError] = useState("");
  const [toast, setToast] = useState<{
    message: string;
    error: boolean;
  } | null>(null);
  const [resumeJob, setResumeJob] = useState<Job | null>(null);
  const active = library.jobs.filter(
    (job) => job.status === "queued" || job.status === "running",
  );

  const refresh = useCallback(async () => {
    try {
      const [audio, models, projects, jobs] = await Promise.all([
        api<Library["audio"]>("/audio"),
        api<Library["models"]>("/models"),
        api<Library["projects"]>("/projects"),
        api<Library["jobs"]>("/jobs"),
      ]);
      setLibrary({ audio, models, projects, jobs });
      setConnectionError("");
    } catch (error) {
      setConnectionError(message(error));
    }
  }, []);

  const refreshSystem = useCallback(async () => {
    try {
      setSystem(await api<SystemInfo>("/system"));
    } catch {
      /* Connection status is reported by the library poll. */
    }
  }, []);

  useEffect(() => {
    void refresh();
    void refreshSystem();
    const interval = window.setInterval(() => {
      void refresh();
    }, 2500);
    const systemInterval = window.setInterval(() => {
      void refreshSystem();
    }, 15000);
    return () => {
      window.clearInterval(interval);
      window.clearInterval(systemInterval);
    };
  }, [refresh, refreshSystem]);

  useEffect(() => {
    if (!toast || toast.error) return;
    const timeout = window.setTimeout(() => setToast(null), 5000);
    return () => window.clearTimeout(timeout);
  }, [toast]);

  const notify = (text: string, error = false) =>
    setToast({ message: text, error });
  const navigate = (destination: Page) => {
    setPage(destination);
    setMobileOpen(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };
  const resume = (job: Job) => {
    setResumeJob(job);
    navigate("training");
  };
  const title =
    navigation.find((item) => item.page === page)?.label ?? "System & Speicher";
  const ready = system?.assets.every((asset) => asset.ready);

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">
        Zum Inhalt
      </a>
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />
      {mobileOpen && (
        <button
          className="sidebar-scrim"
          aria-label="Menü schließen"
          onClick={() => setMobileOpen(false)}
        />
      )}
      <aside className={`sidebar ${mobileOpen ? "open" : ""}`}>
        <a
          className="brand"
          href="#"
          onClick={(event) => {
            event.preventDefault();
            navigate("studio");
          }}
        >
          <div className="brand-mark">
            <AudioLines size={25} />
          </div>
          <span>
            VoiceSwap<span className="brand-ai">AI</span>
            <small>YOUR VOICE. REIMAGINED.</small>
          </span>
        </a>
        <div className="workspace-chip">
          <div className="workspace-avatar">V</div>
          <div>
            <strong>Mein Studio</strong>
            <small>Lokaler Workspace</small>
          </div>
          <ChevronRight size={14} />
        </div>
        <div className="nav-label">WORKSPACE</div>
        <nav aria-label="Hauptnavigation">
          {navigation.map((item) => (
            <button
              key={item.page}
              className={`nav-item ${page === item.page ? "active" : ""}`}
              aria-current={page === item.page ? "page" : undefined}
              onClick={() => navigate(item.page)}
            >
              <item.icon size={19} />
              <span>{item.label}</span>
              {item.page === "results" && active.length > 0 && (
                <span className="nav-count">{active.length}</span>
              )}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="local-card">
            <Radio size={17} />
            <strong>Alles bleibt bei dir.</strong>
            <p>
              Deine Modelle. Deine Audios.
              <br />
              Deine Hardware.
            </p>
            <span>
              <span className="tiny-dot" /> LOCAL FIRST
            </span>
          </div>
          <button
            className={`nav-item ${page === "system" ? "active" : ""}`}
            onClick={() => navigate("system")}
          >
            <Settings2 size={18} />
            <span>System & Speicher</span>
          </button>
          <div className="sidebar-version">
            VOICE SWAP AI <span>v0.1</span>
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumbs">
            <button
              className="icon-button mobile-menu"
              aria-label="Menü öffnen"
              onClick={() => setMobileOpen(true)}
            >
              <Menu size={20} />
            </button>
            <span>Mein Studio</span>
            <ChevronRight size={13} />
            <strong>{title}</strong>
          </div>
          <div className="topbar-right">
            <button
              className="hardware-pill"
              onClick={() => navigate("system")}
            >
              <span
                className={`tiny-dot ${connectionError || system?.gpu.error ? "red" : ""}`}
              />
              <Cpu size={14} />
              <span>
                {system?.gpu.name.replace("NVIDIA GeForce ", "") ??
                  "Hardware wird erkannt"}
              </span>
            </button>
            <button
              className="icon-button help-button"
              aria-label="System und Einrichtung anzeigen"
              onClick={() => navigate("system")}
            >
              <CircleHelp size={18} />
            </button>
            <div className="user-avatar">V</div>
          </div>
        </header>
        <main id="main">
          {connectionError && (
            <div role="alert" className="banner error">
              <TriangleAlert size={18} />
              <span>Verbindung zur App unterbrochen. {connectionError}</span>
              <button className="text-button" onClick={refresh}>
                Erneut verbinden
              </button>
            </div>
          )}
          {!ready && system && page !== "system" && (
            <div className="setup-strip">
              <span className="pulse-dot" />
              <span>
                {active.some((job) => job.kind === "setup")
                  ? "Dein Studio wird eingerichtet. Die Basisgewichte werden heruntergeladen."
                  : "Einige Basisgewichte fehlen noch. Sie werden bei Bedarf eingerichtet."}
              </span>
              <button
                onClick={() =>
                  navigate(
                    active.some((job) => job.kind === "setup")
                      ? "results"
                      : "system",
                  )
                }
              >
                Details <ChevronRight size={13} />
              </button>
            </div>
          )}
          <div hidden={page !== "studio"}>
            <Studio
              directml={system?.gpu.backend === "DirectML"}
              library={library}
              refresh={refresh}
              notify={notify}
              navigate={navigate}
            />
          </div>
          <div hidden={page !== "models"}>
            <Models library={library} refresh={refresh} notify={notify} />
          </div>
          <div hidden={page !== "training"}>
            <Training
              directml={system?.gpu.backend === "DirectML"}
              library={library}
              refresh={refresh}
              notify={notify}
              resumeJob={resumeJob}
              clearResume={() => setResumeJob(null)}
              onResume={resume}
            />
          </div>
          <div hidden={page !== "results"}>
            <Results
              library={library}
              refresh={refresh}
              notify={notify}
              resume={resume}
            />
          </div>
          <div hidden={page !== "system"}>
            <System
              info={system}
              library={library}
              refresh={refresh}
              refreshSystem={refreshSystem}
              notify={notify}
            />
          </div>
          <footer className="page-footer">
            <span>
              <AudioLines size={14} /> VoiceSwapAI
            </span>
            <span>Gemacht für deinen nächsten Sound.</span>
            <span>100 % lokale Verarbeitung</span>
          </footer>
        </main>
      </div>
      {toast && (
        <div
          className={`toast ${toast.error ? "error" : ""}`}
          role={toast.error ? "alert" : "status"}
        >
          {toast.error ? <TriangleAlert size={20} /> : <Check size={20} />}
          <span>{toast.message}</span>
          <button
            className="icon-button"
            aria-label="Meldung schließen"
            onClick={() => setToast(null)}
          >
            <X size={17} />
          </button>
        </div>
      )}
    </div>
  );
}
