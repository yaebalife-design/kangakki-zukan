# -*- coding: utf-8 -*-
"""記事・固定ページに埋める自作SVG図解（管楽器図鑑）。

  ・図は「仕様表の項目がどこの寸法・部位を指すか」を示す模式図。実機の外観は描かない（絶対ルール8）
  ・文字は図の外側（余白）か専用の帯に置き、線や図形と重ねない
  ・viewBox は 720 幅で統一。文字サイズは 14〜18（モバイルでも読める）
"""

BRASS = "#8A5A17"
DEEP = "#5C3A0C"
INK = "#2A2620"
SOFT = "#6B6258"
LINE = "#E3DCD0"
WASH = "#F7F0E2"
GOLD = "#E6B85C"
FONT = 'font-family="Zen Kaku Gothic New,Hiragino Kaku Gothic ProN,Yu Gothic,sans-serif"'


def _fig(svg: str, caption: str) -> str:
    hint = '  <p class="scrollhint fighint">図は横にスクロールできます。</p>\n'
    return f'<figure class="fig">\n{hint}{svg}\n  <figcaption>{caption}</figcaption>\n</figure>'


def _t(x, y, s, size=15, fill=INK, anchor="start", weight="normal"):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" {FONT}>{s}</text>'


def _arrow_defs(uid, color=BRASS):
    return (f'<defs><marker id="{uid}" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto">'
            f'<path d="M0 0 L10 5 L0 10 z" fill="{color}"/></marker></defs>')


def brass_terms() -> str:
    """金管の仕様表の項目（ベル径・ボア・マウスピース・仕上げ）がどこを指すかの模式図。"""
    svg = f'''  <svg viewBox="0 0 720 380" role="img" aria-labelledby="fig-br-t">
    <title id="fig-br-t">金管楽器の仕様表の項目が指す部位（模式図）</title>
    {_arrow_defs("ar-br")}
    <rect width="720" height="380" fill="#FFFFFF"/>
    <!-- 管（直管の模式） -->
    <path d="M80 190 h330" stroke="{BRASS}" stroke-width="22" stroke-linecap="round"/>
    <path d="M80 190 h330" stroke="{WASH}" stroke-width="10" stroke-linecap="round"/>
    <!-- ベル -->
    <path d="M410 179 q120 -6 170 -70 v162 q-50 -64 -170 -70 z" fill="{WASH}" stroke="{BRASS}" stroke-width="2.5"/>
    <!-- マウスピース -->
    <path d="M40 182 h40 v16 h-40 q-14 0 -14 -8 q0 -8 14 -8 z" fill="#FFFFFF" stroke="{BRASS}" stroke-width="2.5"/>
    <!-- ベル径 -->
    <path d="M600 109 v162" stroke="{DEEP}" stroke-width="2" marker-start="url(#ar-br)" marker-end="url(#ar-br)"/>
    {_t(614, 186, "ベル径", 16, DEEP, "start", "bold")}
    {_t(614, 206, "ベルの開口部の直径（mm）", 13, SOFT)}
    <!-- ボア -->
    <path d="M250 179 v22" stroke="{DEEP}" stroke-width="2" marker-start="url(#ar-br)" marker-end="url(#ar-br)"/>
    {_t(250, 250, "ボア", 16, DEEP, "middle", "bold")}
    {_t(250, 270, "管の内径。ML／L のような記号か mm 表記", 13, SOFT, "middle")}
    <!-- マウスピース -->
    {_t(60, 140, "付属マウスピース", 15, DEEP, "middle", "bold")}
    {_t(60, 158, "付属品欄に型番", 13, SOFT, "middle")}
    <!-- 仕上げ -->
    {_t(470, 340, "仕上げ＝表面処理（ラッカー／銀メッキ／金メッキ など）", 14, INK, "middle")}
    {_t(470, 360, "ベル材質＝ベル部分の金属（イエローブラス／ゴールドブラス など）", 14, INK, "middle")}
  </svg>'''
    return _fig(svg, "金管楽器の仕様表でよく出る項目が指す部位。当サイトの「ベル径」「ボア」「仕上げ」「ベル材質」「付属マウスピース」は、"
                     "メーカー・正規代理店の仕様表の表記をそのまま転記しています（記号・単位もメーカー表記のまま）。")


