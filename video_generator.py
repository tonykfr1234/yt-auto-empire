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
import threading
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
        self._flow_lock = threading.Lock()
        self._flow_auth_ready = True

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

    def _load_or_save_flow_project_url(self, new_url: Optional[str] = None) -> Optional[str]:
        """讀取或保存 Google Flow 專屬固定專案網址 (`flow_project_state.json`)，確保所有 YouTube 影片都在同一個專屬專案內生成。"""
        import json
        state_file = os.path.abspath("flow_project_state.json")
        project_name = os.getenv("FLOW_PROJECT_NAME", "YT-Auto-Empire YouTube 爆款影片總部")
        if new_url and ("/project/" in new_url or "flow.google.com" in new_url) and "/about" not in new_url:
            payload = {
                "project_name": project_name,
                "project_url": new_url,
                "model": "Veo 3.1 - Quality (Highest Quality 1080p)",
                "resolution": "1080p"
            }
            try:
                with open(state_file, "w", encoding="utf-8") as f:
                    json.dump(payload, f, indent=2, ensure_ascii=False)
            except Exception:
                pass
            return new_url

        if os.path.exists(state_file):
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("project_url")
            except Exception:
                return None
        return None

    def _connect_flow_browser(self, p, flow_profile_dir: str):
        """
        優先順序：
        1. 檢查使用者主 Chrome (`User Data/DevToolsActivePort`) 是否已開啟 `chrome://inspect/#remote-debugging`
        2. 檢查本地 CDP 9222 埠 (`http://127.0.0.1:9222`)
        3. 啟動持久化 `chrome_profile`
        """
        local_app_data = os.environ.get("LOCALAPPDATA", os.path.expanduser("~/AppData/Local"))
        active_port_file = os.path.join(local_app_data, "Google", "Chrome", "User Data", "DevToolsActivePort")
        if os.path.exists(active_port_file):
            try:
                with open(active_port_file, "r", encoding="utf-8") as f:
                    lines = [ln.strip() for ln in f.read().splitlines() if ln.strip()]
                if lines:
                    port = int(lines[0])
                    ws_path = lines[1] if len(lines) > 1 else ""
                    endpoint = f"ws://127.0.0.1:{port}{ws_path}" if ws_path else f"http://127.0.0.1:{port}"
                    browser = p.chromium.connect_over_cdp(endpoint, timeout=4000)
                    ctx = browser.contexts[0] if browser.contexts else browser.new_context(accept_downloads=True)
                    return browser, ctx, ctx.new_page()
            except Exception:
                pass

        try:
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222", timeout=2500)
            ctx = browser.contexts[0] if browser.contexts else browser.new_context(accept_downloads=True)
            return browser, ctx, ctx.new_page()
        except Exception:
            ctx = p.chromium.launch_persistent_context(
                user_data_dir=flow_profile_dir,
                channel="chrome",
                headless=True,
                accept_downloads=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            pg = ctx.pages[0] if ctx.pages else ctx.new_page()
            return None, ctx, pg

    def generate_clip_via_google_flow_web(
        self,
        scene: Dict[str, Any],
        output_path: str,
        aspect_ratio: str = "16:9",
        duration_sec: int = 10
    ) -> str:
        """
        在 Google Flow (`https://flow.google.com/`) 固定專屬專案 (`YT-Auto-Empire YouTube 爆款影片總部`) 中自動建立並生成每支影片：
        - 自動選擇最高畫質 (`1080p Upscaled / Highest Quality`) 與最好模型 (`Veo 3.1 - Quality` / `Veo 3 - Quality`)
        - 每個分鏡皆帶入「擬真人物主播 + 逐句字幕連動情境」Prompt，絕不重複畫面
        """
        if not self._flow_auth_ready:
            return self.generate_clip_via_omni_api(
                scene=scene,
                output_path=output_path,
                aspect_ratio=aspect_ratio,
                duration_sec=duration_sec
            )

        raw_prompt = scene.get("visual_prompt", "")
        narration = scene.get("narration", "")
        project_title = os.getenv("FLOW_PROJECT_NAME", "YT-Auto-Empire YouTube 爆款影片總部")
        prompt = (
            f"[1080p Highest Quality | Veo 3.1 Quality Model | {aspect_ratio}] "
            f"Cinematic {aspect_ratio} video featuring an expressive human tech creator presenter in frame, "
            f"visually illustrating the exact subtitle narration: '{narration[:100]}'. "
            f"Scene details: {raw_prompt}. Ultra-detailed lighting, smooth 60fps camera motion, zero static loop."
        )
        print(
            f"[VideoGenerator/GoogleFlow] 正在進入專屬專案【{project_title}】以最高畫質 (1080p) + 最佳模型 (Veo Quality) 生成: "
            f"{prompt[:60]}..."
        )
        try:
            from playwright.sync_api import sync_playwright

            flow_profile_dir = os.path.abspath(self.chrome_user_data_dir or "chrome_profile")
            os.makedirs(flow_profile_dir, exist_ok=True)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with self._flow_lock:
                if not self._flow_auth_ready:
                    raise RuntimeError("Google Flow 尚未完成首次登入或未開啟 chrome://inspect/#remote-debugging。")
                with sync_playwright() as p:
                    browser_cdp, context, page = self._connect_flow_browser(p, flow_profile_dir)

                    saved_project_url = self._load_or_save_flow_project_url()
                    target_url = saved_project_url or "https://flow.google.com/"
                    page.goto(target_url, timeout=25000)
                    page.wait_for_load_state("domcontentloaded", timeout=15000)
                    page.wait_for_timeout(2000)

                    # 若停留在介紹頁 (flow.google.com/about)，自動點擊「使用 Google Flow 建立」進入工作區
                    if "/about" in page.url:
                        for b in page.locator("button, a").all():
                            txt = (b.inner_text() or "").strip()
                            if any(k in txt for k in ["使用 Google Flow 建立", "試用 Google Flow", "Create with Google Flow", "Create with Flow"]):
                                b.click()
                                page.wait_for_timeout(3500)
                                break

                    # 若被導向 accounts.google.com 登入頁，代表尚未授權登入
                    if "accounts.google.com" in page.url:
                        self._flow_auth_ready = False
                        if browser_cdp:
                            page.close()
                        else:
                            context.close()
                        raise RuntimeError(
                            "Google Flow 尚未取得登入憑證（請於 Chrome 開啟 chrome://inspect/#remote-debugging 勾選 Enable remote debugging，或於登入視窗登入一次）。"
                        )

                    # 若尚未進入固定專案，自動建立/開啟「YT-Auto-Empire YouTube 爆款影片總部」專案並鎖定該專案網址
                    if not saved_project_url or "/project/" not in page.url:
                        existing_proj = page.locator(f"text={project_title}").first
                        if existing_proj.count() > 0:
                            existing_proj.click()
                            page.wait_for_timeout(2500)
                        else:
                            for b in page.locator("button, a").all():
                                txt = (b.inner_text() or "").strip()
                                if any(k in txt for k in ["New project", "新增專案", "建立專案", "New Project", "+"]):
                                    try:
                                        b.click(timeout=2500)
                                        page.wait_for_timeout(2500)
                                        break
                                    except Exception:
                                        pass
                            # 嘗試將新專案命名為 YT-Auto-Empire YouTube 爆款影片總部
                            try:
                                title_input = page.locator("input[placeholder*='Untitled'], input[placeholder*='未命名'], [aria-label*='Project name'], [aria-label*='專案名稱']").first
                                if title_input.count() > 0:
                                    title_input.click()
                                    title_input.fill(project_title)
                                    page.keyboard.press("Enter")
                            except Exception:
                                pass

                        if "flow.google.com" in page.url or "labs.google" in page.url:
                            self._load_or_save_flow_project_url(page.url)

                    # 自動偵測並同步 Google Flow 網頁上的 Google One Ultra 真實剩餘點數
                    try:
                        body_text = page.locator("body").inner_text(timeout=3000)
                        credit_match = re.search(r"([\d,]+)\s*(?:credits|點|點數)", body_text, re.IGNORECASE)
                        if credit_match:
                            live_credits = int(credit_match.group(1).replace(",", ""))
                            self.quota_maximizer.sync_live_balance_from_flow_ui(live_credits)
                    except Exception:
                        pass

                    # 自動切換為「最好模型 (Veo 3.1 - Quality / Highest Quality)」與對應長寬比 (16:9 / 9:16)
                    try:
                        for btn in page.locator("button, [role='button'], [role='combobox']").all():
                            btxt = (btn.inner_text() or "").strip()
                            if any(k in btxt for k in ["Fast", "Veo", "Model", "模型", "品質", "Quality", "Settings", "設定"]):
                                btn.click(timeout=1500)
                                page.wait_for_timeout(600)
                                q_opt = page.locator("text=/Veo.*Quality|Highest Quality|最高品質|最高畫質/i").first
                                if q_opt.count() > 0:
                                    q_opt.click(timeout=1500)
                                break
                        ratio_label = "16:9" if aspect_ratio == "16:9" else "9:16"
                        ratio_opt = page.locator(f"button:has-text('{ratio_label}'), [role='option']:has-text('{ratio_label}')").first
                        if ratio_opt.count() > 0:
                            ratio_opt.click(timeout=1500)
                    except Exception:
                        pass

                    # 尋找 Google Flow 的提示詞輸入框
                    prompt_box = page.locator(
                        "textarea, [contenteditable='true'], input[type='text']"
                    ).first
                    if prompt_box.count() == 0:
                        self._flow_auth_ready = False
                        if browser_cdp:
                            page.close()
                        else:
                            context.close()
                        raise RuntimeError("Google Flow 專案工作區輸入框尚未就緒。")

                    prompt_box.click()
                    prompt_box.fill(prompt)
                    page.keyboard.press("Enter")

                    with page.expect_download(timeout=180000) as download_info:
                        download_btn = page.locator(
                            "button:has-text('Download'), button:has-text('下載'), a[download], [aria-label*='Download'], [aria-label*='下載']"
                        ).first
                        download_btn.wait_for(state="visible", timeout=150000)
                        download_btn.click()
                        page.wait_for_timeout(800)
                        # 若彈出畫質選單，優先選擇「1080p Upscaled / 最高畫質 1080p」
                        upscale_opt = page.locator("text=/1080p|Upscaled|最高畫質|Original/i").first
                        if upscale_opt.count() > 0:
                            try:
                                upscale_opt.click(timeout=2000)
                            except Exception:
                                pass

                    download = download_info.value
                    download.save_as(output_path)
                    if browser_cdp:
                        page.close()
                    else:
                        context.close()
                    self.quota_maximizer.record_flow_consumption(clips_count=1)
                    print(
                        f"[VideoGenerator/GoogleFlow] 專屬專案【{project_title}】1080p 最高畫質生成並下載成功: {output_path} "
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
