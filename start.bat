@echo off
echo Demarrage de Savora...

:: 1. PostgreSQL Docker
echo [1/3] Demarrage PostgreSQL...
docker start postgres_db

:: 2. API FastAPI
echo [2/3] Demarrage API FastAPI...
start "Savora API" cmd /k "cd /d %~dp0savora_api && uvicorn main:app --reload"

:: Attendre que l'API soit prête
timeout /t 4 /nobreak > nul

:: 3. Client lourd
echo [3/3] Demarrage client lourd...
start "Savora Desktop" cmd /k "cd /d %~dp0savora_desktop && python main.py"

echo Tout est lance !
