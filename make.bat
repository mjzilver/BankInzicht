@echo off
setlocal

set "SRC_DIR=src"
set "ENTRY=%SRC_DIR%\app.py"
set "VENV_DIR=venv"
set "REQS=requirements.txt"

if "%1"=="install" goto install
if "%1"=="run" goto run
if "%1"=="format" goto format
goto end

:activate_venv 
    call "%VENV_DIR%\Scripts\activate.bat"
    exit /b 0

:install
    if not exist "%VENV_DIR%" (
        python -m venv "%VENV_DIR%"
    )
    call :activate_venv

    pip install -r "%REQS%"
    
    goto end

:run
    call :activate_venv
    python "%ENTRY%"
    goto end

:format
    call :activate_venv

    for /R "%SRC_DIR%" %%f in (*.py) do (
        black "%%f"
    )
    goto end

:end
endlocal
