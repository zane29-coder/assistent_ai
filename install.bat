@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Python virtual muhit yaratilmoqda...
python -m venv .venv
if errorlevel 1 (
  echo Python topilmadi. python.org dan Python 3.10+ ni o'rnating va "Add python.exe to PATH" belgisini qo'ying.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
echo.
echo O'rnatish tugadi. Endi run.bat ni ishga tushiring.
pause
