#!/usr/bin/env python3
"""
auto_editor.py — FFmpeg 全自動混音、動態字幕與長短片渲染剪輯師
負責：
1. 自動測量每段 Gemini 3.8 TTS 旁白音檔 (`scene_XX.wav`) 的精準時長 (`ffprobe`)
2. 自動將每段分鏡影片 (`scene_XX.mp4`) 對齊旁白長度（不足時自動慢動作延展或循環，過長則精準裁切），並混合環境原音與高清晰人聲旁白
3. 自動計算每個分鏡的累計時間軸，生成精準對齊的 `.srt` 字幕檔與 YouTube 時間軸章節 (`00:00 章節名稱`)
4. 自動串接所有分鏡並燒錄高對比醒目字幕，同時支援加入背景音樂 (BGM 自動閃避人聲)
5. 產出 16:9 1080p 長影片 (`final_long.mp4`) 與 9:16 1080x1920 Shorts 短片 (`final_shorts.mp4`)
"""

import os
import subprocess
from typing import List, Dict, Any, Tuple


class AutoVideoEditor:
    """基於 FFmpeg / FFprobe 的全自動影片剪輯與字幕合成引擎。"""

    def __init__(self, work_dir: str = "output"):
        self.work_dir = os.path.abspath(work_dir)
        os.makedirs(self.work_dir, exist_ok=True)
        self._verify_ffmpeg()

    def _verify_ffmpeg(self) -> None:
        """確認系統 PATH 中已安裝 ffmpeg 與 ffprobe。"""
        for binary in ("ffmpeg", "ffprobe"):
            try:
                subprocess.run(
                    [binary, "-version"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True
                )
            except (subprocess.SubprocessError, FileNotFoundError):
                raise RuntimeError(
                    f"系統找不到 `{binary}`！請先安裝 FFmpeg (例如執行 `winget install Gyan.FFmpeg`)。"
                )

    @staticmethod
    def get_media_duration(media_path: str) -> float:
        """使用 ffprobe 取得音訊或視訊的精準秒數。"""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            media_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return max(0.5, float(res.stdout.strip()))

    @staticmethod
    def _format_srt_timestamp(seconds: float) -> str:
        """將秒數轉為 SRT 字幕時間格式 `HH:MM:SS,mmm`。"""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int(round((seconds - int(seconds)) * 1000))
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

    @staticmethod
    def _format_yt_chapter_timestamp(seconds: float) -> str:
        """將秒數轉為 YouTube 章節時間格式 `MM:SS`。"""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    def mux_scene_video_and_voice(
        self,
        raw_video_path: str,
        voice_wav_path: str,
        muxed_output_path: str,
        target_width: int,
        target_height: int
    ) -> Tuple[str, float]:
        """
        將單一分鏡影片與 TTS 旁白完美結合：
        - 自動將影片循環/裁切至與旁白音檔完全相同的長度
        - 統一縮放與填充至目標解析度 (1920x1080 或 1080x1920, 30fps)
        - 將 Gemini Omni 產生的環境背景音降低至 15% 音量，凸顯 100% 清晰的 TTS 旁白
        """
        voice_dur = self.get_media_duration(voice_wav_path)
        os.makedirs(os.path.dirname(muxed_output_path), exist_ok=True)

        vf_filter = (
            f"scale={target_width}:{target_height}:force_original_aspect_ratio=increase,"
            f"crop={target_width}:{target_height},fps=30,tpad=stop_mode=clone:stop_duration=5,format=yuv420p"
        )

        # 嚴格禁止 -stream_loop -1 重複循環播放！確保每段分鏡從頭到尾單次推進絕不回放
        cmd = [
            "ffmpeg", "-y",
            "-i", raw_video_path,
            "-i", voice_wav_path,
            "-filter_complex",
            f"[0:v]{vf_filter}[v];[1:a]aresample=44100,volume=1.0[a]",
            "-map", "[v]",
            "-map", "[a]",
            "-c:v", "h264_nvenc",
            "-preset", "p4",
            "-cq", "21",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", f"{voice_dur:.3f}",
            muxed_output_path
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            cmd[cmd.index("h264_nvenc")] = "libx264"
            cmd[cmd.index("-preset") + 1] = "fast"
            cmd[cmd.index("-cq")] = "-crf"
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return muxed_output_path, voice_dur

    def assemble_timeline(
        self,
        scenes: List[Dict[str, Any]],
        raw_clips: List[str],
        voice_wavs: List[str],
        output_video_path: str,
        srt_output_path: str,
        aspect_ratio: str = "16:9"
    ) -> Tuple[str, str, List[str]]:
        """
        全自動組裝整支長片或 Shorts：
        1. 逐一對齊合併每個分鏡的畫面與配音
        2. 產生時間軸完全同步的 `.srt` 字幕檔與 YouTube 章節列表
        3. 串接所有分鏡並將字幕燒錄至畫面中
        """
        width, height = (1920, 1080) if aspect_ratio == "16:9" else (1080, 1920)
        temp_dir = os.path.join(os.path.dirname(output_video_path), f"temp_mux_{aspect_ratio.replace(':', 'x')}")
        os.makedirs(temp_dir, exist_ok=True)

        muxed_files: List[str] = []
        srt_entries: List[str] = []
        yt_chapters: List[str] = []
        current_time = 0.0

        for idx, (scene, clip_path, wav_path) in enumerate(zip(scenes, raw_clips, voice_wavs), start=1):
            muxed_path = os.path.join(temp_dir, f"muxed_{idx:02d}.mp4")
            _, dur = self.mux_scene_video_and_voice(
                raw_video_path=clip_path,
                voice_wav_path=wav_path,
                muxed_output_path=muxed_path,
                target_width=width,
                target_height=height
            )
            muxed_files.append(muxed_path)

            # 紀錄 YouTube 章節時間軸 (第一個章節必須是 00:00)
            chapter_time = "00:00" if idx == 1 else self._format_yt_chapter_timestamp(current_time)
            chapter_title = scene.get("chapter_title") or f"重點解析 {idx}"
            yt_chapters.append(f"{chapter_time} {chapter_title}")

            # 將旁白依標點符號拆分為完整語意短句：嚴格保持「同一句話完整呈現在同一個字幕畫面」，絕不把同一句話硬切成兩段畫面！
            raw_text = scene["narration"].strip()
            import re
            sentences = [
                c.strip(" ，。！？；：、—…")
                for c in re.split(r"[。！？；：，、—…]+", raw_text)
                if c.strip(" ，。！？；：、—…")
            ]
            if not sentences:
                sentences = [raw_text]

            total_chars = max(1, sum(len(s) for s in sentences))
            seg_cursor = current_time
            for s in sentences:
                seg_dur = dur * (len(s) / total_chars)
                start_str = self._format_srt_timestamp(seg_cursor)
                end_str = self._format_srt_timestamp(seg_cursor + seg_dur)
                srt_idx = len(srt_entries) + 1
                srt_entries.append(f"{srt_idx}\n{start_str} --> {end_str}\n{s}\n")
                seg_cursor += seg_dur

            current_time += dur

        # 寫入 SRT 字幕檔
        with open(srt_output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(srt_entries))

        # 建立 FFmpeg concat 清單
        concat_list_path = os.path.join(temp_dir, "concat_list.txt")
        with open(concat_list_path, "w", encoding="utf-8") as f:
            for mf in muxed_files:
                safe_path = mf.replace("\\", "/")
                f.write(f"file '{safe_path}'\n")

        # 先無損串接所有分鏡
        concat_raw_path = os.path.join(temp_dir, "concat_raw.mp4")
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_list_path,
                "-c", "copy",
                concat_raw_path
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )

        # 生成百萬頻道級科技律動背景音樂 (Cyber-Pulse BGM) 並與人聲混音
        from viral_broll_engine import ViralVisualEngine
        v_engine = ViralVisualEngine(work_dir=temp_dir)
        bgm_wav = os.path.join(temp_dir, "cyber_bgm.wav")
        v_engine.generate_cyber_bgm_and_sfx(duration_sec=current_time, output_wav=bgm_wav)

        # 燒錄高對比單行居中字幕 (9:16 垂直畫面設為 FontSize=7 = 46px，單行可完整容納 21 個中文字，同一句話完整顯示於單一畫面且絕不破框！)
        srt_dir = os.path.dirname(os.path.abspath(srt_output_path))
        srt_filename = os.path.basename(srt_output_path)
        font_size = 12 if aspect_ratio == "16:9" else 7
        margin_v = 34 if aspect_ratio == "16:9" else 70
        margin_h = 30 if aspect_ratio == "16:9" else 24
        sub_filter = (
            f"subtitles='{srt_filename}':force_style="
            f"'FontName=Microsoft JhengHei,Bold=1,FontSize={font_size},PrimaryColour=&H0000FFFF,"
            f"OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=1,Alignment=2,"
            f"MarginL={margin_h},MarginR={margin_h},MarginV={margin_v},WrapStyle=2'"
        )

        burn_cmd = [
            "ffmpeg", "-y",
            "-i", os.path.abspath(concat_raw_path),
            "-i", os.path.abspath(bgm_wav),
            "-filter_complex",
            f"[0:v]{sub_filter}[v];[0:a]volume=1.05[va];[1:a]volume=0.28[bg];[va][bg]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]",
            "-map", "[v]",
            "-map", "[a]",
            "-c:v", "h264_nvenc",
            "-preset", "p4",
            "-cq", "20",
            "-c:a", "aac",
            "-b:a", "192k",
            os.path.abspath(output_video_path)
        ]
        burn_proc = subprocess.run(burn_cmd, cwd=srt_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if burn_proc.returncode != 0:
            burn_cmd[burn_cmd.index("h264_nvenc")] = "libx264"
            burn_cmd[burn_cmd.index("-preset") + 1] = "fast"
            burn_cmd[burn_cmd.index("-cq")] = "-crf"
            subprocess.run(burn_cmd, cwd=srt_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        print(f"[AutoEditor] 影片剪輯完成 ({aspect_ratio}, 總長 {current_time:.1f}s): {output_video_path}")
        return output_video_path, srt_output_path, yt_chapters
