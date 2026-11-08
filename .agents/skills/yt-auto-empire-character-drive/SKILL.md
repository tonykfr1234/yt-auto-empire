---
name: yt-auto-empire-character-drive
description: Autonomous 24/7 YouTube & Shorts video production pipeline with Google Flow dedicated project (Veo 3.1 Highest Quality 1080p), Google Drive unified vault sync, Google flagship model character generation, non-repeating subtitle-contextual 60fps animated scenes, audible background music (BGM), female creator voiceover, single-clause intact subtitles throughout the entire video, 9:1 Viral-to-GitHub topic ratio, and 90+ Self-Critic QA gatekeeper.
---

# YT-Auto-Empire: Google Flow 1080p + Character & Subtitle-Contextual Video Engine + Google Drive Vault Skill

Use this skill whenever building, maintaining, upgrading, or executing the autonomous YouTube 16:9 long-form and 9:16 Shorts generation pipeline (`YT-Auto-Empire` at `C:\Users\tonyk\.gemini\antigravity\scratch\yt-auto-empire`).

---

## 1. Google Flow Dedicated Project & Highest Quality Engine (`video_generator.py`)

Every video MUST be generated/remade via **Google Flow (`https://flow.google.com/`)** inside a single unified project:
- **Dedicated Project Name**: `YT-Auto-Empire YouTube 爆款影片總部` (persisted in `flow_project_state.json`)
- **Model & Quality**: Always select **`Veo 3.1 - Quality` / `Highest Quality (最高品質)`** and export at **`1080p Upscaled`** (`engine_mode="flow"`).
- **Browser Connection Priority (`_connect_flow_browser`)**:
  1. Connects directly to the user's logged-in Chrome via `User Data/DevToolsActivePort` (enabled at `chrome://inspect/#remote-debugging`).
  2. Connects via local CDP port `http://127.0.0.1:9222`.
  3. Launches persistent `chrome_profile`.

---

## 2. Unified Google Drive Video Vault (`gdrive_sync.py`)

All completed videos, thumbnails, and subtitle files MUST be automatically synchronized to a single unified folder on Google Drive:
- **Root Vault Path**: `G:\我的雲端硬碟\YT-Auto-Empire-Videos`
- **Subdirectory Structure**:
  1. `G:\我的雲端硬碟\YT-Auto-Empire-Videos\01_16x9_橫式深度長片` — Named `[16x9長片]_<timestamp>_<topic>.mp4`
  2. `G:\我的雲端硬碟\YT-Auto-Empire-Videos\02_9x16_直式爆款Shorts` — Named `[9x16短片]_<timestamp>_<topic>.mp4`
  3. `G:\我的雲端硬碟\YT-Auto-Empire-Videos\03_完整專案包_含縮圖與字幕\<campaign_id>_<topic>\` — Contains `final_long_16x9.mp4`, `final_shorts_9x16.mp4`, `thumbnail_16x9.jpg`, `final_long_16x9.srt`, `final_shorts_9x16.srt`, and `02_campaign_summary.json`
  4. `G:\我的雲端硬碟\YT-Auto-Empire-Videos\00_影片總表清單.md` — Auto-generated Markdown index of all completed campaigns and direct file paths.

---

## 3. Human Character + Zero Scene Repetition + 100% Full-Duration Subtitle-Synced Visuals (`viral_broll_engine.py` & `auto_editor.py`)

Every video scene MUST satisfy four strict visual and audio rules:
1. **Every Scene Features a Human Character (`人物`)**:
   - Calls Google's flagship image generation models (`models/gemini-3-pro-image` -> `models/gemini-nano-banana-2.1` -> `models/gemini-3.1-flash-lite-image`) via `google-genai` SDK (`_generate_google_best_model_illustration()`).
   - Renders a 60fps articulated 2D/3D virtual tech presenter (`drawAnimatedCreator()`) with **24 distinct personas across 24 scenes** (`sid = 1..24`), natural eye blinking, breathing, pointing arm, and real-time voice-synced mouth animation (`talkOpen`).
2. **Zero Scene Repetition (`每一個畫面都不能重複`)**:
   - Strictly forbid `-stream_loop -1` or reusing identical visual backgrounds across scenes.
3. **Full-Duration Subtitles Synchronized 1:1 with Visuals (`全程都有字幕 配合畫面`)**:
   - Both `viral_broll_engine.py` and `auto_editor.py` split narration using the exact same punctuation regex (`r"[。！？；：，、—…]+"`) and calculate each clause's exact cumulative character ratio (`cumChars / totalChars`).
   - As each subtitle clause appears at the bottom of the screen from `00:00.000` to the end of the video, the on-screen character gesture and central stage illustration (`drawSubtitleContextualStage()`) switch at the **exact millisecond** to illustrate that exact subtitle sentence.
   - Burned-in subtitles execute with `cwd=srt_dir` and relative filename `subtitles='final_long_16x9.srt'` (`FontSize=12` for 16:9, `FontSize=7` for 9:16) so subtitles never fail or overflow screen edges.
4. **Audible Rhythmic Background Music (`加上背景音樂`)**:
   - `generate_cyber_bgm_and_sfx()` synthesizes a full-duration stereo Synthwave/Tech rhythm track (bassline pulse + chord progression + 120BPM arpeggio) and mixes it with the female creator voiceover (`zh-TW-HsiaoChenNeural`) using `amix=inputs=2:duration=first:dropout_transition=0:normalize=0` (`[0:a]volume=1.05[va];[1:a]volume=0.28[bg]`).

---

## 4. Standing Editorial Rules
1. **9:1 Viral-to-GitHub Topic Ratio (`daemon_24_7.py`)**: 9 YouTube viral competitor remakes (`cycle_num % 10 != 0`) to 1 GitHub Trending open-source showcase (`cycle_num % 10 == 0`).
2. **Unified Stress Testing Chapter**: Never split stress testing (`壓力測試`) into `(上)/(下)`.
3. **Self-Critic QA Gatekeeper (`self_critic_and_analytics.py`)**: Every video must score **>= 90/100** before archiving to Google Drive and uploading to YouTube.
