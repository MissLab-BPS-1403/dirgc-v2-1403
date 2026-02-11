@echo off
echo ============================================
echo Instalasi Library MatchaPro Automation
echo ============================================

REM Pastikan Python sudah terpasang dan ada di PATH

echo.
echo >> Meng-upgrade pip...
python -m pip install --upgrade pip

echo.
echo >> Meng-install dependencies utama...
python -m pip install playwright pandas openpyxl PyQt5 PyQt-Fluent-Widgets

echo.
echo >> Meng-install browser Chromium untuk Playwright...
python -m playwright install chromium

echo.
echo ============================================
echo Instalasi selesai!
echo ============================================

pause