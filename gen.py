"""Claude Code thinking sticker generator.

Usage:
    python3 gen.py gif <word>                   # 橙色动画 GIF (e.g. "Pondering")
    python3 gen.py gif "Whirring" -o out.gif

    python3 gen.py png "Cooked for 58s"         # 灰色静态完成态 PNG
    python3 gen.py png "Brewed for 8m 43s"
    python3 gen.py png "recap:" --star ※
    python3 gen.py png "Cooked for 58s" --color orange   # 强制橙色

输出文件名由文本自动 slugify（小写、空格→下划线），可用 -o 覆盖。
"""
import argparse
import re
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ───────── 全局样式 ─────────
OUT_DIR = Path(__file__).parent
ORANGE = (217, 119, 87)   # Claude brand #D97757
GRAY = (142, 142, 142)    # 完成态灰
COLORS = {"orange": ORANGE, "gray": GRAY}

SS = 3                    # supersampling
FONT_PATH = "/System/Library/Fonts/Menlo.ttc"
STAR_FONT_SIZE = 84
WORD_FONT_SIZE = 64
WORD_FONT = ImageFont.truetype(FONT_PATH, WORD_FONT_SIZE * SS)

# 星号字体 fallback 链：第一个能正确渲染该字符的就用它
STAR_FONT_FALLBACKS = [
    "/System/Library/Fonts/Menlo.ttc",         # ✻ ✼ ✽ ✶ ✢ ✳ · 都有
    "/System/Library/Fonts/Apple Symbols.ttf", # ※ 等
]


def _has_glyph(font: ImageFont.FreeTypeFont, ch: str) -> bool:
    """检测字符是否有真实字形（非 .notdef tofu）。
    用 \\uE000 私有区（必为 .notdef）作为对照，bytes 一致即 tofu。"""
    try:
        a = bytes(font.getmask(ch))
        b = bytes(font.getmask(""))
    except Exception:
        return False
    return a != b


def get_star_font(ch: str, size_px: int) -> ImageFont.FreeTypeFont:
    for path in STAR_FONT_FALLBACKS:
        f = ImageFont.truetype(path, size_px)
        if _has_glyph(f, ch):
            return f
    return ImageFont.truetype(STAR_FONT_FALLBACKS[0], size_px)

# 布局（最终输出坐标系）
STAR_ANCHOR = (72, 70)    # 星号视觉中心
WORD_LEFT = 140           # 文字左边
WORD_Y_CENTER = 70        # 文字垂直中心
PAD_RIGHT = 40            # 右边留白
CANVAS_H = 140
# 固定画布宽度：保证所有 sticker 发出去后字号一致。
# 当前词汇表最长是 Whatchamacalliting (912px)，留 8px buffer。
CANVAS_W = 920

# 真实 spinner 序列（10 帧首尾相接）
STAR_SEQUENCE = ["·", "✢", "✳", "✶", "✻", "✽", "✻", "✶", "✳", "✢"]


# ───────── 渲染工具 ─────────
def measure_text_width(text: str) -> int:
    """测量文字的实际像素宽度（最终输出坐标系）。"""
    tmp = Image.new("L", (4000, 200), 0)
    d = ImageDraw.Draw(tmp)
    d.text((0, 0), text, font=WORD_FONT, fill=255)
    bbox = tmp.getbbox()
    if bbox is None:
        return 0
    return (bbox[2] - bbox[0]) // SS


def canvas_width_for(text: str) -> int:
    """文字所需最小宽度（如果超过固定 CANVAS_W 则扩展，否则用固定值统一字号）。"""
    needed = WORD_LEFT + measure_text_width(text) + PAD_RIGHT
    return max(CANVAS_W, needed)


def render_word_mask(text: str, W: int) -> Image.Image:
    big = Image.new("L", (W * SS, CANVAS_H * SS), 0)
    d = ImageDraw.Draw(big)
    # 用 anchor='lm' 让文字基于"左中"对齐到 WORD_Y_CENTER
    d.text((WORD_LEFT * SS, WORD_Y_CENTER * SS), text,
           font=WORD_FONT, fill=255, anchor="lm")
    return big.resize((W, CANVAS_H), Image.LANCZOS)


