import gc
from pathlib import Path

import numpy as np
import soundfile as sf
import torch

from .assets import base_assets, ensure_assets
from .audio import decode, encode
from .crossfade import CrossfadeWriter
from .checkpoints import load_voice_weights
from .settings import DATA, data_path


class VoiceConverter:
    def __init__(self, model):
        from configs.config import Config
        from infer.hubert import load_hubert_model
        from infer.module.models import (
            SynthesizerTrnMs256NSFsid,
            SynthesizerTrnMs256NSFsid_nono,
            SynthesizerTrnMs768NSFsid,
            SynthesizerTrnMs768NSFsid_nono,
        )
        from infer.vc.pipeline import Pipeline

        self.config = Config()
        checkpoint = load_voice_weights(data_path(model["path"]))
        checkpoint["config"][-3] = checkpoint["weight"]["emb_g.weight"].shape[0]
        self.sample_rate = checkpoint["config"][-1]
        self.version = checkpoint.get("version", "v1")
        self.f0 = checkpoint.get("f0", 1)
        classes = {
            ("v1", 1): SynthesizerTrnMs256NSFsid,
            ("v1", 0): SynthesizerTrnMs256NSFsid_nono,
            ("v2", 1): SynthesizerTrnMs768NSFsid,
            ("v2", 0): SynthesizerTrnMs768NSFsid_nono,
        }
        self.network = classes[self.version, self.f0](*checkpoint["config"], is_half=self.config.is_half)
        del self.network.enc_q
        incompatible = self.network.load_state_dict(checkpoint["weight"], strict=False)
        if incompatible.missing_keys:
            raise ValueError(
                "Dem Modell fehlen benötigte Gewichte: " + ", ".join(incompatible.missing_keys[:5])
            )
        self.network.eval().to(device=self.config.device, dtype=self.config.dtype)
        self.hubert = load_hubert_model(self.config.device, self.config.is_half)
        synth_device = next(self.network.parameters()).device
        hubert_device = next(self.hubert.parameters()).device
        if synth_device != torch.device(self.config.device) or hubert_device != synth_device:
            raise RuntimeError("Das Voice-Modell wurde nicht auf das ausgewählte Rechengerät geladen.")
        print(f"Stimmenaustausch: Synthesizer={synth_device}, HuBERT={hubert_device}", flush=True)
        self.pipeline = Pipeline(self.sample_rate, self.config)
        self.index = str(data_path(model["index_path"])) if model.get("index_path") else ""

    def convert(self, audio, rate, options):
        import librosa

        mono = librosa.resample(audio.mean(axis=1), orig_sr=rate, target_sr=16000)
        peak = np.abs(mono).max()
        if peak > 0.95:
            mono = mono * (0.95 / peak)
        with torch.no_grad() if self.config.device.startswith("privateuseone") else torch.inference_mode():
            converted = self.pipeline.pipeline(
                self.hubert,
                self.network,
                options["speaker_id"],
                mono,
                [0, 0, 0],
                options["pitch"],
                options["pitch_method"],
                self.index,
                options["index_rate"] if self.index else 0,
                self.f0,
                self.sample_rate,
                0,
                options["rms_mix"],
                self.version,
                options["protect"],
            )
        result = converted.astype(np.float32)
        if not np.isfinite(result).all():
            raise ValueError("Das Modell erzeugt ungültige Audiowerte. Modell und Stimmenindex prüfen.")
        result = librosa.resample(result, orig_sr=self.sample_rate, target_sr=rate)
        return np.pad(result, (0, max(0, len(audio) - len(result))))[: len(audio)]


class VocalSeparator:
    def __init__(self, device):
        from demucs.pretrained import get_model

        # Hybrid Demucs uses complex STFT tensors, which DirectML cannot hold.
        # Voice conversion itself remains on the selected GPU.
        self.device = "cpu" if str(device).startswith("privateuseone") else device
        # Demucs RemoteRepo verifies the published checkpoint hash. Its trusted
        # package includes model classes; user .pth uploads remain weights_only.
        self.model = get_model("htdemucs").eval().to(self.device)

    def separate(self, audio):
        from demucs.apply import apply_model

        waveform = torch.from_numpy(audio.T.copy())
        reference = waveform.mean(0)
        mean, std = reference.mean(), reference.std().clamp_min(1e-6)
        with torch.inference_mode():
            sources = apply_model(
                self.model,
                ((waveform - mean) / std)[None],
                device=self.device,
                shifts=0,
                split=True,
                overlap=0.25,
                progress=False,
            )[0].cpu()
        sources = sources * std + mean
        vocal_index = self.model.sources.index("vocals")
        vocals = sources[vocal_index].T.numpy()
        accompaniment = sources[[i for i in range(len(sources)) if i != vocal_index]].sum(0).T.numpy()
        return vocals, accompaniment


