@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo  YT-Auto-Empire 一鍵安裝
echo ============================================================
where python >nul 2>&1 || (echo [錯誤] 找不到 Python，請先安裝 Python 3.12 以上並勾選 Add to PATH & pause & exit /b 1)
where ffmpeg >nul 2>&1 || (echo [提醒] 找不到 FFmpeg，正在用 winget 安裝... & winget install -e --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements)
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt || (echo [錯誤] 套件安裝失敗 & pause & exit /b 1)
python -m playwright install chromium
if not exist .env (copy .env.example .env >nul & echo [完成] 已建立 .env，請打開填入 GEMINI_API_KEY 與 YOUTUBE_CHANNEL_EMAIL)
echo.
echo [完成] 安裝結束。下一步：
echo   1. 打開 .env 填好金鑰
echo   2. 雙擊「啟動_Google_Flow_專屬專案綁定.bat」登入 Google 一次
echo   3. 執行 python main_pipeline.py 產出第一支影片
pause
