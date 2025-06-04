@echo off
setlocal

REM Erstelle virtuelle Umgebung
python -m venv .venv

REM Aktiviert die virtuelle Umgebung
call "%~dp0.venv\Scripts\activate.bat"

REM Installiere Bibliotheken
pip install -r requirements.txt

REM Starte dein Python-Programm
python "%~dp0src\main.py"

endlocal
pause
