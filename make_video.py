"""
春日の森を感じながらのお食事 — プロモーション動画
"""
import os, unicodedata
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from moviepy import VideoClip, AudioFileClip

IMAGE_DIR = "/home/user/kakanonoyaya/images"
OUTPUT    = "/home/user/kakanonoyaya/kasuga_dining.mp4"
MUSIC     = "/root/.claude/uploads/28a3daed-590d-5329-9d4a-97d354e41fb2/9113c14d-Tables_for_Two.mp3"
MUSIC2    = "/root/.claude/uploads/28a3daed-590d-5329-9d4a-97d354e41fb2/101c468c-Linen_and_Leaves.mp3"
W, H      = 1080, 1920
FPS       = 30
DURATION  = 6.2   # 8枚 × 6.2 - 7 × 1.5 = 39.1s
FADE      = 1.5

FONT_MAIN = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"
FONT_SUB  = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"

_file_map = {unicodedata.normalize("NFC", f): f for f in os.listdir(IMAGE_DIR)}
def resolve(name):
    nfc = unicodedata.normalize("NFC", name)
    return os.path.join(IMAGE_DIR, _file_map.get(nfc, name))

SLIDES = [
    # ── 昼・冒頭 ──────────────────────────────────────
    {"file": "7C1A4295.jpg", "night": False,
     "text": "千年の杜が\n窓の外に広がる",
     "sub":  ""},
    {"file": "7C1A5139.jpg", "night": False,
     "text": "森を望む\n静かな食卓",
     "sub":  ""},
    # ── モーニング ────────────────────────────────────
    {"file": "イメージ_モーニング集合0001.jpg", "night": False,
     "text": "春日の森に包まれて\n始まる朝",
     "sub":  ""},
    {"file": "イメージ_モーニング集合0036.jpg", "night": False,
     "text": "森の光とともに\n朝の食卓へ",
     "sub":  ""},
    # ── 夜への転換 ────────────────────────────────────
    {"file": "7C1A5468.jpg", "night": False,
     "text": "夜になると\n春日の森は静寂に包まれる",
     "sub":  ""},
    # ── 夜の食卓（ディナー前） ────────────────────────
    {"file": "7C1A5171.jpg", "night": False,
     "text": "窓の外に広がる\n春日の夜",
     "sub":  ""},
    # ── ディナー（元の明るさ） ────────────────────────
    {"file": "イメージ_ディナー集合0011.jpg", "night": False,
     "text": "森の静けさが\n食卓に宿る夜",
     "sub":  ""},
    {"file": "イメージ_ディナー集合0029修.jpg", "night": False,
     "text": "この場所でしか\n味わえない贅沢",
     "sub":  ""},
]

NIGHT_START = None


