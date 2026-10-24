"""Check real DirectML forward/backward operations without creating library data."""

import argparse
import io
import sys

import torch
import torch_directml

from .devices import device_info, select_device
from .runtime import configure_engine


def check_voice_source(device):
    from infer.module.models import SineGen

    # A successful GPU operation can still return wrong audio. Check values, not
    # just finiteness: mixed integer/float broadcasting once flattened the tone.
    pitch = (200 + 80 * torch.sin(torch.arange(100) * 0.017)).reshape(1, -1, 1)
    for rate in (32000, 40000, 48000):
        generator = SineGen(rate)
        expected = generator._f02sine(pitch, rate // 100)
        actual = generator._f02sine(pitch.to(device), rate // 100).cpu()
        if not torch.allclose(actual, expected, rtol=0, atol=0.002):
            raise RuntimeError(
                f"DirectML erzeugt eine abweichende Stimm-Grundwelle bei {rate} Hz. "
                "App und Grafiktreiber aktualisieren; die GPU-Prüfung muss erfolgreich sein."
            )
    print("Stimm-Grundwelle bei 32/40/48 kHz stimmt mit der CPU-Referenz überein: OK", flush=True)


def check():
    configure_engine()
    from train.mel_processing import mel_spectrogram_torch
    from tools.checkpoint import portable_state
    from infer.module.attentions import MultiHeadAttention

    device = torch.device(select_device())
    if device.type != "privateuseone":
        raise RuntimeError("Dieser Test benötigt VOICESWAP_DEVICE=directml.")
    print(f"DirectML: {device_info()['name']} ({device})", flush=True)
    torch.set_num_threads(4)
    torch.manual_seed(42)
    check_voice_source(device)
    network = torch.nn.Sequential(
        torch.nn.Conv1d(1, 8, 5, padding=2),
        torch.nn.LeakyReLU(0.1),
        torch.nn.Conv1d(8, 1, 5, padding=2),
    ).to(device)
    optimizer = torch.optim.AdamW(network.parameters(), lr=0.001, foreach=False)
    original = network[0].weight.detach().cpu().clone()
    waveform = torch.randn(1, 1, 4096).to(device)
    output = network(waveform)
    mel = mel_spectrogram_torch(output[:, 0], 512, 40, 40000, 128, 512, 0, 20000)
    loss = mel.square().mean()
    loss.backward()
    if not all(p.grad is not None and torch.isfinite(p.grad.cpu()).all() for p in network.parameters()):
        raise RuntimeError("Der DirectML-Trainingsgradient ist ungültig.")
    optimizer.step()
    if torch.equal(original, network[0].weight.detach().cpu()):
        raise RuntimeError("Die GPU-Modellgewichte wurden beim Trainingsschritt nicht aktualisiert.")
    checkpoint = io.BytesIO()
    torch.save(
        portable_state({"model": network.state_dict(), "optimizer": optimizer.state_dict()}), checkpoint
    )
    checkpoint.seek(0)
    restored = torch.load(checkpoint, map_location="cpu", weights_only=True)
    network.load_state_dict(restored["model"])
    optimizer.load_state_dict(restored["optimizer"])
    attention = MultiHeadAttention(192, 192, 2, window_size=10).to(device)
    signal = torch.randn(1, 192, 80).to(device)
    attention(signal, signal).square().mean().backward()
    if not torch.isfinite(attention.emb_rel_v.grad.cpu()).all():
        raise RuntimeError("Ungültige Gradienten in der RVC-Attention.")
    print("GPU-Rechnung, Spektralgradient, RVC-Attention, Optimierung und Checkpoint: OK", flush=True)
    print(
        "Dies prüft Grundoperationen; ein kompletter RVC-Lauf prüft das Voice-Modell zusätzlich.", flush=True
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true")
    options = parser.parse_args()
    try:
        if options.list:
            for index in range(torch_directml.device_count()):
                print(f"{index}: {torch_directml.device_name(index).rstrip(chr(0))}")
        else:
            check()
    except (RuntimeError, ValueError) as error:
        print(f"DirectML-Prüfung fehlgeschlagen: {error}", file=sys.stderr)
        sys.exit(1)
