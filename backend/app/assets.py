import hashlib
import json
import time

import requests

from .settings import DATA, REPO

MANIFEST = json.loads((REPO / "engine" / "assets.json").read_text(encoding="utf-8"))


def asset_path(name):
    return DATA / "assets" / name


def installed(name):
    path = asset_path(name)
    return path.is_file() and path.stat().st_size == MANIFEST["files"][name]["size"]


def status():
    return [
        {"name": name, "ready": installed(name), "size": info["size"]}
        for name, info in MANIFEST["files"].items()
    ]


def ensure_assets(names, report):
    for number, name in enumerate(names):
        metadata = MANIFEST["files"][name]
        destination = asset_path(name)
        if installed(name):
            continue

        destination.parent.mkdir(parents=True, exist_ok=True)
        partial = destination.with_suffix(destination.suffix + ".partial")
        url = f"https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/{MANIFEST['revision']}/{metadata['source']}"
        for attempt in range(3):
            try:
                digest = hashlib.sha256()
                downloaded = 0
                last_report = 0
                with requests.get(url, stream=True, timeout=(20, 90)) as response:
                    response.raise_for_status()
                    with partial.open("wb") as output:
                        for chunk in response.iter_content(1024 * 1024):
                            output.write(chunk)
                            digest.update(chunk)
                            downloaded += len(chunk)
                            if time.monotonic() - last_report > 1:
                                report(
                                    f"Basisdateien · {name} · {downloaded / 1024**2:.0f} / {metadata['size'] / 1024**2:.0f} MB",
                                    (number + downloaded / metadata["size"]) / len(names) * 100,
                                )
                                last_report = time.monotonic()
                if downloaded != metadata["size"] or digest.hexdigest() != metadata["sha256"]:
                    raise ValueError(f"Prüfsumme stimmt nicht: {name}")
                partial.replace(destination)
                break
            except (requests.RequestException, ValueError):
                partial.unlink(missing_ok=True)
                if attempt == 2:
                    raise
                time.sleep(2**attempt)


def base_assets():
    return [name for name in MANIFEST["files"] if not name.startswith("pretrained")]
