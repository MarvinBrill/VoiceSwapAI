from pathlib import Path

from app import main


def test_audio_upload_deduplicates_and_serves_range(client, monkeypatch):
    monkeypatch.setattr(main, "probe", lambda path: {"duration": 2, "sample_rate": 44100, "channels": 1})
    first = client.post("/api/audio", files={"file": ("../voice.wav", b"abcdefghijk", "audio/wav")})
    assert first.status_code == 201
    audio = first.json()
    assert audio["name"] == "voice.wav"
    assert ".." not in audio["path"]
    second = client.post("/api/audio", files={"file": ("renamed.wav", b"abcdefghijk", "audio/wav")})
    assert second.json()["id"] == audio["id"]
    response = client.get(f"/api/audio/{audio['id']}/file", headers={"Range": "bytes=2-5"})
    assert response.status_code == 206
    assert response.content == b"cdef"


def test_invalid_uploads_do_not_enter_library(client):
    response = client.post("/api/audio", files={"file": ("payload.exe", b"no", "audio/wav")})
    assert response.status_code == 400
    response = client.post("/api/audio", files={"file": ("empty.wav", b"", "audio/wav")})
    assert response.status_code == 400
    assert client.get("/api/audio").json() == []


def test_foreign_origin_cannot_control_local_app(client):
    response = client.post(
        "/api/projects", json={"name": "bad"}, headers={"Origin": "https://untrusted.example"}
    )
    assert response.status_code == 403


def test_project_validation_and_snapshot(client, records):
    audio, _ = records
    assert client.post("/api/projects", json={"name": "   "}).status_code == 422
    assert client.post("/api/projects", json={"name": "test", "audio_ids": ["missing"]}).status_code == 404
    project = client.post("/api/projects", json={"name": "My voice", "audio_ids": [audio["id"]]}).json()
    job = client.post("/api/training", json={"project_id": project["id"], "epochs": 1}).json()
    assert job["status"] == "queued"
    assert job["parameters"]["audio_ids"] == [audio["id"]]
    client.put(f"/api/projects/{project['id']}", json={"name": "changed", "audio_ids": []})
    assert main.store.get("job", job["id"])["parameters"]["audio_ids"] == [audio["id"]]
    assert client.delete(f"/api/audio/{audio['id']}").status_code == 409


def test_conversion_validation_and_model_lock(client, records):
    audio, model = records
    body = {"audio_ids": [audio["id"]], "model_id": model["id"]}
    assert client.post("/api/conversions", json={**body, "pitch": 25}).status_code == 422
    assert client.post("/api/conversions", json={**body, "speaker_id": 1}).status_code == 400
    assert client.post("/api/conversions", json={**body, "format": "exe"}).status_code == 422
    response = client.post("/api/conversions", json=body)
    assert response.status_code == 202
    assert client.delete(f"/api/models/{model['id']}").status_code == 409
    job = response.json()
    assert client.get(f"/api/jobs/{job['id']}/outputs/-1").status_code == 404
    assert client.post(f"/api/jobs/{job['id']}/cancel").json()["status"] == "cancelled"


def test_unsafe_or_wrong_checkpoint_rejected(client, tmp_path):
    import torch

    path = tmp_path / "wrong.pth"
    torch.save({"model": {"weights": torch.ones(2)}}, path)
    with path.open("rb") as file:
        response = client.post("/api/models", files={"file": ("wrong.pth", file)})
    assert response.status_code == 400
    assert client.get("/api/models").json() == []


def test_pickle_globals_are_never_executed(client, tmp_path):
    import torch

    marker = tmp_path / "must-not-exist"

    class Unsafe:
        def __reduce__(self):
            return Path.touch, (marker,)

    payload = tmp_path / "unsafe.pth"
    torch.save(Unsafe(), payload)
    with payload.open("rb") as file:
        response = client.post("/api/models", files={"file": ("unsafe.pth", file)})
    assert response.status_code == 400
    assert not marker.exists()


def test_resume_requires_checkpoints(client, records):
    audio, _ = records
    project = client.post("/api/projects", json={"name": "Voice", "audio_ids": [audio["id"]]}).json()
    job = client.post("/api/training", json={"project_id": project["id"]}).json()
    main.store.update("job", job["id"], status="failed")
    result = client.post("/api/training", json={"project_id": project["id"], "resume_job_id": job["id"]})
    assert result.status_code == 400
