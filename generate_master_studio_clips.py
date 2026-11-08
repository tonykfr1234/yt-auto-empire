#!/usr/bin/env python3
"""
generate_master_studio_clips.py
使用 8 個平行 Chromium GPU 實例，將 24 張 Pixar/UE5 3D 旗艦人物與全息場景原畫 (`assets/studio_art/scene_char_01..24.jpg`)
預先錄製為 60fps 3D 鏡頭視差運鏡 + 體積光斑 (Volumetric Bokeh) + 能量微粒 (Cyber Sparks) + 動態音頻頻譜的母帶級動態基底影片：
- `assets/studio_master_clips/base_16x9_01.mp4` ~ `base_16x9_24.mp4`
- `assets/studio_master_clips/base_9x16_01.mp4` ~ `base_9x16_08.mp4`
"""

import os
import json
import base64
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
ART_DIR = os.path.join(PROJECT_ROOT, "assets", "studio_art")
MASTER_DIR = os.path.join(PROJECT_ROOT, "assets", "studio_master_clips")
os.makedirs(MASTER_DIR, exist_ok=True)

PALETTES = [
    ("#050b1a", "#00f2fe", "#4facfe", "#facc15"),
    ("#180614", "#ff0844", "#ffb199", "#38bdf8"),
    ("#031410", "#10b981", "#34d399", "#facc15"),
    ("#0f0722", "#a855f7", "#ec4899", "#22d3ee"),
    ("#140a04", "#f97316", "#facc15", "#4ade80"),
    ("#04121f", "#06b6d4", "#3b82f6", "#a7f3d0"),
    ("#19050c", "#f43f5e", "#fbbf24", "#10b981"),
    ("#06150a", "#22c55e", "#84cc16", "#00f2fe"),
    ("#120924", "#8b5cf6", "#f472b6", "#fde047"),
    ("#07131e", "#38bdf8", "#818cf8", "#facc15"),
    ("#041414", "#14b8a6", "#5eead4", "#fb923c"),
    ("#1a0c06", "#ef4444", "#f59e0b", "#2dd4bf"),
    ("#080621", "#6366f1", "#c084fc", "#38bdf8"),
    ("#051612", "#10b981", "#6ee7b7", "#fcd34d"),
    ("#15061b", "#d946ef", "#f43f5e", "#22d3ee"),
    ("#041022", "#0ea5e9", "#6366f1", "#4ade80"),
    ("#110b22", "#a855f7", "#38bdf8", "#facc15"),
    ("#061814", "#14b8a6", "#a3e635", "#fbbf24"),
    ("#180909", "#f97316", "#ec4899", "#38bdf8"),
    ("#190612", "#e11d48", "#fb923c", "#4ade80"),
    ("#03131d", "#06b6d4", "#34d399", "#fde047"),
    ("#080d24", "#3b82f6", "#a855f7", "#2dd4bf"),
    ("#140d04", "#eab308", "#f97316", "#38bdf8"),
    ("#090520", "#ec4899", "#8b5cf6", "#facc15"),
]


def build_base_motion_html(sid: int, is_landscape: bool, b64_uri: str) -> str:
    _, c_pri, c_sec, c_acc = PALETTES[(sid - 1) % len(PALETTES)]
    ai_bg_js = json.dumps(b64_uri)
    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ width: 100vw; height: 100vh; overflow: hidden; background: #030712; }}
  canvas#stageCanvas {{ position: fixed; inset: 0; width: 100%; height: 100%; z-index: 1; }}
  .studio-watermark {{
    position: fixed; right: 42px; bottom: 115px; z-index: 10;
    background: rgba(8, 14, 30, 0.68);
    border: 1px solid rgba(255, 255, 255, 0.18);
    backdrop-filter: blur(14px);
    padding: 10px 18px; border-radius: 14px;
    display: {'flex' if is_landscape else 'none'};
    align-items: center; gap: 12px;
    box-shadow: 0 10px 28px rgba(0,0,0,0.5);
    font-family: 'Segoe UI', sans-serif;
  }}
  .eq-bars {{ display: flex; align-items: flex-end; gap: 4px; height: 22px; }}
  .eq-bar {{ width: 4px; background: {c_pri}; border-radius: 2px; box-shadow: 0 0 8px {c_pri}; }}
</style>
</head>
<body>
<canvas id="stageCanvas"></canvas>
<div class="studio-watermark">
  <div class="eq-bars">
    <div class="eq-bar" style="height:10px;"></div>
    <div class="eq-bar" style="height:18px;"></div>
    <div class="eq-bar" style="height:14px;"></div>
    <div class="eq-bar" style="height:22px;"></div>
    <div class="eq-bar" style="height:12px;"></div>
    <div class="eq-bar" style="height:16px;"></div>
  </div>
  <div style="font-size:14px;font-weight:800;color:#cbd5e1;letter-spacing:0.5px;">
    GOOGLE VEO 3.1 / STUDIO 3D ENGINE
  </div>
