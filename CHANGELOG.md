# 更新記錄

## 2026-11-13

- README 改成標準格式（一鍵安裝、徽章、導覽、優點總整理、流程圖、常見問題、名詞解釋、參考來源）。
- 新增 `INSTALL.bat` 一鍵安裝（Python 套件、Playwright Chromium、FFmpeg、建立 `.env`）。
- 個資清理：程式碼不再寫死 Gmail 帳號，改讀 `.env` 的 `YOUTUBE_CHANNEL_EMAIL`；移除寫死的 `C:\Users\...` 路徑；啟動批次檔改用相對路徑。
- 執行狀態檔（上傳佇列、發布紀錄、點數帳本等）移出版控並加入 `.gitignore`，程式第一次執行會自動重新建立。
- 修正 `main_pipeline.py` 章節標題 f-string 的語法錯誤（原本主程式無法啟動）。

## 2026-11-13（第二版）

- 預設 README 改成英文，另附 `README.zh-TW.md`、`README.zh-CN.md` 與語言切換列。
- 新增 `CONTRIBUTING.md`、`SECURITY.md`。
