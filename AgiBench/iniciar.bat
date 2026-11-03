@echo off
title Iniciar AgiBench
cd /d "%~dp0"

echo ======================================================
echo             AGIBENCH - BENCHMARK UNIVERSAL
echo ======================================================
echo.
echo Verificando ambiente Python...

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao foi encontrado instalado no sistema.
    echo Por favor, instale o Python em https://www.python.org/
    pause
    exit /b 1
)

echo Instalando/Atualizando dependencias necessarias...
python -m pip install -r requirements.txt --quiet --disable-pip-version-check

echo Iniciando o AgiBench...
start "" pythonw main.py
exit
