# -*- coding: utf-8 -*-
"""管楽器図鑑 全ページの品質チェック。生成後に必ず通すこと。

スキマー図鑑の qa_site.py を土台に、NGリストを「音の断定・実証不能な比較・No.1・最安・後継の断定・レビュー転載」へ差し替えた
（ローカルCLAUDE.md 絶対ルール2／執筆ルール§2）。

  ① NG_HARD 検出 = エラー（公開不可）
  ② NG_WARN 検出 = 要レビュー一覧
  ③ 内部リンク切れ = エラー
  ④ 必須常設表記 = エラー（PR表記／各メーカーと無関係／価格の注記／表のあるページの「メーカー未記載」の説明）
  ⑤ FAQPage JSON-LD の設問数 == 表示FAQ数 = エラー
  ⑥ 数値段落（¥）に出典の言及があるか = 要レビュー（記事のみ）
  ⑦ href="#" 検出 = エラー
  ⑧ title / description / canonical / OGP / viewport 欠落 = エラー
  ⑨ 「メーカー未記載」セル率：記事の表で25%超 = 要レビュー
  ⑩ 空セル = エラー
  ⑪ Amazonリンクの整合：USE_AMAZON=False でリンクがある／リンクがあるページに規約5条文言が無い = エラー
  ⑫ もしも・A8リンクの整合：SHOW_AFFILIATE_LINKS=False でリンクがある = エラー
  ⑬ 楽天・Amazonのレビュー転載・出品件数の転記 = エラー
"""
import collections
import json
import re
import sys
from pathlib import Path
from urllib.parse import urldefrag

TOOLS = Path(__file__).parent
SITE = TOOLS.parent / "site"
sys.path.insert(0, str(TOOLS))

import site_config as cfg
import kangakki_db as db

NG_HARD = [  # 検出=公開不可（執筆ルール§2 NG_HARD）
    r"音が(良|よ|い)い", r"音色が(美し|良|よ)", r"鳴りやすい", r"吹きやすい", r"響きが豊か", r"音が(太|明る|暗|柔らか)",
    r"初心者に最適", r"プロ御用達", r"プロ仕様", r"最強", r"完璧", r"間違いな", r"No\.?1", r"日本一", r"世界一",
    r"買うべき", r"損しな", r"今すぐ", r"迷ったらこれ", r"これを買えば", r"絶対",
    r"上達(が早|しやすい)", r"上手くな", r"うまくな",
    # 「鳴りやすさ・吹きやすさ・上達しやすさは書きません」の方針文は POLICY_OK で先に除く。断定形（〜やすい）だけ止める
    # 最安（当サイトの実測値に「実売の最安値＋店＋確認日」の形で付けるのは可）
    r"(業界|国内|日本|ネット|通販|地域)最安", r"最安(で|です|！|!|保証)", r"最安値(で|です|！|!|保証|宣言)",
    # レビュー転載・伝聞
    r"みんなのレビュー", r"レビューによる", r"レビューでは", r"口コミ(では|による|で[はも])", r"評判(が|は)(良|高)",
    r"星\d(つ|\.)", r"評価\d\.\d",
    # 煽り
    r"プレミア", r"値上がり", r"今すぐ買わないと", r"二度と手に入らない", r"最後のチャンス", r"転売",
]
# 当サイトの方針文（否定形）。NG語を含むが断定ではないので、検査の前に本文から除く
POLICY_OK = [
    "音の良し悪し・吹きやすさ・上達しやすさは実証できないため書きません", "音の良し悪し・吹きやすさ・上達しやすさは判断しません",
    "音の良し悪しや吹きやすさは扱いません", "音の良し悪し・吹きやすさは当サイトでは扱いません", "音の良し悪し・吹きやすさを書きません",
    "音色・鳴りやすさ・吹きやすさ・上達しやすさは実証できないため書きません", "鳴りやすさ・吹きやすさ・上達しやすさ",
]
NG_WARN = [  # 検出=人間レビュー（メーカー表記の引用・否定文なら可）
    r"おすすめ", r"人気", r"定番", r"上位機種", r"入門機", r"(?<!「)後継(?!」)", r"同じ音", r"違いは無い", r"違いはない",
    r"高音質", r"高級", r"コスパ", r"お得", r"安い(?!順)", r"高い(です|と)", r"軽い", r"重い",
    r"といわれて", r"と言われて", r"という声", r"らしい", r"ようです", r"と思われ", r"と考えられ",
    r"最適", r"ぴったり", r"ベスト", r"大丈夫", r"問題(ない|あり)", r"安心",
]

