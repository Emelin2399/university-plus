@echo off
REM ============================================================
REM  UNIVERSITY PLUS - Iniciar Backend
REM  Doble clic para encender el servidor backend (FastAPI).
REM  Deja esta ventana abierta mientras uses la app.
REM ============================================================
title UNIVERSITY PLUS - Backend
echo.
echo ========================================
echo   UNIVERSITY PLUS - Iniciando Backend
echo ========================================
echo.

cd /d "%~dp0backend"

REM Activar el entorno virtual de Python
call ".venv\Scripts\activate.bat"

echo Arrancando el servidor... (espera "Application startup complete")
echo.

REM Iniciar el servidor backend
python -m uvicorn app.main:app --reload

REM Si el servidor se cierra, no cerrar la ventana de golpe
echo.
echo El servidor se detuvo. Presiona una tecla para cerrar.
pause >nul
