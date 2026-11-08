#!/usr/bin/env python3
"""
gemini_director.py — Gemini 4 Argon / 3.8 Flash 總導演模組
負責生成：
1. 長影片完整分鏡腳本（專為衝高觀看時長、突破 8 分鐘中插廣告門檻設計）
2. 高留存 Shorts 短影音腳本（前 3 秒黃金 Hook，引流至長影片與商品連結）
3. Gemini Omni 1.2 Flash / Google Flow 專用英文視覺運鏡 Prompt
4. Gemini 3.8 Flash TTS 擬真配音（內建 Edge-TTS 台灣自然語音高擬真備援，免 Key 亦可全自動配音）
5. Gemini Nano Banana 2.1 高點閱率 (CTR) 縮圖生成（內建 Pillow 高對比爆款縮圖自動渲染備援）
"""

import asyncio
import base64
import json
import os
import subprocess
from typing import Dict, Any, List
from google import genai
from PIL import Image, ImageDraw, ImageFont


class GeminiDirector:
    """統籌腳本企劃、AI 配音與高點擊縮圖生成。"""

    def __init__(self, output_dir: str = "output"):
        self.api_key = os.getenv("GEMINI_API_KEY")
        from google.genai import types
        self.client = (
            genai.Client(http_options=types.HttpOptions(timeout=15_000))
            if self.api_key
            else None
        )
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def create_production_blueprint(
        self,
        product_info: Dict[str, Any],
        long_scene_count: int = 8,
        shorts_scene_count: int = 4
    ) -> Dict[str, Any]:
        """
        使用 Gemini 4 Argon 根據爆品資訊生成「長影片 + Shorts 短片 + SEO 變現包」完整結構化藍圖。
        若環境尚未配置 GEMINI_API_KEY，則由內建的 Antigravity 導演引擎直接根據即時抓到的 GitHub 爆品產出高轉換分鏡藍圖。
        """
        print(f"[GeminiDirector] 正在為【{product_info['product_name']}】策劃高收益長短片腳本與分鏡...")
        evolution_directives_str = ""
        if os.path.exists("evolution_memory.json"):
            try:
                with open("evolution_memory.json", "r", encoding="utf-8") as ef:
                    emem = json.load(ef)
                dirs = emem.get("optimization_directives", [])
                if dirs:
                    evolution_directives_str = "\n【過去影片自我審閱與演算法優化強制指令（務必遵守）】\n- " + "\n- ".join(dirs) + "\n"
            except Exception:
                pass

        from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

        def _call_cloud_with_hard_timeout(fn, timeout_sec: float = 12.0):
            ex = ThreadPoolExecutor(max_workers=1)
            fut = ex.submit(fn)
            try:
                return fut.result(timeout=timeout_sec)
            finally:
                ex.shutdown(wait=False, cancel_futures=True)

        if self.client:
            prompt = f"""
你是一位擁有千萬訂閱操盤經驗的 YouTube 總導演與演算法專家。
我們要針對以下爆品製作一套「長影片（衝 AdSense 高額廣告分潤）+ Shorts 短片（爆發引流 + 聯盟帶貨）」的雙軌內容：

【爆品資料】
{json.dumps(product_info, ensure_ascii=False, indent=2)}
{evolution_directives_str}
請設計一份完整的影片製作藍圖（Production Blueprint），完美對標百萬訂閱科技博主的黃金片長與留存結構：
1. `long_video`（16:9 橫式深度評測長片，共 {long_scene_count} 個核心分鏡段落，目標總片長 **8 分 30 秒 ~ 10 分鐘（500~600秒）**，精準開啟 YouTube 8 分鐘片中插播廣告 Mid-roll Ads 翻倍收益門檻！）：
   - **每個分鏡的 `narration`（旁白台詞）必須極度充實、口語化、有深度案例與數據對比，每個分鏡台詞字數必須達到 120~150 個中文字（語音時長約 28~32 秒）！切勿只寫一兩句話！**
   - `duration_sec` 固定設為 `28`。
2. `shorts_video`（9:16 直式爆款短影音，共 {shorts_scene_count} 個快節奏分鏡段落，目標黃金總片長 **45 秒 ~ 58 秒**，前 3 秒極限痛點鉤子 + 結尾無縫循環 Loop 設計，衝刺 120%+ 完播率！）：
   - 每個 Shorts 分鏡的 `narration` 台詞字數必須在 **55~65 個中文字（語音時長約 12~14 秒）**，`duration_sec` 設為 `13`。
3. `seo_metadata`（YouTube 演算法極大化 SEO 與變現配置）
"""
            scene_schema = {
                "type": "object",
                "properties": {
                    "scene_id": {"type": "integer"},
                    "chapter_title": {"type": "string"},
                    "narration": {"type": "string"},
                    "voice_style": {"type": "string"},
                    "visual_prompt": {"type": "string"},
                    "duration_sec": {"type": "integer"},
                    "use_google_flow": {"type": "boolean"}
                },
                "required": [
                    "scene_id",
                    "chapter_title",
                    "narration",
                    "voice_style",
                    "visual_prompt",
                    "duration_sec",
                    "use_google_flow"
                ]
            }

            blueprint_schema = {
                "type": "object",
                "properties": {
                    "long_video": {
                        "type": "object",
                        "properties": {
                            "scenes": {"type": "array", "items": scene_schema}
                        },
                        "required": ["scenes"]
                    },
                    "shorts_video": {
                        "type": "object",
                        "properties": {
                            "scenes": {"type": "array", "items": scene_schema}
                        },
                        "required": ["scenes"]
                    },
                    "seo_metadata": {
                        "type": "object",
                        "properties": {
                            "long_title": {"type": "string"},
                            "shorts_title": {"type": "string"},
                            "description": {"type": "string"},
                            "tags": {"type": "array", "items": {"type": "string"}},
                            "thumbnail_prompt": {"type": "string"},
                            "pinned_comment": {"type": "string"}
                        },
                        "required": [
                            "long_title",
                            "shorts_title",
                            "description",
                            "tags",
                            "thumbnail_prompt",
                            "pinned_comment"
                        ]
                    }
                },
                "required": ["long_video", "shorts_video", "seo_metadata"]
            }

            blueprint = None
            for model_candidate in ("gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-3.8-flash"):
                try:
                    interaction = _call_cloud_with_hard_timeout(
                        lambda m=model_candidate: self.client.interactions.create(
                            model=m,
                            input=prompt,
                            response_format={
                                "type": "text",
                                "mime_type": "application/json",
                                "schema": blueprint_schema
                            }
                        ),
                        timeout_sec=15.0
                    )
                    blueprint = json.loads(interaction.output_text)
                    # 若雲端模型偷懶寫太短（單段台詞少於 90 字或分鏡數不足），自動與本地百萬博主深度長片結構融合擴充，確保長片突破 8 分鐘！
                    cloud_long = blueprint.get("long_video", {}).get("scenes", [])
                    total_narration_chars = sum(len(s.get("narration", "")) for s in cloud_long)
                    if len(cloud_long) < 14 or total_narration_chars < 1600:
                        print(f"[GeminiDirector] 雲端生成字數 ({total_narration_chars}字) 未達 8 分鐘門檻，自動啟動【百萬博主 8分30秒 深度擴充引擎】！")
                        rich_bp = self._build_autonomous_blueprint(product_info, long_scene_count, shorts_scene_count)
                        blueprint["long_video"] = rich_bp["long_video"]
                        if sum(len(s.get("narration", "")) for s in blueprint.get("shorts_video", {}).get("scenes", [])) < 180:
                            blueprint["shorts_video"] = rich_bp["shorts_video"]
                    print(f"[GeminiDirector] 成功透過雲端模型 `{model_candidate}` 生成完整分鏡腳本！")
                    break
                except Exception as e:
                    print(f"[GeminiDirector] 雲端模型 `{model_candidate}` 15s 快速切換備援 ({e})")

            if not blueprint:
                blueprint = self._build_autonomous_blueprint(product_info, long_scene_count, shorts_scene_count)
        else:
            blueprint = self._build_autonomous_blueprint(product_info, long_scene_count, shorts_scene_count)

        # 嚴格防重複守門員：確保長短片中絕無任何重複的章節標題或重複旁白台詞
        for key in ("long_video", "shorts_video"):
            raw_scenes = blueprint.get(key, {}).get("scenes", [])
            unique_scenes = []
            seen_titles = set()
            seen_narrations = set()
            for sc in raw_scenes:
                ct = sc.get("chapter_title", "").strip()
                nr = sc.get("narration", "").strip()[:60]
                if ct in seen_titles or nr in seen_narrations:
                    continue
                seen_titles.add(ct)
                seen_narrations.add(nr)
                sc["scene_id"] = len(unique_scenes) + 1
                unique_scenes.append(sc)
            if key in blueprint:
                blueprint[key]["scenes"] = unique_scenes

        blueprint_path = os.path.join(self.output_dir, "production_blueprint.json")
        with open(blueprint_path, "w", encoding="utf-8") as f:
            json.dump(blueprint, f, indent=2, ensure_ascii=False)

        print(f"[GeminiDirector] 腳本藍圖已儲存至: {blueprint_path}")
        return blueprint

    def _build_autonomous_blueprint(
        self,
        product_info: Dict[str, Any],
        long_scene_count: int = 18,
        shorts_scene_count: int = 4
    ) -> Dict[str, Any]:
        """
        對標百萬訂閱科技博主的黃金片長規格：
        - 長片 (Long Video): 18 個深度分鏡 × 每段 ~28 秒詳盡解說 = 總長約 **8 分 30 秒 (510 秒)**，100% 突破 YouTube 8 分鐘多重片中廣告 (Mid-roll Ads) 門檻！
        - 短片 (Shorts): 4 個快節奏分鏡 × 每段 ~13 秒 = 總長約 **52 秒**（TikTok / YouTube Shorts 最高收益與最高完播率 45~58 秒黃金區間）！
        """
        pname = product_info["product_name"]
        is_github_topic = ("github" in pname.lower()) or ("github" in str(product_info.get("tagline", "")).lower())
        ch1_title = (
            "01｜震撼開場：GitHub 一週狂攬 4000 星的免費怪獸"
            if is_github_topic
            else "01｜震撼開場：全網突破百萬觀看的 AI 自動化神級工作流"
        )
        ch1_narration = (
            f"別再每個月花兩百美金訂閱那些半吊子的 AI 軟體當冤大頭了！就在這禮拜，全球工程師社群與 GitHub 飆升榜突然殺出了一匹黑馬開源怪獸：{pname}！短短不到七天時間，星星數直接突破四千大關。為什麼連矽谷頂級開發者都在瘋傳？因為它真正做到了讓 AI 助理在你的電腦背景二十四小時自己接單、自己寫程式、自己除錯，甚至連你半夜睡覺的時候，它都在幫你持續產出專案與被動收入！今天這支完整深度實測，我會手把手帶你看懂它的底層黑科技，以及普通人如何用三分鐘免費部署這台全天候印鈔機！"
            if is_github_topic
            else f"別再每個月花兩百美金訂閱那些半吊子的 AI 軟體當冤大頭了！就在這禮拜，YouTube 科技圈與矽谷開發者社群突然瘋傳這套突破百萬點閱的自動化怪獸：{pname}！為什麼連頂級一人公司創辦人都在熬夜實測？因為它真正做到了讓 AI 助理在你的電腦背景二十四小時自己接單、自己執行任務、自己除錯，甚至連你半夜睡覺的時候，它都在幫你持續產出專案與被動收入！今天這支完整深度實測，我會手把手帶你看懂它的底層黑科技，以及普通人如何用三分鐘免費部署這台全天候印鈔機！"
        )
        base_long_scenes = [
            {
                "scene_id": 1,
                "chapter_title": ch1_title,
                "narration": ch1_narration,
                "voice_style": "dramatic and enthusiastic",
                "visual_prompt": "Cinematic 4K 3D holographic showcase of autonomous AI workflow engine with live terminal windows.",
                "duration_sec": 28,
                "use_google_flow": True
            },
            {
                "scene_id": 2,
                "chapter_title": "02｜傳統 AI 工具的最大痛點：為什麼你成了 AI 的保母？",
                "narration": "老實說，過去這一年我們測試過上百款 AI 工具，不管是對話機器人還是輔助編程外掛，大家最大的崩潰痛點都一樣：那就是你問一句、它才動一下！只要中間遇到一個網路超時、一個套件版本衝突、或是小小的語法報錯，整個程序就會瞬間卡死停擺。你原本以為自己是請了一個全自動化的百萬年薪員工，結果最後自己卻變成二十四小時不敢離開電腦螢幕的全職保母！這種假自動化不僅沒有幫你省下時間，反而讓你每天都在重複複製貼上錯誤訊息，心力交瘁。",
                "voice_style": "empathetic and persuasive",
                "visual_prompt": "Comparison between traditional stuck AI prompt and smooth autonomous background daemon loop.",
                "duration_sec": 28,
                "use_google_flow": True
            },
            {
                "scene_id": 3,
                "chapter_title": "03｜核心架構拆解：什麼是 Unattended AutoLoop 自癒閉環？",
                "narration": "而這套開源神器之所以能徹底顛覆市場，關鍵就在於它獨創的「無人值守自癒閉環架構」。當你把一個複雜的大型目標丟給它之後，它不會像傳統 AI 那樣瞎猜硬寫，而是先在本地建立一份結構化的狀態機與任務佇列。接著，背景守護進程會自動啟動沙盒環境，每寫完一個模組就自動跑一次單元測試；如果測試失敗，它會自己讀取錯誤日誌、自己定位問題行數並完成修正，直到百分之百通過驗證才會推進到下一個節點，全程完全不需要人類插手！",
                "voice_style": "confident and analytical",
                "visual_prompt": "3D architecture diagram of autonomous state machine, unit test verification, and self-healing loop.",
                "duration_sec": 28,
                "use_google_flow": True
            },
            {
                "scene_id": 4,
                "chapter_title": "04｜關鍵決策卡片機制：平常不煩你，大事才找你拍板",
                "narration": "更聰明的是，很多全自動 Agent 最怕的就是在背景亂改資料庫或是走偏方向。這套系統設計了一個極具巧思的「非同步決策卡片機制」。在百分之九十五的常規開發、爬蟲抓取、資料清洗與轉檔過程中，它會在背景安安靜靜地自己幹活；只有當它遇到涉及金流權限、架構重大分歧、或是拿不準的商業邏輯時，才會自動整理好 A 方案與 B 方案的利弊分析卡片，推播到你的手機或桌面上，讓你喝口咖啡花三秒鐘按下一鍵拍板，立刻繼續往下狂奔！",
                "voice_style": "excited and clear",
                "visual_prompt": "Interactive decision card notification popping up with Option A vs Option B while background workers run.",
                "duration_sec": 28,
                "use_google_flow": True
            },
            {
                "scene_id": 5,
                "chapter_title": "05｜極限壓力測試全紀錄：連續 40 回合自動除錯與整合",
                "narration": "光說不練假把式，我們現在直接進入實機壓力測試！我們要求它在無人干預下，自動建立跨平台的趨勢探測與影音合成管線，並在過程中故意製造緩衝區死鎖與超時陷阱。你看畫面上的即時監控，當遇到網路超時或管道阻塞時，巡檢守門員立刻偵測到異常，自動定位原因、修改原始碼並重啟服務，在背景連續自主迭代四十幾個回合，一覺醒來所有模組全部亮起綠燈通過，穩定度直接碾壓月費兩百美金的商業軟體！",
                "voice_style": "energetic and convincing",
                "visual_prompt": "Live 3D stress test animation showing autonomous error recovery and 40/40 green light verification.",
                "duration_sec": 28,
                "use_google_flow": True
            },
            {
                "scene_id": 6,
                "chapter_title": "06｜平行沙盒隔離機制：如何保護本機檔案與環境安全？",
                "narration": "很多專業開發者一定會好奇，讓 AI 在背景擁有這麼高的執行權限，萬一它不小心改壞了系統核心檔案怎麼辦？這就要談到它非常嚴謹的「多層次平行沙盒隔離技術」。每一次啟動新任務時，引擎都會先建立一個獨立的工作分支目錄，所有的套件安裝、檔案讀寫與指令測試，都被嚴格限制在這個加密沙盒內運作，只有當所有驗收測試百分之百通過後，才會安全合併回主專案，讓你既能享受全自動的高效率，又能確保本機資料萬無一失！",
                "voice_style": "enthusiastic and analytical",
                "visual_prompt": "3D holographic security shield and isolated sandbox workspace container animation.",
                "duration_sec": 28,
                "use_google_flow": True
            },
            {
                "scene_id": 7,
                "chapter_title": "07｜殘酷成本大對決：月費 $200 商業 SaaS vs 免費方案",
                "narration": "我們來算一筆最真實的經濟帳。如果你現在去訂閱市面上主打全自動 Agent 的商業雲端服務，光是基礎月費就要兩百美金，一年下來就是兩千四百美金，相當於快八萬塊台幣！而且最致命的是，雲端沙盒往往限制你的執行時間與硬體算力，跑沒幾個任務就把額度扣光了。反觀今天實測的這套方案，軟體本身完全免費，還能直接調用你本地電腦的獨立顯卡與多核心處理器，速度比雲端虛擬機快上五到十倍，每年直接幫你省下好幾萬的智商稅！",
                "voice_style": "persuasive and emphatic",
                "visual_prompt": "Cost comparison chart: $2,400/year commercial SaaS vs $0 Free Open Source running on local GPU.",
                "duration_sec": 28,
                "use_google_flow": True
            },
            {
                "scene_id": 8,
                "chapter_title": "08｜硬體加速秘訣：如何榨乾本地 GPU 與雲端雙軌算力？",
                "narration": "很多觀眾會問，如果我想讓這套系統二十四小時全年無休地運轉，硬體該怎麼配置最划算？其實秘訣就在於「雲端與本地雙軌協同」。你可以把輕量級的趨勢雷達與文字推理交給高配額的極速模型，同時把最吃資源的畫面渲染與影音編碼，全部交給本地的 NVIDIA 顯卡硬體加速引擎處理。這樣一來，不僅完全不會遇到雲端排隊卡死的問題，單支高畫質專案的產出時間更能大幅壓縮到短短三分鐘以內！",
                "voice_style": "professional and clear",
                "visual_prompt": "Hybrid cloud + local NVIDIA RTX GPU hardware acceleration telemetry dashboard.",
                "duration_sec": 28,
                "use_google_flow": True
            },
            {
                "scene_id": 9,
                "chapter_title": "09｜一人公司變現模式：打造全自動高 CPM 數位內容工廠",
                "narration": "當你掌握了這套二十四小時不知疲倦的自動化武器後，到底該怎麼把它變成真金白銀的現金流？最直接的暴利模式，就是打造「高 CPM 科技自媒體矩陣」。就像我們現在演示的一樣，讓系統每天自動去全網挖掘最新爆紅的熱門話題與黑科技工具，自動生成深度評測長片與引流短片。因為科技與軟體領域的廣告單價是一般娛樂頻道的八到十倍，只要穩定累積作品庫，光靠平台廣告分潤就能形成極為可觀的被動收益！",
                "voice_style": "inspiring and strategic",
                "visual_prompt": "Monetization funnel diagram showing high-CPM tech content matrix generating passive AdSense revenue.",
                "duration_sec": 28,
                "use_google_flow": True
            },
            {
                "scene_id": 10,
                "chapter_title": "10｜企業私有化代部署商機：切入高單價技術顧問市場",
                "narration": "除了自媒體廣告分潤之外，背後還有潛力更大的「高單價企業服務市場」。當成千上萬的觀眾與中小企業老闆看到這些強大的自動化工具時，他們往往缺乏自己動手配置環境的時間，這時候你在說明欄掛上雲端主機與工具包的專屬推薦連結，每成交一單就能獲得三十到一百五十美金的推廣分潤，甚至還能提供一對一的企業私有化代部署顧問服務，輕鬆打造第二條高毛利收入曲線！",
                "voice_style": "enthusiastic and persuasive",
                "visual_prompt": "Affiliate commission dashboard and B2B deployment service revenue stream visualization.",
                "duration_sec": 28,
                "use_google_flow": True
            },
            {
                "scene_id": 11,
                "chapter_title": "11｜手把手零門檻教學：三分鐘完成本地環境與依賴安裝",
                "narration": "接下來進入大家最期待的保母級實操教學環節！就算你之前沒有深厚的程式背景也不用擔心，整個安裝過程只需要三行指令。第一步，先打開你的終端機，將官方的 GitHub 儲存庫完整克隆到你的電腦資料夾中；第二步，執行環境初始化腳本，系統會自動幫你把所需的依賴套件與無頭瀏覽器核心全部配置到位；第三步，打開環境設定檔，將你的定時巡檢週期與目標工作目錄填進去，整個基礎建設就大功告成了！",
                "voice_style": "helpful and step-by-step",
                "visual_prompt": "Step-by-step terminal tutorial showing git clone, dependency install, and .env configuration.",
                "duration_sec": 28,
                "use_google_flow": True
            },
            {
                "scene_id": 12,
                "chapter_title": "12｜進階防坑指南：如何設定超時保護與自動重啟守門員？",
                "narration": "在實際長期運行的過程中，有三個百萬博主不會告訴你的實戰防坑細節一定要注意！第一，千萬不要相信任何外部 API 的預設超時設定，務必在呼叫外層加上硬性執行緒超時切斷器，一旦超過十五秒沒回應就立刻切換備援；第二，在使用子行程處理大量影音串流時，記得將標準錯誤輸出導向空裝置或非同步讀取，徹底避免緩衝區溢位死鎖；第三，搭配每三十分鐘一次的排程巡檢守門員，才能真正實現三百六十五天零中斷運轉！",
                "voice_style": "authoritative and practical",
                "visual_prompt": "Pro tips checklist: Hard thread timeout, pipe buffer deadlock prevention, and 30-minute watchdog cron.",
                "duration_sec": 28,
                "use_google_flow": True
            },
            {
                "scene_id": 13,
                "chapter_title": "13｜未來趨勢預判：為什麼 2026 是自主 Agent 全面爆發年？",
                "narration": "站在更宏觀的科技浪潮來看，為什麼這類自動循環專案會在今年徹底引爆全球開發者社群？因為 AI 已經正式從「陪你聊天的對話框時代」，跨越到「替你交付結果的自主代理時代」。未來的職場與商業競爭，不再比誰會寫提示詞，而是比誰手底下擁有更多二十四小時全自動協同運作的 Agent 軍團。越早把這套開源工作流整合進你的日常業務，你就越能在這波生產力洗牌中建立起別人追不上的護城河！",
                "voice_style": "visionary and inspiring",
                "visual_prompt": "Futuristic timeline evolving from Chatbots to 24/7 Autonomous Agent Swarms in 2026.",
                "duration_sec": 28,
                "use_google_flow": True
            },
            {
                "scene_id": 14,
                "chapter_title": "14｜常見問題 Q&A：舊電腦能跑嗎？會不會有資安風險？",
                "narration": "我也整理了社群裡大家最常問的兩個核心問題。第一：如果我的電腦沒有頂規獨立顯卡，還跑得動這套開源工具嗎？答案是完全可以！因為它的核心調度邏輯非常輕量，就算是一般文書筆電或是十美金的迷你伺服器都能流暢運作。第二：讓 AI 在背景自己執行指令會不會有資安風險？這正是開源方案最大的優勢，所有程式碼完全公開透明，你可以將它的執行權限嚴格限制在專屬的工作沙盒目錄內，安全又放心！",
                "voice_style": "warm and reassuring",
                "visual_prompt": "FAQ visual cards answering hardware requirements and sandbox security isolation.",
                "duration_sec": 28,
                "use_google_flow": True
            },
            {
                "scene_id": 15,
                "chapter_title": "15｜多代理協同進階架構：讓 Researcher 與 Coder 分工合作",
                "narration": "當你熟悉了單一代理的自動化循環之後，這套框架還支援更強大的「多代理平行協同模式」。你可以同時配置一個專門負責上網檢索最新技術文件的調研代理、一個專門負責撰寫與重構核心模組的開發代理，以及一個專門負責撰寫極端邊界測試的品管代理。三個代理在本地透過結構化訊息佇列即時溝通，就像在你的電腦裡免費養了一整支矽谷敏捷開發團隊！",
                "voice_style": "confident and analytical",
                "visual_prompt": "Multi-agent swarm architecture showing Researcher, Coder, and QA Tester agents communicating in real time.",
                "duration_sec": 28,
                "use_google_flow": True
            },
            {
                "scene_id": 16,
                "chapter_title": "16｜MCP 工具生態系整合：無縫串接資料庫、瀏覽器與雲端硬碟",
                "narration": "除此之外，它還完整相容目前最火紅的標準化工具呼叫協定。這意味著你不需要自己手寫繁瑣的第三方介面串接程式，只要在設定檔裡掛載現成的瀏覽器自動化插件、本地資料庫插件或是辦公文件插件，你的 AI 就能直接讀取表格數據、自動操作網頁表單，並把分析完的視覺化圖表自動歸檔到你的本地資料夾中，擴充性幾乎沒有上限！",
                "voice_style": "enthusiastic and clear",
                "visual_prompt": "MCP plugin ecosystem connecting browser automation, SQL database, and workspace document generation.",
                "duration_sec": 28,
                "use_google_flow": True
            },
            {
                "scene_id": 17,
                "chapter_title": "17｜自我審閱與演算法反饋閉環：越跑越聰明的進化記憶庫",
                "narration": "更讓人驚艷的是它的「長期演化記憶庫機制」。一般的自動化腳本不管跑一千次還是一萬次，犯過的錯下次還是會再犯；但這套系統在每一次任務結束後，都會自動啟動自我審閱模組，針對剛剛的執行耗時、記憶體佔用與產出品質進行量化評分，並把最佳實踐參數寫入長期記憶檔。這讓你的自動化管線每跑完一輪就會自動進化一次，真正做到越用越聰明！",
                "voice_style": "inspiring and analytical",
                "visual_prompt": "Self-critic QA feedback loop updating evolution_memory.json with performance telemetry and optimization rules.",
                "duration_sec": 28,
                "use_google_flow": True
            },
            {
                "scene_id": 18,
                "chapter_title": "18｜真實案例拆解：一人開發者如何靠它一週交付三個商業專案？",
                "narration": "我們來看一個社群裡真實發生的開發者案例。一位獨立接案工程師原本每個月最多只能消化一個中小型網站與數據爬蟲外包案；自從導入這套無人值守循環引擎後，他在白天只負責跟客戶確認需求規格並轉化為驗收測試腳本，到了晚上睡覺前啟動三個獨立的沙盒工作區同步運轉，隔天早上起來直接驗收打包，短短一個禮拜就高品質交付了三個商業專案！",
                "voice_style": "persuasive and energetic",
                "visual_prompt": "Solo developer case study showing 3 parallel project workspaces completing overnight with 100% test pass rate.",
                "duration_sec": 28,
                "use_google_flow": True
            },
            {
                "scene_id": 19,
                "chapter_title": "19｜Token 與配額極致優化：如何用最少成本跑出最大產能？",
                "narration": "很多觀眾也會關心：如果讓 AI 二十四小時在背景跑迴圈，會不會把 API 額度瞬間燒光？這套專案內建了非常精妙的「漸進式上下文壓縮與快取機制」。它不會笨笨地把幾萬行的歷史對話全部塞進每一次請求裡，而是只保留最關鍵的狀態摘要與最後十行錯誤追蹤碼，成功把每次迭代的運算消耗降低了百分之八十以上，幫你把每一分免費配額都發揮到極致！",
                "voice_style": "practical and helpful",
                "visual_prompt": "Token context compression and quota optimization chart showing 82% reduction in API token usage.",
                "duration_sec": 28,
                "use_google_flow": True
            },
            {
                "scene_id": 20,
                "chapter_title": "20｜新手最常踩的三大誤區：為什麼別人的 Agent 總在原地打轉？",
                "narration": "在協助社群觀眾部署的過程中，我也發現新手最容易踩到三個致命誤區。第一是給的目標太過模糊，沒有定義清楚什麼叫做「完成」；第二是忘記提供可自動執行的驗證指令，導致 AI 無法判斷自己改對了沒；第三則是把所有不相關的任務塞在同一個工作目錄。只要避開這三個誤區，並套用我們準備好的標準化專案模板，你的成功率就能直接拉滿到百分之百！",
                "voice_style": "authoritative and clear",
                "visual_prompt": "Top 3 beginner pitfalls comparison table with clear red X mistakes vs green check best practices.",
                "duration_sec": 28,
                "use_google_flow": True
            },
            {
                "scene_id": 21,
                "chapter_title": "21｜全天候監控儀表板：隨時掌握 CPU、VRAM 與任務健康度",
                "narration": "為了讓你隨時掌握背景系統的健康狀態，我們還在套件中整合了即時的系統狀態快照功能。它會自動記錄每一輪任務的開始時間、目前執行進度、獨立顯卡硬體加速狀態以及錯誤自癒次數。不管是透過桌面狀態檔還是定時巡檢快報，你都能一目了然地看到整座數位工廠的即時運轉數據，享受真正安心的全自動被動產出體驗！",
                "voice_style": "confident and clear",
                "visual_prompt": "Real-time system health dashboard monitoring CPU, RTX GPU NVENC utilization, and task completion telemetry.",
                "duration_sec": 28,
                "use_google_flow": True
            },
            {
                "scene_id": 22,
                "chapter_title": "22｜跨平台容器化部署：從 Windows 本機一鍵遷移至雲端叢集",
                "narration": "當你的自動化業務規模持續擴大，這套架構也支援零痛點的容器化擴展。你在本地 Windows 電腦搭配顯卡除錯完成的整套配置，只需要一行封裝指令，就能無縫打包成標準容器映像檔，直接部署到任何支援 GPU 的雲端主機或居家伺服器上。本地開發測試、多節點平行擴展，讓你的個人自動化系統隨時具備企業級的高可用性！",
                "voice_style": "professional and visionary",
                "visual_prompt": "Containerized deployment workflow scaling from local Windows workstation to multi-node cloud cluster.",
                "duration_sec": 28,
                "use_google_flow": True
            },
            {
                "scene_id": 23,
                "chapter_title": "23｜實戰資源大禮包：一鍵部署腳本與中文配置檔免費領取",
                "narration": "為了幫大家省去自己摸索與除錯的時間，我已經把今天影片中實測用到的「全自動常駐守護腳本」、「硬體加速渲染模組」以及「完整繁體中文環境設定範本」，全部打包整理好了！你不需要自己從頭寫一行程式碼，現在就可以直接滑到影片下方的說明欄第一行，或是查看我的置頂留言，點擊連結就能免費下載整套懶人包，同時還有我們為頻道觀眾爭取到的雲端主機專屬超值優惠！",
                "voice_style": "energetic call to action",
                "visual_prompt": "Resource bundle showcase with one-click download link in description and pinned comment.",
                "duration_sec": 28,
                "use_google_flow": True
            },
            {
                "scene_id": 24,
                "chapter_title": "24｜總結與下期預告：打造屬於你的 24/7 自動化被動收入帝國",
                "narration": "總結來說，這套在 GitHub 暴增四千顆星的開源專案，不僅徹底解放了我們的雙手，更讓一人公司擁有媲美大型技術團隊的全天候執行力。如果你覺得今天的深度實測對你有幫助，請務必幫這支影片點個讚、收藏到你的AI工具箱播放清單，並訂閱頻道開啟小鈴鐺！因為我們每週都會為你實測全網最新、最暴利的開源黑科技。你最想讓 AI 自動幫你完成什麼工作？歡迎在下方留言告訴我，我們下期影片見！",
                "voice_style": "enthusiastic outro",
                "visual_prompt": "High-retention outro screen with subscribe bell, playlist recommendation, and comment prompt.",
                "duration_sec": 28,
                "use_google_flow": True
            }
        ]

        # 嚴格禁止任何取餘數循環 (`%`)！最多取 24 個完全不重複的獨立深度章節，並確保最後兩鏡永遠為資源領取與總結片尾！
        target_long_cnt = min(max(16, long_scene_count), len(base_long_scenes))
        if target_long_cnt < len(base_long_scenes):
            selected_raw = base_long_scenes[: target_long_cnt - 2] + base_long_scenes[-2:]
        else:
            selected_raw = list(base_long_scenes)

        long_scenes: List[Dict[str, Any]] = []
        for idx, item in enumerate(selected_raw, start=1):
            template = dict(item)
            template["scene_id"] = idx
            # 重新對齊章節編號前綴 (01｜, 02｜...)
            raw_title = template["chapter_title"]
            if "｜" in raw_title:
                raw_title = f"{idx:02d}｜" + raw_title.split("｜", 1)[1]
            template["chapter_title"] = raw_title
            long_scenes.append(template)

        # Shorts 對標百萬博主 48~55 秒黃金高留存結構（每句皆控制在 10~15 字以內，確保同一句話 100% 完整呈現在單一畫面、絕不跨畫面切斷！）
        base_shorts_scenes = [
            {
                "scene_id": 1,
                "chapter_title": "黃金前3秒痛點暴擊",
                "narration": f"別再每個月花兩百美金，當 AI 的全職保母了！這禮拜全網突然爆紅的，免費自動化神器 {pname}，居然能讓電腦二十四小時，自己在背景接單寫程式，連你睡覺時都在幫你賺錢！",
                "voice_style": "fast and shocking",
                "visual_prompt": "Vertical 9:16 high-impact 3D holographic AI core explosion and 24/7 autonomous engine.",
                "duration_sec": 13,
                "use_google_flow": True
            },
            {
                "scene_id": 2,
                "chapter_title": "核心黑科技反差揭秘",
                "narration": "以前你用傳統 AI 工具，問一句它才動一下，遇到小報錯就立刻卡死停擺；現在這套自癒閉環引擎，會在背景自己跑測試、自己修 Bug 重啟服務，遇到大事才發卡片請你拍板！",
                "voice_style": "energetic and rhythmic",
                "visual_prompt": "Vertical 9:16 3D neural network synapse animation and self-healing loop.",
                "duration_sec": 13,
                "use_google_flow": True
            },
            {
                "scene_id": 3,
                "chapter_title": "實測數據與成本碾壓",
                "narration": "我們實測把跨平台任務丟給它，它在背景連續迭代四十回合，全部亮起綠燈完美通過！不僅軟體完全免費開源，還能直接榨乾本地顯卡算力，速度比雲端虛擬機快十倍，每年省下八萬塊訂閱費！",
                "voice_style": "convincing and fast",
                "visual_prompt": "Vertical 9:16 3D warp tunnel and 10x GPU acceleration wave animation.",
                "duration_sec": 13,
                "use_google_flow": True
            },
            {
                "scene_id": 4,
                "chapter_title": "引流8分鐘長片與懶人包",
                "narration": "想看完整的實機壓力測試，還有免費領取我整理好的，一鍵安裝中文懶人包嗎？現在馬上點擊畫面左下角，觀看完整深度實測長片，或是打開說明欄免費領取，別忘了訂閱開啟小鈴鐺！",
                "voice_style": "urgent call to action",
                "visual_prompt": "Vertical 9:16 3D Jarvis HUD reactor and glowing pointer to related long video.",
                "duration_sec": 13,
                "use_google_flow": True
            }
        ]

        target_shorts_cnt = min(max(4, shorts_scene_count), len(base_shorts_scenes))
        shorts_scenes: List[Dict[str, Any]] = []
        for idx, item in enumerate(base_shorts_scenes[:target_shorts_cnt], start=1):
            template = dict(item)
            template["scene_id"] = idx
            shorts_scenes.append(template)

        long_title_str = (
            f"【GitHub 暴增4000星】別再當 AI 保母！{pname} 讓 Agent 24小時自動接單幹活，徹底取代 $200 月費軟體！(完整實測教學)"
            if is_github_topic
            else f"【全網瘋傳爆款實測】別再當 AI 保母！{pname} 讓 Agent 24小時自動接單幹活，徹底取代 $200 月費軟體！(保母級教學)"
        )
        shorts_title_str = (
            f"GitHub 狂攬4000星！{pname} 讓 AI 24小時自己接單幹活 🔥 #Shorts #AI神器 #GitHub"
            if is_github_topic
            else f"全網瘋傳百萬爆款！{pname} 讓 AI 24小時自己接單幹活 🔥 #Shorts #AI神器 #自動化"
        )
        desc_intro = (
            f"本集深度開箱本週 GitHub 飆升榜冠軍開源專案：{pname}！\n"
            if is_github_topic
            else f"本集深度拆解全網突破百萬觀看的爆款 AI 自動化實戰工作流：{pname}！\n"
        )
        return {
            "long_video": {"scenes": long_scenes},
            "shorts_video": {"scenes": shorts_scenes},
            "seo_metadata": {
                "long_title": long_title_str,
                "shorts_title": shorts_title_str,
                "description": (
                    desc_intro +
                    "不用再人工盯場，讓你的 AI Agent 在背景 24 小時全自動循環執行任務，一人公司產能直接放大 10 倍！"
                ),
                "tags": [
                    "AI神器", "AI自動化", "AgentAutoLoop", "ClaudeCode", "Gemini",
                    "免費AI工具", "一人公司", "被動收入", "爆款實測", "自動化賺錢",
                    "AI Agent教學", "科技評測", "高效率工具", "程式自動化", "黑科技"
                ],
                "thumbnail_prompt": "High CTR YouTube thumbnail 16:9, futuristic 3D holographic AI core working on multiple screens while a human sleeps peacefully, ultra vibrant neon cyan and yellow contrast.",
                "pinned_comment": f"🔥 想要這套【{pname}】的一鍵部署指令與中文懶人包嗎？我已經全部整理在上方說明欄第一行！搭配推薦的高 CP 值雲端主機還能享專屬折扣！"
            }
        }

    def synthesize_narration(
        self,
        text: str,
        style: str,
        output_wav_path: str,
        voice: str = "Aoede"
    ) -> str:
        """
        百萬訂閱女博主高感染力配音引擎：
        1. 優先使用台灣最自然清亮的高人氣女聲模型 `zh-TW-HsiaoChenNeural`（曉臻）與 `Aoede` (Gemini 女聲)
        2. 根據每個分鏡的情緒標籤 (`style`) 自動動態調節「語速 (Rate)」、「音調 (Pitch)」與「音量張力 (Volume)」：
           - 開場痛點暴擊 / Shorts 快節奏：`rate="+18%"`, `pitch="+4Hz"`（節奏明快、抓耳不拖泥帶水）
           - 實測數據 / 商業變現揭秘：`rate="+15%"`, `pitch="+3Hz"`（自信飽滿、極具說服力）
           - 架構拆解 / 手把手教學：`rate="+13%"`, `pitch="+2Hz"`（字字清晰、親切專業）
        3. 透過 FFmpeg 錄音室人聲母帶濾鏡（低頻切除防悶音 + 高頻空氣感增益 + 廣播級動態壓縮），呈現百萬 YouTuber 頂級電容麥克風音質！
        """
        from concurrent.futures import ThreadPoolExecutor

        def _call_cloud_with_hard_timeout(fn, timeout_sec: float = 10.0):
            ex = ThreadPoolExecutor(max_workers=1)
            fut = ex.submit(fn)
            try:
                return fut.result(timeout=timeout_sec)
            finally:
                ex.shutdown(wait=False, cancel_futures=True)

        os.makedirs(os.path.dirname(output_wav_path), exist_ok=True)
        if self.client:
            try:
                print(f"[GeminiDirector/TTS] 正在透過 Gemini 3.8 女聲 TTS ({voice}, {style}) 生成語音: {text[:25]}...")
                interaction = _call_cloud_with_hard_timeout(
                    lambda: self.client.interactions.create(
                        model="gemini-3.8-flash-tts",
                        input=[{
                            "type": "user_input",
                            "content": [{
                                "type": "text",
                                "text": text,
                                "annotations": [{
                                    "type": "speech_metadata",
                                    "style": style or "bright, energetic female tech creator"
                                }]
                            }]
                        }],
                        response_format={"type": "audio"},
                        generation_config={
                            "speech_config": [{"voice": voice}]
                        }
                    ),
                    timeout_sec=10.0
                )
                audio_bytes = base64.b64decode(interaction.output_audio.data)
                with open(output_wav_path, "wb") as f:
                    f.write(audio_bytes)
                return output_wav_path
            except Exception as e:
                print(f"[GeminiDirector/TTS] 雲端 TTS 快速切換至台灣百萬女博主神經網路語音 ({e})")

        # 依據分鏡情緒風格動態調校女聲語速、音調與感染力
        style_lower = (style or "").lower()
        if any(k in style_lower for k in ("fast", "shocking", "dramatic", "urgent")):
            rate_str, pitch_str, vol_str = "+18%", "+4Hz", "+10%"
        elif any(k in style_lower for k in ("energetic", "enthusiastic", "convincing", "persuasive", "excited")):
            rate_str, pitch_str, vol_str = "+15%", "+3Hz", "+8%"
        else:
            rate_str, pitch_str, vol_str = "+13%", "+2Hz", "+6%"

        female_voice = "zh-TW-HsiaoChenNeural"
        print(
            f"[GeminiDirector/EdgeTTS] 正在合成台灣百萬女博主語音 ({female_voice} | 語速:{rate_str} | 音調:{pitch_str}): "
            f"{text[:25]}..."
        )
        temp_mp3 = output_wav_path + ".mp3"
        import edge_tts
        import time

        async def _run_edge_tts():
            communicate = edge_tts.Communicate(
                text,
                voice=female_voice,
                rate=rate_str,
                pitch=pitch_str,
                volume=vol_str
            )
            await communicate.save(temp_mp3)

        tts_ok = False
        for attempt in range(3):
            try:
                asyncio.run(_run_edge_tts())
                if os.path.exists(temp_mp3) and os.path.getsize(temp_mp3) > 500:
                    tts_ok = True
                    break
            except Exception as e:
                print(f"[GeminiDirector/EdgeTTS] 女聲語音合成重試 ({attempt + 1}/3): {e}")
                time.sleep(1.5)

        if tts_ok:
            # 錄音室電容麥克風母帶處理：高通濾波消除低頻渾濁 + 3.5kHz 清晰度激勵 + 動態壓縮讓每個字飽滿有穿透力
            vocal_master_filter = (
                "highpass=f=85,"
                "equalizer=f=3500:t=q:w=1.2:g=2.8,"
                "acompressor=threshold=-18dB:ratio=2.6:attack=5:release=60:makeup=2,"
                "alimiter=limit=0.95"
            )
            res = subprocess.run(
                [
                    "ffmpeg", "-y", "-i", temp_mp3,
                    "-af", vocal_master_filter,
                    "-ar", "44100", "-ac", "2", output_wav_path
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            if res.returncode != 0:
                subprocess.run(
                    ["ffmpeg", "-y", "-i", temp_mp3, "-ar", "44100", "-ac", "2", output_wav_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True
                )
            if os.path.exists(temp_mp3):
                os.remove(temp_mp3)
        else:
            # Windows SAPI 離線台灣女聲保底合成
            safe_txt = text.replace("'", "").replace('"', "")
            ps_cmd = (
                f"Add-Type -AssemblyName System.Speech; "
                f"$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                f"$s.SelectVoiceByHints([System.Speech.Synthesis.VoiceGender]::Female); "
                f"$s.Rate = 2; "
                f"$s.SetOutputToWaveFile('{output_wav_path}'); "
                f"$s.Speak('{safe_txt}'); "
                f"$s.Dispose();"
            )
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], check=True)
        return output_wav_path

    def generate_thumbnail(self, prompt: str, output_image_path: str) -> str:
        """
        優先使用 Gemini Nano Banana 2.1 (`gemini-nano-banana-2.1`) 生成 16:9 高點閱 YouTube 縮圖。
        若未配置 API Key，自動使用 Pillow 渲染高對比霓虹科技感爆款縮圖 (1920x1080)。
        """
        from concurrent.futures import ThreadPoolExecutor

        def _call_cloud_with_hard_timeout(fn, timeout_sec: float = 10.0):
            ex = ThreadPoolExecutor(max_workers=1)
            fut = ex.submit(fn)
            try:
                return fut.result(timeout=timeout_sec)
            finally:
                ex.shutdown(wait=False, cancel_futures=True)

        os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
        if self.client:
            try:
                print(f"[GeminiDirector] 正在使用 Nano Banana 2.1 生成高點擊 YouTube 縮圖...")
                interaction = _call_cloud_with_hard_timeout(
                    lambda: self.client.interactions.create(
                        model="gemini-nano-banana-2.1",
                        input=prompt,
                        response_format={
                            "type": "image",
                            "aspect_ratio": "16:9",
                            "image_size": "2K",
                            "mime_type": "image/jpeg"
                        }
                    ),
                    timeout_sec=10.0
                )
                img_bytes = base64.b64decode(interaction.output_image.data)
                with open(output_image_path, "wb") as f:
                    f.write(img_bytes)
                print(f"[GeminiDirector] 縮圖已生成: {output_image_path}")
                return output_image_path
            except Exception as e:
                print(f"[GeminiDirector] Nano Banana 雲端 10s 快速切換至本地高對比縮圖引擎 ({e})")

        print(f"[GeminiDirector] 正在使用 Chromium GPU 渲染 1920x1080 百萬博主級 (High-CTR) 視覺衝擊封面縮圖...")
        try:
            from playwright.sync_api import sync_playwright

            thumb_html = os.path.join(self.output_dir, "_thumb_render.html")
            html_content = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    width: 1920px; height: 1080px; overflow: hidden;
    font-family: 'Microsoft JhengHei', 'PingFang TC', sans-serif;
    background: #060913;
    position: relative;
  }
  .split-bg {
    position: absolute; inset: 0;
    background: linear-gradient(112deg, #1e050d 0%, #0f172a 46%, #022c22 100%);
  }
  .glow-left {
    position: absolute; width: 900px; height: 900px; left: -150px; top: 90px;
    background: radial-gradient(circle, rgba(239,68,68,0.45) 0%, transparent 70%);
  }
  .glow-right {
    position: absolute; width: 1100px; height: 1100px; right: -150px; top: -50px;
    background: radial-gradient(circle, rgba(16,185,129,0.5) 0%, transparent 70%);
  }
  .grid-overlay {
    position: absolute; inset: 0;
    background-image: linear-gradient(rgba(255,255,255,0.05) 2px, transparent 2px),
                      linear-gradient(90deg, rgba(255,255,255,0.05) 2px, transparent 2px);
    background-size: 80px 80px;
  }
  .vs-slash {
    position: absolute; left: 48%; top: -10%; width: 18px; height: 120%;
    background: linear-gradient(180deg, #facc15, #f97316, #ef4444);
    transform: rotate(14deg);
    box-shadow: 0 0 45px #facc15;
    z-index: 5;
  }
  .top-tag {
    position: absolute; top: 62px; left: 78px; z-index: 10;
    background: linear-gradient(90deg, #dc2626, #ea580c);
    color: #fff; font-size: 64px; font-weight: 900;
    padding: 16px 48px; border-radius: 24px;
    border: 5px solid #fef08a;
    box-shadow: 0 20px 50px rgba(220,38,38,0.7);
    letter-spacing: 2px;
  }
  .hero-title-1 {
    position: absolute; top: 235px; left: 78px; z-index: 10;
    font-size: 168px; font-weight: 900; color: #facc15;
    text-shadow: 0 12px 0 #000, 0 22px 50px rgba(0,0,0,0.95), 0 0 40px rgba(250,204,21,0.5);
    -webkit-text-stroke: 6px #000;
    letter-spacing: 3px;
  }
  .hero-title-2 {
    position: absolute; top: 445px; left: 78px; z-index: 10;
    font-size: 156px; font-weight: 900; color: #ffffff;
    text-shadow: 0 12px 0 #000, 0 22px 50px rgba(0,0,0,0.95), 0 0 40px rgba(34,211,238,0.7);
    -webkit-text-stroke: 6px #000;
    letter-spacing: 2px;
  }
  .compare-panel {
    position: absolute; bottom: 72px; left: 78px; right: 78px; height: 295px; z-index: 10;
    display: grid; grid-template-columns: 1fr 1.15fr; gap: 42px;
  }
  .card-bad {
    background: rgba(69, 10, 10, 0.88);
    border: 5px solid #ef4444; border-radius: 32px;
    padding: 32px 44px; display: flex; flex-direction: column; justify-content: center;
    box-shadow: 0 25px 60px rgba(0,0,0,0.8);
  }
  .card-good {
    background: rgba(6, 78, 59, 0.92);
    border: 6px solid #34d399; border-radius: 32px;
    padding: 32px 44px; display: flex; flex-direction: column; justify-content: center;
    box-shadow: 0 25px 60px rgba(0,0,0,0.8), 0 0 50px rgba(52,211,153,0.45);
  }
  .c-label { font-size: 46px; font-weight: 800; color: #fca5a5; margin-bottom: 12px; }
  .c-label-good { font-size: 46px; font-weight: 800; color: #6ee7b7; margin-bottom: 12px; }
  .c-val { font-size: 82px; font-weight: 900; color: #fff; }
  .c-val-good { font-size: 88px; font-weight: 900; color: #fef08a; text-shadow: 0 0 25px rgba(254,240,138,0.7); }
</style>
</head>
<body>
  <div class="split-bg"></div>
  <div class="glow-left"></div>
  <div class="glow-right"></div>
  <div class="grid-overlay"></div>
  <div class="vs-slash"></div>

  <div class="top-tag">🔥 2026 實測封神｜徹底顛覆認知</div>
  <div class="hero-title-1">別再繳智商稅！</div>
  <div class="hero-title-2">24H 全自動印鈔神器</div>

  <div class="compare-panel">
    <div class="card-bad">
      <div class="c-label">❌ 傳統付費軟體 / 人工盯場</div>
      <div class="c-val">$200/月 + 狂報錯卡死</div>
    </div>
    <div class="card-good">
      <div class="c-label-good">✅ 開源黑科技 AutoLoop</div>
      <div class="c-val-good">$0 免費 + 10倍速全自動</div>
    </div>
  </div>
</body>
</html>"""
            with open(thumb_html, "w", encoding="utf-8") as f:
                f.write(html_content)

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(viewport={"width": 1920, "height": 1080})
                page.goto(f"file:///{thumb_html.replace(os.sep, '/')}")
                page.wait_for_timeout(300)
                page.screenshot(path=output_image_path, type="jpeg", quality=95)
                browser.close()
            if os.path.exists(thumb_html):
                os.remove(thumb_html)
            print(f"[GeminiDirector] 百萬博主級高點閱縮圖已儲存: {output_image_path}")
            return output_image_path
        except Exception as e:
            print(f"[GeminiDirector] Chromium 縮圖備援 ({e})")
        width, height = 1920, 1080
        img = Image.new("RGB", (width, height), (10, 14, 28))
        draw = ImageDraw.Draw(img)

        # 繪製科技感漸層背景與光暈網格
        for y in range(0, height, 4):
            r = int(10 + (y / height) * 25)
            g = int(15 + (y / height) * 45)
            b = int(35 + (y / height) * 85)
            draw.line([(0, y), (width, y)], fill=(r, g, b), width=4)

        for x in range(0, width, 120):
            draw.line([(x, 0), (x, height)], fill=(25, 55, 95), width=1)
        for y in range(0, height, 120):
            draw.line([(0, y), (width, y)], fill=(25, 55, 95), width=1)

        # 頂部爆款紅底標籤框
        draw.rounded_rectangle([(80, 70), (920, 210)], radius=24, fill=(220, 25, 45), outline=(255, 215, 0), width=6)

        font_path = "C:/Windows/Fonts/msjhbd.ttc"
        if not os.path.exists(font_path):
            font_path = "C:/Windows/Fonts/msjh.ttc"

        try:
            font_badge = ImageFont.truetype(font_path, 76)
            font_main = ImageFont.truetype(font_path, 132)
            font_sub = ImageFont.truetype(font_path, 88)
        except Exception:
            font_badge = ImageFont.load_default()
            font_main = ImageFont.load_default()
            font_sub = ImageFont.load_default()

        draw.text((125, 90), "GitHub 狂攬 4000+ 星！", fill=(255, 255, 255), font=font_badge)

        # 主視覺超大黃金對比字
        draw.text((88, 288), "別再當 AI 保母！", fill=(0, 0, 0), font=font_main)
        draw.text((80, 280), "別再當 AI 保母！", fill=(255, 230, 0), font=font_main)

        draw.text((88, 468), "24H 自動接單神器", fill=(0, 0, 0), font=font_main)
        draw.text((80, 460), "24H 自動接單神器", fill=(0, 255, 220), font=font_main)

        # 底部對比橫幅
        draw.rounded_rectangle([(80, 720), (1840, 930)], radius=28, fill=(18, 28, 52), outline=(0, 255, 200), width=5)
        draw.text((130, 775), "100% 免費開源  vs  徹底取代 $200/月 付費軟體", fill=(255, 255, 255), font=font_sub)

        img.save(output_image_path, "JPEG", quality=95)
        print(f"[GeminiDirector] 高點閱縮圖已儲存: {output_image_path}")
        return output_image_path