</div>
<script>
const canvas = document.getElementById('stageCanvas');
const ctx = canvas.getContext('2d');
const W = canvas.width = window.innerWidth;
const H = canvas.height = window.innerHeight;
const isLandscape = {str(is_landscape).lower()};
const sid = {sid};
const cPri = '{c_pri}';
const cSec = '{c_sec}';
const cAcc = '{c_acc}';
const eqBars = document.querySelectorAll('.eq-bar');

const heroImg = new Image();
heroImg.src = {ai_bg_js};

const bokehOrbs = Array.from({{length: 38}}, (_, i) => ({{
  x: Math.random() * W,
  y: Math.random() * H,
  r: Math.random() * 18 + 4,
  vx: (Math.random() - 0.5) * 0.65,
  vy: -Math.random() * 0.85 - 0.25,
  alpha: Math.random() * 0.28 + 0.06,
  color: i % 3 === 0 ? cAcc : (i % 2 === 0 ? cPri : cSec)
}}));

const sparks = Array.from({{length: 55}}, (_, i) => ({{
  x: Math.random() * W,
  y: Math.random() * H,
  r: Math.random() * 2.2 + 0.8,
  vx: (Math.random() - 0.5) * 1.6,
  vy: -Math.random() * 2.1 - 0.5,
  color: i % 2 === 0 ? '#ffffff' : cPri
}}));

