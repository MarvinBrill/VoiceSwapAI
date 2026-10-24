"""Exercise checkpoint resume, long audio boundaries, alternate pitch and formats.

Run after scripts/smoke.py; reuses only its explicitly labeled test artifacts.
"""

import argparse
import io
import json
import time

import numpy as np
import soundfile as sf

from smoke import request, wait


def run(base, epochs=2):
    with open("test-results/smoke.json", encoding="utf-8") as file:
        previous = json.load(file)
    jobs = request(base, "/jobs").json()
    original = next(job for job in jobs if job["id"] == previous["training_job"])
    parameters = {
        key: value
        for key, value in original["parameters"].items()
        if key not in ("audio_ids", "project_name", "experiment_id")
    }
    parameters.update(epochs=epochs, resume_job_id=original["id"])
    resumed = request(base, "/training", method="POST", json=parameters).json()
    trained = wait(base, resumed["id"])
    source = request(base, f"/audio/{previous['audio_ids'][1]}/file")
    samples, rate = sf.read(io.BytesIO(source.content))
    long_audio = io.BytesIO()
    sf.write(long_audio, np.tile(samples, 8), rate, format="WAV", subtype="PCM_16")
    audio = request(
        base,
        "/audio",
        method="POST",
        files={"file": ("Smoke-Test-40s.wav", long_audio.getvalue(), "audio/wav")},
    ).json()
    body = {
        "audio_ids": [audio["id"]],
        "model_id": trained["model_id"],
        "pitch_method": "fcpe",
        "pitch": 12,
        "format": "flac",
        "sample_rate": 48000,
    }
    cancelled = request(base, "/conversions", method="POST", json=body).json()
    for _ in range(30):
        current = next(job for job in request(base, "/jobs").json() if job["id"] == cancelled["id"])
        if current["status"] == "running":
            break
        time.sleep(0.5)
    result = request(base, f"/jobs/{cancelled['id']}/cancel", method="POST").json()
    assert result["status"] == "cancelled"
    print("Running job cancelled", flush=True)
    for options, duration in (
        (body, 40),
        (
            {
                **body,
                "audio_ids": [previous["audio_ids"][1]],
                "pitch_method": "pm",
                "format": "mp3",
                "pitch": -12,
                "sample_rate": 44100,
            },
            5,
        ),
    ):
        job = request(base, "/conversions", method="POST", json=options).json()
        wait(base, job["id"])
        result = request(base, f"/jobs/{job['id']}/outputs/0")
        waveform, output_rate = sf.read(io.BytesIO(result.content))
        assert abs(len(waveform) / output_rate - duration) < 0.15
        assert output_rate == options["sample_rate"]
        assert np.isfinite(waveform).all() and np.max(np.abs(waveform)) > 0.00001
        print(f"Verified {options['pitch_method']} / {options['format']} / {duration}s", flush=True)
    print("EXTENDED CHECKS PASSED", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:7860")
    parser.add_argument("--epochs", type=int, default=2, help="Neue Gesamtepochenzahl beim Fortsetzen")
    args = parser.parse_args()
    run(args.url, args.epochs)
