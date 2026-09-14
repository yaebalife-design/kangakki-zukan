# -*- coding: utf-8 -*-
"""価格ラダー（税込希望小売価格の階段図）と価格レンジ図の自作SVG。

  ・数値は全て kangakki_db の msrp（メーカー・正規代理店の公表値）。定価の無い型番は図に載せず、件数だけ添える
  ・横軸は対数（¥3万〜¥600万を1本の軸に載せるため）。目盛りは ¥5万／10万／20万／50万／100万／200万／500万
  ・実機は描かない。図形は棒と点だけ
"""
import itertools
import math

import kangakki_db as db
from render import esc

BRAND_COLORS = {
    "yamaha": "#6A3D9A", "yanagisawa": "#1F6F8B", "selmer": "#B03A2E", "jupiter": "#2E7D32", "cannonball": "#37474F",
    "antigua": "#C77D00", "bach": "#8A5A17", "jmichael": "#5C6BC0", "kaerntner": "#AD1457", "chateau": "#00838F",
    "forestone": "#558B2F", "pmauriat": "#6D4C41", "rampone": "#7B1FA2", "playtech": "#9E9E9E", "buffet": "#1565C0",
    "festi": "#EF6C00", "marcato": "#00695C", "soleil": "#C9A227", "eastman": "#455A64",
}
INK, SOFT, LINE, WASH, BRASS, DEEP = "#2A2620", "#6B6258", "#E3DCD0", "#F7F0E2", "#8A5A17", "#5C3A0C"
FONT = 'font-family="Zen Kaku Gothic New,Hiragino Kaku Gothic ProN,Yu Gothic,sans-serif"'
TICKS = [50_000, 100_000, 200_000, 500_000, 1_000_000, 2_000_000, 5_000_000]


def color(bk: str) -> str:
    return BRAND_COLORS.get(bk, "#777777")


def _yen(v: int) -> str:
    if v >= 10_000 and v % 10_000 == 0:
        return f"{v // 10_000}万"
    if v >= 10_000:
        return f"{v / 10_000:.1f}万".replace(".0万", "万")
    return f"{v:,}"


def _scale(prices: list, x0: float, x1: float):
    lo = min(prices) * 0.85
    hi = max(prices) * 1.15
    if hi / lo < 1.6:          # 範囲が狭いときも目盛りが読めるように広げる
        lo, hi = lo / 1.3, hi * 1.3
    llo, lhi = math.log10(lo), math.log10(hi)

    def x(p):
        return x0 + (math.log10(p) - llo) / (lhi - llo) * (x1 - x0)
    return x, lo, hi


