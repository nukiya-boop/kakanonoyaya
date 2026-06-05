"""
春日の森を感じながらのお食事 — プロモーション動画生成スクリプト
"""
import os
import unicodedata
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import VideoClip, AudioFileClip

IMAGE_DIR  = "/home/user/kakanonoyaya/images"
OUTPUT     = "/home/user/kakanonoyaya/kasuga_dining.mp4"
MUSIC      = "/root/.claude/uploads/a5d067d5-75b4-465a-8b3d-e2d22af93c00/bb1ab356-Paper_Lantern_Waltz.mp3"
W, H       = 1920, 1080
FPS        = 30
DURATION   = 4.5   # 1枚あたり秒数 (9枚 × 4.5 - 8 × 1.5 = 28.5s ≈ 音楽尺)
FADE       = 1.5   # クロスフェード秒数（長めでなめらかに）

FONT_MAIN = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"
FONT_SUB  = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"

# ファイル名 NFD→NFC 解決マップ
_file_map = {unicodedata.normalize("NFC", f): f for f in os.listdir(IMAGE_DIR)}

def resolve(name: str) -> str:
    nfc = unicodedata.normalize("NFC", name)
    return os.path.join(IMAGE_DIR, _file_map.get(nfc, name))

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
        "text": "深い緑に包まれた\nかけがえのない食卓",
        "sub":  "― 静寂の中に、記憶に残る味わいが宿る ―",
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


def fit_letterbox(path: str, w: int, h: int) -> np.ndarray:
    """
    アスペクト比を保ち全体を表示 (黒帯レターボックス)。
    画像は一切切り取らない。
    """
    img = Image.open(path).convert("RGB")
    iw, ih = img.size
    scale = min(w / iw, h / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    img = img.resize((nw, nh), Image.LANCZOS)

    canvas = Image.new("RGB", (w, h), (0, 0, 0))
    ox = (w - nw) // 2
    oy = (h - nh) // 2
    canvas.paste(img, (ox, oy))
    return np.array(canvas)


def make_text_layer(text: str, sub: str, w: int, h: int, t: float, total: float) -> np.ndarray:
    """RGBA テロップレイヤーを生成"""
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    try:
        font_main = ImageFont.truetype(FONT_MAIN, 68)
        font_sub  = ImageFont.truetype(FONT_SUB,  34)
    except Exception:
        font_main = ImageFont.load_default()
        font_sub  = font_main

    # フェードイン / アウト
    fade_in  = min(t / 1.2, 1.0)
    fade_out = min((total - t) / 1.0, 1.0)
    alpha    = int(255 * min(fade_in, fade_out))

    lines     = text.split("\n")
    line_h    = 82
    n_lines   = len(lines)
    sub_gap   = 16
    sub_h     = 44
    block_h   = n_lines * line_h + sub_gap + sub_h
    margin_b  = 60
    start_y   = h - block_h - margin_b

    # 半透明グラデーション帯
    grad_top = start_y - 30
    band_h   = h - grad_top
    for dy in range(band_h):
        ratio = dy / band_h
        a = int(alpha * min(ratio * 2, 1.0) * 0.70)
        draw.rectangle([(0, grad_top + dy), (w, grad_top + dy)], fill=(0, 0, 0, a))

    # メインテロップ
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font_main)
        tw   = bbox[2] - bbox[0]
        x    = (w - tw) // 2
        y    = start_y + i * line_h
        # 影
        draw.text((x + 2, y + 2), line, font=font_main, fill=(0, 0, 0, alpha))
        draw.text((x, y),         line, font=font_main, fill=(255, 248, 230, alpha))

    # サブテロップ
    sy   = start_y + n_lines * line_h + sub_gap
    bbox = draw.textbbox((0, 0), sub, font=font_sub)
    tw   = bbox[2] - bbox[0]
    sx   = (w - tw) // 2
    draw.text((sx + 1, sy + 1), sub, font=font_sub, fill=(0, 0, 0, alpha))
    draw.text((sx, sy),         sub, font=font_sub, fill=(200, 235, 210, alpha))

    return np.array(canvas)



def crossfade_concat(frames_list, dur, fade):
    """
    各スライドの静止フレームをクロスフェードで繋ぐ単一 VideoClip を返す。
    テロップは各スライドの局所時刻で描画する。
    """
    n      = len(frames_list)
    step   = dur - fade                        # スライドの開始間隔
    total  = step * (n - 1) + dur              # 総尺

    def make_frame(t):
        # どのスライドが表示中か特定
        idx   = min(int(t / step), n - 1)
        local = t - idx * step                 # スライド内の局所時刻

        base  = frames_list[idx]["frame"].copy()
        slide = frames_list[idx]["slide"]
        ov    = make_text_layer(slide["text"], slide["sub"], W, H, local, dur).astype(np.float32)
        a     = ov[:, :, 3:4] / 255.0
        result = base * (1 - a) + ov[:, :, :3] * a

        # クロスフェード：前のスライドからフェードイン
        if idx > 0 and local < fade:
            alpha_fade = local / fade          # 0→1
            prev_frame = frames_list[idx - 1]["frame"]
            result = prev_frame * (1 - alpha_fade) + result * alpha_fade

        return result.clip(0, 255).astype(np.uint8)

    return VideoClip(make_frame, duration=total)


print("スライドを生成中...")
raw_frames = []
for s in SLIDES:
    path  = resolve(s["file"])
    frame = fit_letterbox(path, W, H).astype(np.float32)
    raw_frames.append({"frame": frame, "slide": s})

print("クリップを連結中...")
video = crossfade_concat(raw_frames, DURATION, FADE)

print("音楽を合成中...")
audio = AudioFileClip(MUSIC)
# 動画尺に合わせて音楽をトリム（または音楽尺に合わせて動画をトリム）
video_dur = video.duration
audio = audio.with_end(min(audio.duration, video_dur))
video = video.with_audio(audio).with_duration(min(video_dur, audio.duration))

print(f"動画を出力中: {OUTPUT}  (尺: {video.duration:.1f}秒)")
video.write_videofile(OUTPUT, fps=FPS, codec="libx264",
                      audio_codec="aac", preset="medium",
                      ffmpeg_params=["-crf", "18"])
print("完了！")
