import logging
import sys
import traceback

from .runtime import configure_engine
from .store import Store, now


def run(job_id):
    configure_engine()
    logging.basicConfig(level=logging.INFO)
    store = Store()
    job = store.get("job", job_id)

    def report(phase, progress):
        store.update("job", job_id, phase=phase, progress=round(progress, 1))
        print(phase, flush=True)

    try:
        if job["kind"] == "setup":
            from .assets import MANIFEST, ensure_assets

            ensure_assets(list(MANIFEST["files"]), report)
            result = {}
        elif job["kind"] == "conversion":
            from .conversion import run_conversion

            result = run_conversion(store, job, report)
        else:
            from .training import run_training

            result = run_training(store, job, report)
        store.update(
            "job",
            job_id,
            status="completed",
            phase="Abgeschlossen",
            progress=100,
            finished_at=now(),
            **result,
        )
    except Exception as error:
        traceback.print_exc()
        store.update(
            "job", job_id, status="failed", phase="Fehlgeschlagen", error=str(error), finished_at=now()
        )
        sys.exit(1)


if __name__ == "__main__":
    run(sys.argv[1])
