@echo off
chcp 65001 > nul
title SavoraApp - Lancement

echo.
echo  =============================================
echo    SAVORA APP - Demarrage de l'environnement
echo  =============================================
echo.

set "ROOT=%~dp0"
set "API_DIR=%ROOT%savora_api"
set "DESKTOP_DIR=%ROOT%savora_desktop"

:: ─────────────────────────────────────────────
:: 1. PostgreSQL Docker (optionnel, SQLite sinon)
:: ─────────────────────────────────────────────
echo [1/3] Verification Docker + PostgreSQL...

docker info > nul 2>&1
if %errorlevel% == 0 (
    docker start postgres_db > nul 2>&1
    if %errorlevel% == 0 (
        echo  [OK] PostgreSQL demarre sur Docker
    ) else (
        echo  [INFO] Container postgres_db introuvable, SQLite utilise
    )
) else (
    echo  [INFO] Docker non disponible, SQLite utilise
)

:: ─────────────────────────────────────────────
:: 2. API FastAPI
:: ─────────────────────────────────────────────
echo.
echo [2/3] Demarrage API FastAPI (port 8000)...

start "Savora API" cmd /k "cd /d "%API_DIR%" && echo. && echo  API FastAPI - http://localhost:8000 && echo  Docs Swagger - http://localhost:8000/docs && echo. && uvicorn main:app --reload --port 8000"

:: Attendre que l'API soit vraiment prete
echo  Attente de l'API...
:WAIT_API
timeout /t 2 /nobreak > nul
curl -s http://localhost:8000/health > nul 2>&1
if %errorlevel% neq 0 (
    curl -s http://localhost:8000/ > nul 2>&1
    if %errorlevel% neq 0 (
        goto WAIT_API
    )
)
echo  [OK] API prete sur http://localhost:8000

:: ─────────────────────────────────────────────
:: 3. Client lourd (Desktop)
:: ─────────────────────────────────────────────
echo.
echo [3/3] Demarrage client lourd...

start "Savora Desktop" cmd /k "cd /d "%DESKTOP_DIR%" && python main.py"

echo  [OK] Client lourd demarre

:: ─────────────────────────────────────────────
:: Recap
:: ─────────────────────────────────────────────
echo.
echo  =============================================
echo    Tout est lance !
echo.
echo    API REST   : http://localhost:8000
echo    Swagger    : http://localhost:8000/docs
echo    Desktop    : fenetre Savora ouverte
echo  =============================================
echo.
echo  Appuyez sur une touche pour fermer ce launcher...
pause > nul
