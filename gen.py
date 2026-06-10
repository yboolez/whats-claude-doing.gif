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

# 微信表情包格式（240×60 横版）
WX_W = 240
WX_H = 60
WX_SIZE_DEFAULT = 25       # 默认字号
WX_SIZE_LONG = 24          # 长词降一档
WX_LIGHT_BG = (245, 240, 235)  # 假定聊天底色（浅米色），用于"假抗锯齿"调色板


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


# ───────── 微信表情包：240×60，左对齐 + 假抗锯齿调色板 ─────────
WX_SS = 4   # 微信版 supersample 略高，反走样更顺


def _wx_blend(fg, bg, t):
    return tuple(int(fg[i] * t + bg[i] * (1 - t)) for i in range(3))


def _wx_palette(color):
    """4 阶调色板：0=透明, 1=纯色, 2=70%混底, 3=40%混底。"""
    pal = [0, 0, 0]
    for t in (1.0, 0.70, 0.40):
        pal += list(_wx_blend(color, WX_LIGHT_BG, t))
    return pal + [0] * (256 * 3 - len(pal))


def _wx_alpha_to_idx(arr):
    out = np.zeros_like(arr, dtype=np.uint8)
    out[arr >= 192] = 1
    out[(arr >= 96) & (arr < 192)] = 2
    out[(arr >= 32) & (arr < 96)] = 3
    return out


def _wx_compute_layout(text: str):
    """决定字号 + 字间距压缩量。返回 (size, letter_adj, star_advance, space_advance)。
    短词用 25px 不压缩；长词降到 24px，若仍装不下则字间距压缩。"""
    for size in (WX_SIZE_DEFAULT, WX_SIZE_LONG):
        wf = ImageFont.truetype(FONT_PATH, size * WX_SS)
        sf = get_star_font("✼", size * WX_SS)
        star_adv = sf.getlength("✼") / WX_SS
        space_adv = wf.getlength(" ") / WX_SS
        word_nat = sum(wf.getlength(c) / WX_SS for c in text)
        if star_adv + space_adv + word_nat <= WX_W:
            return size, 0.0, star_adv, space_adv
    # 24px 还不够 → 字间距压缩
    size = WX_SIZE_LONG
    wf = ImageFont.truetype(FONT_PATH, size * WX_SS)
    sf = get_star_font("✼", size * WX_SS)
    star_adv = sf.getlength("✼") / WX_SS
    space_adv = wf.getlength(" ") / WX_SS
    word_nat = sum(wf.getlength(c) / WX_SS for c in text)
    space_for_word = WX_W - star_adv - space_adv
    n_gaps = max(len(text) - 1, 1)
    adj = (space_for_word - word_nat) / n_gaps
    return size, adj, star_adv, space_adv


def _wx_render_text(text: str, size: int, x_start: float, letter_adj: float = 0.0) -> Image.Image:
    """逐字符渲染，支持字间距调整（负数=压缩）。返回 (WX_W × WX_H) 灰度 mask。"""
    font = ImageFont.truetype(FONT_PATH, size * WX_SS)
    big = Image.new("L", (WX_W * WX_SS, WX_H * WX_SS), 0)
    d = ImageDraw.Draw(big)
    x = x_start * WX_SS
    y_center = (WX_H / 2) * WX_SS
    for c in text:
        d.text((x, y_center), c, font=font, fill=255, anchor="lm")
        x += font.getlength(c) + letter_adj * WX_SS
    return big.resize((WX_W, WX_H), Image.LANCZOS)


