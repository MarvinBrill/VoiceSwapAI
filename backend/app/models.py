from pathlib import Path

from .checkpoints import load_voice_weights


def inspect_model(path: Path):
    import torch

    try:
        checkpoint = load_voice_weights(path)
    except Exception as error:
        raise ValueError(
            "Die .pth-Datei lässt sich nicht als sicheres RVC-Modell laden. Bitte ein exportiertes RVC-v1/v2-Modell verwenden."
        ) from error

    if not isinstance(checkpoint, dict) or not {"weight", "config"} <= checkpoint.keys():
        raise ValueError(
            "Kein exportiertes RVC-Modell. Trainings-Checkpoints (G_*.pth) bitte zuerst als Inferenzmodell exportieren."
        )
    config = checkpoint["config"]
    version = checkpoint.get("version", "v1")
    embedding = checkpoint["weight"].get("emb_g.weight")
    if version not in ("v1", "v2") or not isinstance(config, (list, tuple)) or len(config) != 18:
        raise ValueError("Unbekanntes RVC-Modellformat.")
    if embedding is None or not isinstance(embedding, torch.Tensor) or embedding.ndim != 2:
        raise ValueError("Die Sprecher-Einbettung im Modell fehlt.")
    sample_rate = int(config[-1])
    if sample_rate not in (32000, 40000, 48000) or checkpoint.get("f0", 1) not in (0, 1):
        raise ValueError("Das Modell verwendet eine nicht unterstützte RVC-Konfiguration.")
    return {
        "version": version,
        "sample_rate": sample_rate,
        "speakers": embedding.shape[0],
        "pitch_guidance": bool(checkpoint.get("f0", 1)),
    }


def inspect_index(path, dimension):
    import faiss

    try:
        index = faiss.read_index(str(path))
    except Exception as error:
        raise ValueError("Die Indexdatei ist nicht lesbar.") from error
    if index.d != dimension or index.ntotal < 8:
        raise ValueError(f"Der Index muss {dimension} Dimensionen und mindestens 8 Einträge besitzen.")
