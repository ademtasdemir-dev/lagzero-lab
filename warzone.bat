@echo off
chcp 65001 >nul
title nightcut - Warzone
cd /d "%~dp0"

rem Warzone-Aufnahmen auf diese Datei ziehen (eine oder mehrere).
rem 1. Stimmen vom Spielsound trennen (Ordner "getrennt" neben der Aufnahme)
rem 2. nightcut mit Warzone-Profil: Timeline, Shorts, YouTube-Texte
rem 3. Ergebnisordner oeffnen
rem Einstellungen: config\local.yaml, sonst config\examples\warzone.yaml

if "%~1"=="" (
    echo.
    echo  Zieh eine oder mehrere Warzone-Aufnahmen auf diese Datei.
    echo.
    pause
    exit /b
)

set "CONFIG=config\examples\warzone.yaml"
if exist "config\local.yaml" set "CONFIG=config\local.yaml"

for %%F in (%*) do (
    echo.
    echo  ===== %%~nxF =====
    uv run python split_tracks.py "%%~fF" || goto :fail
    uv run nightcut run "%%~dpFgetrennt\%%~nxF" --profile warzone --config "%CONFIG%" --no-fill --name "%%~nF warzone" || goto :fail
    start "" "%~dp0output\%%~nF warzone"
)
echo.
echo  Fertig.
pause
exit /b 0

:fail
echo.
echo  Abgebrochen. Die Meldung oben zeigt, was schiefging.
pause
exit /b 1
