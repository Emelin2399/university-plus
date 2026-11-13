@echo off
REM ============================================================
REM  UNIVERSITY PLUS - Iniciar TODO
REM  Doble clic para arrancar backend + frontend y abrir la app.
REM  Se abriran dos ventanas (backend y frontend). No las cierres
REM  mientras uses la aplicacion.
REM ============================================================
title UNIVERSITY PLUS - Lanzador
echo.
echo =================================================
echo   UNIVERSITY PLUS - Encendiendo todo
echo =================================================
echo.
echo Se abriran 2 ventanas (Backend y Frontend).
echo Espera unos segundos y el navegador se abrira solo.
echo.

REM 1) Abrir el BACKEND en una ventana nueva
start "UNIVERSITY PLUS - Backend" cmd /k "cd /d "%~dp0backend" && call .venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload"

REM 2) Abrir el FRONTEND en otra ventana nueva
start "UNIVERSITY PLUS - Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

REM 3) Esperar unos segundos a que los servidores arranquen
echo Esperando a que los servidores inicien...
timeout /t 8 /nobreak >nul

REM 4) Abrir la app en el navegador
start "" "http://localhost:5173"

echo.
echo Listo. La app deberia abrirse en tu navegador.
echo Si no, abre manualmente: http://localhost:5173
echo.
echo Puedes cerrar ESTA ventana. Las otras dos deben quedar abiertas.
pause >nul
