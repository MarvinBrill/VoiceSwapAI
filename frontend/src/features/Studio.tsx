import { useState } from "react";
import {
  ArrowRight,
  AudioLines,
  ChevronDown,
  Layers3,
  Mic2,
  Plus,
  Sparkles,
} from "lucide-react";
import { duration, message, send, uploadAudio } from "../api";
import {
  AudioRow,
  Dropzone,
  Empty,
  Panel,
  Slider,
} from "../components/Controls";
import { JobCard } from "../components/JobCard";
import type { Library, Notify, Page } from "../types";

const AUDIO_ACCEPT =
  ".wav,.mp3,.flac,.m4a,.ogg,.aac,.opus,.aiff,.wma,.mp4,.webm";

export function Studio({
  library,
  refresh,
  notify,
  navigate,
  directml,
}: {
  library: Library;
  refresh: () => Promise<void>;
  notify: Notify;
  navigate: (page: Page) => void;
  directml: boolean;
}) {
  const [audioIds, setAudioIds] = useState<string[]>([]);
  const [modelId, setModelId] = useState("");
  const [uploading, setUploading] = useState("");
  const [busy, setBusy] = useState(false);
  const [browse, setBrowse] = useState(false);
  const [pitch, setPitch] = useState(0);
  const [indexRate, setIndexRate] = useState(0.75);
  const [protect, setProtect] = useState(0.33);
  const [rms, setRms] = useState(0.25);
  const [pitchMethod, setPitchMethod] = useState("rmvpe");
  const [format, setFormat] = useState("wav");
  const [sampleRate, setSampleRate] = useState(0);
  const [speaker, setSpeaker] = useState(0);
  const [separate, setSeparate] = useState(false);
  const [vocalGain, setVocalGain] = useState(0);
  const [backingGain, setBackingGain] = useState(0);
  const selected = library.audio.filter((audio) => audioIds.includes(audio.id));
  const model = library.models.find((item) => item.id === modelId);
  const latestJobs = library.jobs
    .filter((job) => job.kind === "conversion")
    .slice(0, 3);

  async function addFiles(files: File[]) {
    if (!files.length) return;
    const ids: string[] = [];
    try {
      for (const [index, file] of files.entries()) {
        setUploading(`${index + 1}/${files.length} · ${file.name}`);
        const audio = await uploadAudio(file, (progress) =>
          setUploading(
            `${index + 1}/${files.length} · ${file.name} · ${progress} %`,
          ),
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

  async function convert() {
    setBusy(true);
    try {
      await send("/conversions", {
        audio_ids: selected.map((item) => item.id),
        model_id: modelId,
        pitch,
        pitch_method: pitchMethod,
        index_rate: indexRate,
        protect,
        rms_mix: rms,
        speaker_id: speaker,
        separate_vocals: separate,
        vocal_gain: vocalGain,
        instrumental_gain: backingGain,
        format,
        sample_rate: sampleRate,
      });
      await refresh();
      notify("Konvertierung zur Warteschlange hinzugefügt.");
    } catch (error) {
      notify(message(error), true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">
            <span /> DEIN LOKALES VOICE STUDIO
          </div>
          <h1>
            Dein Sound.
            <br />
            <em>Neue Stimme.</em>
          </h1>
          <p>Verwandle Sprache und Gesang mit deinen eigenen Voice-Modellen.</p>
        </div>
        <div className="hero-art" aria-hidden="true">
          <div className="sound-orbit">
            <AudioLines size={64} strokeWidth={1} />
          </div>
          <span className="art-label">CREATE SOMETHING YOU.</span>
        </div>
      </div>
      <div className="studio-grid">
        <div className="studio-main">
          <Panel
            title="Dein Audio"
            step="01"
            aside={
              <span className="badge">
                {selected.length
                  ? `${selected.length} Dateien · ${duration(selected.reduce((sum, item) => sum + item.duration, 0))}`
                  : "Sprache & Gesang"}
              </span>
            }
          >
            <Dropzone
              accept={AUDIO_ACCEPT}
              onFiles={addFiles}
              busy={uploading}
              title="Audio hier ablegen"
              subtitle="WAV, MP3, FLAC und mehr · Mehrere Dateien möglich"
            />
            {selected.length > 0 && (
              <div className="file-list">
                {selected.map((item) => (
                  <AudioRow
                    key={item.id}
                    item={item}
                    onRemove={() =>
                      setAudioIds((previous) =>
                        previous.filter((id) => id !== item.id),
                      )
                    }
                  />
                ))}
              </div>
            )}
            {library.audio.length > 0 && (
              <>
                <button
                  className="text-button library-link"
                  onClick={() => setBrowse(!browse)}
                >
                  <Layers3 size={15} /> Aus Audiobibliothek wählen{" "}
                  <ChevronDown size={14} />
                </button>
                {browse && (
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
            <div className="privacy-note">
              <span className="tiny-dot" /> Deine Dateien bleiben auf deinem
              Rechner.
            </div>
          </Panel>
          <Panel
            title="Klang anpassen"
            step="03"
            aside={<span className="subtle">Dein Feinschliff</span>}
          >
            <div className="preset-row">
              <button
                className={!separate ? "preset active" : "preset"}
                onClick={() => setSeparate(false)}
              >
                <Mic2 size={18} />
                <span>
                  <strong>Stimme pur</strong>
                  <small>Sprache oder isolierter Gesang</small>
                </span>
                {!separate && <span className="selected-dot" />}
              </button>
              <button
                className={separate ? "preset active" : "preset"}
                onClick={() => setSeparate(true)}
              >
                <AudioLines size={18} />
                <span>
                  <strong>Kompletter Song</strong>
                  <small>Gesang trennen & neu mischen</small>
                </span>
                {separate && <span className="selected-dot" />}
              </button>
            </div>
            {directml && separate && (
              <p className="info-note">
                Die Stimme wird auf deiner GPU ersetzt. Die vorherige
                Gesangstrennung nutzt im DirectML-Modus die CPU und kann länger
                dauern.
              </p>
            )}
            <div className="control-grid">
              <Slider
                label="Tonhöhe"
                value={pitch}
                min={-24}
                max={24}
                step={1}
                unit=" HT"
                onChange={setPitch}
                hint="0 behält die Melodie bei. ±12 entspricht einer Oktave."
              />
              <Slider
                label="Stimmenähnlichkeit"
                value={indexRate}
                min={0}
                max={1}
                onChange={setIndexRate}
                hint={
                  model?.index_path
                    ? "Wie stark der Stimmenindex die Klangfarbe prägt."
                    : "Für diesen Regler wird eine .index-Datei benötigt."
                }
              />
            </div>
            {separate && (
              <div className="mix-controls">
                <p className="info-note">
                  Hybrid Demucs trennt den Gesang. Du erhältst den fertigen Mix,
                  die neue Stimme und die Begleitung separat.
                </p>
                <div className="control-grid">
                  <Slider
                    label="Neue Stimme"
                    value={vocalGain}
                    min={-24}
                    max={12}
                    step={1}
                    unit=" dB"
                    onChange={setVocalGain}
                  />
                  <Slider
                    label="Begleitung"
                    value={backingGain}
                    min={-24}
                    max={12}
                    step={1}
                    unit=" dB"
                    onChange={setBackingGain}
                  />
                </div>
              </div>
            )}
            <details className="advanced">
              <summary>
                Erweiterte Einstellungen <ChevronDown size={15} />
              </summary>
              <div className="control-grid">
                <Slider
                  label="Konsonantenschutz"
                  value={protect}
                  min={0}
                  max={0.5}
                  onChange={setProtect}
                  hint="Kleinere Werte schützen Atemgeräusche. 0,5 deaktiviert den Schutz."
                />
                <Slider
                  label="Lautstärkeverlauf"
                  value={rms}
                  min={0}
                  max={1}
                  onChange={setRms}
                  hint="0 folgt dem Original, 1 dem konvertierten Audio."
                />
                <label className="field">
                  Pitch-Erkennung
                  <select
                    value={pitchMethod}
                    onChange={(event) => setPitchMethod(event.target.value)}
                  >
                    <option value="rmvpe">RMVPE · ausgewogen</option>
                    <option value="fcpe">FCPE · schnell</option>
                    <option value="pm">Parselmouth · CPU</option>
                  </select>
                </label>
                <label className="field">
                  Sprecher-ID
                  <input
                    type="number"
                    min="0"
                    max={Math.max(0, (model?.speakers ?? 1) - 1)}
                    value={speaker}
                    onChange={(event) => setSpeaker(Number(event.target.value))}
                  />
                </label>
              </div>
            </details>
          </Panel>
        </div>
        <aside className="studio-side">
          <Panel title="Deine neue Stimme" step="02">
            <label className="field">
              Voice-Modell
              <select
                value={modelId}
                onChange={(event) => {
                  setModelId(event.target.value);
                  setSpeaker(0);
                }}
              >
                <option value="">Modell auswählen …</option>
                {library.models.map((item) => (
                  <option value={item.id} key={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </label>
            {model ? (
              <div className="selected-model">
                <div className="model-avatar">
                  <AudioLines size={31} />
                </div>
                <h3>{model.name}</h3>
                <p>
                  RVC {model.version.toUpperCase()} <i>·</i>{" "}
                  {model.sample_rate / 1000} kHz
                </p>
                <span className="badge green">
                  {model.index_path
                    ? "Stimmenindex verbunden"
                    : "Modell bereit"}
                </span>
              </div>
            ) : (
              <div className="model-placeholder">
                <div className="model-avatar">
                  <Mic2 size={27} />
                </div>
                <p>Welchen Klang hast du im Kopf?</p>
                <small>
                  Füge ein .pth-Modell hinzu oder trainiere deine eigene Stimme.
                </small>
              </div>
            )}
            <button
              className="button secondary full"
              onClick={() => navigate("models")}
            >
              <Plus size={16} /> Modell hinzufügen
            </button>
          </Panel>
          <Panel title="Dein Export" className="export-panel">
            <div className="format-tabs" role="group" aria-label="Exportformat">
              {["wav", "flac", "mp3"].map((value) => (
                <button
                  key={value}
                  aria-pressed={format === value}
                  className={format === value ? "active" : ""}
                  onClick={() => setFormat(value)}
                >
                  {value.toUpperCase()}
                </button>
              ))}
            </div>
            <label className="field">
              Samplerate
              <select
                value={sampleRate}
                onChange={(event) => setSampleRate(Number(event.target.value))}
              >
                <option value="0">Wie das Voice-Modell</option>
                {[32000, 40000, 44100, 48000].map((value) => (
                  <option value={value} key={value}>
                    {value / 1000} kHz
                  </option>
                ))}
              </select>
            </label>
            <div className="export-summary">
              <span>{selected.length} Audiodateien</span>
              <span>{format === "mp3" ? "320 kbit/s" : "24 Bit"}</span>
            </div>
            <button
              className="button primary full"
              disabled={!selected.length || !model || !!uploading || busy}
              onClick={convert}
            >
              <Sparkles size={17} />
              {busy ? "Wird eingereiht …" : "Stimme verwandeln"}
              <ArrowRight size={17} />
            </button>
            <p className="caption">
              {!model
                ? "Wähle ein Voice-Modell, um loszulegen."
                : !selected.length
                  ? "Füge eine Audiodatei hinzu, um loszulegen."
                  : "Ergebnis direkt anhören und herunterladen."}
            </p>
          </Panel>
          <div className="tip-card">
            <Sparkles size={18} />
            <div>
              <strong>Ein guter Ausgangspunkt</strong>
              <p>
                Trockene, klare Stimmen liefern die besten Ergebnisse. Bei Musik
                übernimmt die Song-Option die Gesangstrennung.
              </p>
            </div>
          </div>
        </aside>
      </div>
      <div className="section-title">
        <h2>Deine letzten Konvertierungen</h2>
        <button className="text-button" onClick={() => navigate("results")}>
          Alle Ergebnisse <ArrowUpRightIcon />
        </button>
      </div>
      {latestJobs.length ? (
        <div className="jobs-grid">
          {latestJobs.map((job) => (
            <JobCard key={job.id} job={job} refresh={refresh} notify={notify} />
          ))}
        </div>
      ) : (
        <Empty title="Hier beginnt dein nächster Sound">
          Deine Konvertierungen erscheinen hier, sobald du einen Auftrag
          startest.
        </Empty>
      )}
    </>
  );
}

function ArrowUpRightIcon() {
  return <ArrowRight size={15} className="diagonal" />;
}

export { AUDIO_ACCEPT };
