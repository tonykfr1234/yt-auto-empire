#!/usr/bin/env python3
r"""
gdrive_sync.py — Google Drive 統一影片雲端歸檔引擎 (GoogleDriveVideoVault)
自動將所有完片並通過審閱的 16:9 長片、9:16 Shorts、縮圖、字幕與說明欄資訊，
同步歸檔至本機掛載之 Google Drive 統一資料夾：`G:\我的雲端硬碟\YT-Auto-Empire-Videos`
"""

import os
import re
import sys
import json
import shutil
from datetime import datetime
from typing import Dict, Any, Optional, List

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


class GoogleDriveVideoVault:
    """統一管理 Google Drive 影片存放資料夾與自動同步歸檔。"""

    def __init__(self, custom_vault_dir: Optional[str] = None):
        self.vault_dir = custom_vault_dir or self._detect_google_drive_vault()
        self.long_dir = os.path.join(self.vault_dir, "01_16x9_橫式深度長片")
        self.shorts_dir = os.path.join(self.vault_dir, "02_9x16_直式爆款Shorts")
        self.campaigns_dir = os.path.join(self.vault_dir, "03_完整專案包_含縮圖與字幕")
        os.makedirs(self.long_dir, exist_ok=True)
        os.makedirs(self.shorts_dir, exist_ok=True)
        os.makedirs(self.campaigns_dir, exist_ok=True)

    @staticmethod
    def _detect_google_drive_vault() -> str:
        candidates = [
            r"G:\我的雲端硬碟\YT-Auto-Empire-Videos",
            r"G:\My Drive\YT-Auto-Empire-Videos",
            os.path.expanduser(r"~\Google Drive\YT-Auto-Empire-Videos"),
        ]
        for c in candidates:
            parent = os.path.dirname(c)
            if os.path.exists(parent):
                os.makedirs(c, exist_ok=True)
                return c
        fallback = os.path.abspath("gdrive_vault_fallback")
        os.makedirs(fallback, exist_ok=True)
        return fallback

    @staticmethod
    def _sanitize_filename(name: str, max_len: int = 45) -> str:
        cleaned = re.sub(r'[\\/:*?"<>|\r\n]+', "_", str(name)).strip(" ._")
        return cleaned[:max_len] if cleaned else "AI_Viral_Video"

    def sync_campaign(self, run_dir: str, summary: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """
        將單一完片專案資料夾同步至 Google Drive 統一資料夾：
        1. `01_16x9_橫式深度長片/[長片]_<主題>_<時間戳>.mp4`
        2. `02_9x16_直式爆款Shorts/[Shorts]_<主題>_<時間戳>.mp4`
        3. `03_完整專案包_含縮圖與字幕/<時間戳>_<主題>/`
        """
        run_dir = os.path.abspath(run_dir)
        folder_name = os.path.basename(run_dir)
        ts_tag = folder_name.replace("campaign_", "")

        product_name = "AI_Viral_Topic"
        if summary and summary.get("product"):
            product_name = summary["product"]
        else:
            prod_json = os.path.join(run_dir, "01_selected_product.json")
            if os.path.exists(prod_json):
                try:
                    with open(prod_json, "r", encoding="utf-8") as f:
                        product_name = json.load(f).get("product_name", product_name)
                except Exception:
                    pass

        safe_prod = self._sanitize_filename(product_name)
        pkg_dir = os.path.join(self.campaigns_dir, f"{ts_tag}_{safe_prod}")
        os.makedirs(pkg_dir, exist_ok=True)

        src_long = os.path.join(run_dir, "final_long_16x9.mp4")
        src_shorts = os.path.join(run_dir, "final_shorts_9x16.mp4")
        src_thumb = os.path.join(run_dir, "thumbnail_16x9.jpg")
        src_long_srt = os.path.join(run_dir, "final_long_16x9.srt")
        src_shorts_srt = os.path.join(run_dir, "final_shorts_9x16.srt")
        src_blueprint = os.path.join(run_dir, "production_blueprint.json")

        synced_paths: Dict[str, str] = {"vault_root": self.vault_dir, "package_dir": pkg_dir}

        if os.path.exists(src_long) and os.path.getsize(src_long) > 100_000:
            dst_long_flat = os.path.join(self.long_dir, f"[16x9長片]_{ts_tag}_{safe_prod}.mp4")
            dst_long_pkg = os.path.join(pkg_dir, "final_long_16x9.mp4")
            if not os.path.exists(dst_long_flat) or os.path.getsize(dst_long_flat) != os.path.getsize(src_long):
                shutil.copy2(src_long, dst_long_flat)
            if not os.path.exists(dst_long_pkg) or os.path.getsize(dst_long_pkg) != os.path.getsize(src_long):
                shutil.copy2(src_long, dst_long_pkg)
            synced_paths["gdrive_long_mp4"] = dst_long_flat

        if os.path.exists(src_shorts) and os.path.getsize(src_shorts) > 50_000:
            dst_shorts_flat = os.path.join(self.shorts_dir, f"[9x16短片]_{ts_tag}_{safe_prod}.mp4")
            dst_shorts_pkg = os.path.join(pkg_dir, "final_shorts_9x16.mp4")
            if not os.path.exists(dst_shorts_flat) or os.path.getsize(dst_shorts_flat) != os.path.getsize(src_shorts):
                shutil.copy2(src_shorts, dst_shorts_flat)
            if not os.path.exists(dst_shorts_pkg) or os.path.getsize(dst_shorts_pkg) != os.path.getsize(src_shorts):
                shutil.copy2(src_shorts, dst_shorts_pkg)
            synced_paths["gdrive_shorts_mp4"] = dst_shorts_flat

        for extra_src in [src_thumb, src_long_srt, src_shorts_srt, src_blueprint]:
            if os.path.exists(extra_src):
                dst_extra = os.path.join(pkg_dir, os.path.basename(extra_src))
                if not os.path.exists(dst_extra):
                    shutil.copy2(extra_src, dst_extra)

        if summary:
            meta_path = os.path.join(pkg_dir, "video_summary.json")
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)

        self._refresh_master_index()
        print(f"[GoogleDriveVault] 影片已同步歸檔至 Google Drive: {self.vault_dir}")
        return synced_paths

    def sync_all_existing_runs(self, runs_root: str) -> List[Dict[str, str]]:
        """批次掃描 `runs/` 下所有已完片專案，統一同步至 Google Drive 資料夾。"""
        results = []
        if not os.path.exists(runs_root):
            return results
        for name in sorted(os.listdir(runs_root)):
            rdir = os.path.join(runs_root, name)
            if not os.path.isdir(rdir) or not name.startswith("campaign_"):
                continue
            long_mp4 = os.path.join(rdir, "final_long_16x9.mp4")
            shorts_mp4 = os.path.join(rdir, "final_shorts_9x16.mp4")
            if os.path.exists(long_mp4) and os.path.getsize(long_mp4) > 1_000_000 and os.path.exists(shorts_mp4):
                results.append(self.sync_campaign(rdir))
        self._refresh_master_index()
        return results

    def _refresh_master_index(self) -> None:
        """在 Google Drive 資料夾根目錄自動生成 `00_影片總表清單.md` 方便隨時查閱。"""
        index_md = os.path.join(self.vault_dir, "00_影片總表清單.md")
        long_files = sorted(os.listdir(self.long_dir)) if os.path.exists(self.long_dir) else []
        shorts_files = sorted(os.listdir(self.shorts_dir)) if os.path.exists(self.shorts_dir) else []

        lines = [
            "# 🎬 YT-Auto-Empire Google Drive 統一影片庫",
            f"> 最後更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"> Google Drive 根目錄：`{self.vault_dir}`",
            "",
            f"## 📺 1. 16:9 橫式深度長片 (`01_16x9_橫式深度長片`，共 {len(long_files)} 支)",
        ]
        for idx, fn in enumerate(long_files, start=1):
            fpath = os.path.join(self.long_dir, fn)
            sz_mb = round(os.path.getsize(fpath) / (1024 * 1024), 1) if os.path.exists(fpath) else 0
            lines.append(f"{idx}. `{fn}` ({sz_mb} MB) — `{fpath}`")

        lines.append("")
        lines.append(f"## 📱 2. 9:16 直式爆款 Shorts (`02_9x16_直式爆款Shorts`，共 {len(shorts_files)} 支)")
        for idx, fn in enumerate(shorts_files, start=1):
            fpath = os.path.join(self.shorts_dir, fn)
            sz_mb = round(os.path.getsize(fpath) / (1024 * 1024), 1) if os.path.exists(fpath) else 0
            lines.append(f"{idx}. `{fn}` ({sz_mb} MB) — `{fpath}`")

        with open(index_md, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    vault = GoogleDriveVideoVault()
    synced = vault.sync_all_existing_runs(os.path.abspath("runs"))
    print(f"已完成 {len(synced)} 組專案同步至 Google Drive: {vault.vault_dir}")
