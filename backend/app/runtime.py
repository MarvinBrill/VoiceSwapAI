import os
import sys

from .settings import DATA, ENGINE


def configure_engine():
    sys.path.insert(0, str(ENGINE))
    os.environ["RVC_ASSETS"] = str(DATA / "assets")
    os.environ["RVC_LOGS"] = str(DATA / "training")
    os.environ["weight_root"] = str(DATA / "models")
    os.environ["rmvpe_root"] = str(DATA / "assets" / "rmvpe")
    os.environ["TORCH_HOME"] = str(DATA / "assets" / "torch")
    os.environ["HF_HOME"] = str(DATA / "assets" / "huggingface")
    os.environ["RVC_AUDIO_FORCE_CPU"] = "1"
    os.environ["RVC_CUDA_GRAPH"] = "0"
    os.environ["OMP_NUM_THREADS"] = os.getenv("VOICESWAP_THREADS", "4")
