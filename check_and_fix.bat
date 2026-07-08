@echo off
REM ========================================
REM SOT - Pre-Build Checker & Fixer
REM Run this BEFORE building to catch issues
REM ========================================

echo.
echo ========================================
echo  SOT Pre-Build Diagnostic
echo ========================================
echo.

REM [1/8] Check Python
echo [1/8] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo FAIL: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)
python --version
echo OK
echo.

REM [2/8] Check 64-bit
echo [2/8] Checking Python architecture...
python -c "import struct; exit(0 if struct.calcsize('P')*8==64 else 1)" >nul 2>&1
if errorlevel 1 (
    echo FAIL: You are running 32-bit Python!
    echo Download 64-bit Python from https://python.org
    pause
    exit /b 1
)
echo OK: 64-bit Python confirmed
echo.

REM [3/8] Check project structure
echo [3/8] Checking project structure...
if not exist "main.py" (
    echo FAIL: main.py not found - run from project root folder!
    pause
    exit /b 1
)
if not exist "firebase_key.json" (
    echo WARNING: firebase_key.json not found - build will fail!
)
if not exist "core" ( echo FAIL: core folder not found & pause & exit /b 1 )
if not exist "services" ( echo FAIL: services folder not found & pause & exit /b 1 )
if not exist "ui" ( echo FAIL: ui folder not found & pause & exit /b 1 )
if not exist "utils" ( echo FAIL: utils folder not found & pause & exit /b 1 )
echo OK: All required folders found

REM Check asset files required for the UI
if not exist "ui\workspace.jpeg" (
    echo FAIL: ui\workspace.jpeg not found - login background will be missing!
    pause
    exit /b 1
)
if not exist "ui\logo.PNG" (
    echo FAIL: ui\logo.PNG not found - app logo will be missing!
    pause
    exit /b 1
)
if not exist "ui\logo.ico" (
    echo WARNING: ui\logo.ico not found - generating from logo.PNG...
    python -c "from PIL import Image; img=Image.open('ui/logo.PNG').convert('RGBA'); img.save('ui/logo.ico',format='ICO',sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)]); print('Created ui\\logo.ico')"
    if errorlevel 1 (
        echo FAIL: Could not create logo.ico - install Pillow: pip install pillow
        pause
        exit /b 1
    )
)
echo OK: Asset files present
echo.

REM [4/8] Check __init__.py files
echo [4/8] Checking __init__.py files...
set MISSING_INIT=0
if not exist "core\__init__.py" (
    type nul > "core\__init__.py"
    set MISSING_INIT=1
    echo Created: core\__init__.py
)
if not exist "services\__init__.py" (
    type nul > "services\__init__.py"
    set MISSING_INIT=1
    echo Created: services\__init__.py
)
if not exist "ui\__init__.py" (
    type nul > "ui\__init__.py"
    set MISSING_INIT=1
    echo Created: ui\__init__.py
)
if not exist "utils\__init__.py" (
    type nul > "utils\__init__.py"
    set MISSING_INIT=1
    echo Created: utils\__init__.py
)
if %MISSING_INIT%==0 (
    echo OK: All __init__.py files present
)
echo.

REM [5/8] Check dependencies
echo [5/8] Checking dependencies...
set DEPS_MISSING=0

pip show PySide6 >nul 2>&1
if errorlevel 1 (
    echo MISSING: PySide6
    set DEPS_MISSING=1
) else (
    echo OK: PySide6
)

pip show firebase-admin >nul 2>&1
if errorlevel 1 (
    echo MISSING: firebase-admin
    set DEPS_MISSING=1
) else (
    echo OK: firebase-admin
)

pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo MISSING: pyinstaller
    set DEPS_MISSING=1
) else (
    echo OK: pyinstaller
)

pip show openpyxl >nul 2>&1
if errorlevel 1 (
    echo MISSING: openpyxl
    set DEPS_MISSING=1
) else (
    echo OK: openpyxl
)

pip show requests >nul 2>&1
if errorlevel 1 (
    echo MISSING: requests
    set DEPS_MISSING=1
) else (
    echo OK: requests
)

if %DEPS_MISSING%==1 (
    echo.
    echo Some dependencies are missing!
    choice /C YN /M "Install missing dependencies now"
    if errorlevel 1 pip install -r requirements.txt
)
echo.

REM [6/8] Check old build artifacts
echo [6/8] Checking for previous build artifacts...
if exist "build" (
    echo Found old build folder
    choice /C YN /M "Delete it"
    if errorlevel 1 (
        rmdir /s /q build
        echo Deleted
    )
)
if exist "dist" (
    echo Found old dist folder
    choice /C YN /M "Delete it"
    if errorlevel 1 (
        rmdir /s /q dist
        echo Deleted
    )
)
if exist "SOT.spec" (
    echo Found old SOT.spec
    choice /C YN /M "Delete it"
    if errorlevel 1 (
        del SOT.spec
        echo Deleted
    )
)
echo.

REM [7/8] Check Inno Setup
echo [7/8] Checking Inno Setup...
set INNO_FOUND=0
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set INNO_FOUND=1
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set INNO_FOUND=1
if %INNO_FOUND%==1 (
    echo OK: Inno Setup found
) else (
    echo WARNING: Inno Setup not found
    echo Download from: https://jrsoftware.org/isdl.php
)

if not exist "vc_redist.x64.exe" (
    echo WARNING: vc_redist.x64.exe not found
    echo Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe
    echo Place it in this folder
) else (
    echo OK: vc_redist.x64.exe found
)
echo.

REM [8/8] Test imports
echo [8/8] Testing Python imports...
set TEST_FAIL=0

python -c "import PySide6" 2>nul
if errorlevel 1 (
    echo FAIL: Cannot import PySide6
    set TEST_FAIL=1
) else (
    echo OK: PySide6
)

python -c "import firebase_admin" 2>nul
if errorlevel 1 (
    echo FAIL: Cannot import firebase_admin
    set TEST_FAIL=1
) else (
    echo OK: firebase_admin
)

python -c "from core import auth" 2>nul
if errorlevel 1 (
    echo FAIL: Cannot import core.auth
    set TEST_FAIL=1
) else (
    echo OK: core modules
)

python -c "import openpyxl" 2>nul
if errorlevel 1 (
    echo FAIL: Cannot import openpyxl
    set TEST_FAIL=1
) else (
    echo OK: openpyxl
)
echo.

REM Result
echo ========================================
echo  Diagnostic Complete
echo ========================================
echo.

if %TEST_FAIL%==1 (
    echo ISSUES DETECTED - fix errors above before building
    pause
    exit /b 1
)

echo ALL CHECKS PASSED - Ready to build!
echo.
choice /C YN /M "Start building now"
if errorlevel 2 goto end
call build.bat

:end
pause