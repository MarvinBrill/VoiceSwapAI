"""Install and launch the native Windows DirectML edition, without Docker."""

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".windows-runtime"
PYTHON = ROOT / ".venv-directml" / "Scripts" / "python.exe"


def run(arguments, cwd=ROOT):
    subprocess.run([str(value) for value in arguments], cwd=cwd, check=True)


def refresh_path():
    import winreg

    paths = [os.environ.get("PATH", "")]
    for hive, key in (
        (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
        (winreg.HKEY_CURRENT_USER, r"Environment"),
    ):
        try:
            with winreg.OpenKey(hive, key) as registry:
                paths.append(os.path.expandvars(winreg.QueryValueEx(registry, "Path")[0]))
        except FileNotFoundError:
            continue
    packages = Path(os.environ["LOCALAPPDATA"]) / "Microsoft/WinGet/Packages"
    paths.extend(str(path) for path in packages.glob("Gyan.FFmpeg_*/ffmpeg-*/bin"))
    # Repeated tool installs refresh PATH. Deduplicate it to stay below cmd.exe's
    # environment limit when npm.cmd launches node on a fresh Windows setup.
    unique = {}
    for path in os.pathsep.join(paths).split(os.pathsep):
        if path.strip():
            unique.setdefault(os.path.normcase(path.strip()), path.strip())
    os.environ["PATH"] = os.pathsep.join(unique.values())


def ensure_tool(command, package):
    if shutil.which(command):
        return
    print(f"Installiere {package} über WinGet …", flush=True)
    run(
        [
            "winget",
            "install",
            "--id",
            package,
            "--exact",
            "--source",
            "winget",
            "--accept-package-agreements",
            "--accept-source-agreements",
        ]
    )
    refresh_path()
    if not shutil.which(command):
        raise RuntimeError(f"{command} fehlt noch. Terminal neu öffnen und start-windows.cmd erneut starten.")


def fingerprint(paths):
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(str(path.relative_to(ROOT)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def prepare():
    RUNTIME.mkdir(exist_ok=True)
    refresh_path()
    ensure_tool("node", "OpenJS.NodeJS.LTS")
    ensure_tool("ffmpeg", "Gyan.FFmpeg")
    ensure_tool("ffprobe", "Gyan.FFmpeg")
    if not PYTHON.is_file():
        run(["uv", "venv", "--python", "3.12", ROOT / ".venv-directml"])

    requirements = [ROOT / "backend/requirements.txt", ROOT / "backend/requirements-directml.txt"]
    marker = RUNTIME / "dependencies.sha256"
    signature = fingerprint(requirements)
    if not marker.exists() or marker.read_text() != signature:
        run(["uv", "pip", "install", "--python", PYTHON, "-r", requirements[1]])
        run(["uv", "pip", "check", "--python", PYTHON])
        marker.write_text(signature)

    frontend = ROOT / "frontend"
    sources = [
        path for folder in ("src", "public") for path in (frontend / folder).rglob("*") if path.is_file()
    ]
    sources += [
        path for path in frontend.iterdir() if path.is_file() and path.suffix in {".json", ".ts", ".html"}
    ]
    marker = RUNTIME / "frontend.sha256"
    signature = fingerprint(sources)
    if not (frontend / "dist/index.html").exists() or not marker.exists() or marker.read_text() != signature:
        npm = shutil.which("npm.cmd")
        if not npm:
            raise RuntimeError("npm fehlt. Node.js LTS installieren und erneut starten.")
        run([npm, "ci"], frontend)
        run([npm, "run", "build"], frontend)
        marker.write_text(signature)


def open_when_ready(url):
    for _ in range(120):
        try:
            with urllib.request.urlopen(url + "/api/health", timeout=1):
                webbrowser.open(url)
                return
        except OSError:
            time.sleep(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", type=int, help="DirectML-GPU-Nummer aus --list-devices")
    parser.add_argument("--list-devices", action="store_true")
    parser.add_argument("--check", action="store_true", help="GPU-Berechnung und Trainingsgradienten prüfen")
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--no-browser", action="store_true")
    options = parser.parse_args()
    if sys.platform != "win32":
        raise RuntimeError(
            "Dieser Startweg ist für Windows. Unter Linux die Compose-Konfiguration verwenden."
        )
    prepare()

    os.environ["PYTHONPATH"] = str(ROOT / "backend")
    os.environ["PYTHONUTF8"] = "1"
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["VOICESWAP_DEVICE"] = "directml"
    os.environ.setdefault("VOICESWAP_DATA", str(ROOT / "data"))
    if options.device is not None:
        os.environ["VOICESWAP_DIRECTML_DEVICE"] = str(options.device)
    if options.list_devices:
        run([PYTHON, "-m", "app.directml_check", "--list"])
        return
    run([PYTHON, "-m", "app.directml_check"])
    if options.check:
        return

    with socket.socket() as probe:
        if probe.connect_ex(("127.0.0.1", options.port)) == 0:
            raise RuntimeError(
                f"Port {options.port} ist belegt. Andere App stoppen oder --port 7861 verwenden."
            )
    url = f"http://localhost:{options.port}"
    print(
        f"\nVoiceSwapAI: {url}\nZum Beenden Strg+C drücken. Daten: {os.environ['VOICESWAP_DATA']}\n",
        flush=True,
    )
    if not options.no_browser:
        threading.Thread(target=open_when_ready, args=(url,), daemon=True).start()
    run([PYTHON, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(options.port)])


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print(f"\nVoiceSwapAI: {error}", file=sys.stderr)
        sys.exit(1)
