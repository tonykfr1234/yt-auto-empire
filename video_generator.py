#!/usr/bin/env python3
"""
video_generator.py — 雙引擎影片生成模組 (Gemini Omni 1.2 Flash API + Google Flow 網頁操控 + 本地動態科技分鏡引擎)
支援：
1. 透過 Playwright 持久化 Chrome Profile 直接操控 Google Flow (`https://labs.google/fx/tools/flow`)
   網頁介面生成電影級連續鏡頭，並同步消耗與追蹤 Google One AI Ultra 月度點數。
2. 透過官方 `google-genai` Interactions API 呼叫 `gemini-omni-1.2-flash` 批次生成 16:9 與 9:16 高畫質影片片段。
3. 當處於離線、尚未登入 Google Flow 或未設定 API Key 時，自動啟動本地「Cyber-Tech 動態視覺運鏡渲染器 (Pillow + FFmpeg Zoompan)」，
   確保全自動流水線 100% 產出高質感 1080p 分鏡影片！
"""

import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types
from PIL import Image, ImageDraw, ImageFont
from ultra_quota_maximizer import UltraQuotaMaximizer
from viral_broll_engine import ViralVisualEngine


class DualVideoGenerator:
    """結合 Google Flow 網頁自動化、Gemini Omni 1.2 API 與本地動態運鏡保底的三重影片生成器。"""

    def __init__(
        self,
        engine_mode: str = "ultra",
        resolution: str = "1080p",
        chrome_user_data_dir: str = "./chrome_profile",
        quota_maximizer: Optional[UltraQuotaMaximizer] = None
    ):
        self.engine_mode = engine_mode.lower()  # "ultra", "flow", "api", "hybrid"
        self.resolution = resolution
        self.chrome_user_data_dir = os.path.abspath(chrome_user_data_dir)
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = (
            genai.Client(http_options=types.HttpOptions(timeout=45_000))
            if self.api_key
            else None
        )
        self.quota_maximizer = quota_maximizer or UltraQuotaMaximizer()

    def generate_clip_via_local_kinetic_studio(
        self,
        scene: Dict[str, Any],
        output_path: str,
        aspect_ratio: str = "16:9",
        duration_sec: int = 10
    ) -> str:
        """
        百萬訂閱級多鏡頭實機 B-Roll 動態渲染器：
        自動擷取真實 GitHub 專案網頁捲動畫面、60fps macOS 暗黑終端機即時打字動畫與動態暴衝數據儀表板，
        每 3.5 秒自動進行閃白快切 (Jump-Cut)，徹底拒絕陽春靜態簡報！
        """
        engine = ViralVisualEngine(work_dir=os.path.dirname(output_path))
        github_url = scene.get("github_url", "https://github.com/KKKKhazix/agent-autoloop")
        return engine.render_high_retention_broll_clip(
            scene=scene,
            output_mp4=output_path,
            aspect_ratio=aspect_ratio,
            duration_sec=duration_sec,
            github_url=github_url
        )

    def generate_clip_via_omni_api(
        self,
        scene: Dict[str, Any],
        output_path: str,
        aspect_ratio: str = "16:9",
        duration_sec: int = 10
    ) -> str:
        """
        使用 Gemini Omni 1.2 Flash (`gemini-omni-1.2-flash`) 官方 Interactions API 生成影片並下載。
        若未配置 API Key，自動切換至本地動態運鏡渲染器。
        """
        if not self.client:
            return self.generate_clip_via_local_kinetic_studio(
                scene=scene,
                output_path=output_path,
                aspect_ratio=aspect_ratio,
                duration_sec=duration_sec
            )

        prompt = scene["visual_prompt"]
        duration_clamped = max(3, min(15, int(duration_sec)))
        print(
            f"[VideoGenerator/OmniAPI] 生成中 ({aspect_ratio}, {duration_clamped}s, {self.resolution}): "
            f"{prompt[:50]}..."
        )

        try:
            ex = ThreadPoolExecutor(max_workers=1)
            fut = ex.submit(
                lambda: self.client.interactions.create(
                    model="gemini-omni-1.2-flash",
                    input=[{"type": "text", "text": prompt}],
                    response_format={
                        "type": "video",
                        "delivery": "uri",
                        "aspect_ratio": aspect_ratio,
                        "duration": f"{duration_clamped}s",
                        "resolution": self.resolution
                    }
                )
            )
            try:
                interaction = fut.result(timeout=20.0)
            finally:
                ex.shutdown(wait=False, cancel_futures=True)

            output_video = interaction.output_video
            if not output_video or not output_video.uri:
                raise RuntimeError(f"Gemini Omni 1.2 Flash 未回傳影片 URI: {prompt}")

            video_bytes = self.client.files.download(file=output_video.uri)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(video_bytes)

            self.quota_maximizer.record_api_consumption(clips_count=1)
            print(
                f"[VideoGenerator/OmniAPI] 雲端 AI 影片片段已儲存: {output_path} "
                f"(當月剩餘 API 點數: {self.quota_maximizer.state.get('remaining_api_credits', 0):,})"
            )
            return output_path
        except Exception as e:
            print(f"[VideoGenerator/OmniAPI] 雲端算圖 20s 快速切換至本地 RTX 3070 動態運鏡引擎 ({e})！")
            return self.generate_clip_via_local_kinetic_studio(
                scene=scene,
                output_path=output_path,
                aspect_ratio=aspect_ratio,
                duration_sec=duration_sec
            )

    def generate_clip_via_google_flow_web(
        self,
        scene: Dict[str, Any],
        output_path: str,
        aspect_ratio: str = "16:9",
        duration_sec: int = 10
    ) -> str:
        """
        使用 Playwright 啟動持久化 Chrome 設定檔，直接開啟 Google Flow (`https://labs.google/fx/tools/flow`)
        自動填入分鏡 Prompt、觸發生成並攔截/下載產出的 MP4 影片。
        若尚未登入 Google 帳號，會自動切換至 Gemini Omni 1.2 Flash API 或本地動態運鏡引擎保底完成生成。
        """
        prompt = scene["visual_prompt"]
        print(f"[VideoGenerator/GoogleFlow] 正在啟動瀏覽器操控 Google Flow 網頁引擎: {prompt[:45]}...")
        try:
            import shutil
            from playwright.sync_api import sync_playwright

            local_app_data = os.environ.get("LOCALAPPDATA", "C:/Users/tonyk/AppData/Local")
            src_user_data = os.path.join(local_app_data, "Google", "Chrome", "User Data")
            flow_profile_dir = os.path.abspath("chrome_flow_tonykfr1234")
            os.makedirs(flow_profile_dir, exist_ok=True)

            # 自動同步 tonykfr1234@gmail.com 的 Chrome Default 憑證設定檔
            local_state_src = os.path.join(src_user_data, "Local State")
            local_state_dst = os.path.join(flow_profile_dir, "Local State")
            if os.path.exists(local_state_src) and not os.path.exists(local_state_dst):
                shutil.copy2(local_state_src, local_state_dst)

            default_src = os.path.join(src_user_data, "Default")
            default_dst = os.path.join(flow_profile_dir, "Default")
            if os.path.exists(default_src) and not os.path.exists(default_dst):
                shutil.copytree(
                    default_src,
                    default_dst,
                    ignore=shutil.ignore_patterns("Cache*", "Code Cache*", "GPUCache*", "Service Worker*", "*.lock", "LOCK"),
                    dirs_exist_ok=True
                )

            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=flow_profile_dir,
                    channel="chrome",
                    headless=True,
                    accept_downloads=True,
                    args=[
                        "--profile-directory=Default",
                        "--disable-blink-features=AutomationControlled"
                    ]
                )
                page = context.pages[0] if context.pages else context.new_page()
                page.goto("https://labs.google/fx/tools/flow", timeout=25000)
                page.wait_for_load_state("domcontentloaded", timeout=15000)

                # 自動偵測並同步 Google Flow 網頁上的 Google One Ultra 真實剩餘點數
                try:
                    body_text = page.locator("body").inner_text(timeout=3000)
                    credit_match = re.search(r"([\d,]+)\s*(?:credits|點|點數)", body_text, re.IGNORECASE)
                    if credit_match:
                        live_credits = int(credit_match.group(1).replace(",", ""))
                        self.quota_maximizer.sync_live_balance_from_flow_ui(live_credits)
                except Exception:
                    pass

                # 尋找 Google Flow 的提示詞輸入框
                prompt_box = page.locator(
                    "textarea, [contenteditable='true'], input[type='text']"
                ).first
                if prompt_box.count() == 0:
                    context.close()
                    raise RuntimeError("Google Flow 尚未完成首次 Google 帳號登入授權。")

                prompt_box.click()
                prompt_box.fill(prompt)
                page.keyboard.press("Enter")

                with page.expect_download(timeout=180000) as download_info:
                    download_btn = page.locator(
                        "button:has-text('Download'), a[download], [aria-label*='Download']"
                    ).first
                    download_btn.wait_for(state="visible", timeout=150000)
                    download_btn.click()

                download = download_info.value
                download.save_as(output_path)
                context.close()
                self.quota_maximizer.record_flow_consumption(clips_count=1)
                print(
                    f"[VideoGenerator/GoogleFlow] 網頁生成並下載成功: {output_path} "
                    f"(當月剩餘 Ultra 點數: {self.quota_maximizer.state['remaining_credits']:,})"
                )
                return output_path

        except Exception as e:
            print(
                f"[VideoGenerator/GoogleFlow] 網頁登入狀態提示 ({e}) -> "
                f"自動無縫切換至備援渲染引擎，確保全自動產片不中斷！"
            )
            return self.generate_clip_via_omni_api(
                scene=scene,
                output_path=output_path,
                aspect_ratio=aspect_ratio,
                duration_sec=duration_sec
            )

    def render_scene_clip(
        self,
        scene: Dict[str, Any],
        output_path: str,
        aspect_ratio: str = "16:9"
    ) -> str:
        """根據模式 (ultra / flow / api / hybrid) 與分鏡標記決定使用哪個引擎生成該片段。"""
        if os.path.exists(output_path) and os.path.getsize(output_path) > 10_000:
            print(f"[VideoGenerator] 發現已存在的片段，跳過重複生成: {output_path}")
            return output_path

        duration = scene.get("duration_sec", 10)
        use_flow = scene.get("use_google_flow", False)
        has_ultra_credits = self.quota_maximizer.state["remaining_credits"] >= self.quota_maximizer.credits_per_flow_clip

        if (
            self.engine_mode == "flow"
            or (self.engine_mode == "ultra" and has_ultra_credits)
            or (self.engine_mode == "hybrid" and use_flow and has_ultra_credits)
        ):
            return self.generate_clip_via_google_flow_web(
                scene=scene,
                output_path=output_path,
                aspect_ratio=aspect_ratio,
                duration_sec=duration
            )
        else:
            return self.generate_clip_via_omni_api(
                scene=scene,
                output_path=output_path,
                aspect_ratio=aspect_ratio,
                duration_sec=duration
            )

    def batch_render_scenes(
        self,
        scenes: List[Dict[str, Any]],
        clips_dir: str,
        aspect_ratio: str = "16:9",
        concurrency: int = 2
    ) -> List[str]:
        """平行批次渲染多個分鏡片段，大幅縮短影片製作時間。"""
        os.makedirs(clips_dir, exist_ok=True)
        ordered_paths: Dict[int, str] = {}

        # 第一次先測試首個分鏡是否需走瀏覽器或直接走高速渲染
        workers = 1 if self.engine_mode == "flow" else concurrency

        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_sid = {}
            for scene in scenes:
                sid = scene["scene_id"]
                out_path = os.path.join(clips_dir, f"scene_{sid:02d}.mp4")
                future = executor.submit(self.render_scene_clip, scene, out_path, aspect_ratio)
                future_to_sid[future] = sid

            for future in as_completed(future_to_sid):
                sid = future_to_sid[future]
                ordered_paths[sid] = future.result()

        return [ordered_paths[s["scene_id"]] for s in scenes]
