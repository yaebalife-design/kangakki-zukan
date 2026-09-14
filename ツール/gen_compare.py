# -*- coding: utf-8 -*-
"""型番ペア差分ページ（compare/<a>--<b>.html）をDBから生成する。

想定ユースケース（KW_20260910.md §3）：「YAS-280 YAS-380 違い」のように、隣り合うグレードの2型番で何が違うかを知りたい。
  ・対象＝同ブランド・同楽器種の現行型番を税込定価順に並べたときの隣同士（両方に定価がある）＋実在KWのペア
  ・本文は「定価差」「メーカー公表値が違う項目（だけ）」「片方にしか無い付属品」。どちらが良いかは書かない
  ・仕上げ違い（S＝銀メッキ等）で仕様が同じペアは「違いは仕上げと定価だけ」と言い切れる（それも答え）
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import site_config as cfg
import site_chrome as chrome
import kangakki_db as db
import render
import ladder
import catalog
from render import esc

PREFIX = "../"
# ペア需要が実在するブランド（KW班：ヤマハに集中。他は単体型番＋評価／中古で呼ばれる）＋主要9ブランド
PAIR_BRANDS = ("yamaha", "yanagisawa", "selmer", "jupiter", "bach", "buffet", "jmichael", "kaerntner", "antigua", "cannonball")
# 実在KWのペア（KW_20260910.md §3）。隣接でなくても作る
KW_PAIRS = [
    ("yamaha", "YAS-280", "YAS-380"), ("yamaha", "YAS-380", "YAS-480"), ("yamaha", "YAS-480", "YAS-62"),
    ("yamaha", "YTS-380", "YTS-480"), ("yamaha", "YCL-450", "YCL-650"), ("yamaha", "YTR-3335", "YTR-4335GII"),
    # 検索語は「yep-621」「yhr-667」だが、ヤマハ公式の現行一覧にあるのは YEP-621S・YHR-671D（2026-09-14 確認）
    ("yamaha", "YEP-321", "YEP-621S"), ("yamaha", "YEP-621S", "YEP-642S"), ("yamaha", "YHR-314II", "YHR-567"), ("yamaha", "YHR-567", "YHR-671D"),
    ("yamaha", "YFL-212", "YFL-312"), ("yamaha", "YFL-312", "YFL-412"),
    ("yanagisawa", "A-WO1", "A-WO10"), ("yanagisawa", "A-WO2", "A-WO20"), ("yanagisawa", "A-WO1", "A-WO2"),
]


def pair_slug(a: dict, b: dict) -> str:
    return f"{a['slug']}--{b['slug']}"


def _plain(html: str) -> str:
    return " ".join(re.sub(r'<span class="src">.*?</span>', "", html).replace("<br>", "／").replace("<[^>]+>", "").split())


def diff_rows(a: dict, b: dict) -> tuple:
    """(違う項目 [(label, va, vb)], 同じ項目 [label])。値は表示文字列（メーカー表記のまま）。"""
    same, diff = [], []
    for label, fn in render.CMP_ROWS:
        va = re.sub(r"<[^>]+>", "", re.sub(r'<span class="src">.*?</span>', "", fn(a)).replace("<br>", "／"))
        vb = re.sub(r"<[^>]+>", "", re.sub(r'<span class="src">.*?</span>', "", fn(b)).replace("<br>", "／"))
        (diff if va != vb else same).append((label, va, vb))
    return diff, [s[0] for s in same]


def all_pairs() -> list:
    pairs, seen = [], set()

    def add(a, b):
        if a["slug"] == b["slug"]:
            return
        k = pair_slug(a, b)
        if k in seen:
            return
        seen.add(k)
        pairs.append((a, b))

    for bk, model_a, model_b in KW_PAIRS:
        try:
            a, b = db.find(bk, model_a), db.find(bk, model_b)
        except KeyError as e:
            print("  [warn] KWペアの型番がDBに無い:", str(e).encode("utf-8", "replace").decode("utf-8"))
            continue
        if a["msrp_kind"] == "price" and b["msrp_kind"] == "price" and a["msrp"] > b["msrp"]:
            a, b = b, a
        add(a, b)
    groups = defaultdict(list)
    for m in db.CURRENT:
        if m["brand_key"] in PAIR_BRANDS and m["msrp_kind"] == "price":
            groups[(m["brand_key"], m["instrument"])].append(m)
    for rows in groups.values():
        rows.sort(key=lambda m: (m["msrp"], m["model"]))
        for i in range(len(rows) - 1):
            add(rows[i], rows[i + 1])
    return pairs


def _acc_diff(a: dict, b: dict) -> str:
    la, lb = set(db.accessories_list(a)), set(db.accessories_list(b))
    if not la and not lb:
        return ""
    only_a, only_b = sorted(la - lb), sorted(lb - la)
    if not only_a and not only_b:
        return f'<p>付属品はメーカー表記で同じ{len(la)}点です（{esc("・".join(sorted(la))[:120])}）。</p>'
    out = []
    if only_a:
        out.append(f'<li><b>{esc(a["name"])}にだけ</b>：{esc("／".join(only_a))}</li>')
    if only_b:
        out.append(f'<li><b>{esc(b["name"])}にだけ</b>：{esc("／".join(only_b))}</li>')
    return "<ul>" + "".join(out) + "</ul><p class=\"tnote\">付属品はメーカー・正規代理店の表記どおり。ケースやマウスピースの型番が違うだけの場合もあります。</p>"


def verdict_html(a: dict, b: dict, diff: list, same: list) -> str:
    pa, pb = a["msrp"], b["msrp"]
    d = pb - pa if (pa is not None and pb is not None) else None
    price_line = (f'税込希望小売価格は <b>{esc(a["name"])} ¥{pa:,}</b> と <b>{esc(b["name"])} ¥{pb:,}</b>、定価差は <b>¥{d:,}</b>（{pb / pa:.2f}倍）。'
                  if d is not None else "税込希望小売価格はどちらか一方がメーカー未記載・オープン価格・時価です。")
    labels = [x[0] for x in diff if x[0] != "税込希望小売価格"]
    diff_line = (f'メーカー公表値が違う項目は <b>{len(labels)}つ</b>：{esc("・".join(labels))}。' if labels
                 else "税込希望小売価格以外に、メーカー公表値が違う項目はありません（当サイトの比較項目の範囲）。")
    same_line = f'同じ項目：{esc("・".join(same))}。' if same else ""
    ser = f'メーカーのシリーズ分けは {esc(db.txt(a, "series"))} と {esc(db.txt(b, "series"))}。' if db.txt(a, "series") != db.txt(b, "series") else ""
    return f"""    <div class="verdict" id="verdict">
      <div class="vhead"><span class="tab">要点</span><span class="stamp">{esc(max(a["fetched"], b["fetched"]))} 確認</span></div>
      <ul>
        <li>{price_line}</li>
        <li>{diff_line}</li>
        <li>{same_line}{ser}</li>
        <li>音の良し悪し・吹きやすさは当サイトでは扱いません。並べているのはメーカー・正規代理店の公表値だけです。</li>
      </ul>
      <div class="src">出典：{esc(db.source_kind(a))}／{esc(db.source_kind(b))}（各型番ページの出典欄）。値はメーカー公表のまま、当サイトは推測で補いません。</div>
    </div>"""


def faqs(a: dict, b: dict, diff: list) -> list:
    pa, pb = a["msrp"], b["msrp"]
    out = []
    if pa is not None and pb is not None:
        out.append({"q": f"{a['name']}と{b['name']}の定価はいくら違いますか？",
                    "a": f"メーカー公表の税込希望小売価格は{a['name']}が¥{pa:,}、{b['name']}が¥{pb:,}で、差は¥{pb - pa:,}です（確認日 {max(a['fetched'], b['fetched'])}）。実際の販売価格は店ごとに異なります。"})
    labels = [x[0] for x in diff if x[0] != "税込希望小売価格"]
    out.append({"q": f"{a['name']}と{b['name']}は何が違いますか？",
                "a": (f"メーカー・正規代理店の公表値で違うのは{('・'.join(labels))}です。" if labels else "税込希望小売価格以外に、当サイトの比較項目でメーカー公表値が違うところはありません。")
                     + "音色や吹きやすさの違いは当サイトでは扱いません。購入前の試奏を各メーカー・楽器店が推奨しています。"})
    out.append({"q": f"{b['name']}は{a['name']}の「後継」ですか？",
                "a": ("メーカーが前身・「後継」を明記している場合だけそう書きます。" +
                      (f"この2型番についてメーカーの明記は「{db.txt(b, 'predecessor')}」です。" if db.txt(b, "predecessor") and not db.txt(b, "predecessor").startswith("—")
                       else "この2型番については明記が見つからないため、当サイトは同じブランド・同じ楽器種で定価が隣り合う型番として並べています。"))})
    return out


def article_of_pair(a: dict, b: dict):
    """この2型番を扱う解説記事（あれば）。同じKWで記事と食い合わないよう、差分ページから記事へ誘導する。"""
    from articles_data import ARTICLES
    slugs = {a["slug"], b["slug"]}
    for art in ARTICLES:
        if art["category"] == "pair" and {db.find(*r)["slug"] for r in art.get("models", [])} == slugs:
            return art
    return None


def page_body(a: dict, b: dict) -> str:
    diff, same = diff_rows(a, b)
    hero = catalog.spec_hero_html([a, b], PREFIX, {})
    art = article_of_pair(a, b)
    art_note = (f'  <div class="note"><b>この2型番の解説記事：</b><a href="../articles/{esc(art["slug"])}.html">{esc(art["name"])}</a>。'
                'メーカーの説明文の引用・買う前の確認点・よくある質問はそちらにまとめています。このページは公表値の差分表です。</div>\n' if art else "")
    sib = db.siblings(a)
    lad = ladder.fig(ladder.lineup_ladder(sib, PREFIX, me={a["slug"], b["slug"]}, caption=f"{a['brand_label']} {a['instrument_label']} 現行型番の税込希望小売価格"),
                     f"{a['brand_label']}の{a['instrument_label']}・現行型番の税込希望小売価格（定価あり）。この2型番の前後にどんな型番があるかが読めます。棒を押すと型番ページへ。")
    toc = [("verdict", "要点"), ("cmp", "仕様と定価の比較表（違う行に色）"), ("acc", "付属品の違い"), ("ladder", "ラインナップの中の位置"), ("faq", "よくある質問")]
    toc_html = "\n".join(f'        <li><a href="#{k}">{v}</a></li>' for k, v in toc)
    return f"""  <p class="crumb measure"><a href="../index.html">トップ</a> &gt; <a href="index.html">型番ペアの違い</a> &gt; {esc(a["name"])} と {esc(b["name"])}</p>
  <p class="prnote measure">{cfg.NOTICE_PR}</p>
  <div class="measure mpage">
    <p class="kicker">{esc(a["brand_label"])}<span>{esc(a["instrument_label"])}</span><span>型番ペアの違い</span></p>
    <h1>{esc(a["name"])}と{esc(b["name"])}の違い<small>税込定価・仕様・付属品をメーカー公表値で比較（{esc(a["brand_label"])} {esc(a["instrument_label"])}）</small></h1>
{art_note}{verdict_html(a, b, diff, same)}
{hero}
    <p class="lead-p">{esc(a["brand_label"])}の{esc(a["instrument_label"])}で定価が隣り合う「{esc(a["name"])}」と「{esc(b["name"])}」を、メーカー公式ページ・正規代理店の公表値だけで1表に並べました。色の付いた行が違う項目です。どちらが良いかは書きません。</p>
    <nav class="toc" aria-label="目次"><b>このページの内容</b><ol>
{toc_html}
    </ol></nav>
  </div>
  <div class="measure mpage">
    <h2 id="cmp">仕様と定価の比較表<small>（メーカー公表値・違う行に色）</small></h2>
{render.cmp_table_html([a, b], prefix=PREFIX)}
    <h2 id="acc">付属品の違い</h2>
{_acc_diff(a, b) or '<p><span class="na">—（付属品はどちらもメーカー未記載）</span></p>'}
    <h2 id="ladder">ラインナップの中の位置</h2>
{lad}
    <p class="soft"><a href="../models/{esc(a["slug"])}.html">{esc(a["name"])}の型番ページ</a>／<a href="../models/{esc(b["slug"])}.html">{esc(b["name"])}の型番ページ</a>／<a href="../instruments/{esc(a["group_key"])}.html">{esc(a["group_label"])}の全ブランド一覧</a></p>
    <h2 id="faq">よくある質問</h2>
{chr(10).join(f'  <details class="faq"><summary>{esc(f["q"])}</summary>{chr(10)}    <p>{esc(f["a"])}</p></details>' for f in faqs(a, b, diff))}
    <p class="tnote">{cfg.NOTICE_PRICE} {cfg.NOTICE_NA}</p>
    <div class="caution">{cfg.NOTICE_PARALLEL}</div>
    <a class="totop" href="#main">↑ ページの先頭へ</a>
  </div>"""


def description_of(a: dict, b: dict, diff: list) -> str:
    labels = [x[0] for x in diff if x[0] != "税込希望小売価格"]
    pa, pb = a["msrp"], b["msrp"]
    s = f"{a['brand_label']} {a['instrument_label']}の{a['name']}と{b['name']}の違い。"
    if pa is not None and pb is not None:
        s += f"税込希望小売価格は¥{pa:,}と¥{pb:,}（差¥{pb - pa:,}）。"
    s += (f"メーカー公表値が違うのは{'・'.join(labels)}。" if labels else "定価以外にメーカー公表値の違いはありません。")
    s += "付属品の差と出典・確認日つき。"
    return s[:135]


def jsonld(a: dict, b: dict, rel: str, fq: list) -> str:
    url = cfg.canonical_url(rel)
    page = {"@context": "https://schema.org", "@type": "WebPage", "url": url, "name": f"{a['name']}と{b['name']}の違い", "inLanguage": "ja",
            "dateModified": max(a["fetched"], b["fetched"]), "isPartOf": {"@type": "WebSite", "name": cfg.SITE_NAME, "url": cfg.BASE_URL + "/"},
            "about": [{"@type": "Product", "name": x["name"], "brand": {"@type": "Brand", "name": x["brand_roman"]}, "url": cfg.canonical_url(f"models/{x['slug']}.html")} for x in (a, b)]}
    faq = {"@context": "https://schema.org", "@type": "FAQPage", "url": url,
           "mainEntity": [{"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in fq]}
    crumb = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "トップ", "item": cfg.BASE_URL + "/"},
        {"@type": "ListItem", "position": 2, "name": "型番ペアの違い", "item": cfg.canonical_url("compare/index.html")},
        {"@type": "ListItem", "position": 3, "name": f"{a['name']}と{b['name']}の違い", "item": url}]}
    return "".join(f'<script type="application/ld+json">{json.dumps(d, ensure_ascii=False)}</script>\n' for d in (page, faq, crumb))


def generate(a: dict, b: dict) -> str:
    rel = f"compare/{pair_slug(a, b)}.html"
    diff, _same = diff_rows(a, b)
    title = f"{a['name']}と{b['name']}の違い（{a['brand_label']} {a['instrument_label']}・定価と仕様）｜{cfg.SITE_NAME}"
    chrome.write_page(rel, chrome.page_html(title=title, description=description_of(a, b, diff), rel_path=rel, body=page_body(a, b),
                                            current="compare", og_type="article", extra_head=jsonld(a, b, rel, faqs(a, b, diff))))
    return rel


def gen_index_page(pairs: list):
    rel = "compare/index.html"
    kw = set()
    for bk, ma, mb in KW_PAIRS:
        try:
            kw.add(pair_slug(*sorted((db.find(bk, ma), db.find(bk, mb)), key=lambda m: (m["msrp"] or 0))))
        except KeyError:
            pass
    featured = [(a, b) for a, b in pairs if pair_slug(a, b) in kw]
    by_group = defaultdict(list)
    for a, b in pairs:
        by_group[a["group_key"]].append((a, b))
    feat = "\n".join(f'    <a class="paircard" href="{pair_slug(a, b)}.html"><span class="pc-b">{esc(a["brand_label"])}・{esc(a["instrument_label"])}</span>'
                     f'<span class="pc-n">{esc(a["name"])} <i>vs</i> {esc(b["name"])}</span><span class="pc-p">¥{a["msrp"]:,} → ¥{b["msrp"]:,}<small>定価差 ¥{b["msrp"] - a["msrp"]:,}</small></span></a>'
                     for a, b in featured)
    secs = []
    for g, lst in by_group.items():
        by_brand = defaultdict(list)
        for a, b in lst:
            by_brand[a["brand_key"]].append((a, b))
        inner = []
        for bk, ps in by_brand.items():
            lis = "".join(f'<li><a href="{pair_slug(a, b)}.html">{esc(a["name"])} と {esc(b["name"])}</a><span class="soft">　{esc(a["instrument_label"])}／定価差 ¥{b["msrp"] - a["msrp"]:,}</span></li>' for a, b in ps)
            inner.append(f'  <details class="help"><summary>{esc(db.BRANDS[bk]["label"])}の{len(ps)}組を開く</summary>\n  <ul class="mlist">{lis}</ul></details>')
        secs.append(f'  <section id="g-{g}"><h2>{esc(db.GROUP_LABEL[g])}<small>（{len(lst)}組）</small></h2>\n' + "\n".join(inner) + "\n  </section>")
    body = f"""  <p class="crumb measure left"><a href="../index.html">トップ</a> &gt; 型番ペアの違い</p>
  <p class="prnote measure left">{cfg.NOTICE_PR}</p>
  <div class="measure left">
    <h1>型番ペアの違い<small>（{len(pairs)}組・同ブランド同楽器種で定価が隣り合う2型番）</small></h1>
    <p class="lead-p">「YAS-280とYAS-380は何が違う？」のように、1つ上のグレードとの違いを知りたいときのページです。
    メーカー・正規代理店の公表値（税込希望小売価格・調子・仕上げ・材質・機構・付属品）を1表に並べ、違う行だけに色を付けています。音の良し悪しは書きません。</p>
  </div>
  <h2 id="featured">よく調べられているペア</h2>
  <div class="pairgrid">
{feat}
  </div>
  <div class="measure left">
{chr(10).join(secs)}
  </div>"""
    items = [{"@type": "ListItem", "position": i, "url": cfg.canonical_url(f"compare/{pair_slug(a, b)}.html"), "name": f"{a['name']}と{b['name']}の違い"} for i, (a, b) in enumerate(pairs, 1)]
    ld = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": "型番ペアの違い", "url": cfg.canonical_url(rel), "inLanguage": "ja",
           "mainEntity": {"@type": "ItemList", "numberOfItems": len(pairs), "itemListElement": items[:200]}}]
    extra = "".join(f'<script type="application/ld+json">{json.dumps(d, ensure_ascii=False)}</script>\n' for d in ld)
    chrome.write_page(rel, chrome.page_html(title=f"管楽器の型番ペアの違い一覧（{len(pairs)}組・定価と仕様の差分）｜{cfg.SITE_NAME}",
                                            description=f"同じブランド・同じ楽器種で定価が隣り合う2型番の違いを{len(pairs)}組。税込希望小売価格の差、メーカー公表値が違う項目、付属品の差を出典つきで。YAS-280とYAS-380、YAS-480とYAS-62など。",
                                            rel_path=rel, body=body, current="compare", extra_head=extra))


def pair_map() -> dict:
    """{型番slug: [(相手, rel), …]}。gen_model が「1つ上との違い」リンクに使う。"""
    out = defaultdict(list)
    for a, b in all_pairs():
        out[a["slug"]].append((b, f"compare/{pair_slug(a, b)}.html"))
        out[b["slug"]].append((a, f"compare/{pair_slug(a, b)}.html"))
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    pairs = all_pairs()
    keep = set()
    for a, b in pairs:
        keep.add(Path(generate(a, b)).name)
    gen_index_page(pairs)
    keep.add("index.html")
    d = chrome.SITE_DIR / "compare"
    removed = 0
    for p in d.glob("*.html"):
        if p.name not in keep:
            p.unlink()
            removed += 1
    print(f"型番ペア差分ページ {len(pairs)} 組＋一覧1 を生成（古いHTML {removed} 件を削除）")


if __name__ == "__main__":
    main()
