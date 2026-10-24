"""End-to-end hardware smoke test using only locally synthesized test audio.

Usage: python scripts/smoke.py --url http://localhost:7860
Leaves clearly labeled test models/results in the app for inspection.
This checks execution, persistence and audio integrity, not voice quality.
"""

import argparse
import io
import json
import tempfile
import time
from pathlib import Path

import numpy as np
import requests
import soundfile as sf


def request(base, path, **options):
    response = requests.request(options.pop("method", "GET"), base + "/api" + path, timeout=90, **options)
    if not response.ok:
        raise RuntimeError(f"{response.status_code}: {response.text}")
    return response


def wait(base, job_id, timeout=1800):
    deadline = time.monotonic() + timeout
    previous = None
    while time.monotonic() < deadline:
        jobs = request(base, "/jobs").json()
        job = next(item for item in jobs if item["id"] == job_id)
        state = (job["status"], job["phase"])
        if state != previous:
            print(job_id[:8], *state, flush=True)
            previous = state
        if job["status"] == "completed":
            return job
        if job["status"] in ("failed", "cancelled", "interrupted"):
            print(request(base, f"/jobs/{job_id}/log").json()["text"])
            raise RuntimeError(job.get("error") or job["status"])
        time.sleep(3)
    raise TimeoutError(job_id)


def run(base, separate=False):
    system = request(base, "/system").json()
    print(json.dumps(system["gpu"], indent=2), flush=True)
    assert not system["gpu"].get("error")
    setup = request(base, "/setup", method="POST").json()
    wait(base, setup["id"])
    with tempfile.TemporaryDirectory(prefix="voiceswap-smoke-") as directory:
        audio_ids = []
        for number, seconds in enumerate((1, 5)):
            rate = 40000
            time_axis = np.arange(rate * seconds) / rate
            frequency = 150 + number * 50 + 8 * np.sin(2 * np.pi * 4 * time_axis)
            phase = 2 * np.pi * np.cumsum(frequency) / rate
            waveform = sum(np.sin(phase * harmonic) / harmonic**1.4 for harmonic in range(1, 9))
            waveform = (0.6 + 0.4 * np.sin(2 * np.pi * 2 * time_axis)) * waveform * 0.25
            path = Path(directory) / f"Smoke-Test-{seconds}s.wav"
            sf.write(path, waveform, rate)
            with path.open("rb") as source:
                audio = request(
                    base, "/audio", method="POST", files={"file": (path.name, source, "audio/wav")}
                ).json()
            audio_ids.append(audio["id"])
        project = request(
            base,
            "/projects",
            method="POST",
            json={"name": "Smoke-Test · synthetische Teststimme", "audio_ids": audio_ids},
        ).json()
        training = request(
            base,
            "/training",
            method="POST",
            json={
                "project_id": project["id"],
                "epochs": 1,
                "batch_size": 1,
                "save_every": 1,
                "sample_rate": 40000,
            },
        ).json()
        trained = wait(base, training["id"])
        exported = request(base, f"/models/{trained['model_id']}/file")
        assert len(exported.content) > 1000000
        index = request(base, f"/models/{trained['model_id']}/file?index=true")
        assert len(index.content) > 1000
        # Re-import the actual trained artifact through the public upload path.
        imported = request(
            base, "/models", method="POST", files={"file": ("Smoke-Reimport.pth", exported.content)}
        ).json()
        request(
            base,
            f"/models/{imported['id']}/index",
            method="POST",
            files={"file": ("Smoke-Reimport.index", index.content)},
        )
        conversion = request(
            base,
            "/conversions",
            method="POST",
            json={
                "audio_ids": audio_ids,
                "model_id": imported["id"],
                "format": "wav",
                "separate_vocals": separate,
            },
        ).json()
        converted = wait(base, conversion["id"])
        assert len(converted["outputs"]) == (6 if separate else 2)
        for number, output in enumerate(converted["outputs"]):
            response = request(base, f"/jobs/{converted['id']}/outputs/{number}?download=true")
            samples, rate = sf.read(io.BytesIO(response.content))
            assert np.isfinite(samples).all()
            assert len(samples) / rate >= 0.95
            if output["kind"] == "mix":
                assert np.max(np.abs(samples)) > 0.00001
            print(f"Verified {output['name']}: {len(samples) / rate:.2f}s @ {rate} Hz", flush=True)
        report = {
            "gpu": system["gpu"],
            "training_job": trained["id"],
            "model_id": trained["model_id"],
            "conversion_job": converted["id"],
            "project_id": project["id"],
            "audio_ids": audio_ids,
        }
        Path("test-results").mkdir(exist_ok=True)
        Path("test-results/smoke.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("SMOKE PASSED", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:7860")
    parser.add_argument("--separate", action="store_true")
    args = parser.parse_args()
    run(args.url, args.separate)
