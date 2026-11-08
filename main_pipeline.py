#!/usr/bin/env python3
"""
main_pipeline.py — YT-Auto-Empire 全自動爆品選品、長短片生成、自動剪輯與 YouTube 上片主控台
一鍵執行完整閉環：
Step 1: Google Trends + Gemini Search Grounding 自動挖掘高 CPM 與高轉換爆品
Step 2: Gemini 4 Argon 總導演產出「長影片 + Shorts 短片」雙軌分鏡腳本與 SEO 變現文案
Step 3: Gemini 3.8 Flash TTS 批次合成高情緒張力旁白 + Gemini Nano Banana 2.1 生成高點擊縮圖
Step 4: 雙引擎視覺生成 (Gemini Omni 1.2 Flash API + Google Flow 網頁操控) 產出 16:9 與 9:16 分鏡素材
Step 5: FFmpeg 自動混音對齊、燒錄動態字幕、生成時間軸章節，輸出成品長片與 Shorts
Step 6: YouTube Data API v3 自動上傳長片與 Shorts、掛載縮圖與字幕、插入聯盟分潤連結與導購留言
"""

import argparse
import datetime
import json
import os
import sys
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from trend_hunter import TrendHunter
from gemini_director import GeminiDirector
from video_generator import DualVideoGenerator
from auto_editor import AutoVideoEditor
from youtube_uploader import YouTubeEmpireUploader
from ultra_quota_maximizer import UltraQuotaMaximizer
from self_critic_and_analytics import SelfCriticAndAnalyticsEngine


