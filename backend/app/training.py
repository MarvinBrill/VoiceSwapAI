import gc
import json
import os
import shutil
import subprocess
import sys
import time
import uuid

import numpy as np
import soundfile as sf
import torch

from .assets import asset_path, base_assets, ensure_assets
from .audio import decode
from .devices import select_device
from .models import inspect_model
from .settings import DATA, ENGINE, ROOT, data_path


def prepare_dataset(store, audio_ids, folder, rate, report):
    import librosa
    from scipy.signal import butter, sosfilt

    ground = folder / "0_gt_wavs"
    low_rate = folder / "1_16k_wavs"
    ground.mkdir(exist_ok=True)
    low_rate.mkdir(exist_ok=True)
    highpass = butter(5, 48, "highpass", fs=rate, output="sos")
    count = 0
    for number, audio_id in enumerate(audio_ids):
        audio = store.get("audio", audio_id)
        decoded = folder / "decoded.wav"
        decode(data_path(audio["path"]), decoded, rate)
        with sf.SoundFile(decoded) as source:
            for block_number, block in enumerate(
                source.blocks(blocksize=int(rate * 3.7), overlap=int(rate * 0.3), dtype="float32")
            ):
                filtered = sosfilt(highpass, block).astype(np.float32)
                intervals = librosa.effects.split(filtered, top_db=42)
                for segment_number, (start, end) in enumerate(intervals):
                    clip = filtered[start:end]
                    if len(clip) < int(rate * 0.4) or np.max(np.abs(clip)) < 0.0001:
                        continue
                    # Keep short user clips; the sampler also accepts <1 s records.
                    clip = clip / max(np.max(np.abs(clip)), 1e-6) * 0.9
                    key = f"{number:06d}_{block_number:06d}_{segment_number}"
                    sf.write(ground / f"{key}.wav", clip, rate, subtype="PCM_16")
                    sf.write(
                        low_rate / f"{key}.wav",
                        librosa.resample(clip, orig_sr=rate, target_sr=16000),
                        16000,
                        subtype="FLOAT",
                    )
                    count += 1
                report(
                    f"Audio vorbereiten · {audio['name']} · {count} Abschnitte",
                    10 + 12 * (number + source.tell() / len(source)) / len(audio_ids),
                )
        decoded.unlink()
    if count == 0:
        raise ValueError(
            "Keine nutzbaren Sprachabschnitte gefunden. Bitte hörbare Sprache oder trockenen Gesang bereitstellen."
        )


