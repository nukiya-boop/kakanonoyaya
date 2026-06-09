"""
春日の森を感じながらのお食事 — プロモーション動画
"""
import os, unicodedata
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from moviepy import VideoClip, AudioFileClip

IMAGE_DIR = "/home/user/kakanonoyaya/images"
OUTPUT    = "/home/user/kakanonoyaya/kasuga_dining.mp4"
MUSIC     = "/root/.claude/uploads/28a3daed-590d-5329-9d4a-97d354e41fb2/956816aa-A_Quiet_Path_Through_Moss.mp3"
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
     "sub":  "― 春日の森とともに過ごす、特別なひととき ―"},
    {"file": "7C1A5139.jpg", "night": False,
     "text": "森を望む\n静かな食卓",
     "sub":  "― 窓の外の緑が、器の美しさをより深く映す ―"},
    # ── モーニング ────────────────────────────────────
    {"file": "イメージ_モーニング集合0001.jpg", "night": False,
     "text": "春日の森に包まれて\n始まる朝",
     "sub":  "― 杜の気配が満ちる中で、朝の恵みをいただく ―"},
    {"file": "イメージ_モーニング集合0036.jpg", "night": False,
     "text": "森の光とともに\n朝の食卓へ",
     "sub":  "― 窓の外の緑が揺れる、贅沢な朝のひととき ―"},
    # ── 夜への転換 ────────────────────────────────────
    {"file": "7C1A5468.jpg", "night": True,
     "text": "夜になると\n春日の森は静寂に包まれる",
     "sub":  "― 千年の杜が闇に沈む頃、特別な夜が始まる ―"},
    # ── 夜の食卓（ディナー前） ────────────────────────
    {"file": "7C1A5171.jpg", "night": True,
     "text": "窓の外に広がる\n春日の夜",
     "sub":  "― 夜の杜に抱かれた個室で、静かな夜を ―"},
    # ── ディナー（元の明るさ） ────────────────────────
    {"file": "イメージ_ディナー集合0011.jpg", "night": False,
     "text": "森の静けさが\n食卓に宿る夜",
     "sub":  "― 春日の夜景を眺めながら、上質なひとときを ―"},
    {"file": "イメージ_ディナー集合0029修.jpg", "night": False,
     "text": "この場所でしか\n味わえない贅沢",
     "sub":  "― 春日の杜とともに、心に残る一夜を ―"},
]

NIGHT_START = next(i for i, s in enumerate(SLIDES) if s["night"])


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

if os.path.exists(MUSIC):
    print("音楽を合成中...")
    from moviepy import afx
    src = AudioFileClip(MUSIC)
    vid_dur = video.duration
    if src.duration < vid_dur:
        src = src.with_effects([afx.AudioLoop(duration=vid_dur)])
    else:
        src = src.with_end(vid_dur)
    night_t  = NIGHT_START * (DURATION - FADE)
    fade_len = 2.0
    def vol_curve(t):
        if t < night_t - fade_len:
            return 1.0
        elif t < night_t:
            return 1.0 - 0.35 * ((t - (night_t - fade_len)) / fade_len)
        else:
            return 0.65
    audio = src.with_effects([afx.MultipliedAudio(vol_curve), afx.AudioFadeOut(2.0)])
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
