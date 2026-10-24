"""Restricted user weights loader, including for the older DirectML runtime."""

import zipfile


def load_voice_weights(path):
    import torch

    # PyTorch <2.6 has an unsafe legacy-TAR path even with weights_only=True.
    # ZIP-only admission closes that path before invoking its deserializer.
    # No pickle allowlists or unrestricted retry are permitted for user files.
    with open(path, "rb") as source:
        if source.read(4) != b"PK\x03\x04" or not zipfile.is_zipfile(source):
            raise ValueError("Bitte ein RVC-Modell im aktuellen PyTorch-ZIP-Format verwenden.")
        with zipfile.ZipFile(source) as archive:
            names = archive.namelist()
            if any(name.endswith("/constants.pkl") or "/code/" in name for name in names):
                raise ValueError("TorchScript-Programme sind keine unterstützten Voice-Gewichte.")
            if sum(name.endswith("/data.pkl") for name in names) != 1:
                raise ValueError("Die Datei enthält keine eindeutigen PyTorch-Modellgewichte.")
        source.seek(0)
        return torch.load(source, map_location="cpu", weights_only=True)
