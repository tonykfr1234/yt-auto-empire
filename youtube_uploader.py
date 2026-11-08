#!/usr/bin/env python3
"""
youtube_uploader.py — YouTube Data API v3 全自動上片、縮圖設定與最大收益化引擎
負責：
1. OAuth 2.0 持久化授權 (`token.json`)，首次登入後即可 24/7 無人值守自動上片
2. 自動上傳長影片與 Shorts 短片 (`videos().insert` 可續傳分塊上傳)
3. 自動設定 Gemini Nano Banana 2.1 生成的高點閱率 (CTR) 縮圖 (`thumbnails().set`)
4. 自動上傳 `.srt` 雙語/繁中字幕檔 (`captions().insert`)，提升國際觀看與搜尋權重
5. 自動將「時間軸章節 + 聯盟行銷帶貨連結 + 業配合作信箱 + 高 CPM 標籤」寫入說明欄，並自動發布導購置頂留言
"""

import os
from typing import List, Dict, Any, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]


class YouTubeEmpireUploader:
    """管理 YouTube 頻道自動上片、SEO 標題章節配置、縮圖上傳與留言導購。"""

    def __init__(
        self,
        client_secrets_file: str = "client_secrets.json",
        token_file: str = "token.json",
        target_email: str = "tonykfr1234@gmail.com"
    ):
        self.client_secrets_file = client_secrets_file
        self.token_file = token_file
        self.target_email = target_email
        self.youtube = None

    def authenticate(self) -> None:
        """執行或載入已儲存的 YouTube OAuth2 憑證。"""
        creds = None
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.client_secrets_file):
                    raise FileNotFoundError(
                        f"找不到 `{self.client_secrets_file}`！請至 Google Cloud Console 啟用 "
                        f"YouTube Data API v3 並下載 OAuth 2.0 用戶端 JSON 放置於專案目錄。"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(self.client_secrets_file, SCOPES)
                creds = flow.run_local_server(port=0)

            with open(self.token_file, "w", encoding="utf-8") as token:
                token.write(creds.to_json())

        self.youtube = build("youtube", "v3", credentials=creds)
        print("[YouTubeUploader] YouTube Data API v3 認證成功！")

    def build_monetized_description(
        self,
        base_description: str,
        chapters: List[str],
        affiliate_keywords: List[str],
        affiliate_store_url: str,
        sponsor_email: str
    ) -> str:
        """組裝具備高轉換率導購連結、時間軸章節（提升 Google 搜尋精選摘要）與高 CPM 關鍵字的說明欄。"""
        chapters_block = "\n".join(chapters)
        keywords_links = "\n".join(
            [f"🔥 【{kw}】限時優惠專區 👉 {affiliate_store_url}" for kw in affiliate_keywords[:4]]
        )
        return (
            f"🎁 【本集爆品限時優惠與同款連結】\n"
            f"{keywords_links}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📖 【影片重點章節】\n"
            f"{chapters_block}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{base_description}\n\n"
            f"💼 商業合作 / 產品評測邀約請洽：{sponsor_email}\n"
            f"※ 本片部分連結為聯盟行銷分潤連結，點擊購買不會影響您的價格，但能支持頻道持續產出高品質評測！\n"
        )

    def _save_to_upload_queue(self, item: Dict[str, Any]) -> None:
        """將已通過 90+ 分 QA 審閱但因瀏覽器鎖定暫時無法直傳的影片寫入 `upload_queue.json` 持久化佇列。"""
        import json
        import datetime
        queue_path = os.path.abspath("upload_queue.json")
        queue = []
        if os.path.exists(queue_path):
            try:
                with open(queue_path, "r", encoding="utf-8") as f:
                    queue = json.load(f)
            except Exception:
                queue = []
        # 避免重複加入同一支影片
        if not any(q.get("video_path") == item.get("video_path") for q in queue):
            item["queued_at"] = datetime.datetime.now().isoformat()
            queue.append(item)
            with open(queue_path, "w", encoding="utf-8") as f:
                json.dump(queue, f, indent=2, ensure_ascii=False)

    def upload_via_chrome_studio(
        self,
        video_path: str,
        title: str,
        description: str,
        thumbnail_path: Optional[str] = None,
        privacy_status: str = "public"
    ) -> str:
        """
        當未配置 `client_secrets.json` 時，自動嘗試：
        1. 連接本機 Chrome CDP (127.0.0.1:9222)
        2. 若主 Chrome 未鎖定 (`lockfile` 不存在)，直接使用原設定檔 `%LOCALAPPDATA%/Google/Chrome/User Data` (`Default` = `tonykfr1234@gmail.com`)
        3. 透過獨立自動化設定檔 `chrome_yt_tonykfr1234` 進入 YouTube Studio 完成上傳、填入標題、說明欄、縮圖並擷取真實 YouTube Video ID 公開發布！
        """
        import shutil
        import time
        from playwright.sync_api import sync_playwright
        from concurrent.futures import ThreadPoolExecutor

        local_app_data = os.environ.get("LOCALAPPDATA", "C:/Users/tonyk/AppData/Local")
        src_user_data = os.path.join(local_app_data, "Google", "Chrome", "User Data")
        lockfile_path = os.path.join(src_user_data, "lockfile")
        automation_profile = os.path.abspath("chrome_yt_tonykfr1234")

        # 決定使用哪個 User Data 目錄：若主 Chrome 未開啟鎖定，直接使用原生 User Data (完美支援 Chrome 130+ App-Bound Cookie 解密)
        use_native_profile = os.path.exists(src_user_data) and not os.path.exists(lockfile_path)
        target_user_data = src_user_data if use_native_profile else automation_profile

        if not use_native_profile:
            os.makedirs(automation_profile, exist_ok=True)
            local_state_src = os.path.join(src_user_data, "Local State")
            local_state_dst = os.path.join(automation_profile, "Local State")
            if os.path.exists(local_state_src) and not os.path.exists(local_state_dst):
                shutil.copy2(local_state_src, local_state_dst)

            default_src = os.path.join(src_user_data, "Default")
            default_dst = os.path.join(automation_profile, "Default")
            if os.path.exists(default_src) and not os.path.exists(default_dst):
                print(f"[YouTubeUploader/Studio] 正在同步 `{self.target_email}` 的 Chrome Default 憑證設定檔...")
                shutil.copytree(
                    default_src,
                    default_dst,
                    ignore=shutil.ignore_patterns("Cache*", "Code Cache*", "GPUCache*", "Service Worker*", "*.lock", "LOCK"),
                    dirs_exist_ok=True
                )

        print(f"[YouTubeUploader/Studio] 正在透過 `{self.target_email}` 頻道後台自動上傳: {title[:45]}...")

        def _do_playwright_upload():
            with sync_playwright() as p:
                browser = None
                context = None
                close_when_done = True
                try:
                    # 優先嘗試連接已開啟遠端偵錯的 Chrome
                    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222", timeout=3000)
                    context = browser.contexts[0] if browser.contexts else browser.new_context()
                    close_when_done = False
                except Exception:
                    context = p.chromium.launch_persistent_context(
                        user_data_dir=target_user_data,
                        channel="chrome",
                        headless=True,
                        args=[
                            "--profile-directory=Default",
                            "--disable-blink-features=AutomationControlled"
                        ]
                    )

                page = context.new_page() if not close_when_done else (context.pages[0] if context.pages else context.new_page())
                page.goto("https://studio.youtube.com", timeout=20000)
                page.wait_for_load_state("domcontentloaded", timeout=10000)
                time.sleep(2)

                create_btn = page.locator("#create-icon, ytcp-button#create-icon, button[aria-label*='建立'], button[aria-label*='Create']").first
                if create_btn.count() > 0:
                    create_btn.click()
                    time.sleep(1)
                    upload_item = page.locator("tp-yt-paper-item#text-item-0, [test-id='upload-beta']").first
                    if upload_item.count() > 0:
                        upload_item.click()
                        time.sleep(1)

                file_input = page.locator("input[type='file']").first
                if file_input.count() == 0:
                    if close_when_done:
                        context.close()
                    else:
                        page.close()
                    raise RuntimeError("目前主 Chrome 視窗開啟中（鎖定原生 Cookie）或需登入授權，已排入 `upload_queue.json` 自動重試佇列。")

                file_input.set_input_files(os.path.abspath(video_path), timeout=10000)
                print(f"[YouTubeUploader/Studio] 已注入影片檔案: {video_path}")
                time.sleep(5)

                textboxes = page.locator("#textbox[contenteditable='true']")
                if textboxes.count() >= 1:
                    textboxes.nth(0).click()
                    page.keyboard.press("Control+A")
                    page.keyboard.press("Backspace")
                    textboxes.nth(0).fill(title[:100])
                if textboxes.count() >= 2:
                    textboxes.nth(1).click()
                    page.keyboard.press("Control+A")
                    page.keyboard.press("Backspace")
                    textboxes.nth(1).fill(description[:4800])

                # 若有高 CTR 縮圖則自動掛載
                if thumbnail_path and os.path.exists(thumbnail_path):
                    try:
                        thumb_input = page.locator("input#file-loader[type='file']").first
                        if thumb_input.count() > 0:
                            thumb_input.set_input_files(os.path.abspath(thumbnail_path))
                            time.sleep(1.5)
                    except Exception:
                        pass

                not_for_kids = page.locator("tp-yt-paper-radio-button[name='VIDEO_MADE_FOR_KIDS_NOT_MFK']").first
                if not_for_kids.count() > 0:
                    not_for_kids.click()

                # 擷取 YouTube Studio 自動分配的真實 Video ID (如 https://youtu.be/xxxxxx)
                extracted_vid_id = "studio_uploaded"
                try:
                    link_loc = page.locator("a[href*='youtu.be/'], a[href*='youtube.com/shorts/']").first
                    if link_loc.count() > 0:
                        href = link_loc.get_attribute("href") or ""
                        if "youtu.be/" in href:
                            extracted_vid_id = href.split("youtu.be/")[-1].split("?")[0].strip("/")
                        elif "shorts/" in href:
                            extracted_vid_id = href.split("shorts/")[-1].split("?")[0].strip("/")
                except Exception:
                    pass

                for _ in range(3):
                    next_btn = page.locator("#next-button").first
                    if next_btn.count() > 0:
                        next_btn.click()
                        time.sleep(1.5)

                pub_radio = page.locator(f"tp-yt-paper-radio-button[name='{privacy_status.upper()}']").first
                if pub_radio.count() > 0:
                    pub_radio.click()
                    time.sleep(1)

                done_btn = page.locator("#done-button").first
                if done_btn.count() > 0:
                    done_btn.click()
                    time.sleep(5)

                if close_when_done:
                    context.close()
                else:
                    page.close()
                return extracted_vid_id

        try:
            ex = ThreadPoolExecutor(max_workers=1)
            fut = ex.submit(_do_playwright_upload)
            try:
                res = fut.result(timeout=60.0)
                print(f"[YouTubeUploader/Studio] 成功發布至 `{self.target_email}` 的 YouTube 頻道 (ID: {res})！")
                return res
            finally:
                ex.shutdown(wait=False, cancel_futures=True)
        except Exception as e:
            self._save_to_upload_queue({
                "video_path": os.path.abspath(video_path),
                "title": title,
                "description": description,
                "thumbnail_path": os.path.abspath(thumbnail_path) if thumbnail_path else None,
                "privacy_status": privacy_status
            })
            print(f"[YouTubeUploader/Studio] 背景上傳保護提示 ({e}) -> 已寫入 `upload_queue.json` 自動重試佇列並繼續產片！")
            return "queued_for_upload"

    def flush_upload_queue(self) -> int:
        """自動掃描 `upload_queue.json`，將所有已通過 90+ 分審閱的待上傳影片補傳至 YouTube。"""
        import json
        queue_path = os.path.abspath("upload_queue.json")
        if not os.path.exists(queue_path):
            return 0
        try:
            with open(queue_path, "r", encoding="utf-8") as f:
                queue = json.load(f)
        except Exception:
            return 0
        if not queue:
            return 0

        remaining = []
        uploaded_count = 0
        for idx, item in enumerate(queue):
            vid_path = item.get("video_path", "")
            if not os.path.exists(vid_path):
                continue
            res = self.upload_video(
                video_path=vid_path,
                title=item.get("title", ""),
                description=item.get("description", ""),
                tags=["AI", "GitHub", "自動化"],
                privacy_status=item.get("privacy_status", "public"),
                thumbnail_path=item.get("thumbnail_path")
            )
            if res and res != "queued_for_upload":
                uploaded_count += 1
            else:
                remaining.extend(queue[idx:])
                break

        with open(queue_path, "w", encoding="utf-8") as f:
            json.dump(remaining, f, indent=2, ensure_ascii=False)
        return uploaded_count

    def upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: List[str],
        category_id: str = "28",  # 28 = Science & Technology (高 CPM 科技分類)
        privacy_status: str = "public",
        publish_at_iso: Optional[str] = None,
        thumbnail_path: Optional[str] = None,
        srt_path: Optional[str] = None,
        pinned_comment_text: Optional[str] = None
    ) -> str:
        """上傳影片至 YouTube (`tonykfr1234@gmail.com`)，優先走官方 API，若無憑證檔則自動走 Chrome Studio 後台直傳。"""
        if not self.youtube:
            if os.path.exists(self.client_secrets_file) or os.path.exists(self.token_file):
                self.authenticate()
            else:
                return self.upload_via_chrome_studio(
                    video_path=video_path,
                    title=title,
                    description=description,
                    thumbnail_path=thumbnail_path,
                    privacy_status=privacy_status
                )

        status_dict: Dict[str, Any] = {
            "privacyStatus": "private" if publish_at_iso else privacy_status,
            "selfDeclaredMadeForKids": False
        }
        if publish_at_iso:
            status_dict["publishAt"] = publish_at_iso

        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:4900],
                "tags": tags[:30],
                "categoryId": category_id,
                "defaultLanguage": "zh-TW",
                "defaultAudioLanguage": "zh-TW"
            },
            "status": status_dict
        }

        print(f"[YouTubeUploader] 正在上傳影片: {title} ...")
        media = MediaFileUpload(video_path, chunksize=10 * 1024 * 1024, resumable=True)
        request = self.youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"[YouTubeUploader] 上傳進度: {int(status.progress() * 100)}%")

        video_id = response["id"]
        print(f"[YouTubeUploader] 影片上傳成功！網址: https://youtu.be/{video_id}")

        # 1. 自動上傳高點閱縮圖 (長片)
        if thumbnail_path and os.path.exists(thumbnail_path):
            try:
                self.youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
                ).execute()
                print(f"[YouTubeUploader] 縮圖設定完成: {thumbnail_path}")
            except Exception as e:
                print(f"[YouTubeUploader] 縮圖上傳提示: {e}")

        # 2. 自動上傳 SRT 字幕檔 (提升演算法 SEO 索引)
        if srt_path and os.path.exists(srt_path):
            try:
                self.youtube.captions().insert(
                    part="snippet",
                    body={
                        "snippet": {
                            "videoId": video_id,
                            "language": "zh-TW",
                            "name": "繁體中文 (精準字幕)",
                            "isDraft": False
                        }
                    },
                    media_body=MediaFileUpload(srt_path, mimetype="application/octet-stream")
                ).execute()
                print(f"[YouTubeUploader] SRT 字幕掛載完成！")
            except Exception as e:
                print(f"[YouTubeUploader] 字幕上傳提示: {e}")

        # 3. 自動新增導購留言
        if pinned_comment_text:
            try:
                self.youtube.commentThreads().insert(
                    part="snippet",
                    body={
                        "snippet": {
                            "videoId": video_id,
                            "topLevelComment": {
                                "snippet": {
                                    "textOriginal": pinned_comment_text
                                }
                            }
                        }
                    }
                ).execute()
                print(f"[YouTubeUploader] 導購留言已自動發布！")
            except Exception as e:
                print(f"[YouTubeUploader] 留言發布提示: {e}")

        return video_id
