import { useId, useState } from "react";
import {
  ArrowDownToLine,
  Check,
  ChevronDown,
  ChevronUp,
  Clock3,
  LoaderCircle,
  Square,
  TriangleAlert,
} from "lucide-react";
import { api, message, send } from "../api";
import type { Job, Notify } from "../types";

const labels = {
  queued: "Wartet",
  running: "In Arbeit",
  completed: "Fertig",
  failed: "Fehlgeschlagen",
  cancelled: "Abgebrochen",
  interrupted: "Unterbrochen",
};

export function JobCard({
  job,
  refresh,
  notify,
  resume,
}: {
  job: Job;
  refresh: () => Promise<void>;
  notify: Notify;
  resume?: (job: Job) => void;
}) {
  const [log, setLog] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [showAdditionalOutputs, setShowAdditionalOutputs] = useState(false);
  const outputsId = useId();
  const active = job.status === "running" || job.status === "queued";
  const failed = job.status === "failed" || job.status === "interrupted";
  const hasMix = job.outputs.some((output) => output.kind === "mix");
  const additionalOutputs = new Set(
    job.outputs.filter(
      (output) => hasMix && ["vocal", "instrumental"].includes(output.kind),
    ),
  );

  async function cancel() {
    setBusy(true);
    try {
      await send(`/jobs/${job.id}/cancel`);
      await refresh();
    } catch (error) {
      notify(message(error), true);
    } finally {
      setBusy(false);
    }
  }

  async function showLog() {
    if (log !== null) {
      setLog(null);
      return;
    }
    try {
      const result = await api<{ text: string }>(`/jobs/${job.id}/log`);
      setLog(result.text || "Noch keine Protokolleinträge.");
    } catch (error) {
      notify(message(error), true);
    }
  }

  return (
    <article className={`job-card ${failed ? "has-error" : ""}`}>
      <div className="job-heading">
        <div className={`job-icon ${job.status}`}>
          {job.status === "completed" ? (
            <Check size={19} />
          ) : failed ? (
            <TriangleAlert size={19} />
          ) : active ? (
            <LoaderCircle
              size={19}
              className={job.status === "running" ? "spin" : ""}
            />
          ) : (
            <Clock3 size={19} />
          )}
        </div>
        <div className="grow">
          <h3>{job.title}</h3>
          <p>
            {new Date(job.created_at).toLocaleString("de-DE", {
              dateStyle: "medium",
              timeStyle: "short",
            })}
          </p>
        </div>
        <span className={`badge ${job.status === "completed" ? "green" : ""}`}>
          {labels[job.status]}
        </span>
        {active && (
          <button
            className="icon-button"
            disabled={busy}
            onClick={cancel}
            aria-label="Auftrag abbrechen"
          >
            <Square size={15} />
          </button>
        )}
      </div>
      {active && (
        <>
          <div className="progress-label">
            <span>{job.phase}</span>
            <strong>{Math.round(job.progress)} %</strong>
          </div>
          <progress max="100" value={job.progress} aria-label={job.phase} />
        </>
      )}
      {job.error && <p className="error-detail">{job.error}</p>}
      {job.model_id && (
        <a
          className="button secondary"
          href={`/api/models/${job.model_id}/file`}
        >
          <ArrowDownToLine size={16} /> Trainiertes .pth herunterladen
        </a>
      )}
      {job.outputs.length > 0 && (
        <div className="output-list" id={outputsId}>
          {job.outputs.map((output, index) => {
            if (additionalOutputs.has(output) && !showAdditionalOutputs)
              return null;
            return (
              <div className="output" key={output.path}>
                <div>
                  <strong>{output.name}</strong>
                  <a
                    href={`/api/jobs/${job.id}/outputs/${index}?download=true`}
                    className="icon-button"
                    aria-label={`${output.name} herunterladen`}
                  >
                    <ArrowDownToLine size={17} />
                  </a>
                </div>
                <audio
                  controls
                  preload="none"
                  src={`/api/jobs/${job.id}/outputs/${index}`}
                  aria-label={output.name}
                />
              </div>
            );
          })}
          {additionalOutputs.size > 0 && (
            <button
              className="text-button"
              aria-expanded={showAdditionalOutputs}
              aria-controls={outputsId}
              onClick={() => setShowAdditionalOutputs(!showAdditionalOutputs)}
            >
              {showAdditionalOutputs ? (
                <ChevronUp size={14} />
              ) : (
                <ChevronDown size={14} />
              )}
              {showAdditionalOutputs ? "Weniger anzeigen" : "Mehr anzeigen"}
            </button>
          )}
        </div>
      )}
      <div className="job-footer">
        <button className="text-button" onClick={showLog}>
          <ChevronDown size={14} />{" "}
          {log === null ? "Protokoll anzeigen" : "Protokoll schließen"}
        </button>
        {job.can_resume && resume && (
          <button className="text-button accent" onClick={() => resume(job)}>
            Training fortsetzen ↗
          </button>
        )}
      </div>
      {log !== null && <pre className="log-view">{log}</pre>}
    </article>
  );
}