def render_star_mask(ch: str, W: int) -> Image.Image:
    """按像素质量重心对齐到 STAR_ANCHOR，杜绝上下跳。"""
    font = get_star_font(ch, STAR_FONT_SIZE * SS)
    tmp = Image.new("L", (W * SS, CANVAS_H * SS), 0)
    d = ImageDraw.Draw(tmp)
    d.text((W * SS // 2, CANVAS_H * SS // 2), ch, font=font, fill=255)

    arr = np.array(tmp, dtype=np.float32)
    total = arr.sum()
    if total == 0:
        return Image.new("L", (W, CANVAS_H), 0)
    ys, xs = np.indices(arr.shape)
    cx = (xs * arr).sum() / total
    cy = (ys * arr).sum() / total

    target_cx = STAR_ANCHOR[0] * SS
    target_cy = STAR_ANCHOR[1] * SS
    dx = int(round(target_cx - cx))
    dy = int(round(target_cy - cy))

    big = Image.new("L", (W * SS, CANVAS_H * SS), 0)
    d2 = ImageDraw.Draw(big)
    d2.text((W * SS // 2 + dx, CANVAS_H * SS // 2 + dy),
            ch, font=font, fill=255)
    return big.resize((W, CANVAS_H), Image.LANCZOS)


# ───────── GIF：橙色闪烁 + 词 ─────────
def compose_gif_frame(star_mask, word_mask, color, W, alpha_cutoff=96):
    pal = [0, 0, 0] + list(color) + [0] * (256 * 3 - 6)
    p = Image.new("P", (W, CANVAS_H), 0)
    p.putpalette(pal)
    p.paste(1, mask=word_mask.point(lambda a: 255 if a > alpha_cutoff else 0))
    p.paste(1, mask=star_mask.point(lambda a: 255 if a > alpha_cutoff else 0))
    return p


def make_gif(word: str, out_path: Path, color=ORANGE, frame_ms: int = 200):
    text = f"{word}…"
    W = canvas_width_for(text)
    word_mask = render_word_mask(text, W)
    frames = [compose_gif_frame(render_star_mask(ch, W), word_mask, color, W)
              for ch in STAR_SEQUENCE]
    frames[0].save(
        out_path,
        save_all=True, append_images=frames[1:],
        duration=frame_ms, loop=0,
        transparency=0, disposal=2, optimize=False,
    )
    print(f"GIF  → {out_path} ({out_path.stat().st_size // 1024} KB, {W}×{CANVAS_H})")


# ───────── PNG：静态、灰色（默认）、保留 anti-alias ─────────
def make_png(text: str, out_path: Path, color=GRAY, star: str = "✻"):
    W = canvas_width_for(text)
    word_mask = render_word_mask(text, W)
    star_mask = render_star_mask(star, W)

    img = Image.new("RGBA", (W, CANVAS_H), (0, 0, 0, 0))
    # 把 mask 当 alpha，颜色填 color
    color_layer = Image.new("RGBA", (W, CANVAS_H), color + (0,))
    # 合成：word + star alpha
    combined_alpha = Image.eval(word_mask, lambda a: a)
    combined_alpha = Image.composite(
        Image.new("L", (W, CANVAS_H), 255),
        combined_alpha,
        star_mask,
    )
    color_layer.putalpha(combined_alpha)
    img.alpha_composite(color_layer)
    img.save(out_path)
    print(f"PNG  → {out_path} ({out_path.stat().st_size // 1024} KB, {W}×{CANVAS_H})")


# ───────── CLI ─────────
def slugify(text: str) -> str:
    s = text.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "_", s.strip())
    return s or "out"


def main():
    p = argparse.ArgumentParser(description="Claude Code thinking sticker generator")
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("gif", help="橙色闪烁动画 GIF")
    g.add_argument("word", help='e.g. "Pondering"')
    g.add_argument("--color", default="orange", choices=COLORS.keys())
    g.add_argument("-o", "--out", help="输出路径")

    n = sub.add_parser("png", help="静态完成态 PNG（默认灰色）")
    n.add_argument("text", help='e.g. "Cooked for 58s" or "recap:"')
    n.add_argument("--star", default="✻", help='前缀符号，默认 ✻，常见还有 ※')
    n.add_argument("--color", default="gray", choices=COLORS.keys())
    n.add_argument("-o", "--out", help="输出路径")

    args = p.parse_args()
    color = COLORS[args.color]

    if args.cmd == "gif":
        out = Path(args.out) if args.out else OUT_DIR / f"{slugify(args.word)}.gif"
        make_gif(args.word, out, color=color)
    elif args.cmd == "png":
        out = Path(args.out) if args.out else OUT_DIR / f"{slugify(args.text)}.png"
        make_png(args.text, out, color=color, star=args.star)


if __name__ == "__main__":
    main()
