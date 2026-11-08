#!/usr/bin/env python3
"""
daemon_24_7.py — 雲端 (Gemini API + Google Flow) + 本地端 (RTX 3070 NVENC) 24/7 雙軌全自動印鈔常駐引擎
功能：
1. 雲端與本地端雙軌協同：
   - 雲端軌道 (Cloud Track)：自動以 15s 快速超時機制呼叫 Gemini 雲端模型與 Google Flow，最大化消耗 Google One Ultra 與 API 點數，絕不因 429 限流而卡死。
   - 本地軌道 (Local RTX 3070 Track)：同步使用本地 i7-11800H + RTX 3070 (`h264_nvenc`) 進行高速平行分鏡渲染、混音、字幕燒錄與 YouTube Studio 自動上片。
2. 自動輪詢 GitHub Trending、Hacker News 與 Google Trends，確保每次產出的主題不重複（自動記錄於 `published_history.json`）。
3. 24/7 全天候常駐循環執行，並即時寫入狀態日誌 `daemon_status.json` 與 `daemon_24_7.log`。
"""

import datetime
import json
import os
import sys
import time
import traceback
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from main_pipeline import run_empire_pipeline
from trend_hunter import TrendHunter
from ultra_quota_maximizer import UltraQuotaMaximizer


HISTORY_FILE = "published_history.json"
STATUS_FILE = "daemon_status.json"


def load_published_topics() -> list:
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_published_topic(topic: str, summary: dict) -> None:
    history = load_published_topics()
    history.append({
        "topic": topic,
        "timestamp": datetime.datetime.now().isoformat(),
        "long_video": summary.get("long_video_path"),
        "shorts_video": summary.get("shorts_video_path"),
        "long_title": summary.get("long_title")
    })
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def update_daemon_status(state: str, detail: str, extra: dict | None = None) -> None:
    payload = {
        "updated_at": datetime.datetime.now().isoformat(),
        "state": state,
        "detail": detail,
        "hardware": "Cloud API + Local Intel i7-11800H & NVIDIA RTX 3070 (h264_nvenc)"
    }
    if extra:
        payload.update(extra)
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def pick_next_interleaved_topic(cycle_num: int) -> tuple[str | None, int]:
    """
    【9:1 爆款影片主導策略（10 片中 9 片爆款影片 + 1 片 GitHub）】：
    - 每 10 支影片中，第 1~9 支 (`cycle_num % 10 != 0`) 100% 全部鎖定 YouTube 高流量爆款影片進行拆解翻拍與片長對標！
    - 僅第 10 支 (`cycle_num % 10 == 0`) 穿插 1 支 GitHub Trending 暴增開源神器（若當下有破 15 萬觀看的超級爆款仍優先拍爆款）。
    """
    hunter = TrendHunter(geo=os.getenv("TREND_GEO", "TW"))
    published_raw = [item.get("topic", "") for item in load_published_topics()]

    def _is_already_published(key_str: str) -> bool:
        for p in published_raw:
            if key_str in p or p in key_str:
                return True
        return False

    # 多領域高 CPM 爆款影片搜索池輪替，確保 90% 爆款影片題材豐富不撞題
    viral_queries = [
        "AI 神器 實測 教學",
        "免費 AI 工具 效率 2026",
        "ChatGPT Gemini 隱藏功能 教學",
        "一人公司 AI 自動化 變現",
        "AI 繪圖 影片生成 免費工具",
        "科技黑科技 生產力工具 推薦"
    ]
    selected_query = viral_queries[(cycle_num - 1) % len(viral_queries)]
    yt_virals = hunter.fetch_youtube_viral_competitor_videos(query=selected_query, limit=10)
    breaking_viral = None
    for v in yt_virals:
        if not _is_already_published(v["title"]):
            breaking_viral = v
            break

    # 嚴格執行「10 片中 9 片爆款影片 (cycle_num % 10 != 0) + 1 片 GitHub (cycle_num % 10 == 0)」
    is_viral_slot = (cycle_num % 10 != 0)
    if is_viral_slot and breaking_viral:
        target_dur = breaking_viral.get("duration_sec", 520)
        matched_scenes = max(16, min(24, round(target_dur / 28)))
        topic_str = f"【對標爆款 {breaking_viral['view_count']:,} 觀看】{breaking_viral['title']}"
        print(
            f"🚨 [9:1 爆款主力引擎 (第 {cycle_num} 輪)] 鎖定高流量爆款影片：{topic_str} "
            f"(原片長 {target_dur}s -> 自動對標設定 {matched_scenes} 個深度分鏡)！"
        )
        return topic_str, matched_scenes

    # 每 10 片的第 10 片 (cycle_num % 10 == 0)：抓取 1 支 GitHub Trending 爆紅開源專案
    gh_repos = hunter.fetch_github_trending_repos(limit=15)
    for repo in gh_repos:
        rname = repo["repo_name"]
        if not _is_already_published(rname):
            gh_topic = f"{rname} (GitHub {repo['stars']}+ Stars AI 神器)"
            print(f"🚨 [9:1 唯一 GitHub 精選位 (第 {cycle_num} 輪)] 鎖定 GitHub 飆升榜開源專案：{gh_topic} (24 個深度分鏡)！")
            return gh_topic, 24

    # 備援：Google Trends 即時熱搜爆款
    trends = hunter.fetch_google_trends_rss(limit=10)
    for tr in trends:
        kw = tr.get("keyword")
        if kw and not _is_already_published(kw):
            return f"【對標全網熱搜爆款】{kw} 深度實測與完整教學", 16

    hn_list = hunter.fetch_hackernews_top_tools(limit=10)
    for hn in hn_list:
        candidate = hn.get("title")
        if candidate and not _is_already_published(candidate):
            return candidate, 16

    return None, 16


