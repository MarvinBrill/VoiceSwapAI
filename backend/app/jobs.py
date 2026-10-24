import os
import subprocess
import sys
import threading

import psutil

from .settings import DATA, ROOT
from .store import now

TERMINAL = {"completed", "failed", "cancelled", "interrupted"}


class JobQueue:
    def __init__(self, store):
        self.store = store
        self.lock = threading.RLock()
        self.stopped = threading.Event()
        self.wakeup = threading.Event()
        self.process = None
        self.current_id = None

    def start(self):
        for job in self.store.list("job"):
            if job["status"] == "running":
                self.store.update(
                    "job",
                    job["id"],
                    status="interrupted",
                    phase="Durch Neustart unterbrochen",
                    finished_at=now(),
                )
        self.thread = threading.Thread(target=self.run, daemon=True, name="voice-jobs")
        self.thread.start()

    def submit(self, kind, title, parameters):
        job = self.store.create(
            "job",
            kind=kind,
            title=title,
            parameters=parameters,
            status="queued",
            phase="Wartet",
            progress=0,
            outputs=[],
            error=None,
        )
        self.wakeup.set()
        return job

    def stop_process(self):
        if self.process and self.process.poll() is None:
            try:
                parent = psutil.Process(self.process.pid)
                children = parent.children(recursive=True)
                for child in children:
                    try:
                        child.kill()
                    except psutil.NoSuchProcess:
                        pass
                parent.kill()
                self.process.wait(timeout=10)
            except (psutil.NoSuchProcess, subprocess.TimeoutExpired):
                pass

    def cancel(self, job_id):
        with self.lock:
            job = self.store.get("job", job_id)
            if job["status"] in TERMINAL:
                return job
            if self.current_id == job_id:
                self.stop_process()
            return self.store.update(
                "job", job_id, status="cancelled", phase="Abgebrochen", finished_at=now()
            )

    def close(self):
        self.stopped.set()
        self.wakeup.set()
        with self.lock:
            self.stop_process()
        self.thread.join(timeout=15)

    def run(self):
        while not self.stopped.is_set():
            with self.lock:
                pending = [j for j in reversed(self.store.list("job")) if j["status"] == "queued"]
                job = pending[0] if pending else None
                if job:
                    self.current_id = job["id"]
                    folder = DATA / "jobs" / job["id"]
                    folder.mkdir(exist_ok=True)
                    self.store.update(
                        "job", job["id"], status="running", phase="Wird gestartet", started_at=now()
                    )
                    env = {**os.environ, "PYTHONPATH": str(ROOT), "PYTHONUNBUFFERED": "1"}
                    try:
                        with (folder / "process.log").open("ab") as log:
                            self.process = subprocess.Popen(
                                [sys.executable, "-m", "app.worker", job["id"]],
                                cwd=ROOT,
                                env=env,
                                stdout=log,
                                stderr=subprocess.STDOUT,
                            )
                    except OSError as error:
                        self.store.update(
                            "job", job["id"], status="failed", error=str(error), finished_at=now()
                        )
                        self.current_id = None
                        continue
            if not job:
                self.wakeup.wait(timeout=2)
                self.wakeup.clear()
                continue

            code = self.process.wait()
            with self.lock:
                latest = self.store.get("job", job["id"])
                if latest["status"] == "running":
                    status = "interrupted" if self.stopped.is_set() else "failed"
                    self.store.update(
                        "job",
                        job["id"],
                        status=status,
                        error=f"Arbeitsprozess wurde beendet (Code {code}). Details im Protokoll.",
                        finished_at=now(),
                    )
                self.process = None
                self.current_id = None
