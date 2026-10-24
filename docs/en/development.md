# Local development and testing

[Guide index](README.md) · [Deutsch](../de/development.md)

For normal use, follow a hardware guide. This guide covers changes to the backend
and interface. Requirements: Python 3.12, Node.js (tested here with version 22), npm,
and FFmpeg/FFprobe on PATH.

## Project layout

| Directory | Contents |
| --- | --- |
| `frontend/` | React, TypeScript, Vite |
| `backend/app/` | FastAPI, SQLite, job processing |
| `engine/rvc/` | Vendored and adapted RVC engine |
| `scripts/` | Windows launcher and integration tests |

The neighboring original RVC repository is not required. Source provenance:
[UPSTREAM.md](../../engine/UPSTREAM.md).

## CUDA or CPU backend

Create a separate environment from the project folder:

```sh
python -m venv .venv
```

Here `python` must be Python 3.12; use `python3.12` on Linux if appropriate.
Without activating the environment, replace every `python` in the commands below
with `.\.venv\Scripts\python.exe` in PowerShell or `.venv/bin/python` on Linux.
Alternatively, run `source .venv/bin/activate` first on Linux.
Run these commands inside that environment:

```sh
python -m pip install torch==2.7.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cu128
python -m pip install -r backend/requirements.txt -r backend/requirements-dev.txt
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

For CPU, replace `cu128` with `cpu` in the first installation command. To explicitly
use CPU, set `VOICESWAP_DEVICE=cpu` (PowerShell: `$env:VOICESWAP_DEVICE='cpu'`;
Linux: `export VOICESWAP_DEVICE=cpu`). Without a setting, the app detects available devices.

## DirectML backend on Windows

First run `start-windows.cmd --check` to complete setup. Then, in PowerShell:

```powershell
$env:VOICESWAP_DEVICE = 'directml'
$env:VOICESWAP_DIRECTML_DEVICE = '0'
.\.venv-directml\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Select the appropriate adapter number. **Do not** install the CUDA packages into
`.venv-directml`: DirectML needs the separate versions in `backend/requirements-directml.txt`.
FFmpeg/FFprobe must also be accessible in this terminal; open a new terminal after
initial installation if necessary.

## Frontend in a second terminal

```sh
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173. Vite proxies `/api` to port 8000. Stop with Ctrl+C;
`npm run build` then produces the production files in `frontend/dist/`.

## Checks

From the project folder, using the selected Python environment and development dependencies:

```sh
python -m pip install -r backend/requirements-dev.txt
python -m pytest
python -m ruff check backend scripts
```

Browser tests need a running backend on port 8000 and a built frontend:

```sh
cd frontend
npm run build
npx playwright install chromium
npm run test:e2e
```

For another test address, set `APP_URL`, for example
`$env:APP_URL='http://localhost:7860'` in PowerShell or
`export APP_URL=http://localhost:7860` on Linux.

The integration tests `scripts/smoke.py` and `scripts/check_extended.py` perform
real training and conversion, creating test recordings, projects, models and outputs.
Run them only against a test instance. Set `VOICESWAP_DATA` to a separate directory
before starting that backend; base weights may be downloaded again there.
See the [project README](../../README.md) for invocation details.
