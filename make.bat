@echo off
setlocal

set "SRC_DIR=src"
set "ENTRY=%SRC_DIR%\app.py"
set "VENV_DIR=venv"
set "REQS=requirements.txt"

if "%1"=="build" goto build
if "%1"=="run" goto run
if "%1"=="format" goto format
goto end

:build
    call "%VENV_DIR%\Scripts\activate.bat"

    if exist "%REQS%" (
        pip install -r "%REQS%"
    ) else (
        echo No requirements.txt found.
    )
    goto end

:run
    call "%VENV_DIR%\Scripts\activate.bat"

    python "%ENTRY%"
    goto end

:format
    call "%VENV_DIR%\Scripts\activate.bat"

    for /R "%SRC_DIR%" %%f in (*.py) do (
        black "%%f"
    )
    goto end

:end
endlocal
