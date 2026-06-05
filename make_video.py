"""
春日の森を感じながらのお食事 — プロモーション動画生成スクリプト
"""
import os
import unicodedata
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, concatenate_videoclips, CompositeVideoClip

IMAGE_DIR = "/home/user/kakanonoyaya/images"

# ファイル名正規化マップ (NFD対応)
_file_map = {unicodedata.normalize("NFC", f): f
             for f in os.listdir(IMAGE_DIR)}

def resolve(name: str) -> str:
    nfc = unicodedata.normalize("NFC", name)
    return os.path.join(IMAGE_DIR, _file_map.get(nfc, name))
OUTPUT    = "/home/user/kakanonoyaya/kasuga_dining.mp4"
W, H      = 1920, 1080   # 出力解像度 (16:9)
FPS       = 30
DURATION  = 5.0          # 1枚あたり表示秒数
FADE      = 0.8          # クロスフェード秒数

# 表示順とテロップ
SLIDES = [
    {
        "file": "イメージ_モーニング集合0001.jpg",
        "text": "朝の光が差し込む\n春日の森のそばで",
        "sub":  "― 静けさの中で始まる、特別な朝食のひととき ―",
    },
    {
        "file": "イメージ_モーニング集合0036.jpg",
        "text": "窓の外には、深緑の木々",
        "sub":  "― 春日の息吹を感じながら、ゆったりとした朝を ―",
    },
    {
        "file": "7C1A5111.jpg",
        "text": "四季折々の恵みを\n一皿に込めて",
        "sub":  "― 旬の食材が織りなす、五感を満たす料理 ―",
    },
    {
        "file": "7C1A5113.jpg",
        "text": "丁寧な仕事が\n生む、静かな美しさ",
        "sub":  "― 器の一つひとつに、職人の心を宿して ―",
    },
    {
        "file": "7C1A5130.jpg",
        "text": "森に抱かれた\n贅沢な食卓",
        "sub":  "― 自然と料理が溶け合う、至福のひととき ―",
    },
    {
        "file": "7C1A5136.jpg",
        "text": "春日大社の社叢が\n窓越しに語りかける",
        "sub":  "― 千年の森が見守る、格別なランチタイム ―",
    },
    {
        "file": "7C1A5140.jpg",
        "text": "光と緑と、\nとびきりの味わい",
        "sub":  "― 奈良・春日の地で育まれた、豊かな食文化 ―",
    },
    {
        "file": "イメージ_ディナー集合0011.jpg",
        "text": "夜の帳が降りる頃\n森は別の表情を見せる",
        "sub":  "― 春日の夜に灯る、上質なディナーのひかり ―",
    },
    {
        "file": "イメージ_ディナー集合0029修.jpg",
        "text": "特別な夜を、\nここで。",
        "sub":  "― 春日の森とともに、心に残る一夜を ―",
    },
]


def fit_image(path: str, w: int, h: int) -> np.ndarray:
    """アスペクト比を保ちながら全面フィット (黒帯なし・中央クロップ)"""
    img = Image.open(path).convert("RGB")
    iw, ih = img.size
    scale = max(w / iw, h / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - w) // 2
    top  = (nh - h) // 2
    img = img.crop((left, top, left + w, top + h))
    return np.array(img)


def make_text_overlay(text: str, sub: str, w: int, h: int, t: float, total: float) -> np.ndarray:
    """テロップ画像 (RGBA) を生成"""
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    # フォント
    try:
        font_main = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 62)
        font_sub  = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 32)
    except Exception:
        font_main = ImageFont.load_default()
        font_sub  = font_main

    # フェード計算
    fade_in  = min(t / 1.0, 1.0)
    fade_out = min((total - t) / 1.0, 1.0)
    alpha    = int(255 * min(fade_in, fade_out))

    # グラデーション帯（下部）
    bar_h = int(h * 0.38)
    for y in range(bar_h):
        a = int(alpha * (1 - y / bar_h) * 0.65)
        draw.rectangle([(0, h - bar_h + y), (w, h - bar_h + y)],
                        fill=(0, 0, 0, a))

    # メインテロップ（中央下寄り）
    lines = text.split("\n")
    line_h = 72
    start_y = h - bar_h + 28
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font_main)
        tw = bbox[2] - bbox[0]
        x = (w - tw) // 2
        y = start_y + i * line_h
        # 影
        draw.text((x+2, y+2), line, font=font_main, fill=(0, 0, 0, alpha))
        draw.text((x, y), line, font=font_main, fill=(255, 248, 230, alpha))

    # サブテロップ
    bbox = draw.textbbox((0, 0), sub, font=font_sub)
    tw = bbox[2] - bbox[0]
    sx = (w - tw) // 2
    sy = start_y + len(lines) * line_h + 12
    draw.text((sx+1, sy+1), sub, font=font_sub, fill=(0, 0, 0, alpha))
    draw.text((sx, sy), sub, font=font_sub, fill=(200, 230, 210, alpha))

    return np.array(canvas)


def make_slide(slide: dict) -> CompositeVideoClip:
    path = resolve(slide["file"])
    frame = fit_image(path, W, H)

    base = ImageClip(frame, duration=DURATION)

    def overlay_frame(t):
        ov = make_text_overlay(slide["text"], slide["sub"], W, H, t, DURATION)
        return ov

    from moviepy import VideoClip

    def make_frame(t):
        ov = overlay_frame(t)          # RGBA
        bg = frame.copy()              # RGB
        alpha = ov[:, :, 3:4] / 255.0
        blended = (bg * (1 - alpha) + ov[:, :, :3] * alpha).astype(np.uint8)
        return blended

    return VideoClip(make_frame, duration=DURATION)


# --- メイン ---
print("スライドを生成中...")
clips = [make_slide(s) for s in SLIDES]

print("クリップを連結中...")
video = concatenate_videoclips(clips, method="compose", padding=-FADE)

print(f"動画を出力中: {OUTPUT}")
video.write_videofile(OUTPUT, fps=FPS, codec="libx264",
                      audio=False, preset="medium",
                      ffmpeg_params=["-crf", "20"])
print("完了！")
