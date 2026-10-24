import hashlib
import os
import shutil
import subprocess
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from starlette.middleware.trustedhost import TrustedHostMiddleware

from . import assets
from .audio import AUDIO_EXTENSIONS, probe
from .devices import device_info
from .jobs import JobQueue, TERMINAL
from .models import inspect_index, inspect_model
from .schemas import ConversionRequest, ProjectRequest, TrainingRequest
from .settings import DATA, FRONTEND, data_path
from .store import Store

store = Store()
queue = JobQueue(store)


@asynccontextmanager
async def lifespan(app):
    queue.start()
    if os.getenv("VOICESWAP_AUTO_SETUP", "1") == "1" and any(not item["ready"] for item in assets.status()):
        if not any(j["kind"] == "setup" and j["status"] not in TERMINAL for j in store.list("job")):
            queue.submit("setup", "Basisdateien einrichten", {})
    yield
    queue.close()


app = FastAPI(title="VoiceSwapAI", lifespan=lifespan)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=os.getenv("VOICESWAP_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]").split(","),
)


@app.middleware("http")
async def local_requests(request: Request, call_next):
    origin = request.headers.get("origin")
    if request.method not in ("GET", "HEAD", "OPTIONS") and origin:
        allowed = {request.headers.get("host"), "localhost:5173", "127.0.0.1:5173"}
        if urlparse(origin).netloc not in allowed:
            return JSONResponse(
                {"detail": "Fremde Webseiten dürfen diese lokale App nicht steuern."}, status_code=403
            )
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@app.exception_handler(KeyError)
async def missing_item(request, error):
    return JSONResponse({"detail": "Eintrag nicht gefunden."}, status_code=404)


@app.exception_handler(ValueError)
async def invalid_input(request, error):
    return JSONResponse({"detail": str(error)}, status_code=400)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/system")
def system():
    usage = shutil.disk_usage(DATA)
    return {
        "gpu": device_info(),
        "assets": assets.status(),
        "disk_free_gb": round(usage.free / 1024**3, 1),
        "version": "0.1.0",
    }


@app.post("/api/setup", status_code=202)
def setup():
    for job in store.list("job"):
        if job["kind"] == "setup" and job["status"] not in TERMINAL:
            return job
    return queue.submit("setup", "Basisdateien einrichten", {})


async def save_upload(upload, folder, allowed):
    name = Path((upload.filename or "Datei").replace("\\", "/")).name
    extension = Path(name).suffix.lower()
    if extension not in allowed:
        raise ValueError(f"Nicht unterstützter Dateityp: {extension}")
    destination = DATA / folder / f"{uuid.uuid4().hex}{extension}"
    digest = hashlib.sha256()
    try:
        with destination.open("wb") as output:
            while chunk := await upload.read(1024 * 1024):
                output.write(chunk)
                digest.update(chunk)
        if not destination.stat().st_size:
            raise ValueError("Die Datei ist leer.")
        return destination, name, digest.hexdigest()
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    finally:
        await upload.close()


@app.get("/api/audio")
def list_audio():
    return store.list("audio")


@app.post("/api/audio", status_code=201)
async def upload_audio(file: UploadFile = File()):
    path, name, digest = await save_upload(file, "uploads", AUDIO_EXTENSIONS)
    try:
        for existing in store.list("audio"):
            if existing.get("sha256") == digest:
                path.unlink()
                return existing
        info = await run_in_threadpool(probe, path)
        return store.create(
            "audio",
            name=name,
            path=str(path.relative_to(DATA)),
            sha256=digest,
            size=path.stat().st_size,
            **info,
        )
    except (subprocess.SubprocessError, StopIteration) as error:
        path.unlink(missing_ok=True)
        raise ValueError("Die Datei konnte nicht als Audio gelesen werden.") from error
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def require_unreferenced(kind, item_id):
    for job in store.list("job"):
        if job["status"] in TERMINAL:
            continue
        parameters = job["parameters"]
        referenced = (
            parameters.get("model_id") == item_id
            if kind == "model"
            else item_id in parameters.get("audio_ids", [])
        )
        if referenced:
            raise HTTPException(409, "Der Eintrag wird von einem wartenden oder laufenden Auftrag verwendet.")


@app.delete("/api/audio/{audio_id}")
def delete_audio(audio_id: str):
    require_unreferenced("audio", audio_id)
    if any(audio_id in project["audio_ids"] for project in store.list("project")):
        raise HTTPException(409, "Die Datei gehört zu einem Trainingsprojekt. Bitte dort zuerst entfernen.")
    audio = store.get("audio", audio_id)
    data_path(audio["path"]).unlink(missing_ok=True)
    store.delete("audio", audio_id)
    return {"deleted": True}


def file_response(path, name=None, download=False):
    if not path.is_file():
        raise HTTPException(404, "Datei nicht gefunden.")
    return FileResponse(
        path, filename=name or path.name, content_disposition_type="attachment" if download else "inline"
    )


@app.get("/api/audio/{audio_id}/file")
def audio_file(audio_id: str, download: bool = False):
    audio = store.get("audio", audio_id)
    return file_response(data_path(audio["path"]), audio["name"], download)


@app.get("/api/models")
def list_models():
    return store.list("model")


@app.post("/api/models", status_code=201)
async def upload_model(file: UploadFile = File(), name: str = Form("")):
    path, filename, digest = await save_upload(file, "models", {".pth"})
    try:
        for existing in store.list("model"):
            if existing.get("sha256") == digest:
                path.unlink()
                return existing
        info = await run_in_threadpool(inspect_model, path)
        return store.create(
            "model",
            name=(name.strip() or Path(filename).stem)[:100],
            path=str(path.relative_to(DATA)),
            sha256=digest,
            size=path.stat().st_size,
            index_path=None,
            origin="imported",
            **info,
        )
    except BaseException:
        path.unlink(missing_ok=True)
        raise