def woodwind_terms() -> str:
    """木管（サックス・フルート）の仕様表の項目（キイシステム・ネック・調子・付属品）の模式図。"""
    svg = f'''  <svg viewBox="0 0 720 380" role="img" aria-labelledby="fig-ww-t">
    <title id="fig-ww-t">木管楽器の仕様表の項目が指す部位（模式図）</title>
    {_arrow_defs("ar-ww")}
    <rect width="720" height="380" fill="#FFFFFF"/>
    <!-- 管体（直管の模式・音孔の列） -->
    <rect x="120" y="170" width="440" height="40" rx="20" fill="{WASH}" stroke="{BRASS}" stroke-width="2.5"/>
    {"".join(f'<circle cx="{170 + i * 48}" cy="190" r="9" fill="#FFFFFF" stroke="{BRASS}" stroke-width="2"/>' for i in range(8))}
    {"".join(f'<circle cx="{170 + i * 48}" cy="190" r="4" fill="{BRASS}" opacity=".35"/>' for i in range(8))}
    <!-- ネック -->
    <path d="M120 190 q-40 0 -60 -40" stroke="{BRASS}" stroke-width="14" fill="none" stroke-linecap="round"/>
    <path d="M120 190 q-40 0 -60 -40" stroke="{WASH}" stroke-width="6" fill="none" stroke-linecap="round"/>
    {_t(60, 120, "ネック", 16, DEEP, "middle", "bold")}
    {_t(60, 138, "ネックの仕様・共通ネック", 13, SOFT, "middle")}
    <!-- キイ -->
    <path d="M300 140 v20" stroke="{DEEP}" stroke-width="2" marker-end="url(#ar-ww)"/>
    {_t(300, 128, "キイ（音孔をふさぐ部品）", 15, DEEP, "middle", "bold")}
    {_t(300, 110, "キイシステム＝キイの配置・機構の方式（カバード／リング、Eメカ など）", 13, SOFT, "middle")}
    <!-- 調子 -->
    {_t(340, 270, "調子＝楽器の基準音（E♭・B♭・C など）", 15, INK, "middle")}
    {_t(340, 292, "同じサックスでもアルトは E♭、テナーは B♭", 13, SOFT, "middle")}
    <!-- 付属品 -->
    <rect x="480" y="300" width="200" height="56" rx="8" fill="{WASH}" stroke="{LINE}"/>
    {_t(580, 324, "付属品", 15, DEEP, "middle", "bold")}
    {_t(580, 344, "ケース・マウスピース・ストラップ等", 13, SOFT, "middle")}
    {_t(120, 340, "管体材質＝管の金属や木材（ブラス／洋白／銀 など）", 14, INK)}
    {_t(120, 360, "仕上げ＝表面処理（ラッカー／銀メッキ など）", 14, INK)}
  </svg>'''
    return _fig(svg, "木管楽器（サックス・フルート・クラリネット）の仕様表でよく出る項目が指す部位。"
                     "当サイトの「キイシステム」「ネック」「調子」「管体材質」「仕上げ」「付属品」は、メーカー・正規代理店の仕様表の表記をそのまま転記しています。")


def family_map() -> str:
    """吹奏楽で使う管楽器の分類（木管／金管）と当サイトの楽器種グループの対応図。"""
    wood = ["サックス", "フルート・ピッコロ", "クラリネット", "オーボエ", "ファゴット"]
    brass = ["トランペット", "コルネット", "フリューゲルホルン", "ホルン", "トロンボーン", "ユーフォニアム", "バリトン・アルトホルン", "チューバ"]
    def col(x, title, items, color):
        out = [f'<rect x="{x}" y="60" width="300" height="{40 + 34 * len(items)}" rx="12" fill="{WASH}" stroke="{LINE}"/>',
               _t(x + 150, 88, title, 17, color, "middle", "bold")]
        for i, s in enumerate(items):
            out.append(f'<rect x="{x + 16}" y="{104 + 34 * i}" width="268" height="26" rx="6" fill="#FFFFFF" stroke="{LINE}"/>')
            out.append(_t(x + 150, 122 + 34 * i, s, 14, INK, "middle"))
        return "".join(out)
    svg = f'''  <svg viewBox="0 0 720 400" role="img" aria-labelledby="fig-fm-t">
    <title id="fig-fm-t">吹奏楽で使う管楽器の分類と当サイトの楽器種グループ</title>
    <rect width="720" height="400" fill="#FFFFFF"/>
    {_t(360, 36, "吹奏楽で使う管楽器（当サイトの楽器種グループ）", 16, INK, "middle", "bold")}
    {col(40, "木管楽器", wood, DEEP)}
    {col(380, "金管楽器", brass, BRASS)}
  </svg>'''
    return _fig(svg, "当サイトの楽器種グループ。木管楽器はリードや唇の振動ではなく「木管」という分類上の名前で、サックスは金属製でも木管楽器に分類されます。"
                     "各グループのページに、ブランド横断の現行型番と税込希望小売価格の一覧があります。")


FIGURES = {
    "brass_terms": brass_terms,
    "woodwind_terms": woodwind_terms,
    "family_map": family_map,
}


def render(key: str) -> str:
    return FIGURES[key]()
