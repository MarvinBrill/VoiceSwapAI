@echo off
setlocal
cd /d "%~dp0"
where uv >nul 2>nul
if not errorlevel 1 goto run
if exist "%LOCALAPPDATA%\Microsoft\WinGet\Links\uv.exe" (
  set "PATH=%LOCALAPPDATA%\Microsoft\WinGet\Links;%PATH%"
  goto run
)
if exist "%USERPROFILE%\.local\bin\uv.exe" (
  set "PATH=%USERPROFILE%\.local\bin;%PATH%"
  goto run
)
echo VoiceSwapAI installiert zuerst die Python-Verwaltung uv ueber WinGet.
winget install --id astral-sh.uv --exact --source winget --accept-package-agreements --accept-source-agreements
if errorlevel 1 goto failed
set "PATH=%LOCALAPPDATA%\Microsoft\WinGet\Links;%USERPROFILE%\.local\bin;%PATH%"
:run
uv run --python 3.12 --no-project "%~dp0scripts\windows.py" %*
if errorlevel 1 goto failed
exit /b 0
:failed
echo.
echo Start fehlgeschlagen. Die Meldung oben zeigt den Grund.
pause
exit /b 1