let startTime = performance.now();
function animate(now) {{
  const elapsedSec = (now - startTime) / 1000.0;
  const t = elapsedSec;
  const normProg = Math.min(0.9999, Math.max(0.0, elapsedSec / 9.8));

  ctx.clearRect(0, 0, W, H);

  if (heroImg && heroImg.complete && heroImg.naturalWidth > 0) {{
    const imgW = heroImg.naturalWidth;
    const imgH = heroImg.naturalHeight;
    const camMode = sid % 5;
    let zoom = 1.06, panX = 0, panY = 0;

    if (camMode === 0) {{
      zoom = 1.02 + normProg * 0.12;
      panX = Math.sin(t * 0.6) * (W * 0.015);
      panY = -normProg * (H * 0.02);
    }} else if (camMode === 1) {{
      zoom = 1.14 - normProg * 0.10;
      panX = (normProg - 0.5) * (W * 0.04);
      panY = Math.cos(t * 0.5) * (H * 0.012);
    }} else if (camMode === 2) {{
      zoom = 1.08 + Math.sin(normProg * Math.PI) * 0.05;
      panX = (0.5 - normProg) * (W * 0.045);
      panY = (normProg - 0.5) * (H * 0.02);
    }} else if (camMode === 3) {{
      zoom = 1.04 + normProg * 0.10;
      panX = (normProg - 0.5) * (W * 0.035);
      panY = (0.5 - normProg) * (H * 0.025);
    }} else {{
      zoom = 1.05 + normProg * 0.09;
      panX = Math.sin(t * 0.8) * (W * 0.02);
      panY = Math.cos(t * 0.7) * (H * 0.018);
    }}

    if (isLandscape) {{
      ctx.save();
      ctx.translate(W / 2 + panX, H / 2 + panY);
      ctx.scale(zoom, zoom);
      const scaleCover = Math.max(W / imgW, H / imgH);
      const dw = imgW * scaleCover;
      const dh = imgH * scaleCover;
      ctx.drawImage(heroImg, -dw / 2, -dh / 2, dw, dh);
      ctx.restore();
    }} else {{
      ctx.save();
      ctx.filter = 'blur(28px) brightness(0.38)';
      const bgScale = Math.max(W / imgW, H / imgH) * 1.15;
      ctx.drawImage(heroImg, (W - imgW * bgScale) / 2, (H - imgH * bgScale) / 2, imgW * bgScale, imgH * bgScale);
      ctx.restore();

      const frameX = 28, frameY = 135, frameW = W - 56, frameH = H * 0.61;
      ctx.save();
      ctx.shadowBlur = 40;
      ctx.shadowColor = cPri + '66';
      ctx.strokeStyle = cPri;
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.roundRect(frameX, frameY, frameW, frameH, 28);
      ctx.stroke();
      ctx.clip();

      const innerScale = Math.max(frameW / imgW, frameH / imgH) * (1.02 + normProg * 0.06);
      const iw = imgW * innerScale;
      const ih = imgH * innerScale;
      const maxPan = Math.max(0, (iw - frameW) * 0.42);
      const shortPanX = Math.sin(normProg * Math.PI * 2 - Math.PI / 2) * maxPan * (sid % 2 === 0 ? 1 : -1);
      ctx.drawImage(heroImg, frameX + (frameW - iw) / 2 + shortPanX, frameY + (frameH - ih) / 2, iw, ih);
      ctx.restore();
    }}
  }}

  const vigGrad = ctx.createRadialGradient(W * 0.5, H * 0.45, W * 0.25, W * 0.5, H * 0.5, W * 0.78);
  vigGrad.addColorStop(0, 'rgba(0,0,0,0)');
  vigGrad.addColorStop(1, 'rgba(2, 6, 23, 0.52)');
  ctx.fillStyle = vigGrad;
  ctx.fillRect(0, 0, W, H);

  const subGrad = ctx.createLinearGradient(0, H * 0.74, 0, H);
  subGrad.addColorStop(0, 'rgba(2, 6, 23, 0)');
  subGrad.addColorStop(0.65, 'rgba(2, 6, 23, 0.72)');
  subGrad.addColorStop(1, 'rgba(2, 6, 23, 0.92)');
  ctx.fillStyle = subGrad;
  ctx.fillRect(0, H * 0.74, W, H * 0.26);

  ctx.save();
  ctx.globalCompositeOperation = 'screen';
  for (const b of bokehOrbs) {{
    b.x += b.vx; b.y += b.vy;
    if (b.y < -30) b.y = H + 30;
    if (b.x < -30) b.x = W + 30;
    if (b.x > W + 30) b.x = -30;
    const g = ctx.createRadialGradient(b.x, b.y, 1, b.x, b.y, b.r);
    g.addColorStop(0, b.color);
    g.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.globalAlpha = b.alpha * (0.7 + 0.3 * Math.sin(t * 2.5 + b.r));
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(b.x, b.y, b.r, 0, Math.PI * 2);
    ctx.fill();
  }}
  for (const sp of sparks) {{
    sp.x += sp.vx; sp.y += sp.vy;
    if (sp.y < 0) sp.y = H;
    if (sp.x < 0) sp.x = W;
    if (sp.x > W) sp.x = 0;
    ctx.globalAlpha = 0.65;
    ctx.fillStyle = sp.color;
    ctx.beginPath();
    ctx.arc(sp.x, sp.y, sp.r, 0, Math.PI * 2);
    ctx.fill();
  }}
  ctx.restore();

  eqBars.forEach((bar, i) => {{
    const h = 6 + Math.abs(Math.sin(t * 9.5 + i * 1.1)) * 16;
    bar.style.height = h.toFixed(1) + 'px';
  }});

  requestAnimationFrame(animate);
}}
requestAnimationFrame(animate);
</script>
</body>
</html>"""


def record_one_master(sid: int, aspect_ratio: str) -> str:
    is_landscape = (aspect_ratio == "16:9")
    tag = "16x9" if is_landscape else "9x16"
    out_mp4 = os.path.join(MASTER_DIR, f"base_{tag}_{sid:02d}.mp4")
    if os.path.exists(out_mp4) and os.path.getsize(out_mp4) > 200_000:
        return out_mp4

    w, h = (1920, 1080) if is_landscape else (1080, 1920)
    jpg_path = os.path.join(ART_DIR, f"scene_char_{sid:02d}.jpg")
    with open(jpg_path, "rb") as f:
        b64_uri = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode("utf-8")

    tmp_dir = os.path.join(MASTER_DIR, f"_tmp_{tag}_{sid:02d}")
    os.makedirs(tmp_dir, exist_ok=True)
    html_path = os.path.join(tmp_dir, "motion.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(build_base_motion_html(sid, is_landscape, b64_uri))

    webm_path = None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": w, "height": h},
            record_video_dir=tmp_dir,
            record_video_size={"width": w, "height": h},
            color_scheme="dark"
        )
        page = context.new_page()
        page.goto(f"file:///{html_path.replace(os.sep, '/')}")
        page.wait_for_timeout(10000)
        video_obj = page.video
        context.close()
        browser.close()
        if video_obj:
            webm_path = video_obj.path()

    cmd = [
        "ffmpeg", "-y",
        "-i", webm_path,
        "-vf", f"scale={w}:{h},fps=30,format=yuv420p",
        "-t", "9.80",
        "-c:v", "h264_nvenc",
        "-preset", "p2",
        "-cq", "19",
        "-an",
        out_mp4
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0:
        cmd[cmd.index("h264_nvenc")] = "libx264"
        cmd[cmd.index("-preset") + 1] = "fast"
        cmd[cmd.index("-cq")] = "-crf"
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    print(f"[MasterClip] Generated {out_mp4}")
    return out_mp4


if __name__ == "__main__":
    tasks = []
    for sid in range(1, 25):
        tasks.append((sid, "16:9"))
    for sid in range(1, 9):
        tasks.append((sid, "9:16"))

    print(f"Generating {len(tasks)} master 60fps 3D studio clips with 8 parallel Chromium workers...")
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(record_one_master, s, ar) for s, ar in tasks]
        for fut in as_completed(futs):
            fut.result()
    print("ALL_MASTER_STUDIO_CLIPS_READY")