REQUIRED_ALL_PAGES = [
    ("PR表記", cfg.NOTICE_PR),
    ("メーカー無関係表記", "当サイトは各メーカー・楽器店・買取業者とは無関係の情報サイトです。"),
    ("価格の注記", cfg.NOTICE_PRICE),
]
NA_WARN_RATE = 0.25

# 社内メモ語（kangakki_db.MEMO_WORDS が正）＋ 販売店の内部商品コード。本文に出ていたらエラー
MEMO_RE = "|".join([re.escape(w) for w in db.MEMO_WORDS if w not in ("None", "null")] + [r"\(\d{8,}\)", r"（\d{8,}）"])


def visible_text(h: str) -> str:
    t = re.sub(r"<!--[\s\S]*?-->", " ", h)
    t = re.sub(r"<script[\s\S]*?</script>", " ", t)
    t = re.sub(r"<style[\s\S]*?</style>", " ", t)
    t = re.sub(r"<svg[\s\S]*?</svg>", " ", t)
    t = re.sub(r"<[^>]+>", "", t)
    for m in re.finditer(r'<meta[^>]+content="([^"]*)"', h):
        t += " " + m.group(1)
    return t


def faq_jsonld_count(h: str):
    for m in re.finditer(r'<script type="application/ld\+json">([\s\S]*?)</script>', h):
        try:
            d = json.loads(m.group(1))
        except json.JSONDecodeError:
            return -1
        if isinstance(d, dict) and d.get("@type") == "FAQPage":
            return len(d.get("mainEntity", []))
    return None


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if not SITE.exists():
        print("🔴 site/ が存在しない。先に build.py を実行すること")
        return 1

    files = sorted(SITE.rglob("*.html"))
    errors, warns = [], []
    existing = {p.relative_to(SITE).as_posix() for p in SITE.rglob("*") if p.is_file()}
    titles = collections.defaultdict(list)
    descs = collections.defaultdict(list)
    total_bytes = 0
    anchor_cache = {}

    def anchors_of(t: str) -> set:
        if t not in anchor_cache:
            th = (SITE / t).read_text(encoding="utf-8")
            anchor_cache[t] = set(re.findall(r'id="([^"]+)"', th))
        return anchor_cache[t]

    for f in files:
        rel = f.relative_to(SITE).as_posix()
        h = f.read_text(encoding="utf-8")
        total_bytes += len(h.encode("utf-8"))
        is_noindex = bool(re.search(r'<meta name="robots" content="[^"]*noindex', h))
        is_article = rel.startswith("articles/") and rel != "articles/index.html"
        is_model = rel.startswith("models/") and rel != "models/index.html"
        text = visible_text(h)
        for ok in POLICY_OK:
            text = text.replace(ok, " ")
        h_nojs = re.sub(r"<script[\s\S]*?</script>", " ", h)

        for tag in ("html", "head", "body", "main", "header", "footer", "nav", "section", "figure", "table", "thead", "tbody",
                    "tr", "th", "td", "div", "ul", "ol", "li", "a", "details", "summary", "span", "p", "h1", "h2", "h3", "h4", "select", "label"):
            o = len(re.findall(rf"<{tag}[ >]", h_nojs))
            c = len(re.findall(rf"</{tag}>", h_nojs))
            if o != c:
                errors.append(f"{rel}: <{tag}> の開閉が不一致 ({o} vs {c})")

        for pat in NG_HARD:
            for mm in re.finditer(pat, text):
                ctx = " ".join(text[max(0, mm.start() - 40):mm.end() + 40].split())
                errors.append(f"{rel}: 🔴NG_HARD「{mm.group(0)}」 … {ctx[:90]}")
        for mm in re.finditer(r"[🟢🟡✅❌🎯🔴]", text):
            ctx = " ".join(text[max(0, mm.start() - 40):mm.end() + 40].split())
            errors.append(f"{rel}: 社内メモ用の記号「{mm.group(0)}」が本文に出ている … {ctx[:80]}")
        if not is_model:      # 型番ページ906本は同じ定型文なので警告を繰り返さない（記事・固定ページだけ見る）
            for pat in NG_WARN:
                for mm in re.finditer(pat, text):
                    ctx = " ".join(text[max(0, mm.start() - 40):mm.end() + 40].split())
                    warns.append(f"{rel}: NG_WARN「{mm.group(0)}」 … {ctx[:90]}")
        else:                 # 型番ページは、メーカー表記の引用「」の外にある評価語だけを見る（監査 2026-09-10）
            t_noq = re.sub(r"「[^」]*」", " ", text)
            for mm in re.finditer(r"名器|初心者向け|プロ向け|上級者向け|プロ仕様|最高級|極上", t_noq):
                ctx = " ".join(t_noq[max(0, mm.start() - 40):mm.end() + 40].split())
                errors.append(f"{rel}: 🔴 評価語「{mm.group(0)}」が引用「」の外にある … {ctx[:90]}")

        for m in re.finditer(r'href="([^"]+)"', h_nojs):
            href = m.group(1)
            if href.startswith(("http://", "https://", "//", "mailto:", "tel:")):
                continue
            if href == "#":
                errors.append(f'{rel}: 🔴 href="#" のダミーリンク')
                continue
            if href.startswith("#"):
                if not re.search(rf'id="{re.escape(href[1:])}"', h):
                    errors.append(f"{rel}: ページ内アンカー切れ → {href}")
                continue
            path, frag = urldefrag(href)
            path = path.split("?")[0]
            if not path or path == "/":
                continue
            target = ((SITE / path.lstrip("/")) if path.startswith("/") else (f.parent / path)).resolve()
            try:
                t = target.relative_to(SITE.resolve()).as_posix()
            except ValueError:
                errors.append(f"{rel}: site外へのリンク {href}")
                continue
            if t not in existing:
                errors.append(f"{rel}: リンク切れ → {href}")
            elif frag and t.endswith(".html") and frag not in anchors_of(t):
                errors.append(f"{rel}: リンク先のアンカーが無い → {href}")

        for label, phrase in REQUIRED_ALL_PAGES:
            if phrase not in h:
                errors.append(f"{rel}: 必須常設表記なし［{label}］")
        if h.count(cfg.NOTICE_PR) < 2:
            errors.append(f"{rel}: ページ上部のPR表記がない（フッター分しかない。絶対ルール9＝各ページ上部＋フッター）")
        if re.search(r'class="(minitbl|cmp|db)', h) and cfg.NOTICE_NA not in h and ("メーカー未記載" in text or "—（未確認）" in text):
            if rel not in ("data.html", "about.html") and not rel.startswith("category/"):
                errors.append(f"{rel}: 表に「メーカー未記載」があるのに定義の注記（NOTICE_NA）がない")
        for m in re.finditer(r'class="buyrow"', h):
            close = h.find("</div>", m.end())
            start = close + len("</div>") if close != -1 else m.end()
            if cfg.NOTICE_SHOP not in h[start:start + 600] and cfg.NOTICE_KAITORI not in h[start:start + 600]:
                errors.append(f"{rel}: buyrow の直下に価格変動／査定の注記がない")
        for m in re.finditer(r"<(p|li|td)(?:\s[^>]*)?>([\s\S]*?)</\1>", h_nojs):
            ptext = re.sub(r"<[^>]+>", "", m.group(2))
            if re.search(r"(Amazon|楽天)[^。]{0,12}\d+\s*件", ptext):
                errors.append(f"{rel}: 🔴 Amazon・楽天の出品件数が転記されている … {' '.join(ptext.split())[:70]}")
            if re.search(r"(Amazon|楽天)[^。]{0,20}レビュー", ptext) and "引用しません" not in ptext and "転載" not in ptext:
                errors.append(f"{rel}: 🔴 通販サイトのレビューへの言及 … {' '.join(ptext.split())[:70]}")
        for m in re.finditer(r"<td(?:\s[^>]*)?>\s*</td>", h_nojs):
            errors.append(f"{rel}: 空の <td> がある（「—（メーカー未記載）」を出すこと）")
        for m in re.finditer(r'href="([^"]*(review\.rakuten|search\.rakuten)[^"]*)"', h_nojs):
            errors.append(f"{rel}: 🔴 楽天のレビュー／検索結果ページへのリンク → {m.group(1)[:70]}")
        # 社内メモ語は kangakki_db.MEMO_WORDS が正。二重管理をやめ、そこから作る（点検 2026-09-13）
        for mm in re.finditer(MEMO_RE, text):
            ctx = " ".join(text[max(0, mm.start() - 40):mm.end() + 40].split())
            errors.append(f"{rel}: 🔴 社内作業メモが本文に出ている「{mm.group(0)}」 … {ctx[:80]}")
        if "￥" in text:
            warns.append(f"{rel}: 全角「￥」が使われている（半角¥に統一）")

        shown = len(re.findall(r'<details class="faq"', h))
        ld = faq_jsonld_count(h)
        if ld == -1:
            errors.append(f"{rel}: JSON-LD がJSONとして壊れている")
        elif shown and ld is None:
            errors.append(f"{rel}: FAQが{shown}問あるのに FAQPage JSON-LD がない")
        elif ld is not None and ld != shown:
            errors.append(f"{rel}: FAQPage JSON-LD {ld}問 != 表示FAQ {shown}問")

        if is_article:
            h_notoc = re.sub(r'<nav class="toc"[\s\S]*?</nav>', " ", h_nojs)
            for m in re.finditer(r"<(p|li)(?:\s[^>]*)?>([\s\S]*?)</\1>", h_notoc):
                ptext = re.sub(r"<[^>]+>", "", m.group(2))
                if re.search(r"[¥]\s*[\d,]+", ptext) and not re.search(r"確認|出典|公式|カタログ|公表|メーカー|代理店|改定|データベース", ptext):
                    warns.append(f"{rel}: 価格の段落に出典の言及がない … {' '.join(ptext.split())[:70]}")

        mt = re.search(r"<title>([^<]+)</title>", h)
        md = re.search(r'name="description" content="([^"]+)"', h)
        if not mt:
            errors.append(f"{rel}: title がない")
        else:
            titles[mt.group(1)].append(rel)
        if not md and not is_noindex:
            errors.append(f"{rel}: description がない")
        elif md:
            descs[md.group(1)].append(rel)
        if not is_noindex:
            if not re.search(r'rel="canonical"', h):
                errors.append(f"{rel}: canonical がない")
            for og in ("og:title", "og:description", "og:url", "og:site_name", "og:image"):
                if f'property="{og}"' not in h:
                    errors.append(f"{rel}: OGP {og} がない")
            im = re.search(r'property="og:image" content="([^"]+)"', h)
            if im and im.group(1).replace(cfg.BASE_URL + "/", "") not in existing:
                errors.append(f"{rel}: og:image のファイルがない → {im.group(1)}")
        if '<link rel="icon"' not in h:
            errors.append(f"{rel}: favicon リンクがない")
        if mt and mt.group(1).count("｜") != 1:
            errors.append(f"{rel}: title の「｜」が1個でない → {mt.group(1)[:60]}")
        if md and not is_noindex and not (70 <= len(md.group(1)) <= 135) and not is_model:
            warns.append(f"{rel}: description が{len(md.group(1))}字（70〜135字が目安）")
        if md and is_model and not (60 <= len(md.group(1)) <= 140):
            warns.append(f"{rel}: description が{len(md.group(1))}字")
        if not re.search(r'<meta name="viewport"', h):
            errors.append(f"{rel}: viewport がない")
        if '<html lang="ja"' not in h:
            errors.append(f"{rel}: <html lang=\"ja\"> がない")

        text_wo_url = re.sub(r"https?://\S+", " ", text)
        for leak in ("None", "{'", "NaN", "undefined", "nan", "[]"):
            if re.search(rf"(?<![A-Za-z]){re.escape(leak)}(?![A-Za-z])", text_wo_url):
                warns.append(f"{rel}: 「{leak}」がHTMLに出ている")

        # ⑪⑫ アフィリ整合性
        if "af.moshimo.com" in h or "a8.net" in h:
            if not cfg.SHOW_AFFILIATE_LINKS:
                errors.append(f"{rel}: SHOW_AFFILIATE_LINKS=False なのにもしも／A8のリンクがある")
            if "アフィリエイト" not in h:
                errors.append(f"{rel}: アフィリリンクがあるのにPR表記がない")
        has_amazon_link = bool(re.search(r'href="https?://(www\.)?amazon\.co\.jp', h_nojs))
        if has_amazon_link and not cfg.USE_AMAZON:
            errors.append(f"{rel}: USE_AMAZON=False なのにAmazonリンクがある")
        if has_amazon_link and cfg.NOTICE_AMAZON not in h:
            errors.append(f"{rel}: 🔴 Amazonリンクがあるのに規約5条文言（NOTICE_AMAZON）がない")
        if cfg.USE_AMAZON and "tag=" + cfg.AMAZON_TRACKING_ID not in h and has_amazon_link:
            errors.append(f"{rel}: AmazonリンクにこのサイトのトラッキングIDが無い")
        # ⑬ 広告表記と実態の整合（提携前に「広告を含みます」と書かない・点検 2026-09-13）
        has_aff_link = has_amazon_link or "af.moshimo.com" in h or "a8.net" in h
        if "アフィリエイト広告" in text and "含みます" in text and not has_aff_link and not rel.startswith(("disclaimer", "about", "privacy")):
            errors.append(f"{rel}: 🔴 広告リンクが1本も無いのに「アフィリエイト広告を含みます」と書いている")
        if not cfg.USE_AMAZON and cfg.NOTICE_AMAZON in text and "提携" not in text:
            errors.append(f"{rel}: 🔴 提携前なのにAmazon規約5条の文言を断定形で出している")
        # ⑭ 二次情報・未確認の型番ページで「メーカー・正規代理店の公表値」と断定していないか
        if is_model and ("二次情報" in text or "—（未確認）" in text):
            if "数値はメーカー・正規代理店の公表値のまま" in text and "二次情報</span>" in h:
                errors.append(f"{rel}: 🔴 二次情報の型番なのに「メーカー・正規代理店の公表値のまま」と書いている")

        if is_article and 'class="minitbl"' in h:
            cells = re.findall(r"<td(?:\s[^>]*)?>([\s\S]*?)</td>", h_nojs)
            if cells:
                na = sum(1 for c in cells if "メーカー未記載" in c or "—（未確認）" in c)
                if na / len(cells) > NA_WARN_RATE:
                    warns.append(f"{rel}: 表のセルの{na / len(cells):.0%}が「メーカー未記載」（{na}/{len(cells)}・25%超）")

    # 発表済みの価格改定が適用日を過ぎていないか（過ぎたら定価そのものを更新する必要がある）
    import datetime
    today = datetime.date.today().isoformat()
    overdue = [m for m in db.MODELS if (m.get("price_revision") or {}).get("date", "9999") <= today]
    if overdue:
        errors.append(f"🔴 メーカー発表の価格改定日を過ぎた型番が {len(overdue)} 件（例 {overdue[0]['model']}）。"
                      "訂正JSONの msrp_jpy を新価格に置き換え、price_revision を消すこと")

    # ── データ側の検査 ──
    from articles_data import ARTICLES, DRAFTS
    slugs = {a["slug"] for a in ARTICLES} | {d["slug"] for d in DRAFTS}
    if len(slugs) != len(ARTICLES) + len(DRAFTS):
        errors.append("articles_data: slug が重複している")
    try:
        kw_json = json.loads((TOOLS.parent / "ナレッジ" / "KW_20260910.json").read_text(encoding="utf-8"))
        kw_set = set()
        def _walk(x):
            if isinstance(x, dict):
                for k, v in x.items():
                    if k in ("kw", "keyword", "query") and isinstance(v, str):
                        kw_set.add(v.lower())
                    _walk(v)
            elif isinstance(x, list):
                for v in x:
                    _walk(v)
            elif isinstance(x, str):
                kw_set.add(x.lower())
        _walk(kw_json)
    except Exception:
        kw_set = set()
    for a in ARTICLES:
        slug = a["slug"]
        if kw_set and a["kw_main"].lower() not in kw_set:
            warns.append(f"articles/{slug}.html: 主KW「{a['kw_main']}」が KW_20260910.json の実在語に無い（推測KW禁止）")
        kw_tokens = [t for t in re.split(r"[\s　]+", a["kw_main"]) if len(t) >= 2]
        if kw_tokens and not any(t.lower() in a["description"].lower() for t in kw_tokens):
            warns.append(f"articles/{slug}.html: description に主KW（{a['kw_main']}）の語が入っていない")
        if len(a["faqs"]) < 2:
            warns.append(f"articles/{slug}.html: FAQが{len(a['faqs'])}問（2問以上が目安）")
        for ref in a.get("models", []) + a.get("cited_models", []):
            try:
                db.find(*ref)
            except KeyError as e:
                errors.append(f"articles/{slug}.html: {e}")
        if a["category"] not in cfg.CATEGORY_LABELS:
            errors.append(f"articles/{slug}.html: 未知のカテゴリ {a['category']}")

    for k, label in (("key", "調子"), ("finish", "仕上げ"), ("msrp_jpy", "定価")):
        r = db.na_rate(db.CURRENT, [k])
        if r > NA_WARN_RATE:
            warns.append(f"index.html: ハブ表の主要列「{label}」の未記載率 {r:.0%}（25%超）")

    for t, ps in titles.items():
        if len(ps) > 1:
            errors.append(f"title 重複 ({len(ps)}件)「{t[:50]}」→ {', '.join(ps[:4])}")
    for d, ps in descs.items():
        if len(ps) > 1:
            warns.append(f"description 重複 ({len(ps)}件) → {', '.join(ps[:4])}")

    if not cfg.OPERATOR_NAME:
        warns.append("site_config.OPERATOR_NAME が空（公開前に運営者名を確定すること）")
    for name in ("robots.txt", "_headers", "_redirects", "assets/favicon.svg", "assets/apple-touch-icon.png", cfg.LOGO_PNG_PATH, cfg.OG_DEFAULT_PATH):
        if name not in existing:
            errors.append(f"{name} がない（build.py を通すこと）")
    rd = SITE / "_redirects"
    if rd.exists():
        for line in rd.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                dest = parts[1].lstrip("/")
                dest_file = "index.html" if dest == "" else (dest if dest.endswith(".html") else dest + ".html")
                if dest_file not in existing:
                    errors.append(f"_redirects: 転送先が存在しない → {line}")
    sm = SITE / "sitemap.xml"
    if sm.exists():
        smx = sm.read_text(encoding="utf-8")
        if cfg.BASE_URL not in smx:
            errors.append(f"sitemap.xml: BASE_URL({cfg.BASE_URL}) が含まれていない")
        print(f"sitemap.xml: {len(re.findall(r'<loc>', smx))} URL")
    else:
        errors.append("sitemap.xml がない（build.py を通すこと）")
    # 🔴 ID流用の検査：他サイトで使っている既知IDが混ざっていないか（スキマー図鑑のIDを例示）
    for bad in ("G-KN2S5XRMV4", "Fux3s2rROWlkds3o4Z_CkPSW1rCzjCUYebCH5jnbbRk", "5794017", "5795242", "5538619", "5538622", "5637369"):
        if bad in (cfg.GA4_ID, cfg.GSC_VERIFICATION, cfg.MOSHIMO_RAKUTEN.get("a_id"), cfg.MOSHIMO_YAHOO.get("a_id")):
            errors.append(f"🔴 他サイトのID {bad} が site_config に入っている（ID流用禁止・絶対ルール13）")

    print(f"チェック対象 {len(files)} ページ / 合計 {total_bytes / 1024:.1f} KB / SHOW_AFFILIATE_LINKS={cfg.SHOW_AFFILIATE_LINKS} "
          f"/ USE_AMAZON={cfg.USE_AMAZON} / 現行{len(db.CURRENT)}型番")
    print()
    lim = 10 ** 6 if "--all" in sys.argv else 80
    if errors:
        print(f"🔴 エラー {len(errors)}件")
        for e in errors[:lim]:
            print("   ", e)
        if len(errors) > lim:
            print(f"    …ほか{len(errors) - lim}件")
    else:
        print("✅ エラーなし")
    print()
    if warns:
        print(f"⚠️ 要レビュー {len(warns)}件（NG_WARNはメーカー表記の引用・否定文なら可。人間が判断すること）")
        warns.sort(key=lambda w: "NG_WARN" in w)
        for w in warns[:120]:
            print("   ", w)
        if len(warns) > 120:
            print(f"    …ほか{len(warns) - 120}件")
    else:
        print("✅ 要レビューなし")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
