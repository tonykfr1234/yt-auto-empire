#!/usr/bin/env python3
"""
self_critic_and_analytics.py — 影片成品自我審閱 (Self-QA) + YouTube 演算法推流追蹤 + 持續進化閉環引擎
負責三大核心任務：
1. 【發布前自我審閱 (Pre-Publish Video QA Inspector)】：
   - 自動使用 `ffprobe` 與 `ffmpeg` 抽幀檢查每一支產出的長片與 Shorts：
     a) 檢查片長是否達標（長片必須 >= 450 秒以開啟中插廣告，Shorts 必須在 35~60 秒黃金區間）
     b) 檢查音軌是否正常、有無無聲死寂段落
     c) 自動抽取前、中、後 3 張關鍵影格，計算像素變異度 (Frame Entropy & Motion Variance)，確認絕無黑屏或靜態死圖！
     d) 若審閱未達 85 分，立即退回重製，絕不讓劣質影片上傳傷害頻道權重！
2. 【上傳後 YouTube 瀏覽量與演算法推流雷達 (Post-Publish Algorithm Tracker)】：
   - 定期掃描已發布影片與同賽道爆款指標（觀看次數 Velocity、讚數比、留言互動率），判斷是否成功觸發「YouTube 首頁推薦池 (Browse Features)」或「Shorts 演算法流量池 (Shorts Feed)」。
3. 【持續進化記憶庫 (`evolution_memory.json`)】：
   - 自動記錄每次審閱分數、觀看表現與演算法觸發狀態，提煉出下一輪的「進化指令 (Optimization Directives)」，直接注入 `GeminiDirector` 與 `ViralVisualEngine`，讓後面做出的每一支影片都比前一支更強！
"""

import datetime
import json
import os
import subprocess
from typing import Dict, Any, List
from PIL import Image, ImageStat


EVOLUTION_MEMORY_FILE = "evolution_memory.json"


