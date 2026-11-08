#!/usr/bin/env python3
"""
login_session.py — Google One AI Ultra (Google Flow) & YouTube Studio 首次登入綁定工具
啟動持久化 Chrome 設定檔 (`./chrome_profile`)，一次開啟：
- 分頁 1: Google Flow (`https://labs.google/fx/tools/flow`) — 消耗 Google One Ultra 點數生成頂級影片
- 分頁 2: YouTube Studio (`https://studio.youtube.com`) — 自動上傳長影片與 Shorts 短片
- 分頁 3: Google AI Studio (`https://aistudio.google.com/apikey`) — 快速複製你的 GEMINI_API_KEY

只要在此瀏覽器登入一次你的 Google One Ultra 帳號，登入狀態與 Cookie 就會永久保存在
`chrome_profile` 資料夾中，之後全自動流水線即可 24/7 無人值守操作！
"""

import os
import sys
import time
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def launch_login_browser():
    profile_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "chrome_profile"))
    os.makedirs(profile_dir, exist_ok=True)

    print("=" * 72)
    print("🔓 正在啟動持久化 Chrome 瀏覽器，請在彈出的視窗中登入你的 Google One Ultra 帳號！")
    print(f"📁 登入狀態將永久保存於: {profile_dir}")
    print("=" * 72)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            channel="chrome",
            headless=False,
            no_viewport=True,
            args=[
                "--start-maximized",
                "--remote-debugging-port=9222",
                "--disable-blink-features=AutomationControlled"
            ]
        )

        # 分頁 1: Google Flow (flow.google.com)
        flow_page = context.pages[0] if context.pages else context.new_page()
        flow_page.goto("https://flow.google.com/", wait_until="domcontentloaded")

        # 分頁 2: YouTube Studio (用於網頁版自動上片與頻道管理)
        yt_page = context.new_page()
        yt_page.goto("https://studio.youtube.com", wait_until="domcontentloaded")

        # 分頁 3: Google AI Studio API Key 頁面
        api_page = context.new_page()
        api_page.goto("https://aistudio.google.com/apikey", wait_until="domcontentloaded")

        # 切回第一個分頁 (Google Flow)
        flow_page.bring_to_front()

        print("\n✅ 瀏覽器已開啟 3 個分頁：")
        print("   1. Google Flow (請確認登入並進入可輸入 Prompt 的畫面)")
        print("   2. YouTube Studio (請確認已切換至你要衝流量的目標 YouTube 頻道)")
        print("   3. Google AI Studio (可順手複製 GEMINI_API_KEY)")
        print("\n👉 登入完成後，你可以直接關閉該瀏覽器視窗，或在對話框告訴我「登入好了」！")

        try:
            while len(context.pages) > 0:
                time.sleep(1)
        except Exception:
            pass

        print("✅ 瀏覽器視窗已關閉，Google One Ultra 與 YouTube 登入狀態已成功綁定保存！")


if __name__ == "__main__":
    launch_login_browser()
