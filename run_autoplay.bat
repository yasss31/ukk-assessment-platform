@echo off
setlocal
set SCRIPT_DIR=%~dp0
if exist "%SCRIPT_DIR%backend\venv\Scripts\python.exe" (
    "%SCRIPT_DIR%backend\venv\Scripts\python.exe" "%SCRIPT_DIR%run_autoplay.py" %*
) else if exist "%SCRIPT_DIR%..\ukk-assessment-platform\backend\venv\Scripts\python.exe" (
    "%SCRIPT_DIR%..\ukk-assessment-platform\backend\venv\Scripts\python.exe" "%SCRIPT_DIR%..\ukk-assessment-platform\run_autoplay.py" %*
) else (
    python "%SCRIPT_DIR%run_autoplay.py" %*
)