def extract_features(folder, device, method, report):
    from infer.hubert import extract_hubert_features, hubert_audio_requires_normalization, load_hubert_model
    from infer.vc.pipeline import Pipeline
    from configs.config import Config

    feature_dir = folder / "3_feature768"
    coarse_dir = folder / "2a_f0"
    pitch_dir = folder / "2b-f0nsf"
    for path in (feature_dir, coarse_dir, pitch_dir):
        path.mkdir(exist_ok=True)
    hubert = load_hubert_model(device, False)
    pitch_config = Config()
    pitch_config.is_half = False
    pipeline = Pipeline(40000, pitch_config)
    normalize = hubert_audio_requires_normalization()
    paths = sorted((folder / "1_16k_wavs").glob("*.wav"))
    rows = []
    for number, path in enumerate(paths):
        waveform, _ = sf.read(path, dtype="float32")
        source = torch.from_numpy(waveform).to(device)
        if normalize:
            source = torch.nn.functional.layer_norm(source, source.shape)
        # DirectML does not support inference tensors' version-counter rules.
        with torch.no_grad() if device.startswith("privateuseone") else torch.inference_mode():
            features = extract_hubert_features(hubert, source[None], "v2").squeeze(0).float().cpu().numpy()
            pitch, continuous = pipeline.get_f0(waveform, len(waveform) // 160, 0, method)
        if not np.isfinite(features).all() or not np.isfinite(continuous).all():
            raise ValueError(f"Ungültige Merkmale für {path.name}. Audiodatei prüfen.")
        if not np.any(continuous):
            print(f"Kein stimmhafter Abschnitt: {path.name}", flush=True)
            continue
        feature_path = feature_dir / f"{path.stem}.npy"
        coarse_path = coarse_dir / f"{path.name}.npy"
        pitch_path = pitch_dir / f"{path.name}.npy"
        np.save(feature_path, features, allow_pickle=False)
        np.save(coarse_path, pitch, allow_pickle=False)
        np.save(pitch_path, continuous, allow_pickle=False)
        rows.append(
            "|".join(
                [
                    str(folder / "0_gt_wavs" / path.name),
                    str(feature_path),
                    str(coarse_path),
                    str(pitch_path),
                    "0",
                ]
            )
        )
        report(
            f"Stimme analysieren · Abschnitt {number + 1} / {len(paths)}", 22 + 18 * (number + 1) / len(paths)
        )
    if not rows:
        raise ValueError("Keine stimmhaften Trainingsdaten gefunden.")
    (folder / "filelist.txt").write_text("\n".join(rows) + "\n", encoding="utf-8")
    del hubert, pipeline
    gc.collect()
    if device.startswith("cuda"):
        torch.cuda.empty_cache()
    elif device.startswith("xpu"):
        torch.xpu.empty_cache()


def train_index(folder, destination, report):
    report("Stimmenindex erstellen", 94)
    # FAISS and PyTorch ship incompatible OpenMP DLLs on Windows. Keep their
    # compute runtimes in separate processes instead of allowing duplicate DLLs.
    subprocess.run(
        [sys.executable, "-m", "app.indexing", str(folder), str(destination)],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
        check=True,
    )


def run_training(store, job, report):
    options = job["parameters"]
    rate_label = f"{options['sample_rate'] // 1000}k"
    weights = [f"pretrained_v2/f0{part}{rate_label}.pth" for part in ("G", "D")]
    ensure_assets(base_assets() + weights, lambda phase, value: report(phase, value * 0.1))
    device = select_device()
    experiment = options.get("experiment_id") or job["id"]
    folder = DATA / "training" / experiment
    folder.mkdir(exist_ok=True)
    store.update("job", job["id"], experiment_id=experiment)

    if not options.get("resume_job_id"):
        prepare_dataset(store, options["audio_ids"], folder, options["sample_rate"], report)
        extract_features(folder, device, options["pitch_method"], report)
    config_path = ENGINE / "configs" / ("v1" if rate_label == "40k" else "v2") / f"{rate_label}.json"
    configuration = json.loads(config_path.read_text(encoding="utf-8"))
    configuration["train"]["learning_rate"] = options["learning_rate"]
    configuration["train"]["epochs"] = options["epochs"]
    configuration["train"]["log_interval"] = 10
    configuration["model"]["spk_embed_dim"] = 1
    (folder / "config.json").write_text(json.dumps(configuration), encoding="utf-8")
    command = [
        sys.executable,
        "-m",
        "train.train",
        "-e",
        experiment,
        "-sr",
        rate_label,
        "-f0",
        "1",
        "-bs",
        str(options["batch_size"]),
        "-te",
        str(options["epochs"]),
        "-se",
        str(options["save_every"]),
        "-pg",
        str(asset_path(weights[0])),
        "-pd",
        str(asset_path(weights[1])),
        "-g",
        "0",
        "-l",
        "1",
        "-c",
        "1" if options["cache_gpu"] and device != "cpu" else "0",
        "-sw",
        "1",
        "-v",
        "v2",
    ]
    report("Modell trainieren · erste Epoche wird vorbereitet", 40)
    environment = {
        **os.environ,
        "PYTHONPATH": str(ENGINE),
        "RVC_RESUME_REQUIRED": "1" if options.get("resume_job_id") else "0",
    }
    trained = DATA / "models" / f"{experiment}.pth"
    previous_export = trained.stat().st_mtime_ns if trained.exists() else 0
    with (folder / "console.log").open("ab") as log:
        process = subprocess.Popen(command, cwd=ENGINE, env=environment, stdout=log, stderr=subprocess.STDOUT)
        while process.poll() is None:
            progress_path = folder / "progress.json"
            if progress_path.exists():
                progress = json.loads(progress_path.read_text(encoding="utf-8"))
                report(
                    f"Training · Epoche {progress['epoch']} / {options['epochs']}",
                    min(92, 40 + 52 * progress["epoch"] / options["epochs"]),
                )
            time.sleep(2)
    if process.returncode:
        tail = (folder / "console.log").read_text(encoding="utf-8", errors="replace")[-4000:]
        raise RuntimeError(f"Training fehlgeschlagen (Code {process.returncode}).\n{tail}")
    if not trained.exists() or trained.stat().st_mtime_ns <= previous_export:
        raise RuntimeError("Das Training hat kein exportiertes Modell erzeugt. Trainingsprotokoll prüfen.")
    model_key = uuid.uuid4().hex
    model_path = DATA / "models" / f"{model_key}.pth"
    index_path = DATA / "models" / f"{model_key}.index"
    train_index(folder, index_path, report)
    shutil.copy2(trained, model_path)
    metadata = inspect_model(model_path)
    model = store.create(
        "model",
        name=options["project_name"],
        path=str(model_path.relative_to(DATA)),
        index_path=str(index_path.relative_to(DATA)),
        size=model_path.stat().st_size,
        origin="trained",
        training_job_id=job["id"],
        **metadata,
    )
    return {"model_id": model["id"], "outputs": [], "experiment_id": experiment}