def run_conversion(store, job, report):
    options = job["parameters"]
    ensure_assets(base_assets(), lambda phase, value: report(phase, value * 0.08))
    model = store.get("model", options["model_id"])
    report("Voice-Modell laden", 8)
    converter = VoiceConverter(model)
    separator = None
    if options["separate_vocals"]:
        report("Gesangstrennung vorbereiten · beim ersten Mal Modell-Download", 10)
        separator = VocalSeparator(converter.config.device)

    output_dir = DATA / "outputs" / job["id"]
    output_dir.mkdir(exist_ok=True)
    outputs = []
    for file_number, audio_id in enumerate(options["audio_ids"]):
        audio = store.get("audio", audio_id)
        temporary = output_dir / f"{file_number}-source.wav"
        mixed_path = output_dir / f"{file_number}-mix.wav"
        vocal_path = output_dir / f"{file_number}-voice.wav"
        backing_path = output_dir / f"{file_number}-backing.wav"
        decode(data_path(audio["path"]), temporary, 44100, channels=2)
        rate = 44100
        block, context = rate * 30, rate

        with (
            sf.SoundFile(temporary) as source,
            sf.SoundFile(mixed_path, "w", rate, 2, subtype="FLOAT") as mixed,
            sf.SoundFile(vocal_path, "w", rate, 1, subtype="PCM_24") as voice,
            sf.SoundFile(backing_path, "w", rate, 2, subtype="PCM_24") as backing,
        ):
            fade_frames = rate // 20
            writer = CrossfadeWriter([mixed, voice, backing], fade_frames)
            for start in range(0, len(source), block):
                end = min(start + block, len(source))
                left, right = max(0, start - context), min(len(source), end + context)
                source.seek(left)
                samples = source.read(right - left, dtype="float32", always_2d=True)
                if separator:
                    vocals, instrumental = separator.separate(samples)
                else:
                    vocals, instrumental = samples, np.zeros_like(samples)
                transformed = converter.convert(vocals, rate, options)
                overlap = fade_frames if start else 0
                selected = slice(start - left - overlap, end - left)
                transformed = transformed[selected]
                instrumental = instrumental[selected]
                result = transformed[:, None] * 10 ** (options["vocal_gain"] / 20) + instrumental * 10 ** (
                    options["instrumental_gain"] / 20
                )
                writer.write([result, transformed, instrumental], final=end == len(source))
                progress = 12 + 82 * (file_number + end / len(source)) / len(options["audio_ids"])
                report(f"{audio['name']} · {end / rate:.0f} / {len(source) / rate:.0f} s", progress)

        # One gain for the entire file avoids pumping between processing chunks.
        peak = 1.0
        for chunk in sf.blocks(mixed_path, blocksize=rate * 30, dtype="float32"):
            peak = max(peak, float(np.max(np.abs(chunk))) / 0.98)
        normalized = output_dir / f"{file_number}-normalized.wav"
        with sf.SoundFile(normalized, "w", rate, 2, subtype="PCM_24") as target:
            for chunk in sf.blocks(mixed_path, blocksize=rate * 30, dtype="float32"):
                target.write(chunk / peak)
        final = output_dir / f"{file_number}-result.{options['format']}"
        encode(normalized, final, options["sample_rate"] or converter.sample_rate)
        outputs.append(
            {
                "name": f"{Path(audio['name']).stem} · {model['name']}",
                "path": str(final.relative_to(DATA)),
                "audio_id": audio_id,
                "kind": "mix",
            }
        )
        if separator:
            outputs.extend(
                [
                    {
                        "name": f"{Path(audio['name']).stem} · Neue Stimme",
                        "path": str(vocal_path.relative_to(DATA)),
                        "kind": "vocal",
                    },
                    {
                        "name": f"{Path(audio['name']).stem} · Begleitung",
                        "path": str(backing_path.relative_to(DATA)),
                        "kind": "instrumental",
                    },
                ]
            )
        else:
            vocal_path.unlink()
            backing_path.unlink()
        for path in (temporary, mixed_path, normalized):
            path.unlink(missing_ok=True)
        store.update("job", job["id"], outputs=outputs)
    del converter, separator
    gc.collect()
    return {"outputs": outputs}
