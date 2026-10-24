import { useEffect, useState } from "react";
import {
  ArrowRight,
  Check,
  FlaskConical,
  FolderPlus,
  Plus,
  Save,
  Search,
} from "lucide-react";
import { duration, message, send, uploadAudio } from "../api";
import { AudioRow, Dropzone, Panel, Toggle } from "../components/Controls";
import { JobCard } from "../components/JobCard";
import type { Job, Library, Notify, Project } from "../types";
import { AUDIO_ACCEPT } from "./Studio";

export function Training({
  library,
  refresh,
  notify,
  resumeJob,
  clearResume,
  onResume,
  directml,
}: {
  library: Library;
  refresh: () => Promise<void>;
  notify: Notify;
  resumeJob: Job | null;
  clearResume: () => void;
  onResume: (job: Job) => void;
  directml: boolean;
}) {
  const [projectId, setProjectId] = useState("");
  const [name, setName] = useState("");
  const [audioIds, setAudioIds] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState("");
  const [search, setSearch] = useState("");
  const [libraryOpen, setLibraryOpen] = useState(false);
  const [epochs, setEpochs] = useState(100);
  const [batchOverride, setBatch] = useState<number | null>(null);
  const batch = batchOverride ?? (directml ? 1 : 4);
  const [rate, setRate] = useState(40000);
  const [saveEvery, setSaveEvery] = useState(10);
  const [learningRate, setLearningRate] = useState(0.0001);
  const [method, setMethod] = useState("rmvpe");
  const [cache, setCache] = useState(false);
  const selected = library.audio.filter((audio) => audioIds.includes(audio.id));
  const totalDuration = selected.reduce((sum, item) => sum + item.duration, 0);
  const jobs = library.jobs.filter((job) => job.kind === "training");

  function chooseProject(id: string) {
    const project = library.projects.find((item) => item.id === id);
    setProjectId(id);
    setName(project?.name ?? "");
    setAudioIds(project?.audio_ids ?? []);
    clearResume();
  }

  useEffect(() => {
    if (!resumeJob) return;
    const options = resumeJob.parameters;
    setProjectId(String(options.project_id));
    setName(String(options.project_name));
    setAudioIds(options.audio_ids as string[]);
    setEpochs(Number(options.epochs) + 50);
    setBatch(Number(options.batch_size));
    setRate(Number(options.sample_rate));
    setSaveEvery(Number(options.save_every));
    setLearningRate(Number(options.learning_rate));
    setMethod(String(options.pitch_method));
  }, [resumeJob]);

  async function saveProject(): Promise<Project> {
    const project = await send<Project>(
      projectId ? `/projects/${projectId}` : "/projects",
      { name, audio_ids: audioIds },
      projectId ? "PUT" : "POST",
    );
    setProjectId(project.id);
    return project;
  }

  async function persistProject() {
    setBusy(true);
    try {
      await saveProject();
      await refresh();
      notify("Trainingsprojekt gespeichert.");
    } catch (error) {
      notify(message(error), true);
    } finally {
      setBusy(false);
    }
  }

  async function addFiles(files: File[]) {
    const ids: string[] = [];
    try {
      for (const [index, file] of files.entries()) {
        setUploading(`${index + 1}/${files.length} · ${file.name}`);
        const audio = await uploadAudio(file, (progress) =>
          setUploading(`${index + 1}/${files.length} · ${progress} %`),
        );
        ids.push(audio.id);
      }
    } catch (error) {
      notify(message(error), true);
    } finally {
      setAudioIds((previous) => [...new Set([...previous, ...ids])]);
      setUploading("");
      await refresh();
    }
  }

  async function start() {
    setBusy(true);
    try {
      const project = resumeJob
        ? library.projects.find((item) => item.id === projectId)!
        : await saveProject();
      await send("/training", {
        project_id: project.id,
        epochs,
        batch_size: batch,
        sample_rate: rate,
        save_every: saveEvery,
        learning_rate: learningRate,
        pitch_method: method,
        cache_gpu: cache,
        resume_job_id: resumeJob?.id ?? null,
      });
      await refresh();
      clearResume();
      notify("Training zur Warteschlange hinzugefügt.");
    } catch (error) {
      notify(message(error), true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <div className="page-heading compact">
        <div>
          <div className="eyebrow">VON DEINEM AUDIO ZU DEINEM MODELL</div>
          <h1>
            Eine Stimme entsteht<span className="heading-dot">.</span>
          </h1>
          <p>
            Trainiere dein eigenes RVC-v2-Modell. Direkt hier, auf deinem
            Rechner.
          </p>
        </div>
        <div className="page-symbol">
          <FlaskConical size={42} strokeWidth={1.25} />
        </div>
      </div>
      {resumeJob && (
        <div className="banner">
          <span>
            Fortsetzen von „{resumeJob.title}“. Die ursprünglichen
            Trainingsdaten werden wiederverwendet.
          </span>
          <button className="text-button" onClick={clearResume}>
            Neues Training
          </button>
        </div>
      )}
      <div className="studio-grid">
        <div className="studio-main">
          <Panel
            title="Dein Trainingsprojekt"
            step="01"
            aside={
              <button className="text-button" onClick={() => chooseProject("")}>
                <FolderPlus size={15} /> Neu
              </button>
            }
          >
            <div className="control-grid">
              <label className="field">
                Gespeichertes Projekt
                <select
                  value={projectId}
                  onChange={(event) => chooseProject(event.target.value)}
                >
                  <option value="">Neues Projekt</option>
                  {library.projects.map((project) => (
                    <option value={project.id} key={project.id}>
                      {project.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                Name der Stimme
                <input
                  placeholder="Zum Beispiel: Meine Gesangsstimme"
                  maxLength={100}
                  value={name}
                  disabled={!!resumeJob}
                  onChange={(event) => setName(event.target.value)}
                />
              </label>
            </div>
          </Panel>
          <Panel
            title="Dein Audio-Datensatz"
            step="02"
            aside={
              <span className="badge">
                {selected.length} Dateien · {duration(totalDuration)}
              </span>
            }
          >
            {!resumeJob && (
              <Dropzone
                accept={AUDIO_ACCEPT}
                onFiles={addFiles}
                busy={uploading}
                title="Trainingsaufnahmen hinzufügen"
                subtitle="Beliebig viele lokale Dateien · keine feste Längenbegrenzung"
              />
            )}
            {selected.length > 0 && (
              <>
                <div className="dataset-summary">
                  <div>
                    <strong>{selected.length}</strong>
                    <span>Aufnahmen</span>
                  </div>
                  <div>
                    <strong>{duration(totalDuration)}</strong>
                    <span>Gesamtdauer</span>
                  </div>
                  <div>
                    <strong>RVC v2</strong>
                    <span>768D · Pitch geführt</span>
                  </div>
                </div>
                <label className="search dataset-search">
                  <Search size={15} />
                  <input
                    placeholder="Aufnahme suchen …"
                    aria-label="Trainingsaufnahmen durchsuchen"
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                  />
                </label>
                <div className="file-list dataset-list">
                  {selected
                    .filter((item) =>
                      item.name.toLowerCase().includes(search.toLowerCase()),
                    )
                    .map((item) => (
                      <AudioRow
                        key={item.id}
                        item={item}
                        onRemove={
                          resumeJob
                            ? undefined
                            : () =>
                                setAudioIds((previous) =>
                                  previous.filter((id) => id !== item.id),
                                )
                        }
                      />
                    ))}
                </div>
              </>
            )}
            {!resumeJob && library.audio.length > 0 && (
              <>
                <button
                  className="text-button library-link"
                  onClick={() => setLibraryOpen(!libraryOpen)}
                >
                  <Plus size={15} /> Aus Audiobibliothek hinzufügen
                </button>
                {libraryOpen && (
                  <div className="library-picker">
                    {library.audio.map((item) => (
                      <AudioRow
                        key={item.id}
                        item={item}
                        selected={audioIds.includes(item.id)}
                        onSelect={() =>
                          setAudioIds((previous) =>
                            previous.includes(item.id)
                              ? previous.filter((id) => id !== item.id)
                              : [...previous, item.id],
                          )
                        }
                      />
                    ))}
                  </div>
                )}
              </>
            )}
            {!resumeJob && (
              <button
                className="button secondary"
                disabled={!name.trim() || busy || !!uploading}
                onClick={persistProject}
              >
                <Save size={16} /> Projekt speichern
              </button>
            )}
          </Panel>
        </div>
        <aside className="studio-side">
          <Panel title="Training einstellen" step="03">
            <label className="field">
              Qualität / Samplerate
              <select
                value={rate}
                disabled={!!resumeJob}
                onChange={(event) => setRate(Number(event.target.value))}
              >
                <option value="32000">32 kHz · ressourcensparend</option>
                <option value="40000">40 kHz · ausgewogen</option>
                <option value="48000">48 kHz · hohe Auflösung</option>
              </select>
            </label>
            <div className="control-grid small">
              <label className="field">
                Gesamtepochen
                <input
                  type="number"
                  min="1"
                  max="10000"
                  value={epochs}
                  onChange={(event) => setEpochs(Number(event.target.value))}
                />
              </label>
              <label className="field">
                Batch-Größe
                <select
                  aria-label="Batch-Größe"
                  value={batch}
                  onChange={(event) => setBatch(Number(event.target.value))}
                >
                  {[1, 2, 4, 6, 8, 12, 16, 24, 32].map((value) => (
                    <option key={value}>{value}</option>
                  ))}
                </select>
              </label>
            </div>
            <p className="caption left">
              {directml
                ? "DirectML startet mit Batch 1. Erhöhe die Größe erst, wenn genügend Grafikspeicher frei bleibt."
                : "Startwert für 16 GB VRAM: Batch 4. Bei Speichermangel auf 2 oder 1 reduzieren."}
            </p>
            <details className="advanced">
              <summary>Erweiterte Einstellungen</summary>
              <label className="field">
                Checkpoint alle … Epochen
                <input
                  type="number"
                  min="1"
                  max="1000"
                  value={saveEvery}
                  onChange={(event) => setSaveEvery(Number(event.target.value))}
                />
              </label>
              <label className="field">
                Lernrate
                <input
                  type="number"
                  min="0.000001"
                  max="0.001"
                  step="0.00001"
                  value={learningRate}
                  disabled={!!resumeJob}
                  onChange={(event) =>
                    setLearningRate(Number(event.target.value))
                  }
                />
              </label>
              <label className="field">
                Pitch-Erkennung
                <select
                  value={method}
                  disabled={!!resumeJob}
                  onChange={(event) => setMethod(event.target.value)}
                >
                  <option value="rmvpe">RMVPE</option>
                  <option value="pm">Parselmouth</option>
                </select>
              </label>
              <Toggle
                checked={cache}
                onChange={setCache}
                title="Datensatz im VRAM cachen"
                description="Schneller, benötigt zusätzlich GPU-Speicher."
              />
            </details>
            <div className="training-steps">
              <span>
                <Check size={14} /> Audio schneiden & normalisieren
              </span>
              <span>
                <Check size={14} /> Pitch und Merkmale extrahieren
              </span>
              <span>
                <Check size={14} /> Modell und Stimmenindex trainieren
              </span>
              <span>
                <Check size={14} /> In deiner Bibliothek speichern
              </span>
            </div>
            <button
              className="button primary full"
              onClick={start}
              disabled={
                busy ||
                !!uploading ||
                !name.trim() ||
                !selected.length ||
                epochs < 1 ||
                saveEvery < 1
              }
            >
              {busy
                ? "Wird vorbereitet …"
                : resumeJob
                  ? "Training fortsetzen"
                  : "Training starten"}
              <ArrowRight size={17} />
            </button>
            <p className="caption">.pth und .index danach herunterladen.</p>
          </Panel>
          <div className="tip-card">
            <FlaskConical size={20} />
            <div>
              <strong>Gutes Material macht den Unterschied.</strong>
              <p>
                Eine einzelne Stimme, wenig Hall und keine Hintergrundmusik.
                Etwa 10 Minuten vielfältige Aufnahmen sind ein guter Start; auch
                kurze Clips werden automatisch vorbereitet.
              </p>
            </div>
          </div>
        </aside>
      </div>
      <div className="section-title">
        <h2>Trainingsverlauf</h2>
        <span className="subtle">Checkpoints bleiben lokal gespeichert</span>
      </div>
      <div className="jobs-grid">
        {jobs.map((job) => (
          <JobCard
            key={job.id}
            job={job}
            refresh={refresh}
            notify={notify}
            resume={onResume}
          />
        ))}
      </div>
    </>
  );
}
