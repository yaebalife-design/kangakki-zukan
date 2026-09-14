# -*- coding: utf-8 -*-
"""OG画像（SNS共有時のサムネイル）を生成する（管楽器図鑑）。

  site/assets/og/default.png   … サイト共通
  site/assets/og/{slug}.png    … 記事ごと（H1・カテゴリ・確認日）

方針:
  ・商品画像NG／AI生成の実機画像NG（絶対ルール8）→ 文字＋抽象的な図形（管の輪郭）だけで構成
  ・フォントは Windows 同梱の游明朝。無ければ Pillow 既定フォントで落ちずに生成
"""
import re
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("⚠ Pillow が無いため OG画像の生成を飛ばした（pip install pillow）")
    sys.exit(0)

import site_config as cfg
from articles_data import ARTICLES

SITE = Path(__file__).parent.parent / "site"
OUT = SITE / "assets" / "og"
W, H = 1200, 630

PAPER = (248, 246, 241)
CARD = (255, 255, 255)
INK = (42, 38, 32)
INK_SOFT = (107, 98, 88)
BRASS = (138, 90, 23)
DEEP = (92, 58, 12)
LINE = (227, 220, 208)
WASH = (247, 240, 226)

FONT_DIR = Path(r"C:\Windows\Fonts")
FONT_BOLD = FONT_DIR / "yumindb.ttf"
FONT_REG = FONT_DIR / "yumin.ttf"


def font(path: Path, size: int):
    try:
        return ImageFont.truetype(str(path), size)
    except OSError:
        return ImageFont.load_default()


def wrap_jp(text: str, max_chars: int):
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    lines = []
    for para in text.split("\n"):
        para = para.strip()
        while len(para) > max_chars:
            cut = max_chars
            for i in range(max_chars, max(max_chars - 8, 1), -1):
                a, b = para[i - 1], para[i]
                if a.isascii() and a.isalnum() and b.isascii() and b.isalnum():
                    continue
                if b in "、。）」・ぁぃぅぇぉっゃゅょ":
                    continue
                cut = i
                break
            lines.append(para[:cut])
            para = para[cut:]
        if para:
            lines.append(para)
    return lines


def base_canvas():
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)
    for x in range(0, W, 26):
        d.line([(x, 0), (x, H)], fill=(240, 236, 228), width=1)
    for y in range(0, H, 26):
        d.line([(0, y), (W, y)], fill=(240, 236, 228), width=1)
    d.rounded_rectangle([48, 48, W - 48, H - 48], radius=18, fill=CARD, outline=LINE, width=2)
    d.rounded_rectangle([48, 48, 60, H - 48], radius=6, fill=BRASS)
    # 抽象的な管とベルの輪郭（右上）。実機を描かない
    d.line([(900, 150), (1040, 150)], fill=BRASS, width=10)
    d.polygon([(1040, 140), (1110, 96), (1110, 204), (1040, 160)], fill=WASH, outline=BRASS)
    for i, cx in enumerate((930, 962, 994, 1026)):
        d.ellipse([cx - 7, 143 - (i % 2) * 2, cx + 7, 157 - (i % 2) * 2], fill=CARD, outline=BRASS, width=2)
    return im, d


def draw_logo(d, x, y):
    d.text((x, y - 12), cfg.SITE_NAME, font=font(FONT_BOLD, 40), fill=INK)


def render_default():
    im, d = base_canvas()
    draw_logo(d, 100, 110)
    y = 200
    for line in wrap_jp(cfg.HERO_TITLE, 18):
        d.text((100, y), line, font=font(FONT_BOLD, 52), fill=INK)
        y += 72
    y += 10
    for line in wrap_jp("税込希望小売価格（改定日つき）・仕様・付属品・隣接型番の差分を、出典URLと確認日つきで。", 34):
        d.text((100, y), line, font=font(FONT_REG, 26), fill=INK_SOFT)
        y += 40
    d.text((100, H - 110), "メーカー公式・正規代理店・公式カタログだけを出典に　／　未公表の項目は「メーカー未記載」", font=font(FONT_REG, 22), fill=BRASS)
    return im


def render_article(a: dict):
    im, d = base_canvas()
    draw_logo(d, 100, 92)
    cat = cfg.CATEGORY_LABELS[a["category"]]
    bf = font(FONT_BOLD, 22)
    bw = d.textlength(cat, font=bf)
    d.rounded_rectangle([100, 166, 100 + bw + 28, 204], radius=6, fill=WASH, outline=DEEP, width=2)
    d.text((114, 170), cat, font=bf, fill=DEEP)
    y = 232
    lines = wrap_jp(a["title_h1"], 20)[:3]
    size = 50 if len(lines) <= 2 else 42
    for line in lines:
        d.text((100, y), line, font=font(FONT_BOLD, size), fill=INK)
        y += int(size * 1.35)
    d.text((100, H - 130), "出典：メーカー公式ページ・正規代理店・公式カタログ（確認日つき）", font=font(FONT_REG, 20), fill=INK_SOFT)
    stamp = a["checked"].replace("-", ".") + " 確認"
    sf = font(FONT_REG, 20)
    sw = d.textlength(stamp, font=sf)
    d.rounded_rectangle([W - 100 - sw - 24, H - 112, W - 100, H - 76], radius=6, fill=WASH, outline=DEEP, width=2)
    d.text((W - 100 - sw - 12, H - 106), stamp, font=sf, fill=DEEP)
    return im


def render_icon(size: int):
    """ロゴSVGと同じ図形（ベルの輪郭＋音孔）をPNG化。"""
    im = Image.new("RGB", (size, size), PAPER)
    d = ImageDraw.Draw(im)
    s = size / 28.0
    d.polygon([(3 * s, 13.5 * s), (14 * s, 13.5 * s), (21 * s, 6.5 * s), (21 * s, 21.5 * s), (14 * s, 13.5 * s)],
              fill=CARD, outline=BRASS)
    d.line([(3 * s, 13.5 * s), (14 * s, 13.5 * s)], fill=BRASS, width=max(2, int(1.6 * s)))
    d.line([(14 * s, 13.5 * s), (21 * s, 6.5 * s)], fill=BRASS, width=max(2, int(1.6 * s)))
    d.line([(14 * s, 13.5 * s), (21 * s, 21.5 * s)], fill=BRASS, width=max(2, int(1.6 * s)))
    d.line([(21 * s, 6.5 * s), (21 * s, 21.5 * s)], fill=BRASS, width=max(2, int(1.6 * s)))
    for cx in (6.5, 10):
        d.ellipse([(cx - 1.2) * s, 12.3 * s, (cx + 1.2) * s, 14.7 * s], fill=BRASS)
    return im


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    render_default().save(OUT / "default.png", optimize=True)
    for a in ARTICLES:
        render_article(a).save(OUT / f"{a['slug']}.png", optimize=True)
    keep = {f"{a['slug']}.png" for a in ARTICLES} | {"default.png"}
    for p in OUT.glob("*.png"):
        if p.name not in keep:
            p.unlink()
    render_icon(180).save(SITE / "assets" / "apple-touch-icon.png", optimize=True)
    render_icon(512).save(SITE / "assets" / "icon-512.png", optimize=True)
    print(f"OG画像 {len(ARTICLES) + 1} 枚＋アイコン2枚を生成（assets/）")


if __name__ == "__main__":
    main()
