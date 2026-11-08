---
name: yt-auto-empire-character-drive
description: Autonomous 24/7 YouTube & Shorts video production pipeline with Google Drive unified vault sync, Google flagship model character generation, non-repeating subtitle-contextual 60fps animated scenes, female creator voiceover, single-clause intact subtitles, 9:1 Viral-to-GitHub topic ratio, and 90+ Self-Critic QA gatekeeper.
---

# YT-Auto-Empire: Google Character & Subtitle-Contextual Video Engine + Google Drive Vault Skill

Use this skill whenever building, maintaining, upgrading, or executing the autonomous YouTube 16:9 long-form and 9:16 Shorts generation pipeline (`YT-Auto-Empire` at `C:\Users\tonyk\.gemini\antigravity\scratch\yt-auto-empire`).

---

## 1. Unified Google Drive Video Vault (`gdrive_sync.py`)

All completed videos, thumbnails, and subtitle files MUST be automatically synchronized to a single unified folder on Google Drive:
- **Root Vault Path**: `G:\我的雲端硬碟\YT-Auto-Empire-Videos`
- **Subdirectory Structure**:
  1. `G:\我的雲端硬碟\YT-Auto-Empire-Videos\01_16x9_橫式深度長片` — Named `<campaign_id>_<safe_topic>_16x9_長片.mp4`
  2. `G:\我的雲端硬碟\YT-Auto-Empire-Videos\02_9x16_直式爆款Shorts` — Named `<campaign_id>_<safe_topic>_9x16_Shorts.mp4`
  3. `G:\我的雲端硬碟\YT-Auto-Empire-Videos\03_完整專案包_含縮圖與字幕\<campaign_id>_<safe_topic>\` — Contains `final_16x9_long.mp4`, `final_9x16_shorts.mp4`, `thumbnail_16x9.png`, `captions_long.srt`, `captions_shorts.srt`, and `campaign_summary.json`
  4. `G:\我的雲端硬碟\YT-Auto-Empire-Videos\00_影片總表清單.md` — Auto-generated Markdown index of all completed campaigns, durations, QA scores, and direct file paths.

### Auto-Sync Execution
- Automatically triggered at Step 7 of [`main_pipeline.py`](file:///C:/Users/tonyk/.gemini/antigravity/scratch/yt-auto-empire/main_pipeline.py) via `GoogleDriveVideoVault().sync_campaign(campaign_dir, summary)`.
- Can also be run standalone to backfill all historical runs:
  ```powershell
  cd "C:\Users\tonyk\.gemini\antigravity\scratch\yt-auto-empire"
  python gdrive_sync.py
  ```

---

## 2. Human Character + Zero Scene Repetition + Subtitle-Contextual Visuals (`viral_broll_engine.py`)

Every video scene MUST satisfy three strict visual rules:
1. **Every Scene Features a Human Character (`人物`)**:
   - Calls Google's flagship image generation models (`models/gemini-3-pro-image` -> `models/gemini-nano-banana-2.1` -> `models/gemini-3.1-flash-lite-image`) via `google-genai` SDK (`_generate_google_best_model_illustration()`) to generate a custom scene illustration with an expressive tech creator character.
   - Renders a 60fps articulated 2D/3D virtual tech presenter (`drawAnimatedCreator()`) with **24 distinct personas across 24 scenes** (`sid = 1..24`):
     - **5 Hairstyles**: `long_wave`, `ponytail`, `short_bob`, `twin_cyber`, `bun_pro`
     - **5 Headwear / Eyewear Styles**: `studio_headset`, `cyber_visor`, `round_glasses`, `ar_monocle`, `none`
     - **6 Interactive Hand Props**: `condenser_mic`, `coffee_mug`, `holo_tablet`, `laser_wand`, `gpu_card`, `energy_shield`
     - **Real-Time Articulation**: Natural eye blinking, chest breathing, dynamic pointing arm, and real-time voice-synced mouth animation (`talkOpen`) tied to the active narration clause.
2. **Zero Scene Repetition (`每一個畫面都不能重複`)**:
   - Strictly forbid `-stream_loop -1` or reusing identical visual backgrounds across scenes.
   - Each scene (`scene_01.mp4` .. `scene_24.mp4`) combines its unique `scene_id` palette, camera orbit, character persona, and clause index (`variant = ((sid - 1) * 4 + clauseIdx) % 12`) so no two shots ever repeat.
   - Each clip is rendered to cover its full voiceover duration (`duration_sec`), using `tpad=stop_mode=clone` only as a safety tail buffer.
3. **Visuals Directly Tied to Subtitles (`並且要跟字幕有關係`)**:
   - `analyzeClauseContext(clauseText, sid, clauseIdx)` parses the exact Chinese/English keywords of the currently spoken subtitle clause in real time and switches the central stage illustration (`drawSubtitleContextualStage()`) to match what is being said:
     - Cost / Pricing (`免費`, `$200`, `成本`, `省下`) -> Cost Comparison Chart (`$200/mo SaaS` vs `$0 Open-Source`)
     - Bug / Self-Healing (`Bug`, `除錯`, `修復`, `報錯`) -> Red Error Alert transforming into Green Self-Healed Checkmark
     - Overnight / 24-7 Automation (`睡覺`, `24`, `無人`, `半夜`) -> Sleeping Creator Moon/Bed vs 24/7 Autonomous AI Agent Dispatch
     - Stress Testing (`壓力測試`, `40`, `極限`, `併發`) -> 40-Round High-Concurrency Green Pass Matrix (`40/40 PASS`)
     - Security / Sandbox (`安全`, `隔離`, `沙盒`, `權限`) -> Cyber Shield & Isolated Container Vault
     - Hardware / Speed (`GPU`, `3070`, `效能`, `加速`) -> RTX GPU Tensor Core Speedometer
     - Installation / CLI (`安裝`, `部署`, `git`, `三分鐘`) -> Live Step-by-Step Terminal Deployment Card
     - Default -> Dynamic Multi-Node AI Workflow Topology synchronized with the active subtitle clause.

---

## 3. Standing Quality & Editorial Rules

1. **9:1 Viral-to-GitHub Topic Ratio (`daemon_24_7.py` & `viral_topic_scout.py`)**:
   - Out of every 10 campaigns:
     - **9 Campaigns (`cycle_num % 10 != 0`)**: High-performing YouTube viral AI/Tech topics (`source_mode="viral_competitor"`).
     - **1 Campaign (`cycle_num % 10 == 0`)**: GitHub Trending open-source showcase (`source_mode="github_trending"`).
2. **Female Million-Sub Creator Voiceover (`tts_engine.py`)**:
   - Uses `zh-TW-HsiaoChenNeural` with punctuation-aware clause prosody (energetic rate/pitch on hooks and exclamations, clear emphasis on technical insights) + FFmpeg studio broadcast EQ (`highpass`, `equalizer`, `acompressor`, `loudnorm`).
3. **Intact Single-Clause Subtitles & Overflow Prevention (`tts_engine.py` & `video_assembler.py`)**:
   - Never split a single continuous clause across two subtitle screens (`_split_sentences()` keeps clauses<=24 chars intact on a single screen and wraps into 2 balanced lines via `\N` if >13 chars).
   - Strict safe margins and font sizes:
     - **16:9 Long Video**: `FontSize=12`, `MarginL=90`, `MarginR=90`
     - **9:16 Shorts**: `FontSize=7`, `MarginL=55`, `MarginR=55`, `MarginV=68`
4. **Unified Topic Chapters (`script_generator.py`)**:
   - Never split stress testing (`壓力測試`) across two separate chapters (`(上)/(下)`); consolidate stress testing into one unified chapter (`極限壓力測試全紀錄`).
5. **Self-Critic QA Gatekeeper (`self_critic_qa.py`)**:
   - Every video must score **>= 90/100** across 5 dimensions (duration targets, audio loudness, visual entropy/non-repetition, subtitle alignment, and thumbnail contrast) before archiving to Google Drive and uploading to YouTube.