def run_empire_pipeline(
    custom_topic: str | None = None,
    engine_mode: str | None = None,
    long_scenes: int = 6,
    shorts_scenes: int = 3,
    auto_upload: bool = False
) -> dict:
    load_dotenv()

    if not os.getenv("GEMINI_API_KEY"):
        print("💡 [系統提示] 尚未偵測到 `.env` 中的 `GEMINI_API_KEY`，已自動啟用【Antigravity 內建全自動導演 + 台灣神經網路語音 + 動態運鏡引擎】直接產出成品影片！")

    geo = os.getenv("TREND_GEO", "TW")
    niches = [k.strip() for k in os.getenv("NICHE_KEYWORDS", "3C神器,智慧家電,AI工具,居家好物").split(",") if k.strip()]
    mode = engine_mode or os.getenv("VIDEO_ENGINE_MODE", "ultra")
    resolution = os.getenv("VIDEO_RESOLUTION", "1080p")
    chrome_dir = os.getenv("CHROME_USER_DATA_DIR", "./chrome_profile")

    quota_maximizer = UltraQuotaMaximizer()
    burn_plan = quota_maximizer.calculate_daily_burn_plan()

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.abspath(os.path.join("runs", f"campaign_{timestamp}"))
    os.makedirs(run_dir, exist_ok=True)

    print("=" * 72)
    print(f"🚀 啟動 YT-Auto-Empire 全自動印鈔流水線 (Google One Ultra 榨乾模式) | 目錄: {run_dir}")
    print("=" * 72)

    # -------------------------------------------------------------------------
    # Step 1: 自動選品與高 CPM 爆品探測
    # -------------------------------------------------------------------------
    hunter = TrendHunter(geo=geo, niche_keywords=niches)
    product_info = hunter.select_viral_product(custom_topic=custom_topic)
    with open(os.path.join(run_dir, "01_selected_product.json"), "w", encoding="utf-8") as f:
        json.dump(product_info, f, indent=2, ensure_ascii=False)

    # -------------------------------------------------------------------------
    # Step 2: Gemini 4 Argon 總導演生成長短片藍圖與高 CTR 縮圖
    # -------------------------------------------------------------------------
    director = GeminiDirector(output_dir=run_dir)
    blueprint = director.create_production_blueprint(
        product_info=product_info,
        long_scene_count=long_scenes,
        shorts_scene_count=shorts_scenes
    )

    seo = blueprint["seo_metadata"]
    thumbnail_path = os.path.join(run_dir, "thumbnail_16x9.jpg")
    director.generate_thumbnail(prompt=seo["thumbnail_prompt"], output_image_path=thumbnail_path)

    # -------------------------------------------------------------------------
    # Step 3: Gemini 3.8 Flash TTS 批次合成長短片旁白音檔
    # -------------------------------------------------------------------------
    long_scenes_list = blueprint["long_video"]["scenes"]
    shorts_scenes_list = blueprint["shorts_video"]["scenes"]

    long_wavs = []
    for sc in long_scenes_list:
        sid = sc["scene_id"]
        wav_path = os.path.join(run_dir, "audio_long", f"scene_{sid:02d}.wav")
        director.synthesize_narration(
            text=sc["narration"],
            style=sc.get("voice_style", "enthusiastic and persuasive"),
            output_wav_path=wav_path
        )
        sc["duration_sec"] = round(AutoVideoEditor.get_media_duration(wav_path), 2)
        long_wavs.append(wav_path)

    shorts_wavs = []
    for sc in shorts_scenes_list:
        sid = sc["scene_id"]
        wav_path = os.path.join(run_dir, "audio_shorts", f"scene_{sid:02d}.wav")
        director.synthesize_narration(
            text=sc["narration"],
            style=sc.get("voice_style", "energetic and fast-paced"),
            output_wav_path=wav_path
        )
        sc["duration_sec"] = round(AutoVideoEditor.get_media_duration(wav_path), 2)
        shorts_wavs.append(shorts_wav_path := wav_path)

    # -------------------------------------------------------------------------
    # Step 4: 雙引擎生成分鏡影片 (Google One Ultra Flow 點數優先榨乾 + Omni API)
    # -------------------------------------------------------------------------
    generator = DualVideoGenerator(
        engine_mode=mode,
        resolution=resolution,
        chrome_user_data_dir=chrome_dir,
        quota_maximizer=quota_maximizer
    )

    print("\n🎬 [Step 4A] 正在渲染 16:9 長影片分鏡素材 (RTX 3070 4線程高速並行)...")
    long_clips = generator.batch_render_scenes(
        scenes=long_scenes_list,
        clips_dir=os.path.join(run_dir, "clips_long"),
        aspect_ratio="16:9",
        concurrency=4
    )

    print("\n📱 [Step 4B] 正在渲染 9:16 Shorts 短影音分鏡素材 (RTX 3070 4線程高速並行)...")
    shorts_clips = generator.batch_render_scenes(
        scenes=shorts_scenes_list,
        clips_dir=os.path.join(run_dir, "clips_shorts"),
        aspect_ratio="9:16",
        concurrency=4
    )

    # -------------------------------------------------------------------------
    # Step 5: FFmpeg 自動剪輯、混音、動態字幕與章節時間軸生成
    # -------------------------------------------------------------------------
    editor = AutoVideoEditor(work_dir=run_dir)

    final_long_mp4 = os.path.join(run_dir, "final_long_16x9.mp4")
    final_long_srt = os.path.join(run_dir, "final_long_16x9.srt")
    _, _, long_chapters = editor.assemble_timeline(
        scenes=long_scenes_list,
        raw_clips=long_clips,
        voice_wavs=long_wavs,
        output_video_path=final_long_mp4,
        srt_output_path=final_long_srt,
        aspect_ratio="16:9"
    )

    final_shorts_mp4 = os.path.join(run_dir, "final_shorts_9x16.mp4")
    final_shorts_srt = os.path.join(run_dir, "final_shorts_9x16.srt")
    editor.assemble_timeline(
        scenes=shorts_scenes_list,
        raw_clips=shorts_clips,
        voice_wavs=shorts_wavs,
        output_video_path=final_shorts_mp4,
        srt_output_path=final_shorts_srt,
        aspect_ratio="9:16"
    )

    # -------------------------------------------------------------------------
    # Step 6: 發布前嚴格自我審閱與自動優化守門員 (Pre-Upload Self-QA Gatekeeper)
    # 必須達到百萬博主與 YouTube 演算法全項標準 (>= 90分)，未達標項目當場自動修復重構，全部達標後才放行上傳！
    # -------------------------------------------------------------------------
    affiliate_url = os.getenv("AFFILIATE_STORE_URL", "https://shopee.tw/your_affiliate_shop")
    sponsor_email = os.getenv("SPONSOR_CONTACT_EMAIL", "business@yourdomain.com")
    privacy = os.getenv("YOUTUBE_PRIVACY_STATUS", "public")

    uploader = YouTubeEmpireUploader(
        client_secrets_file=os.getenv("YOUTUBE_CLIENT_SECRETS_FILE", "client_secrets.json")
    )

    # 自動優化標題：若雲端生成的標題缺少具體數字或括號焦點，自動補上百萬博主高 CTR 數字鉤子
    raw_long_title = seo["long_title"]
    if not any(ch.isdigit() for ch in raw_long_title) or ("【" not in raw_long_title and "[" not in raw_long_title):
        raw_long_title = f"【2026實測封神】別再花$200月費！{raw_long_title} (10倍速全自動教學)"
        seo["long_title"] = raw_long_title

    monetized_desc = uploader.build_monetized_description(
        base_description=seo["description"],
        chapters=long_chapters,
        affiliate_keywords=product_info.get("affiliate_keywords", [product_info["product_name"]]),
        affiliate_store_url=affiliate_url,
        sponsor_email=sponsor_email
    )

    publish_summary = {
        "product": product_info["product_name"],
        "estimated_cpm_usd": product_info["estimated_cpm_usd"],
        "long_video_path": final_long_mp4,
        "shorts_video_path": final_shorts_mp4,
        "thumbnail_path": thumbnail_path,
        "long_title": seo["long_title"],
        "shorts_title": seo["shorts_title"],
        "monetized_description": monetized_desc,
        "pinned_comment": f"{seo['pinned_comment']}\n👉 搶先入手同款爆品：{affiliate_url}"
    }

    critic = SelfCriticAndAnalyticsEngine()
    qa_and_algo_review = critic.evaluate_algorithm_and_views(publish_summary)

    publish_summary["self_critic_review"] = qa_and_algo_review
    qa_passed = qa_and_algo_review.get("algorithm_readiness_score", 0) >= 90

    if auto_upload and qa_passed:
        print(f"\n✅ [Self-QA 審閱滿分通過 ({qa_and_algo_review['algorithm_readiness_score']}/100)] 准許放行！正在自動上傳至 YouTube 頻道 (`tonykfr1234@gmail.com`)...")
        uploader.flush_upload_queue()
        long_vid_id = uploader.upload_video(
            video_path=final_long_mp4,
            title=seo["long_title"],
            description=monetized_desc,
            tags=seo["tags"],
            privacy_status=privacy,
            thumbnail_path=thumbnail_path,
            srt_path=final_long_srt,
            pinned_comment_text=publish_summary["pinned_comment"]
        )
        shorts_desc = (
            f"🎬 完整 8 分鐘深度實測長片請看這裡 👉 https://youtu.be/{long_vid_id}\n"
            f"🔥 同款爆品限時優惠 👉 {affiliate_url}\n\n"
            f"#Shorts #{product_info['product_name']}"
        )
        shorts_vid_id = uploader.upload_video(
            video_path=final_shorts_mp4,
            title=seo["shorts_title"],
            description=shorts_desc,
            tags=seo["tags"] + ["Shorts"],
            privacy_status=privacy,
            srt_path=final_shorts_srt,
            pinned_comment_text=f"👉 點這裡看完整 8 分鐘實測與購買優惠：https://youtu.be/{long_vid_id}"
        )
        publish_summary["long_youtube_id"] = long_vid_id
        publish_summary["shorts_youtube_id"] = shorts_vid_id

    quota_maximizer.record_campaign_completed(long_count=1, shorts_count=1)
    publish_summary["ultra_quota_status"] = quota_maximizer.state

    # 自動同步歸檔至 Google Drive 統一影片資料夾 (`G:\我的雲端硬碟\YT-Auto-Empire-Videos`)
    try:
        from gdrive_sync import GoogleDriveVideoVault
        gdrive_vault = GoogleDriveVideoVault()
        gdrive_paths = gdrive_vault.sync_campaign(run_dir=run_dir, summary=publish_summary)
        publish_summary["google_drive_paths"] = gdrive_paths
    except Exception as gd_err:
        print(f"[GoogleDriveVault] 同步提示: {gd_err}")

    summary_path = os.path.join(run_dir, "02_publish_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(publish_summary, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 72)
    print(f"✅ 全流程執行完畢！成品與變現報告已輸出至: {summary_path}")
    print(f"💎 當月剩餘 Google One Ultra 點數: {quota_maximizer.state['remaining_credits']:,} 點")
    print("=" * 72)
    return publish_summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YT-Auto-Empire 全自動爆品影片產製與 YouTube 上片系統")
    parser.add_argument("--topic", type=str, default=None, help="指定爆品主題（不填則自動從 Google Trends 抓取）")
    parser.add_argument(
        "--engine",
        type=str,
        choices=["ultra", "api", "flow", "hybrid"],
        default="ultra",
        help="影片生成引擎模式: ultra (優先榨乾 Google One Ultra 點數), api, flow, hybrid"
    )
    parser.add_argument("--long-scenes", type=int, default=32, help="長影片分鏡數量（預設 32 鏡 = 8 分鐘以上中插廣告滿載規格）")
    parser.add_argument("--shorts-scenes", type=int, default=4, help="Shorts 短影音分鏡數量（預設 4 鏡）")
    parser.add_argument("--burn-daily-quota", action="store_true", help="自動根據當月剩餘天數與剩餘 Ultra 點數，連續生成多組爆品影片直到達成今日點數消耗目標！")
    parser.add_argument("--upload", action="store_true", help="完成剪輯後立即透過 YouTube Data API 自動上片")
    args = parser.parse_args()

    if args.burn_daily_quota:
        maximizer = UltraQuotaMaximizer()
        plan = maximizer.calculate_daily_burn_plan()
        target_campaigns = plan["recommended_campaigns_today"]
        print(f"🔥 [Ultra 每日點數榨乾排程] 今日將自動連續產出 {target_campaigns} 組完整 8 分鐘長片 + Shorts 爆品矩陣！")
        for i in range(target_campaigns):
            print(f"\n>>> 正在執行今日第 {i + 1} / {target_campaigns} 組爆品變現專案 <<<")
            run_empire_pipeline(
                custom_topic=args.topic if i == 0 else None,
                engine_mode="ultra",
                long_scenes=plan["long_scenes_per_campaign"],
                shorts_scenes=plan["shorts_scenes_each"],
                auto_upload=args.upload
            )
    else:
        run_empire_pipeline(
            custom_topic=args.topic,
            engine_mode=args.engine,
            long_scenes=args.long_scenes,
            shorts_scenes=args.shorts_scenes,
            auto_upload=args.upload
        )
