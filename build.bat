@echo off
REM ========================================
REM SOT Build Script
REM Builds EXE + creates professional installer
REM ========================================
echo.
echo ========================================
echo  SOT - Building Standalone Executable
echo ========================================
echo.

REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist SOT.spec del SOT.spec
echo.
echo Building executable...
echo This may take 3-7 minutes...
echo.

REM Build with ALL necessary files and imports bundled
python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name SOT ^
    --icon="ui/logo.ico" ^
    --add-data "firebase_key.json;." ^
    --add-data "ui/workspace.jpeg;ui" ^
    --add-data "ui/logo.PNG;ui" ^
    --add-data "assets/fonts/Inter-Regular.ttf;assets/fonts" ^
    --add-data "assets/fonts/Inter-Medium.ttf;assets/fonts" ^
    --add-data "assets/fonts/Inter-SemiBold.ttf;assets/fonts" ^
    --add-data "assets/fonts/Inter-Bold.ttf;assets/fonts" ^
    --hidden-import firebase_admin ^
    --hidden-import firebase_admin.credentials ^
    --hidden-import firebase_admin.db ^
    --hidden-import firebase_admin._http_client ^
    --hidden-import google.cloud ^
    --hidden-import google.auth ^
    --hidden-import google.oauth2 ^
    --hidden-import PySide6 ^
    --hidden-import PySide6.QtCore ^
    --hidden-import PySide6.QtGui ^
    --hidden-import PySide6.QtWidgets ^
    --hidden-import openpyxl ^
    --hidden-import openpyxl.styles ^
    --hidden-import requests ^
    --hidden-import pandas ^
    --hidden-import core ^
    --hidden-import core.auth ^
    --hidden-import core.drawings ^
    --hidden-import core.notes ^
    --hidden-import core.projects ^
    --hidden-import core.reports ^
    --hidden-import core.users ^
    --hidden-import services ^
    --hidden-import services.firebase_client ^
    --hidden-import services.auth_client ^
    --hidden-import services.employee_performance_report ^
    --hidden-import services.performance_report ^
    --hidden-import services.project_report ^
    --hidden-import services.project_status_report ^
    --hidden-import ui ^
    --hidden-import ui.main_window ^
    --hidden-import ui.login_view ^
    --hidden-import ui.admin_dashboard ^
    --hidden-import ui.employee_dashboard ^
    --hidden-import ui.admin_projects ^
    --hidden-import ui.admin_review ^
    --hidden-import ui.admin_template ^
    --hidden-import ui.drawing_detail ^
    --hidden-import ui.superadmin_users ^
    --hidden-import utils ^
    --hidden-import utils.logger ^
    --hidden-import utils.validators ^
    --hidden-import utils.modern_dialogs ^
    --hidden-import utils.loading ^
    --collect-all firebase_admin ^
    --collect-all google.auth ^
    --collect-all google.cloud ^
    --collect-binaries PySide6 ^
    --noupx ^
    main.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo  BUILD FAILED!
    echo ========================================
    echo.
    echo Common issues:
    echo 1. Missing dependencies - run: pip install -r requirements.txt
    echo 2. Antivirus blocking PyInstaller
    echo 3. Insufficient permissions
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  EXE BUILD SUCCESSFUL!
echo ========================================
echo.
echo Your executable is ready at: dist\SOT.exe
echo.

REM ========================================
REM NOW BUILD THE INSTALLER
REM ========================================
echo.
echo ========================================
echo  Building Installer Package...
echo ========================================
echo.

REM Check if Inno Setup is installed (common install paths)
set INNO_PATH=""
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set INNO_PATH="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
)
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set INNO_PATH="C:\Program Files\Inno Setup 6\ISCC.exe"
)

if %INNO_PATH%=="" (
    echo ⚠ Inno Setup not found!
    echo.
    echo To build the installer, download and install Inno Setup from:
    echo https://jrsoftware.org/isdl.php
    echo.
    echo After installing, run build.bat again.
    echo.
    echo For now, your EXE is at: dist\SOT.exe
    echo You can distribute that directly, but users may need VC++ runtime.
    echo.
    pause
    exit /b 0
)

echo Found Inno Setup. Compiling installer...
%INNO_PATH% SOT_installer.iss

if errorlevel 1 (
    echo.
    echo ❌ Installer build failed! Check SOT_installer.iss for errors.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  INSTALLER BUILD SUCCESSFUL!
echo ========================================
echo.
echo Installer ready at: installer_output\SOT_Setup.exe
echo.
echo This installer will:
echo  - Automatically install VC++ Runtime if needed
echo  - Install SOT to Program Files
echo  - Create a Desktop shortcut
echo  - Create a Start Menu entry
echo  - Allow clean uninstall from Control Panel
echo.
pause