def _wx_render_star(ch: str, size: int, target_cx: float) -> Image.Image:
    """星号按像素重心对齐到 (target_cx, WX_H/2)。"""
    sfont = get_star_font(ch, size * WX_SS)
    tmp = Image.new("L", (WX_W * WX_SS, WX_H * WX_SS), 0)
    ImageDraw.Draw(tmp).text((WX_W * WX_SS // 2, WX_H * WX_SS // 2),
                              ch, font=sfont, fill=255)
    arr = np.array(tmp, dtype=np.float32)
    tot = arr.sum()
    if tot == 0:
        return Image.new("L", (WX_W, WX_H), 0)
    ys, xs = np.indices(arr.shape)
    scx = (xs * arr).sum() / tot
    scy = (ys * arr).sum() / tot
    dx = int(round(target_cx * WX_SS - scx))
    dy = int(round((WX_H / 2) * WX_SS - scy))
    big = Image.new("L", (WX_W * WX_SS, WX_H * WX_SS), 0)
    ImageDraw.Draw(big).text((WX_W * WX_SS // 2 + dx, WX_H * WX_SS // 2 + dy),
                              ch, font=sfont, fill=255)
    return big.resize((WX_W, WX_H), Image.LANCZOS)


def make_wx_gif(word: str, out_path: Path, color=ORANGE, frame_ms: int = 200):
    text = f"{word}…"
    size, adj, star_adv, space_adv = _wx_compute_layout(text)
    word_start_x = star_adv + space_adv
    word_mask = np.array(_wx_render_text(text, size, word_start_x, adj))
    pal = _wx_palette(color)
    frames = []
    for ch in STAR_SEQUENCE:
        star_mask = np.array(_wx_render_star(ch, size, star_adv / 2))
        merged = np.maximum(word_mask, star_mask)
        idx = _wx_alpha_to_idx(merged)
        p = Image.fromarray(idx).convert("P")
        p.putpalette(pal)
        frames.append(p)
    frames[0].save(out_path, save_all=True, append_images=frames[1:],
                   duration=frame_ms, loop=0,
                   transparency=0, disposal=2, optimize=False)
    print(f"WX GIF → {out_path} ({out_path.stat().st_size // 1024} KB, {WX_W}×{WX_H})")


def make_wx_png(text: str, out_path: Path, color=GRAY, star: str = "✻"):
    """PNG 完成态版本：text 是完整文字（含数字、空格），不加 ellipsis。"""
    size, adj, star_adv, space_adv = _wx_compute_layout(text)
    word_start_x = star_adv + space_adv
    word_mask = _wx_render_text(text, size, word_start_x, adj)
    star_mask = _wx_render_star(star, size, star_adv / 2)

    img = Image.new("RGBA", (WX_W, WX_H), (0, 0, 0, 0))
    color_layer = Image.new("RGBA", (WX_W, WX_H), color + (0,))
    combined_alpha = Image.composite(
        Image.new("L", (WX_W, WX_H), 255),
        word_mask,
        star_mask,
    )
    color_layer.putalpha(combined_alpha)
    img.alpha_composite(color_layer)
    img.save(out_path)
    print(f"WX PNG → {out_path} ({out_path.stat().st_size // 1024} KB, {WX_W}×{WX_H})")


# ───────── CLI ─────────
def slugify(text: str) -> str:
    s = text.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "_", s.strip())
    return s or "out"


def main():
    p = argparse.ArgumentParser(description="Claude Code thinking sticker generator")
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("gif", help="橙色闪烁动画 GIF（920×140 横版）")
    g.add_argument("word", help='e.g. "Pondering"')
    g.add_argument("--color", default="orange", choices=COLORS.keys())
    g.add_argument("-o", "--out", help="输出路径")

    n = sub.add_parser("png", help="静态完成态 PNG（920×140 横版，默认灰色）")
    n.add_argument("text", help='e.g. "Cooked for 58s" or "recap:"')
    n.add_argument("--star", default="✻", help='前缀符号，默认 ✻，常见还有 ※')
    n.add_argument("--color", default="gray", choices=COLORS.keys())
    n.add_argument("-o", "--out", help="输出路径")

    w = sub.add_parser("wx", help="微信表情包 240×60 横版（左对齐，长词字间距压缩）")
    w.add_argument("text", help='词或短句，e.g. "Pondering" / "Cooked for 58s"')
    w.add_argument("--kind", default="gif", choices=["gif", "png"],
                   help="gif=橙色闪烁，png=灰色静态")
    w.add_argument("--star", default="✻", help='png 前缀符号')
    w.add_argument("--color", help="覆盖默认色 (gif→orange, png→gray)")
    w.add_argument("-o", "--out", help="输出路径")

    args = p.parse_args()

    if args.cmd == "gif":
        out = Path(args.out) if args.out else OUT_DIR / f"{slugify(args.word)}.gif"
        make_gif(args.word, out, color=COLORS[args.color])
    elif args.cmd == "png":
        out = Path(args.out) if args.out else OUT_DIR / f"{slugify(args.text)}.png"
        make_png(args.text, out, color=COLORS[args.color], star=args.star)
    elif args.cmd == "wx":
        is_gif = args.kind == "gif"
        ext = "gif" if is_gif else "png"
        out = Path(args.out) if args.out else OUT_DIR / f"{slugify(args.text)}_wx.{ext}"
        default_color = "orange" if is_gif else "gray"
        color = COLORS[args.color or default_color]
        if is_gif:
            make_wx_gif(args.text, out, color=color)
        else:
            make_wx_png(args.text, out, color=color, star=args.star)


if __name__ == "__main__":
    main()