def _axis(x, lo, hi, y, x0, x1, label=True) -> str:
    out = [f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="{LINE}" stroke-width="1.5"/>']
    for t in TICKS:
        if lo <= t <= hi:
            out.append(f'<line x1="{x(t):.1f}" y1="{y - 4}" x2="{x(t):.1f}" y2="{y + 4}" stroke="{SOFT}" stroke-width="1"/>')
            if label:
                out.append(f'<text x="{x(t):.1f}" y="{y + 18}" font-size="11" fill="{SOFT}" text-anchor="middle" {FONT}>¥{_yen(t)}</text>')
    return "".join(out)


def _hex_mix(c: str, t: float, to: str = "#FFFFFF") -> str:
    """c と to を t（0〜1）で混ぜる。棒のグラデーション用。"""
    a = [int(c[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(to[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02X%02X%02X" % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


_SEQ = itertools.count(1)      # 1ページに複数のSVGが載るのでidを一意にする


def lineup_ladder(rows: list, prefix: str = "", me: str = "", caption: str = "", width: int = 720) -> str:
    """同ブランド・同楽器種の型番を定価順に並べた「階段」図。棒の先端を階段状の線でつなぎ、グレードの段差が読める。
    me の型番（複数可）を強調。定価の無い型番は下に件数だけ。"""
    priced = [m for m in rows if m["msrp_kind"] == "price"]
    n_np = len(rows) - len(priced)
    if not priced:
        return ""
    priced = sorted(priced, key=lambda m: m["msrp"])
    mes = ({me} if me else set()) if isinstance(me, str) else set(me or [])
    # 右端のラベル（¥価格＋（+差額））が切れないよう、最長ラベルの推定幅ぶん棒の最大長を詰める
    steps = [priced[i]["msrp"] - priced[i - 1]["msrp"] for i in range(1, len(priced))]
    lab = 7.2 * len(f"¥{priced[-1]['msrp']:,}") + (6.4 * len(f"（+¥{max(steps):,}）") if steps else 0)
    x0, x1 = 190, width - max(96, int(lab) + 24)
    x, lo, hi = _scale([m["msrp"] for m in priced], x0, x1)
    rh = 30
    top = 40
    h = top + rh * len(priced) + 36
    uid = f"ld{next(_SEQ)}-" + (sorted(mes)[0] if mes else priced[0]["slug"])
    bk = priced[0]["brand_key"]
    c = color(bk)
    parts = [f'<svg viewBox="0 0 {width} {h}" role="img" aria-labelledby="{uid}-t" class="ladder">',
             f'<title id="{uid}-t">{esc(caption or "税込希望小売価格の階段図")}</title>',
             f'<defs><linearGradient id="{uid}-g" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="{_hex_mix(c, .35)}"/><stop offset="1" stop-color="{c}"/></linearGradient>'
             f'<linearGradient id="{uid}-m" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="#E6B85C"/><stop offset="1" stop-color="{BRASS}"/></linearGradient></defs>',
             f'<rect class="bg" width="{width}" height="{h}" fill="#FFFFFF" rx="12"/>']
    for t in TICKS:
        if lo <= t <= hi:
            parts.append(f'<line x1="{x(t):.1f}" y1="{top - 8}" x2="{x(t):.1f}" y2="{h - 24}" stroke="{LINE}" stroke-width="1" stroke-dasharray="2 5"/>'
                         f'<text x="{x(t):.1f}" y="{top - 14}" font-size="11" fill="{SOFT}" text-anchor="middle" {FONT}>¥{_yen(t)}</text>')
    # 階段の輪郭（棒の先端をつなぐ段差の線）
    pts = []
    for i, m in enumerate(priced):
        y = top + rh * i
        xe = x(m["msrp"])
        pts.append(f"{xe:.1f},{y + 3:.1f}")
        pts.append(f"{xe:.1f},{y + rh - 3:.1f}")
    parts.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{c}" stroke-width="1.5" opacity=".35" stroke-linejoin="round"/>')
    for i, m in enumerate(priced):
        y = top + rh * i + rh / 2
        is_me = m["slug"] in mes
        name = m["name"] if len(m["name"]) <= 16 else m["name"][:15] + "…"
        href = f'{prefix}models/{m["slug"]}.html'
        if i % 2 == 0:
            parts.append(f'<rect x="8" y="{y - rh / 2}" width="{width - 16}" height="{rh}" rx="6" fill="{WASH}" opacity=".45"/>')
        if is_me:
            parts.append(f'<rect x="8" y="{y - rh / 2 + 1}" width="{width - 16}" height="{rh - 2}" rx="6" fill="{WASH}" stroke="{BRASS}" stroke-width="1.2"/>')
        step = "" if i == 0 else f' <tspan fill="{SOFT}" font-size="10.5">（+¥{m["msrp"] - priced[i - 1]["msrp"]:,}）</tspan>'
        ser = db.txt(m, "series")
        parts.append(f'<a href="{esc(href)}"><title>{esc(m["name"])} 税込 ¥{m["msrp"]:,}（{esc(ser) if not ser.startswith("—") else "シリーズ名未記載"}）</title>'
                     f'<rect x="8" y="{y - rh / 2}" width="{width - 16}" height="{rh}" fill="transparent"/>'
                     f'<text x="{x0 - 12}" y="{y + 4}" font-size="12.5" fill="{DEEP if is_me else INK}" text-anchor="end" font-weight="{"bold" if is_me else "500"}" {FONT}>{esc(name)}</text>'
                     f'<rect class="bar" x="{x0}" y="{y - 8}" width="{max(x(m["msrp"]) - x0, 3):.1f}" height="16" rx="8" fill="url(#{uid}-{"m" if is_me else "g"})"/>'
                     f'<circle cx="{x(m["msrp"]):.1f}" cy="{y}" r="{6 if is_me else 4.5}" fill="#FFFFFF" stroke="{BRASS if is_me else c}" stroke-width="2"/>'
                     f'<text x="{x(m["msrp"]) + 12:.1f}" y="{y + 4}" font-size="12" fill="{INK}" font-weight="{"bold" if is_me else "600"}" {FONT}>¥{m["msrp"]:,}{step}</text></a>')
    foot = f'定価あり {len(priced)} 型番・括弧は1つ下との定価差' + (f'／オープン価格・時価・未記載の {n_np} 型番は図に載せていません' if n_np else "")
    parts.append(f'<text x="{x0}" y="{h - 8}" font-size="11" fill="{SOFT}" {FONT}>{esc(foot)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def constellation(rows: list, prefix: str = "", width: int = 560) -> str:
    """ヒーロー用：現行の全型番を 楽器種（行）×税込希望小売価格（対数軸）に散らした星図。ブランド色の点、押すと型番ページ。
    データベースの全体像（どの楽器種がどの価格帯に何型番あるか）を1枚で見せる。"""
    priced = [m for m in rows if m["msrp_kind"] == "price"]
    groups = [g for g, *_ in db.INSTRUMENT_GROUPS if any(m["group_key"] == g for m in priced)]
    x0, x1 = 142, width - 16
    x, lo, hi = _scale([m["msrp"] for m in priced], x0, x1)
    rh = 30
    top = 34
    h = top + rh * len(groups) + 48
    brands = sorted({m["brand_key"] for m in priced}, key=lambda k: -sum(1 for m in priced if m["brand_key"] == k))
    bidx = {bk: i for i, bk in enumerate(brands)}
    cid = f"cs{next(_SEQ)}"
    parts = [f'<svg viewBox="0 0 {width} {h}" role="img" aria-labelledby="{cid}-t" class="constellation">',
             f'<title id="{cid}-t">現行{len(priced)}型番を楽器種と税込希望小売価格で散らした図（点がブランド色の型番）</title>',
             ]
    for t in TICKS:
        if lo <= t <= hi:
            parts.append(f'<line x1="{x(t):.1f}" y1="{top - 6}" x2="{x(t):.1f}" y2="{h - 34}" stroke="#F5EEDF" stroke-width="1" opacity=".18"/>'
                         f'<text x="{x(t):.1f}" y="{top - 12}" font-size="11" fill="#E6CFA0" text-anchor="middle" {FONT}>¥{_yen(t)}</text>')
    k = 0
    for gi, g in enumerate(groups):
        y = top + rh * gi + rh / 2
        gm = [m for m in priced if m["group_key"] == g]
        parts.append(f'<a href="{prefix}instruments/{g}.html"><title>{esc(db.GROUP_LABEL[g])} {len(gm)}型番</title>'
                     f'<text x="{x0 - 10}" y="{y + 4}" font-size="12" fill="#F5EEDF" text-anchor="end" {FONT}>{esc(db.GROUP_LABEL[g])}</text></a>')
        parts.append(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="#F5EEDF" stroke-width="1" opacity=".10"/>')
        for m in sorted(gm, key=lambda m: m["msrp"]):
            # 同じ価格の点が重ならないよう、ブランドごとに行内で少し上下にずらす
            jit = ((bidx[m["brand_key"]] * 7) % 11 - 5) * 1.6
            parts.append(f'<a href="{prefix}models/{esc(m["slug"])}.html" class="cs-a" style="--i:{k}"><title>{esc(m["brand_label"])} {esc(m["name"])} 税込 ¥{m["msrp"]:,}</title>'
                         f'<circle cx="{x(m["msrp"]):.1f}" cy="{y + jit:.1f}" r="3" fill="{_hex_mix(color(m["brand_key"]), .3)}" stroke="#22150A" stroke-width=".8"/></a>')
            k += 1
    # 凡例（上位6ブランド）
    lx = 16
    ly = h - 12
    for bk in brands:
        lab = db.BRANDS[bk]["label"]
        w = 12 + 11.5 * len(lab) + 16
        if lx + w > width - 8:
            break
        parts.append(f'<circle cx="{lx + 4}" cy="{ly - 4}" r="4" fill="{_hex_mix(color(bk), .35)}"/>'
                     f'<text x="{lx + 12}" y="{ly}" font-size="11" fill="#E9DCC3" {FONT}>{esc(lab)}</text>')
        lx += w
    parts.append("</svg>")
    return "".join(parts)


def brand_strip(rows: list, prefix: str = "", width: int = 720, group_key: str = "") -> str:
    """楽器種内のブランドごとの価格レンジ（最低〜最高の線＋各型番の点）。"""
    priced = [m for m in rows if m["msrp_kind"] == "price"]
    if not priced:
        return ""
    by = {}
    for m in priced:
        by.setdefault(m["brand_key"], []).append(m)
    brands = sorted(by, key=lambda k: min(x["msrp"] for x in by[k]))
    x0, x1 = 170, width - 24
    x, lo, hi = _scale([m["msrp"] for m in priced], x0, x1)
    rh = 30
    top = 34
    h = top + rh * len(brands) + 30
    parts = [f'<svg viewBox="0 0 {width} {h}" role="img" aria-labelledby="bs-{group_key}-t" class="ladder strip">',
             f'<title id="bs-{group_key}-t">ブランド別の税込希望小売価格のレンジ（点が各型番）</title>',
             f'<rect class="bg" width="{width}" height="{h}" fill="#FFFFFF" rx="10"/>']
    for t in TICKS:
        if lo <= t <= hi:
            parts.append(f'<line x1="{x(t):.1f}" y1="{top - 6}" x2="{x(t):.1f}" y2="{h - 26}" stroke="{LINE}" stroke-width="1" stroke-dasharray="3 4"/>'
                         f'<text x="{x(t):.1f}" y="{top - 12}" font-size="11" fill="{SOFT}" text-anchor="middle" {FONT}>¥{_yen(t)}</text>')
    for i, bk in enumerate(brands):
        ms = sorted(by[bk], key=lambda m: m["msrp"])
        y = top + rh * i + rh / 2
        c = color(bk)
        label = db.BRANDS[bk]["label"]
        href = f'{prefix}instruments/{group_key}.html#b-{bk}' if group_key else f'{prefix}brands.html#bk-{bk}'
        parts.append(f'<a href="{esc(href)}"><title>{esc(label)}：{len(ms)}型番 ¥{ms[0]["msrp"]:,}〜¥{ms[-1]["msrp"]:,}</title>'
                     f'<text x="{x0 - 10}" y="{y + 4}" font-size="12.5" fill="{INK}" text-anchor="end" {FONT}>{esc(label)} <tspan fill="{SOFT}" font-size="11">{len(ms)}</tspan></text>'
                     f'<line x1="{x(ms[0]["msrp"]):.1f}" y1="{y}" x2="{x(ms[-1]["msrp"]):.1f}" y2="{y}" stroke="{c}" stroke-width="3" opacity=".35" stroke-linecap="round"/></a>')
        for m in ms:
            parts.append(f'<a href="{prefix}models/{esc(m["slug"])}.html"><title>{esc(m["name"])} 税込 ¥{m["msrp"]:,}</title>'
                         f'<circle cx="{x(m["msrp"]):.1f}" cy="{y}" r="4.5" fill="{c}" stroke="#FFFFFF" stroke-width="1.2"/></a>')
    n_np = len(rows) - len(priced)
    foot = f'点＝各型番の税込希望小売価格（{len(priced)}型番）' + (f'。オープン価格・時価・未記載の {n_np} 型番は載せていません' if n_np else "")
    parts.append(f'<text x="{x0}" y="{h - 8}" font-size="11" fill="{SOFT}" {FONT}>{esc(foot)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def position_strip(rows: list, me: dict, prefix: str = "", width: int = 720) -> str:
    """型番ページ用：同ブランド・同楽器種の定価の並びの中で、この型番がどこにいるか（1本の軸に点）。"""
    priced = sorted([m for m in rows if m["msrp_kind"] == "price"], key=lambda m: m["msrp"])
    if len(priced) < 2 or me["msrp_kind"] != "price" or not any(m["slug"] == me["slug"] for m in priced):
        return ""
    x0, x1 = 24, width - 24
    x, lo, hi = _scale([m["msrp"] for m in priced], x0, x1)
    h = 118
    y = 64
    c = color(me["brand_key"])
    parts = [f'<svg viewBox="0 0 {width} {h}" role="img" aria-labelledby="ps-t" class="ladder strip">',
             f'<title id="ps-t">{esc(me["brand_label"])} {esc(me["instrument_label"])} 現行{len(priced)}型番の税込希望小売価格の並びと、この型番の位置</title>',
             f'<rect class="bg" width="{width}" height="{h}" fill="#FFFFFF" rx="10"/>', _axis(x, lo, hi, y, x0, x1, label=True)]
    idx = next(i for i, m in enumerate(priced) if m["slug"] == me["slug"])
    for i, m in enumerate(priced):
        is_me = m["slug"] == me["slug"]
        parts.append(f'<a href="{prefix}models/{esc(m["slug"])}.html"><title>{esc(m["name"])} 税込 ¥{m["msrp"]:,}</title>'
                     f'<circle cx="{x(m["msrp"]):.1f}" cy="{y}" r="{9 if is_me else 5}" fill="{BRASS if is_me else c}" stroke="#FFFFFF" stroke-width="1.5"/></a>')
    # 自分と両隣のラベル
    for j, anchor in ((idx - 1, "end"), (idx, "middle"), (idx + 1, "start")):
        if 0 <= j < len(priced):
            m = priced[j]
            yy = 34 if j == idx else 30
            parts.append(f'<text x="{x(m["msrp"]):.1f}" y="{yy}" font-size="{12.5 if j == idx else 11}" font-weight="{"bold" if j == idx else "normal"}" fill="{DEEP if j == idx else SOFT}" text-anchor="{anchor}" {FONT}>{esc(m["name"])} ¥{m["msrp"]:,}</text>')
    parts.append(f'<text x="{x0}" y="{h - 8}" font-size="11" fill="{SOFT}" {FONT}>{esc(me["brand_label"])}の{esc(me["instrument_label"])}・現行{len(priced)}型番（定価あり）を安い順に。大きい点がこの型番、両隣が1つ下・1つ上の型番。</text>')
    parts.append("</svg>")
    return "".join(parts)


def fig(svg: str, caption: str) -> str:
    if not svg:
        return ""
    return f'<figure class="fig ladderfig">\n  <p class="scrollhint fighint">図は横にスクロールできます。</p>\n{svg}\n  <figcaption>{caption}</figcaption>\n</figure>'
