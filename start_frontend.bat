@echo off
title Biblioteca Digital - Frontend Cloudinary
echo ========================================================
echo        BIBLIOTECA DIGITAL CON CLOUDINARY
echo ========================================================
echo.

set FRONTEND_DIR=%~dp0frontend

if not exist "%FRONTEND_DIR%" (
    set FRONTEND_DIR=%~dp0Taller_API_FastAPI_Julian_Remolina-main\frontend
)

cd /d "%FRONTEND_DIR%"

echo Abriendo navegador en http://localhost:5173 ...
start "" "http://localhost:5173"

echo Iniciando servidor HTTP local (Node.js)...
node server.js

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Abriendo directamente como archivo HTML...
    start "" "%FRONTEND_DIR%\index.html"
)

pause