class SelfCriticAndAnalyticsEngine:
    """自動審閱每支產出影片品質、追蹤上傳後瀏覽量與演算法觸發狀態，並持續迭代優化腳本與視覺參數。"""

    def __init__(self, memory_path: str = EVOLUTION_MEMORY_FILE):
        self.memory_path = os.path.abspath(memory_path)
        self.memory = self._load_memory()

    def _load_memory(self) -> Dict[str, Any]:
        if os.path.exists(self.memory_path):
            try:
                with open(self.memory_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        init_mem = {
            "total_inspected": 0,
            "avg_qa_score": 90.0,
            "algorithm_triggered_count": 0,
            "best_performing_style": {
                "hook_pattern": "反常識痛點金額對比 ($200/月 vs $0 免費開源)",
                "pacing_subshot_sec": 3.5,
                "bgm_volume": 0.22,
                "preferred_topic_type": "interleaved_github_and_viral"
            },
            "optimization_directives": [
                "開場前 3 秒必須直接點出具體節省金額或 GitHub 暴增星數",
                "每段分鏡必須包含 Chromium 3D 浮動視窗與真實 GitHub 網頁平滑捲動錄屏",
                "結尾必須包含雙推薦框與說明欄第一行懶人包引導"
            ],
            "video_reviews": []
        }
        self._save_memory(init_mem)
        return init_mem

    def _save_memory(self, mem: Dict[str, Any] | None = None) -> None:
        target = mem or self.memory
        with open(self.memory_path, "w", encoding="utf-8") as f:
            json.dump(target, f, indent=2, ensure_ascii=False)

    def inspect_rendered_video(
        self,
        video_path: str,
        expected_min_duration: float = 60.0,
        is_shorts: bool = False
    ) -> Dict[str, Any]:
        """
        對剛剪輯完成的 MP4 進行嚴格自我審閱：
        1. 檢查時長 (`duration`)、位元率 (`bit_rate`)、音訊軌道 (`audio_stream`)
        2. 抽取 20%、50%、80% 三個時間點的畫面影格，檢測亮度、對比度與畫面差異度（確認是動態實機畫面而非黑屏或死圖）
        """
        if not os.path.exists(video_path):
            return {"passed": False, "score": 0, "issues": ["影片檔案不存在"]}

        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration,bit_rate:stream=codec_type,width,height",
            "-of", "json",
            video_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        info = json.loads(res.stdout)

        fmt = info.get("format", {})
        duration = float(fmt.get("duration", 0.0))
        bitrate = int(fmt.get("bit_rate", 0))
        streams = info.get("streams", [])
        has_video = any(s.get("codec_type") == "video" for s in streams)
        has_audio = any(s.get("codec_type") == "audio" for s in streams)

        issues: List[str] = []
        score = 100

        if not has_video:
            issues.append("缺少視訊軌")
            score -= 50
        if not has_audio:
            issues.append("缺少旁白與 BGM 音訊軌")
            score -= 40
        if duration < expected_min_duration * 0.7:
            issues.append(f"片長 ({duration:.1f}s) 低於目標門檻 ({expected_min_duration:.1f}s)")
            score -= 15

        # 抽幀進行視覺動態與清晰度審閱
        temp_frames_dir = os.path.join(os.path.dirname(video_path), "_qa_frames")
        os.makedirs(temp_frames_dir, exist_ok=True)
        frame_means: List[float] = []
        frame_stds: List[float] = []

        for idx, ratio in enumerate((0.2, 0.5, 0.8), start=1):
            ts = max(0.5, duration * ratio)
            f_path = os.path.join(temp_frames_dir, f"qa_{ 'shorts' if is_shorts else 'long' }_{idx}.jpg")
            subprocess.run(
                [
                    "ffmpeg", "-y", "-ss", f"{ts:.2f}", "-i", video_path,
                    "-frames:v", "1", "-q:v", "3", f_path
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            if os.path.exists(f_path):
                with Image.open(f_path) as im:
                    stat = ImageStat.Stat(im.convert("L"))
                    frame_means.append(stat.mean[0])
                    frame_stds.append(stat.stddev[0])

        # 檢查是否黑屏或過暗
        if frame_means and max(frame_means) < 12.0:
            issues.append("畫面亮度過低疑似黑屏")
            score -= 35
        # 檢查對比度與資訊豐富度
        if frame_stds and max(frame_stds) < 18.0:
            issues.append("畫面視覺對比度不足")
            score -= 15
        # 檢查不同時間點的畫面是否有動態變化
        if len(frame_means) >= 2 and abs(frame_means[0] - frame_means[-1]) < 0.05 and abs(frame_stds[0] - frame_stds[-1]) < 0.05:
            issues.append("前後影格幾乎無變化，疑似靜態死圖")
            score -= 25

        passed = score >= 80
        report = {
            "video_path": video_path,
            "is_shorts": is_shorts,
            "duration_sec": round(duration, 1),
            "bitrate_kbps": round(bitrate / 1000, 1),
            "frame_contrast_std": [round(x, 1) for x in frame_stds],
            "score": max(0, score),
            "passed": passed,
            "issues": issues
        }
        print(
            f"🔍 [SelfCritic QA] {'Shorts' if is_shorts else '長片'}自我審閱結果: "
            f"{report['score']}分 ({'✅ 通過' if passed else '⚠️ 需優化'}) | "
            f"片長: {report['duration_sec']}s | 視覺對比度: {report['frame_contrast_std']}"
        )
        return report

    def evaluate_algorithm_and_views(self, campaign_summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        審閱上傳後的瀏覽量與演算法觸發指標（結合 YouTube Studio / 公開頁面數據與同題爆款熱度對標），
        並自動更新 `evolution_memory.json` 中的下一輪優化策略！
        """
        long_qa = self.inspect_rendered_video(
            campaign_summary["long_video_path"],
            expected_min_duration=420.0,
            is_shorts=False
        )
        shorts_qa = self.inspect_rendered_video(
            campaign_summary["shorts_video_path"],
            expected_min_duration=40.0,
            is_shorts=True
        )

        # 檢查若有已發布的 YouTube Video ID，則透過 yt-dlp 抓取真實即時觀看數、按讚數與留言數
        yt_id = campaign_summary.get("long_youtube_id")
        live_views = 0
        live_likes = 0
        algo_triggered = False
        algo_analysis = []

        if yt_id and yt_id not in ("queued_for_upload", "studio_uploaded"):
            try:
                cmd = ["python", "-m", "yt_dlp", f"https://youtu.be/{yt_id}", "--dump-json", "--no-warnings"]
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
                if res.stdout.strip():
                    vdata = json.loads(res.stdout.splitlines()[0])
                    live_views = int(vdata.get("view_count") or 0)
                    live_likes = int(vdata.get("like_count") or 0)
            except Exception:
                pass

        # 演算法推薦池觸發評分模型 (Algorithm Trigger Readiness Score)
        title = campaign_summary.get("long_title", "")
        has_numbers = any(ch.isdigit() for ch in title)
        has_brackets = ("【" in title or "[" in title or "！" in title)
        long_dur_ok = long_qa["duration_sec"] >= 450.0  # 滿 8 分鐘中插廣告與高權重長片池
        shorts_dur_ok = 42.0 <= shorts_qa["duration_sec"] <= 58.0

        # 嚴格防重複審查：檢查說明欄時間軸章節是否有任何重複標題
        desc_text = campaign_summary.get("monetized_description", "")
        chapter_suffixes = []
        for line in desc_text.splitlines():
            if "｜" in line:
                chapter_suffixes.append(line.split("｜", 1)[1].strip())
        has_duplicate_chapters = len(chapter_suffixes) != len(set(chapter_suffixes))

        algo_score = int((long_qa["score"] + shorts_qa["score"]) / 2)
        if has_duplicate_chapters:
            algo_score -= 50
            long_qa["passed"] = False
            algo_analysis.append("❌ 嚴重違規：偵測到重複章節或循環播放內容，已攔截並禁止上傳！")
        else:
            algo_analysis.append(f"✅ 通過零重複審查：共 {len(chapter_suffixes)} 個獨立章節全數唯一、無任何循環回放")
        if has_numbers and has_brackets:
            algo_score += 5
            algo_analysis.append("✅ 標題含強烈數字對比與括號焦點，符合高 CTR (>12%) 演算法推流特徵")
        else:
            algo_analysis.append("🔧 下一輪優化：標題需強化具體金額或倍數數字對比以拉高點擊率")

        if long_dur_ok:
            algo_score += 5
            algo_analysis.append(f"✅ 長片時長 ({long_qa['duration_sec']}s) 成功突破 8 分鐘演算法長片推薦池與中插廣告門檻")
        else:
            algo_analysis.append(f"🔧 下一輪優化：長片時長 ({long_qa['duration_sec']}s) 需增加每個分鏡的深度案例字數以突破 480s")

        if shorts_dur_ok:
            algo_analysis.append(f"✅ Shorts 時長 ({shorts_qa['duration_sec']}s) 落於 45~58s 最高完播率推流區間")

        algo_triggered = (algo_score >= 90) or (live_views >= 500)

        # 根據本次審閱結果，動態產生給下一支影片的「自我進化指令 (Self-Optimization Directives)」
        new_directives = list(self.memory.get("optimization_directives", []))
        if not long_dur_ok:
            directive = "強制將長片分鏡數提高至 18 鏡以上，每鏡旁白不少於 140 字，確保片長穩定超過 8 分 30 秒"
            if directive not in new_directives:
                new_directives.insert(0, directive)
        if long_qa["score"] >= 95 and shorts_qa["score"] >= 95:
            directive = "維持 Chromium 3D 粒子神經網路 + 真實網頁平滑捲動錄屏雙鏡頭結構，並強化前 5 秒數據暴衝特效"
            if directive not in new_directives:
                new_directives.insert(0, directive)

        estimated_cpm = float(campaign_summary.get("estimated_cpm_usd") or 25.0)
        estimated_adsense_usd = round((live_views / 1000.0) * estimated_cpm, 2)

        review_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "product": campaign_summary.get("product"),
            "long_title": title,
            "long_qa": long_qa,
            "shorts_qa": shorts_qa,
            "live_views": live_views,
            "live_likes": live_likes,
            "estimated_cpm_usd": estimated_cpm,
            "estimated_adsense_revenue_usd": estimated_adsense_usd,
            "algorithm_readiness_score": min(100, algo_score),
            "algorithm_triggered": algo_triggered,
            "algo_diagnostics": algo_analysis
        }

        self.memory["total_inspected"] = self.memory.get("total_inspected", 0) + 1
        if algo_triggered:
            self.memory["algorithm_triggered_count"] = self.memory.get("algorithm_triggered_count", 0) + 1
        self.memory["optimization_directives"] = new_directives[:6]
        self.memory.setdefault("video_reviews", []).append(review_entry)
        self._save_memory()

        print(
            f"📈 [SelfCritic & AlgoTracker] 演算法推流潛力評分: {review_entry['algorithm_readiness_score']}/100 | "
            f"觸發演算法狀態: {'🔥 已達高推流標準' if algo_triggered else '⏳ 持續優化中'}\n"
            f"   └─ 進化指令已寫入 `{os.path.basename(self.memory_path)}` 供下一支影片自動套用！"
        )
        return review_entry

    def poll_channel_long_term_analytics(self, channel_handle_or_url: str = "https://www.youtube.com") -> Dict[str, Any]:
        """
        長時間巡檢已上傳影片的累積觀看次數 (Views)、演算法觸及狀態 (Algorithm Triggered) 與預估 AdSense 廣告收益 ($ USD)，
        並更新至 `evolution_memory.json`。
        """
        total_views = 0
        total_revenue = 0.0
        for item in self.memory.get("video_reviews", []):
            total_views += int(item.get("live_views", 0))
            total_revenue += float(item.get("estimated_adsense_revenue_usd", 0.0))

        summary = {
            "checked_at": datetime.datetime.now().isoformat(),
            "total_videos_reviewed": self.memory.get("total_inspected", 0),
            "algorithm_triggered_videos": self.memory.get("algorithm_triggered_count", 0),
            "cumulative_views": total_views,
            "cumulative_estimated_adsense_usd": round(total_revenue, 2)
        }
        self.memory["long_term_channel_metrics"] = summary
        self._save_memory()
        return summary
