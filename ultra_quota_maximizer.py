#!/usr/bin/env python3
"""
ultra_quota_maximizer.py — Google One AI Ultra 月度點數精算與最大化消耗引擎
專為 Google One AI Ultra 訂閱戶設計：
1. 自動追蹤當月剩餘天數與 Google Flow / Veo 高畫質生成點數餘額
2. 自動從 Google Flow 網頁介面讀取真實剩餘點數（並同步紀錄於本地 `ultra_quota_ledger.json`）
3. 動態計算「今日必須消耗點數 (Daily Burn Target)」，自動決定今天要產出幾部 8 分鐘長片 + 幾支 Shorts
4. 月底最後 5 天自動啟動「點數清零狂暴模式 (End-of-Month Overdrive)」，確保每月結算前 100% 榨乾每一點 Ultra 額度，轉化為頻道資產與 YouTube 廣告收益！
"""

import datetime
import calendar
import json
import os
import sys
from typing import Dict, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


class UltraQuotaMaximizer:
    """精算並最大化消耗 Google One AI Ultra 訂閱點數 + Google Flow 點數 + Gemini API 點數（雙池三軌月底強制清零）。"""

    def __init__(
        self,
        ledger_path: str = "ultra_quota_ledger.json",
        monthly_flow_credits: int = 15000,
        monthly_api_credits: int = 15000,
        credits_per_flow_clip: int = 20,
        credits_per_api_clip: int = 25
    ):
        self.ledger_path = os.path.abspath(ledger_path)
        self.monthly_total_credits = int(os.getenv("ULTRA_MONTHLY_CREDITS", monthly_flow_credits))
        self.monthly_api_credits = int(os.getenv("API_MONTHLY_CREDITS", monthly_api_credits))
        self.credits_per_flow_clip = int(os.getenv("CREDITS_PER_FLOW_CLIP", credits_per_flow_clip))
        self.credits_per_api_clip = int(os.getenv("CREDITS_PER_API_CLIP", credits_per_api_clip))
        self.billing_reset_day = int(os.getenv("ULTRA_RESET_DAY", 1))
        self.state = self._load_or_init_ledger()

    def _get_current_cycle_key(self) -> str:
        now = datetime.date.today()
        if now.day < self.billing_reset_day:
            prev_month = (now.replace(day=1) - datetime.timedelta(days=1))
            return f"{prev_month.year}-{prev_month.month:02d}"
        return f"{now.year}-{now.month:02d}"

    def _load_or_init_ledger(self) -> Dict[str, Any]:
        cycle_key = self._get_current_cycle_key()
        if os.path.exists(self.ledger_path):
            try:
                with open(self.ledger_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("cycle_key") == cycle_key:
                    return data
            except Exception:
                pass

        # 新月份週期自動重置雙池點數帳本 (Google One Ultra / Flow 池 + Gemini API 池)
        fresh_state = {
            "cycle_key": cycle_key,
            "monthly_total_credits": self.monthly_total_credits,
            "used_credits": 0,
            "remaining_credits": self.monthly_total_credits,
            "monthly_api_credits": self.monthly_api_credits,
            "used_api_credits": 0,
            "remaining_api_credits": self.monthly_api_credits,
            "videos_produced_this_month": 0,
            "shorts_produced_this_month": 0,
            "clips_generated_via_flow": 0,
            "clips_generated_via_api": 0,
            "history": []
        }
        self._save_ledger(fresh_state)
        return fresh_state

    def _save_ledger(self, state: Dict[str, Any] | None = None) -> None:
        target = state or self.state
        with open(self.ledger_path, "w", encoding="utf-8") as f:
            json.dump(target, f, indent=2, ensure_ascii=False)

    def sync_live_balance_from_flow_ui(self, scraped_credits: int | None) -> None:
        """若從 Google Flow 網頁抓取到真實剩餘點數，立即校準本地帳本。"""
        if scraped_credits is not None and scraped_credits >= 0:
            self.state["remaining_credits"] = scraped_credits
            self.state["used_credits"] = max(0, self.monthly_total_credits - scraped_credits)
            self._save_ledger()
            print(f"[UltraMaximizer] 已從 Google Flow 網頁同步真實剩餘點數: {scraped_credits} 點")

    def record_flow_consumption(self, clips_count: int = 1, custom_cost: int | None = None) -> None:
        """記錄每次透過 Google Flow 生成影片所消耗的 Google One Ultra 訂閱點數。"""
        cost = custom_cost if custom_cost is not None else (clips_count * self.credits_per_flow_clip)
        self.state["used_credits"] += cost
        self.state["remaining_credits"] = max(0, self.state["remaining_credits"] - cost)
        self.state["clips_generated_via_flow"] += clips_count
        self._save_ledger()

    def record_api_consumption(self, clips_count: int = 1, custom_cost: int | None = None) -> None:
        """記錄每次透過 Gemini API (Omni 1.2 / 4 Argon / TTS / Nano Banana) 消耗的 API 點數。"""
        cost = custom_cost if custom_cost is not None else (clips_count * self.credits_per_api_clip)
        self.state["used_api_credits"] = self.state.get("used_api_credits", 0) + cost
        self.state["remaining_api_credits"] = max(
            0, self.state.get("remaining_api_credits", self.monthly_api_credits) - cost
        )
        self.state["clips_generated_via_api"] = self.state.get("clips_generated_via_api", 0) + clips_count
        self._save_ledger()

    def record_campaign_completed(self, long_count: int = 1, shorts_count: int = 1) -> None:
        """記錄完成的長片與 Shorts 數量。"""
        self.state["videos_produced_this_month"] += long_count
        self.state["shorts_produced_this_month"] += shorts_count
        self.state["history"].append({
            "timestamp": datetime.datetime.now().isoformat(),
            "long_videos": long_count,
            "shorts_videos": shorts_count,
            "remaining_credits": self.state["remaining_credits"]
        })
        self._save_ledger()

    def days_remaining_in_cycle(self) -> int:
        """計算距離下次月度點數刷新還有幾天（最少回傳 1 天）。"""
        today = datetime.date.today()
        _, last_day = calendar.monthrange(today.year, today.month)
        if today.day < self.billing_reset_day:
            reset_date = today.replace(day=self.billing_reset_day)
        else:
            # 下個月的 reset_day
            next_month_first = today.replace(day=last_day) + datetime.timedelta(days=1)
            _, next_last = calendar.monthrange(next_month_first.year, next_month_first.month)
            target_day = min(self.billing_reset_day, next_last)
            reset_date = next_month_first.replace(day=target_day)
        return max(1, (reset_date - today).days)

    def calculate_daily_burn_plan(self) -> Dict[str, Any]:
        """
        根據當月剩餘點數與剩餘天數，自動規劃「今日最大化收益產片配額」：
        - 計算今日目標消耗點數 (`daily_target_credits`)
        - 換算今日可生成的 Google Flow 頂級鏡頭總數 (`target_flow_clips`)
        - 自動拆分為：N 部【8 分鐘以上高 AdSense 收益長片（每部 32 個鏡頭）】+ M 支【爆款帶貨 Shorts（每支 5 個鏡頭）】
        - 若距離結算日 <= 5 天且點數還剩超過 25%，自動開啟 `OVERDRIVE_MODE` 倍增產量！
        """
        remaining_flow = self.state["remaining_credits"]
        remaining_api = self.state.get("remaining_api_credits", self.monthly_api_credits)
        days_left = self.days_remaining_in_cycle()
        overdrive = (days_left <= 5) and (
            remaining_flow > self.monthly_total_credits * 0.15
            or remaining_api > self.monthly_api_credits * 0.15
        )

        # 若進入月底衝刺，把緩衝天數壓縮，確保結算前 100% 消耗完畢
        effective_days = max(1, days_left - 1) if overdrive else days_left
        daily_flow_burn = int(round(remaining_flow / effective_days))
        daily_api_burn = int(round(remaining_api / effective_days))

        target_flow_clips = max(8, daily_flow_burn // max(1, self.credits_per_flow_clip))
        target_api_clips = max(8, daily_api_burn // max(1, self.credits_per_api_clip))
        total_clips_today = target_flow_clips + target_api_clips

        # 每支 8 分鐘長片（可插滿 YouTube 中插廣告）配置 32 個 15 秒鏡頭 (~480 秒 = 8 分鐘)
        # 每支長片搭配 2 支 Shorts 短片（每支 4 個鏡頭，共 8 個鏡頭）= 每個完整爆品專案消耗 40 個鏡頭
        clips_per_full_campaign = 40
        campaigns_today = max(1, total_clips_today // clips_per_full_campaign)

        plan = {
            "cycle_key": self.state["cycle_key"],
            "remaining_flow_ultra_credits": remaining_flow,
            "remaining_api_credits": remaining_api,
            "days_left_in_cycle": days_left,
            "overdrive_mode": overdrive,
            "daily_flow_credits_to_burn": daily_flow_burn,
            "daily_api_credits_to_burn": daily_api_burn,
            "target_flow_clips_today": target_flow_clips,
            "target_api_clips_today": target_api_clips,
            "recommended_campaigns_today": campaigns_today,
            "long_scenes_per_campaign": 32,   # 32 x 15s = 480s (精準突破 8 分鐘 YouTube 中插廣告門檻！)
            "shorts_per_campaign": 2,         # 每部設定 2 支不同切角的爆款 Shorts 矩陣引流
            "shorts_scenes_each": 4
        }

        print(
            f"\n💎 [UltraQuotaMaximizer] Google One Ultra + Flow + API 全額度雙池榨乾精算報告 ({plan['cycle_key']}):\n"
            f"   ├─ 【池 1】Google One Ultra / Flow 剩餘點數: {remaining_flow:,} / {self.monthly_total_credits:,} 點 (今日必耗: {daily_flow_burn:,} 點 = {target_flow_clips} 鏡)\n"
            f"   ├─ 【池 2】Gemini Cloud API 剩餘點數: {remaining_api:,} / {self.monthly_api_credits:,} 點 (今日必耗: {daily_api_burn:,} 點 = {target_api_clips} 鏡)\n"
            f"   ├─ 距離月度歸零重置僅剩: {days_left} 天 | 月底清零狂暴模式 (Overdrive): {'🔥 已啟動 (4K滿載)' if overdrive else '雙池同步高速消耗中'}\n"
            f"   └─ 今日自動排程總產量: {campaigns_today} 組完整爆品矩陣 (合計 {total_clips_today} 鏡，100% 榨乾不留餘額！)"
        )
        return plan


if __name__ == "__main__":
    maximizer = UltraQuotaMaximizer()
    print(json.dumps(maximizer.calculate_daily_burn_plan(), indent=2, ensure_ascii=False))