def fit_letterbox(path, w, h, night=False):
    img = Image.open(path).convert("RGB")
    iw, ih = img.size
    scale = min(w / iw, h / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGB", (w, h), (0, 0, 0))
    canvas.paste(img, ((w - nw) // 2, (h - nh) // 2))
    if night:
        canvas = ImageEnhance.Brightness(canvas).enhance(0.50)
        canvas = ImageEnhance.Color(canvas).enhance(0.72)
        r, g, b = canvas.split()
        b = b.point(lambda x: min(x + 20, 255))
        canvas = Image.merge("RGB", (r, g, b))
    return np.array(canvas)


def ease_in_out(x):
    x = max(0.0, min(1.0, x))
    return 3*x*x - 2*x*x*x

def make_text_layer(text, sub, w, h, t, total, night=False):
    FI, FO, DRIFT = 1.2, 1.0, 28
    if t < FI:
        prog  = ease_in_out(t / FI)
        alpha = int(255 * prog)
        drift = int(DRIFT * (1.0 - prog))
    elif t > total - FO:
        prog  = ease_in_out((total - t) / FO)
        alpha = int(255 * prog)
        drift = -int(DRIFT * (1.0 - prog))
    else:
        alpha, drift = 255, 0

    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw   = ImageDraw.Draw(canvas)
    try:
        font_main = ImageFont.truetype(FONT_MAIN, 62)
        font_sub  = ImageFont.truetype(FONT_SUB,  30)
    except Exception:
        font_main = font_sub = ImageFont.load_default()

    lines    = text.split("\n")
    line_h   = 76
    n_lines  = len(lines)
    start_y  = 52 + drift
    block_bottom = start_y + n_lines * line_h + 16 + 40

    band_h = block_bottom + 40
    for dy in range(max(band_h, 0)):
        ratio = 1.0 - dy / band_h
        a = int(alpha * min(ratio * 2, 1.0) * (0.82 if night else 0.68))
        draw.rectangle([(0, dy), (w, dy)], fill=(0, 0, 0, a))

    main_color = (220, 240, 255, alpha) if night else (255, 248, 230, alpha)
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font_main)
        tw   = bbox[2] - bbox[0]
        x    = (w - tw) // 2
        y    = start_y + i * line_h
        draw.text((x+2, y+2), line, font=font_main, fill=(0, 0, 0, alpha))
        draw.text((x,   y),   line, font=font_main, fill=main_color)

    sy   = start_y + n_lines * line_h + 16
    bbox = draw.textbbox((0, 0), sub, font=font_sub)
    tw   = bbox[2] - bbox[0]
    sx   = (w - tw) // 2
    sub_color = (180, 210, 240, alpha) if night else (200, 235, 210, alpha)
    draw.text((sx+1, sy+1), sub, font=font_sub, fill=(0, 0, 0, alpha))
    draw.text((sx,   sy),   sub, font=font_sub, fill=sub_color)

    return np.array(canvas)


def make_video_clip(frames_list, dur, fade):
    n     = len(frames_list)
    step  = dur - fade
    total = step * (n - 1) + dur

    def make_frame(t):
        idx   = min(int(t / step), n - 1)
        local = t - idx * step
        item  = frames_list[idx]
        base  = item["frame"].copy()
        ov    = make_text_layer(item["slide"]["text"], item["slide"]["sub"],
                                W, H, local, dur, item["slide"]["night"]).astype(np.float32)
        a     = ov[:, :, 3:4] / 255.0
        result = base * (1 - a) + ov[:, :, :3] * a
        if idx > 0 and local < fade:
            af = local / fade
            result = frames_list[idx-1]["frame"] * (1 - af) + result * af
        return result.clip(0, 255).astype(np.uint8)

    return VideoClip(make_frame, duration=total)


print("画像を読み込み中...")
raw_frames = []
for s in SLIDES:
    frame = fit_letterbox(resolve(s["file"]), W, H, night=s["night"]).astype(np.float32)
    raw_frames.append({"frame": frame, "slide": s})

print("動画を組み立て中...")
video = make_video_clip(raw_frames, DURATION, FADE)

from moviepy import afx, CompositeAudioClip

# スライド1-4の終わり時刻
switch_t = 4 * (DURATION - FADE)  # 18.8s
fade_len = 2.0

has_audio = False

if os.path.exists(MUSIC2):
    print("音楽を合成中...")
    vid_dur = video.duration

    # BGM1: Linen_and_Leaves → スライド1〜4（switch_tでフェードアウト）
    bgm1 = AudioFileClip(MUSIC2)
    if bgm1.duration < switch_t + fade_len:
        bgm1 = bgm1.with_effects([afx.AudioLoop(duration=switch_t + fade_len)])
    bgm1 = bgm1.with_end(switch_t + fade_len)
    bgm1 = bgm1.with_effects([afx.AudioFadeOut(fade_len)])

    if os.path.exists(MUSIC):
        # BGM2: A_Quiet_Path_Through_Moss → スライド5〜8
        bgm2 = AudioFileClip(MUSIC)
        bgm2_dur = vid_dur - switch_t
        if bgm2.duration < bgm2_dur:
            bgm2 = bgm2.with_effects([afx.AudioLoop(duration=bgm2_dur)])
        bgm2 = bgm2.with_end(bgm2_dur)
        bgm2 = bgm2.with_effects([afx.AudioFadeIn(fade_len), afx.AudioFadeOut(2.0)])
        bgm2 = bgm2.with_start(switch_t)
        audio = CompositeAudioClip([bgm1, bgm2])
    else:
        audio = bgm1

    video = video.with_audio(audio)
    has_audio = True
elif os.path.exists(MUSIC):
    print("音楽を合成中...")
    src = AudioFileClip(MUSIC)
    vid_dur = video.duration
    if src.duration < vid_dur:
        src = src.with_effects([afx.AudioLoop(duration=vid_dur)])
    else:
        src = src.with_end(vid_dur)
    audio = src.with_effects([afx.AudioFadeOut(2.0)])
    video = video.with_audio(audio)
    has_audio = True
else:
    print("音楽なしで出力します。")
    has_audio = False

print(f"出力中: {OUTPUT}  ({video.duration:.1f}秒)")
video.write_videofile(OUTPUT, fps=FPS, codec="libx264",
                      audio=has_audio,
                      audio_codec="aac" if has_audio else None,
                      preset="medium", ffmpeg_params=["-crf", "18"])
print("完了！")
