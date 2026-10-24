import json
import subprocess
from pathlib import Path

AUDIO_EXTENSIONS = {
    ".wav",
    ".mp3",
    ".flac",
    ".ogg",
    ".m4a",
    ".aac",
    ".opus",
    ".aiff",
    ".aif",
    ".wma",
    ".mp4",
    ".webm",
}


def probe(path: Path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    info = json.loads(result.stdout)
    stream = next((s for s in info.get("streams", []) if s["codec_type"] == "audio"), None)
    if not stream:
        raise ValueError("Die Datei enthält keine lesbare Audiospur.")
    duration = float(info.get("format", {}).get("duration", stream.get("duration", 0)))
    if duration <= 0:
        raise ValueError("Die Audiodatei ist leer oder ihre Dauer konnte nicht gelesen werden.")
    return {"duration": duration, "sample_rate": int(stream["sample_rate"]), "channels": stream["channels"]}


def decode(source, destination, sample_rate, channels=1):
    subprocess.run(
        [
            "ffmpeg",
            "-nostdin",
            "-v",
            "error",
            "-y",
            "-i",
            str(source),
            "-map",
            "0:a:0",
            "-vn",
            "-ar",
            str(sample_rate),
            "-ac",
            str(channels),
            "-c:a",
            "pcm_f32le",
            str(destination),
        ],
        check=True,
    )


def encode(source, destination, sample_rate=0):
    args = ["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(source)]
    if sample_rate:
        args += ["-ar", str(sample_rate)]
    suffix = Path(destination).suffix
    args += {
        ".wav": ["-c:a", "pcm_s24le"],
        ".flac": ["-c:a", "flac"],
        ".mp3": ["-c:a", "libmp3lame", "-b:a", "320k"],
    }[suffix]
    subprocess.run([*args, str(destination)], check=True)