def run_24_7_hybrid_daemon(interval_minutes: int = 60, auto_upload: bool = False):
    load_dotenv()
    print("=" * 76)
    print("🔥 [YT-Auto-Empire 24/7 Daemon] 雲端 + 本地 RTX 3070 雙軌全自動常駐引擎已啟動！")
    print("   ├─ 雲端修正：已啟用 15 秒無阻塞 Fast-Fail + Google Flow 1080p 最佳模型")
    print("   ├─ 本地加速：已啟用 NVIDIA GeForce RTX 3070 (h264_nvenc) 硬體光速編碼")
    print("   ├─ 四維度爆款檢視：逐一審核【內容 / 音樂 / 背景人物3D動畫 / 背景文字與字幕】達標 (>=92分)")
    print("   └─ 人工審閱守門員：完片自動歸檔至 Google 雲端硬碟最新檢閱資料夾，待使用者 Review 核准後才上傳 YouTube！")
    print("=" * 76)

    cycle_num = max(1, len(load_published_topics()) + 1)
    while True:
        try:
            maximizer = UltraQuotaMaximizer()
            burn_plan = maximizer.calculate_daily_burn_plan()
            fresh_topic, matched_long_scenes = pick_next_interleaved_topic(cycle_num)

            update_daemon_status(
                state="RUNNING_CAMPAIGN",
                detail=f"正在執行第 {cycle_num} 輪交叉雙軌產片 (主題: {fresh_topic or '自動探測'} | 分鏡數: {matched_long_scenes})",
                extra={"cycle": cycle_num, "burn_plan": burn_plan}
            )

            summary = run_empire_pipeline(
                custom_topic=fresh_topic,
                engine_mode="flow",
                long_scenes=matched_long_scenes,
                shorts_scenes=4,
                auto_upload=auto_upload
            )
            save_published_topic(fresh_topic or summary.get("product", "Unknown"), summary)

            update_daemon_status(
                state="IDLE_WAITING_NEXT_WAVE",
                detail=f"第 {cycle_num} 輪完成！將於 {interval_minutes} 分鐘後啟動下一輪爆品產製。",
                extra={"last_completed_summary": summary}
            )
            print(f"\n✅ [Daemon] 第 {cycle_num} 輪產片與上片完成！休眠 {interval_minutes} 分鐘後繼續榨乾點數...")
            cycle_num += 1
            time.sleep(interval_minutes * 60)

        except Exception as e:
            err_msg = f"第 {cycle_num} 輪發生例外 ({e})，60 秒後自動自癒重啟！"
            print(f"⚠️ [Daemon 自癒機制] {err_msg}")
            traceback.print_exc()
            update_daemon_status(state="RECOVERING", detail=err_msg)
            time.sleep(60)


if __name__ == "__main__":
    run_24_7_hybrid_daemon(interval_minutes=45, auto_upload=False)
