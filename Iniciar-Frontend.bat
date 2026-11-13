@echo off
REM ============================================================
REM  UNIVERSITY PLUS - Iniciar Frontend
REM  Doble clic para encender la parte visual (React/Vite).
REM  Deja esta ventana abierta mientras uses la app.
REM ============================================================
title UNIVERSITY PLUS - Frontend
echo.
echo ========================================
echo   UNIVERSITY PLUS - Iniciando Frontend
echo ========================================
echo.

cd /d "%~dp0frontend"

echo Arrancando la interfaz... (espera a ver http://localhost:5173)
echo.

REM Iniciar el servidor de desarrollo del frontend
call npm run dev

echo.
echo La interfaz se detuvo. Presiona una tecla para cerrar.
pause >nul
