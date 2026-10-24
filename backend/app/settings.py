import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
DATA = Path(os.getenv("VOICESWAP_DATA", REPO / "data")).resolve()
ENGINE = Path(os.getenv("VOICESWAP_ENGINE", REPO / "engine" / "rvc")).resolve()
FRONTEND = Path(os.getenv("VOICESWAP_FRONTEND", REPO / "frontend" / "dist"))


def prepare_directories():
    for folder in ("uploads", "models", "jobs", "assets", "training", "outputs"):
        (DATA / folder).mkdir(parents=True, exist_ok=True)


def data_path(relative: str) -> Path:
    path = (DATA / relative).resolve()
    if not path.is_relative_to(DATA):
        raise ValueError("Ungültiger Dateipfad.")
    return path