@app.post("/api/models/{model_id}/index")
async def upload_index(model_id: str, file: UploadFile = File()):
    require_unreferenced("model", model_id)
    model = store.get("model", model_id)
    path, _, _ = await save_upload(file, "models", {".index"})
    try:
        await run_in_threadpool(inspect_index, path, 768 if model["version"] == "v2" else 256)
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    previous = model.get("index_path")
    updated = store.update("model", model_id, index_path=str(path.relative_to(DATA)))
    if previous:
        data_path(previous).unlink(missing_ok=True)
    return updated


@app.get("/api/models/{model_id}/file")
def model_file(model_id: str, index: bool = False):
    model = store.get("model", model_id)
    relative = model.get("index_path") if index else model["path"]
    if not relative:
        raise HTTPException(404, "Kein Index vorhanden.")
    name = Path(model["name"].replace("\\", "/")).name + (".index" if index else ".pth")
    return file_response(data_path(relative), name, True)


@app.delete("/api/models/{model_id}")
def delete_model(model_id: str):
    require_unreferenced("model", model_id)
    model = store.get("model", model_id)
    for key in ("path", "index_path"):
        if model.get(key):
            data_path(model[key]).unlink(missing_ok=True)
    store.delete("model", model_id)
    return {"deleted": True}


@app.get("/api/projects")
def list_projects():
    return store.list("project")


def verify_audio(ids):
    for audio_id in set(ids):
        store.get("audio", audio_id)


@app.post("/api/projects", status_code=201)
def create_project(body: ProjectRequest):
    verify_audio(body.audio_ids)
    return store.create("project", name=body.name, audio_ids=list(dict.fromkeys(body.audio_ids)))


@app.put("/api/projects/{project_id}")
def update_project(project_id: str, body: ProjectRequest):
    verify_audio(body.audio_ids)
    return store.update("project", project_id, name=body.name, audio_ids=list(dict.fromkeys(body.audio_ids)))


@app.get("/api/jobs")
def list_jobs():
    result = store.list("job")
    for job in result:
        folder = DATA / "training" / job.get("experiment_id", job["id"])
        job["can_resume"] = (
            job["kind"] == "training"
            and job["status"] in TERMINAL
            and any(folder.glob("G_*.pth"))
            and any(folder.glob("D_*.pth"))
        )
    return result


@app.post("/api/conversions", status_code=202)
def conversion(body: ConversionRequest):
    verify_audio(body.audio_ids)
    model = store.get("model", body.model_id)
    if body.speaker_id >= model["speakers"]:
        raise ValueError("Diese Sprecher-ID existiert im Modell nicht.")
    return queue.submit("conversion", f"{model['name']} · {len(body.audio_ids)} Audio(s)", body.model_dump())


@app.post("/api/training", status_code=202)
def training(body: TrainingRequest):
    project = store.get("project", body.project_id)
    if not project["audio_ids"]:
        raise ValueError("Bitte mindestens eine Audiodatei zum Projekt hinzufügen.")
    verify_audio(project["audio_ids"])
    parameters = {**body.model_dump(), "audio_ids": project["audio_ids"], "project_name": project["name"]}
    if body.resume_job_id:
        previous = store.get("job", body.resume_job_id)
        if previous["kind"] != "training" or previous["status"] not in TERMINAL:
            raise ValueError("Dieser Trainingslauf kann nicht fortgesetzt werden.")
        for key in ("project_id", "sample_rate", "pitch_method", "learning_rate"):
            if previous["parameters"][key] != parameters[key]:
                raise ValueError(
                    "Beim Fortsetzen müssen Projekt, Samplerate, Lernrate und Pitch-Methode gleich bleiben."
                )
        experiment = previous.get("experiment_id", previous["id"])
        folder = DATA / "training" / experiment
        if not any(folder.glob("G_*.pth")) or not any(folder.glob("D_*.pth")):
            raise ValueError("Noch kein vollständiger Trainings-Checkpoint vorhanden.")
        progress_path = folder / "progress.json"
        if progress_path.exists():
            import json

            epoch = json.loads(progress_path.read_text())["epoch"]
            if body.epochs <= epoch:
                raise ValueError(f"Zum Fortsetzen mehr als {epoch} Gesamtepochen angeben.")
        parameters["experiment_id"] = experiment
        parameters["audio_ids"] = previous["parameters"]["audio_ids"]
    return queue.submit("training", f"Training · {project['name']}", parameters)


@app.post("/api/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    return queue.cancel(job_id)


@app.get("/api/jobs/{job_id}/log")
def job_log(job_id: str):
    job = store.get("job", job_id)
    paths = [DATA / "jobs" / job_id / "process.log"]
    if job["kind"] == "training":
        folder = DATA / "training" / job.get("experiment_id", job_id)
        paths.extend([folder / "train.log", folder / "console.log"])
    chunks = []
    for path in paths:
        if path.is_file():
            with path.open("rb") as file:
                file.seek(max(0, path.stat().st_size - 16000))
                chunks.append(path.name + "\n" + file.read().decode("utf-8", errors="replace"))
    return {"text": "\n\n".join(chunks)}


@app.get("/api/jobs/{job_id}/outputs/{output_index}")
def output_file(job_id: str, output_index: int, download: bool = False):
    job = store.get("job", job_id)
    if output_index < 0 or output_index >= len(job["outputs"]):
        raise HTTPException(404, "Ausgabe nicht gefunden.")
    output = job["outputs"][output_index]
    path = data_path(output["path"])
    name = Path(output["name"].replace("\\", "/")).name + path.suffix
    return file_response(path, name, download)


if FRONTEND.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")
