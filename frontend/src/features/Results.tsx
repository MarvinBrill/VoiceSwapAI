import { useState } from "react";
import { Empty } from "../components/Controls";
import { JobCard } from "../components/JobCard";
import type { Job, Library, Notify } from "../types";

export function Results({
  library,
  refresh,
  notify,
  resume,
}: {
  library: Library;
  refresh: () => Promise<void>;
  notify: Notify;
  resume: (job: Job) => void;
}) {
  const [filter, setFilter] = useState("all");
  const jobs = library.jobs.filter(
    (job) => filter === "all" || job.kind === filter,
  );
  return (
    <>
      <div className="page-heading compact">
        <div>
          <div className="eyebrow">DEIN KREATIVER VERLAUF</div>
          <h1>
            Alles, was du erschaffst<span className="heading-dot">.</span>
          </h1>
          <p>
            Aufträge verfolgen, Ergebnisse vorhören und deine Dateien mitnehmen.
          </p>
        </div>
      </div>
      <div className="filter-tabs">
        {[
          ["all", "Alle Aufträge"],
          ["conversion", "Konvertierungen"],
          ["training", "Training"],
          ["setup", "Einrichtung"],
        ].map(([value, label]) => (
          <button
            key={value}
            className={filter === value ? "active" : ""}
            onClick={() => setFilter(value)}
          >
            {label}
          </button>
        ))}
      </div>
      {jobs.length ? (
        <div className="jobs-grid">
          {jobs.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              refresh={refresh}
              notify={notify}
              resume={resume}
            />
          ))}
        </div>
      ) : (
        <Empty title="Noch ganz am Anfang">
          Starte eine Konvertierung oder ein Training. Hier behältst du alles im
          Blick.
        </Empty>
      )}
    </>
  );
}
