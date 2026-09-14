# -*- coding: utf-8 -*-
"""現行・終了を含む全型番の詳細ページ（models/<slug>.html）と一覧（models/index.html）をDBから生成する。

  ・本文は全てDBの値（メーカー・正規代理店の公表値）から組み立てる。推測で埋めない
  ・価格は「税込希望小売価格＋改定日（無ければ『改定日はメーカー未記載』＋確認日）＋出典」の3点セット
  ・隣接型番（同ブランド・同楽器種を定価順）と派生・仕上げ違い（基本型番が同じ）を表で示す。
    「後継」はメーカー明記（predecessor／successor 列）だけを出す
  ・購入リンクは提携後だけ。「この型番を売るなら」は A8 提携後だけ見出しごと出す（ダミー禁止）
  ・音の良し悪し・吹きやすさは書かない（qa_site の NG_HARD で機械強制）
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
import catalog
import moshimo_link
import price_data
import ladder
import gen_compare
from articles_data import ARTICLES
from render import esc

PREFIX = "../"
PAIRS = gen_compare.pair_map()


def articles_of_model() -> dict:
    """{型番slug: [記事dict, …]}。記事の models／cited_models に載っている型番。"""
    out = defaultdict(list)
    for a in ARTICLES:
        for ref in a.get("models", []) + a.get("cited_models", []):
            out[db.find(*ref)["slug"]].append(a)
    return out


ART_OF = articles_of_model()


def pair_article(m: dict, other: dict):
    for a in ART_OF.get(m["slug"], []):
        if a["category"] == "pair" and any(db.find(*r)["slug"] == other["slug"] for r in a.get("models", [])):
            return a
    return None


def flags_caution(m: dict) -> str:
    out = []
    if not m["is_current"]:
        out.append(f'この型番はメーカー・代理店の表記が<b>「{esc(m["status_label"])}」</b>です（確認日 {esc(m["fetched"])}）。'
                   "定価・仕様は掲載時点の表記のまま残しています。")
    if m["is_secondary"]:
        out.append("この型番はメーカー・正規代理店の日本語ページに到達できず、<b>楽器店ページ（二次情報）</b>を出典にしています。数値はその表記のままです。")
    if m["unverified"]:
        out.append("この型番は発売元のサイトを当サイトの環境から取得できず、<b>型番と製品ページのURL以外を確認できていません</b>。仕様・価格は「—（未確認）」のままにしています。")
    elif m["unverified_spec"]:
        out.append("この型番は発売元ページの仕様表を取得できず、<b>価格以外の仕様を確認できていません</b>。仕様は「—（未確認）」のままにしています。")
    return "".join(f'  <div class="caution">{x}</div>\n' for x in out)


def article_lead(m: dict) -> str:
    arts = ART_OF.get(m["slug"], [])
    if not arts:
        return ""
    links = "／".join(f'<a href="../articles/{a["slug"]}.html">{esc(a["name"])}</a>' for a in arts[:3])
    return f'  <div class="note"><b>この型番を扱う記事：</b>{links}。このページはメーカー公表の定価・仕様データです。</div>\n'


def keypoints_html(m: dict, r: dict) -> str:
    n, total, _ = db.transparency(m)
    acc = db.accessories_list(m)
    lis = [
        f'{esc(m["brand_label"])}の<b>{esc(m["instrument_label"])}</b>' + (f'、シリーズは<b>{esc(r["series"])}</b>' if not r["series"].startswith("—") else "、シリーズ名はメーカー未記載") + "。",
        f'調子 <b>{esc(r["key"])}</b>／仕上げ <b>{esc(r["finish"])}</b>／材質 {esc(r["material"])}。',
        (f'付属品はメーカー表記で<b>{len(acc)}点</b>（{esc("・".join(acc[:4]))}{"…" if len(acc) > 4 else ""}）。' if acc else f'付属品：{esc(r["acc"])}。'),
        f'メーカー・代理店の表記は<b>{esc(m["status_label"])}</b>（確認日 {esc(m["fetched"])}）。',
        f'{"出典ページに載っている" if (m.get("is_secondary") or m.get("unverified") or m.get("unverified_spec")) else "メーカーが公表している"}主要項目は <b>{n}／{total}</b>、'
        f'公表情報の充実度スコアは <b>{r["score"]}／{r["scoreMax"]}点</b>（載っている情報の多さで、楽器の性能の優劣ではありません）。',
    ]
    price = db.msrp_txt(m)
    pdate = db.msrp_date_txt(m)
    plabel = "税込・メーカーの希望小売価格は未公表" if m.get("msrp_is_street") else "税込希望小売価格"
    big = (f'<div class="bigprice">{esc(price)}<small>{plabel}{"／" + esc(pdate) if pdate else ""}</small></div>'
           if m["msrp_kind"] == "price" else f'<div class="bigprice">{esc(price)}<small>{esc(pdate) if pdate else "税込希望小売価格"}</small></div>')
    if m.get("msrp_converted") and m["msrp_kind"] == "price":   # 二次情報の税抜表示を当サイトが換算した型番（Rampone&Cazzani）
        big += ('    <p class="tnote">この税込表示は、楽器店ページ（二次情報）の税抜表示を当サイトが×1.10で換算した値です。'
                'メーカー・代理店が税込で公表している価格ではありません。</p>')
    # 出典の種類によって「値の出どころ」の説明を変える（二次情報・未確認の型番に『メーカー公表値』と書かない）
    if m.get("is_secondary"):
        src_note = "数値は楽器店ページ（二次情報）の表記のままで、当サイトは推測で補いません。"
    elif m.get("unverified") or m.get("unverified_spec"):
        src_note = "確認できた項目だけを載せ、取得できなかった項目は「—（未確認）」のままにしています。"
    else:
        src_note = "数値はメーカー・正規代理店の公表値のままで、当サイトは推測で補いません。"
    return f"""    <div class="verdict">
      <div class="vhead"><span class="tab">要点</span><span class="stamp">{esc(m["fetched"])} 確認</span></div>
      {big}
      <ul>
{chr(10).join(f"        <li>{x}</li>" for x in lis)}
      </ul>
      <div class="src">出典：{esc(db.source_kind(m))}（{len(db.sources(m))}件・下の「出典」欄）。{src_note}</div>
    </div>"""


def _mall_urls(m: dict) -> tuple:
    u = price_data.urls(m["slug"])
    return u.get("楽天市場", ""), u.get("Yahoo!ショッピング", "")


def buybar_html(m: dict) -> str:
    rk, yh = _mall_urls(m)
    amazon_ok = db.BRANDS[m["brand_key"]].get("amazon") is True and m["is_current"]
    return "  " + moshimo_link.buyrow(amazon_kw=f"{m['brand_roman']} {m['model']}", rakuten_url=rk, yahoo_url=yh, amazon_ok=amazon_ok) + "\n"


def price_html(m: dict) -> str:
    band = db.price_band(m)
    trs = [
        (render.row_label("税込希望小売価格", [m]), render.msrp_html(m)),
        ("価格帯（当サイトの区分）", esc(db.PRICE_BAND_LABEL[band])
         + f'<span class="src"><a href="../data.html#band">区分の定義</a>／<a href="../index.html?group={esc(m["group_key"])}">同じ楽器種の型番を定価順に見る</a></span>'),
    ]
    st = render.street_html(m)
    if st:
        trs.append(("実売の最安値", st))
    elif price_data.HAS_API:
        trs.append(("実売の最安値", '<span class="na">—（当サイト未取得。楽天市場・Yahoo!ショッピングで型番一致の出品を確認できませんでした）</span>'))
    rows = "\n".join(f'      <tr><th scope="row">{esc(a)}</th><td>{b}</td></tr>' for a, b in trs)
    kaitori = moshimo_link.kaitori_row()
    sell = ""
    if kaitori:
        sell = f'\n  <h3 id="sell">この型番を売るなら</h3>\n  <p>買い替えで手放す場合の無料査定です。{kaitori}'
    return f"""  <div class="tblcard"><table class="minitbl"><caption class="visually-hidden">{esc(m["name"])} の価格</caption>
{rows}
  </table></div>
  <p class="tnote">{cfg.NOTICE_PRICE} 定価が複数並存する型番は最新の公式値を採り、旧値は備考に残します。</p>
  <div class="caution">{cfg.NOTICE_PARALLEL}</div>{sell}"""


def variants_html(m: dict) -> str:
    rows = db.variants(m)
    if not rows:
        return ""
    base = db.base_model(m)
    return (f'    <h2 id="variants">{esc(base)} の派生・仕上げ違い<small>（{len(rows)}型番・メーカー表記どおり）</small></h2>\n'
            f'  <p>型番の末尾のサフィックス（S＝銀メッキ、GP＝金メッキ など）はメーカーの表記どおりに並べています。意味はメーカーの型番表記・仕上げ欄の引用で、当サイトは推測で補いません。</p>\n'
            + render.lineup_table_html(rows, PREFIX, {}, me=m["slug"]))


def _pair_link(m: dict, o: dict) -> str:
    """m と o のペア差分ページがあればその rel、無ければ o の型番ページ。"""
    for other, rel in PAIRS.get(m["slug"], []):
        if other["slug"] == o["slug"]:
            return PREFIX + rel
    return f'{esc(o["slug"])}.html'


def neighbors_html(m: dict) -> str:
    """1つ下・1つ上の定価の型番カード（定価差＋違う項目数＋ペア差分ページへ）。"""
    rows = [x for x in db.siblings(m) if x["msrp_kind"] == "price"]
    if m["msrp_kind"] != "price" or len(rows) < 2:
        return ""
    idx = next((i for i, x in enumerate(rows) if x["slug"] == m["slug"]), None)
    if idx is None:
        return ""
    cards = []
    for j, lbl in ((idx - 1, "1つ下の定価"), (idx + 1, "1つ上の定価")):
        if 0 <= j < len(rows):
            o = rows[j]
            d = o["msrp"] - m["msrp"]
            diff, _ = gen_compare.diff_rows(m, o)
            labels = [x[0] for x in diff if x[0] != "税込希望小売価格"]
            what = ("違う項目：" + "・".join(labels[:4]) + ("…" if len(labels) > 4 else "")) if labels else "定価以外にメーカー公表値の違いなし"
            href = _pair_link(m, o)
            cards.append(f'<a href="{href}"><small>{lbl}</small><b>{esc(o["name"])}</b><span class="d">{"+" if d > 0 else ""}¥{d:,}</span><small>{esc(what)}</small><small>{"違いを見る →" if href.startswith(PREFIX + "compare/") else "型番ページへ →"}</small></a>')
        else:
            cards.append(f'<a href="../instruments/{esc(m["group_key"])}.html#b-{esc(m["brand_key"])}"><small>{lbl}</small><b>{"このブランドで最も安い型番です" if j < 0 else "このブランドで最も高い型番です"}</b><small>{esc(m["brand_label"])}の{esc(m["instrument_label"])}一覧へ →</small></a>')
    return f'  <div class="neighbors">{"".join(cards)}</div>\n'


def siblings_html(m: dict) -> str:
    rows = db.siblings(m)
    if len(rows) <= 1:
        return f'  <p>{esc(m["brand_label"])}の{esc(m["instrument_label"])}で現行の型番はこの1件です。<a href="../instruments/{esc(m["group_key"])}.html">他ブランドの{esc(m["group_label"])}一覧</a>。</p>'
    strip = ladder.fig(ladder.position_strip(rows, m, PREFIX), f"{m['brand_label']}の{m['instrument_label']}・現行型番の税込希望小売価格の並び。点を押すと型番ページへ。")
    return (f'  <p>{esc(m["brand_label"])}の{esc(m["instrument_label"])}・現行{len(rows)}型番の中で、この型番がどの位置にあるかと、1つ下・1つ上の型番との差です。</p>\n'
            f'{strip}\n{neighbors_html(m)}'
            f'  <details class="help"><summary>{esc(m["brand_label"])}の{esc(m["instrument_label"])}・現行{len(rows)}型番を表で見る（税込定価順・仕上げ・調子・材質・現行）</summary>\n'
            + render.lineup_table_html(rows, PREFIX, {}, me=m["slug"]) + "\n  </details>" +
            f'\n  <p class="tnote">同じ楽器種の他ブランドは<a href="../instruments/{esc(m["group_key"])}.html">{esc(m["group_label"])}の一覧</a>、'
            f'ブランドの全型番は<a href="../brands.html#bk-{esc(m["brand_key"])}">ブランド一覧</a>にあります。</p>')


def score_section_html(m: dict, r: dict) -> str:
    trs = "\n".join(f'      <tr><th scope="row">{esc(a)}</th><td class="n">{b}／{c}</td></tr>' for a, b, c in r["scoreItems"])
    have = "・".join(r["transpHave"]) or "なし"
    return f"""  <p>このスコアは「メーカー・正規代理店が公表している情報の充実度」を{db.SCORE_MAX}点満点で機械的に数えたもので、
  性能や音の優劣ではありません（<a href="../data.html#score">数え方</a>）。公表している項目：{esc(have)}。</p>
  <div class="tblcard"><table class="minitbl"><caption class="visually-hidden">{esc(m["name"])} の公表情報の充実度スコアの内訳</caption>
      <thead><tr><th scope="col">項目</th><th scope="col">点</th></tr></thead>
      <tbody>
{trs}
      <tr><th scope="row">合計</th><td class="n"><b>{r["score"]}／{r["scoreMax"]}</b></td></tr>
      </tbody></table></div>"""


def checklist_html(m: dict) -> str:
    """買う前に公式資料で確かめられること（DBの値と固定注記だけ。推測は書かない）。"""
    acc = db.accessories_list(m)
    items = []
    items.append(("ok" if acc else "na",
                  f"付属品：メーカー表記で{len(acc)}点（{esc('・'.join(acc[:5]))}{'…' if len(acc) > 5 else ''}）。マウスピース・ケースが付くかはここで確認" if acc
                  else "付属品：メーカー・代理店ページに記載なし。販売店で何が付くかを確認"))
    items.append(("ok" if m["msrp_kind"] == "price" else "na",
                  f"定価：税込希望小売価格 {esc(db.msrp_txt(m))}（{esc(db.msrp_date_txt(m))}）。実売価格は店ごとに違う" if m["msrp_kind"] == "price"
                  else f"定価：{esc(db.msrp_txt(m))}。店頭・販売店で価格を確認"))
    pdf = [u for u in db.sources(m) if db.is_pdf(u)]
    items.append(("ok" if pdf else "na", f"カタログ・取扱説明書PDF：公式サイトに{len(pdf)}件（下の「出典」欄からそのまま開ける）" if pdf else "カタログ・取扱説明書PDF：公式サイトに掲載なし、または未回収"))
    items.append(("ok", f"現行／終了：メーカー表記は「{esc(m['status_label'])}」（確認日 {esc(m['fetched'])}）"))
    items.append(("ok", "並行輸入・中古：メーカー保証や修理受付の対象外になり得る。購入前に販売店とメーカーの案内を確認"))
    items.append(("ok", "試奏：楽器は個体差があり、購入前の試奏を各メーカー・楽器店が推奨"))
    return '  <ul class="checklist">\n' + "\n".join(f'    <li class="{c}">{t}</li>' for c, t in items) + "\n  </ul>"


def sources_html(m: dict) -> str:
    urls = db.sources(m)
    if not urls:
        items = '      <li><span class="na">一次情報（メーカー・正規代理店の製品ページ）に到達できていません。</span></li>'
    else:
        items = "\n".join(
            f'      <li><a href="{esc(u)}" rel="{render._rel(u)}" target="_blank">{esc(render._url_label(u))}<span class="visually-hidden">（別タブで開く）</span></a>'
            f'<span class="srcnote">{esc(render._short_label(u, db.source_kind(m), i))}／確認日 {esc(m["fetched"])}</span></li>' for i, u in enumerate(urls[:12]))
    return f'  <ol class="sources">\n{items}\n  </ol>'


def related_html(m: dict) -> str:
    arts = ART_OF.get(m["slug"], [])
    if not arts:
        return ""
    from gen_index import newcard_html
    cards = "\n".join(newcard_html(a, PREFIX) for a in arts[:6])
    return f"""    <section class="related" aria-labelledby="related-h">
      <h2 id="related-h">この型番を扱う記事</h2>
      <div class="newlist">
{cards}
      </div>
    </section>"""


def description_of(m: dict, r: dict) -> str:
    price = db.msrp_txt(m)
    pd = db.msrp_date_txt(m)
    base = (f'{m["brand_label"]} {m["instrument_label"]}「{m["name"]}」の税込希望小売価格は{price}'
            + (f'（{pd}）' if pd and m["msrp_kind"] == "price" else "")
            + f'。調子{r["key"]}・仕上げ{r["finish"]}・付属品・現行／生産終了を、メーカー公式・正規代理店の表記のまま出典URLと確認日つきで掲載。同ブランドの隣接型番との定価差も。')
    base = base.replace("—（メーカー未記載）", "メーカー未記載").replace("—（未確認）", "未確認").replace("—（楽器店ページに記載なし）", "未記載")
    if len(base) > 135:
        base = (f'{m["brand_label"]} {m["instrument_label"]}「{m["name"]}」の税込希望小売価格は{price}。調子・仕上げ・付属品・現行／生産終了をメーカー公式・正規代理店の表記のまま出典と確認日つきで掲載。')
        base = base.replace("—（メーカー未記載）", "メーカー未記載").replace("—（未確認）", "未確認")
    if len(base) > 135:
        base = base[:134] + "。"
    return base


def _props(m: dict) -> list:
    out = []
    for key, name in (("key", "調子"), ("finish", "仕上げ"), ("body_material", "管体材質"), ("bell_material", "ベル材質"),
                      ("series", "シリーズ"), ("bell_diameter_raw", "ベル径"), ("bore_raw", "ボア"), ("key_system", "キイシステム")):
        v = m.get(key)
        if v in (None, "") or (isinstance(v, str) and v.startswith("メーカー未記載")):
            continue
        out.append({"@type": "PropertyValue", "name": name, "value": db.clean_text(str(v))})
    if m["msrp_kind"] == "price":
        out.append({"@type": "PropertyValue", "name": "税込希望小売価格（メーカー公表）", "value": f"{m['msrp']} JPY"})
    return out


def jsonld(m: dict, r: dict, rel: str) -> str:
    url = cfg.canonical_url(rel)
    product = {"@type": "Product", "name": m["name"], "model": m["model"],
               "brand": {"@type": "Brand", "name": m["brand_roman"]},
               "manufacturer": {"@type": "Organization", "name": m["maker"]},
               "category": m["instrument_label"], "url": url, "description": description_of(m, r),
               "additionalProperty": _props(m)}
    page = {"@context": "https://schema.org", "@type": "ItemPage", "url": url, "name": m["name"], "inLanguage": "ja",
            "dateModified": m["fetched"], "isPartOf": {"@type": "WebSite", "name": cfg.SITE_NAME, "url": cfg.BASE_URL + "/"},
            "mainEntity": product}
    crumb = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "トップ", "item": cfg.BASE_URL + "/"},
        {"@type": "ListItem", "position": 2, "name": m["group_label"], "item": cfg.canonical_url(f"instruments/{m['group_key']}.html")},
        {"@type": "ListItem", "position": 3, "name": m["name"], "item": url}]}
    return "".join(f'<script type="application/ld+json">{json.dumps(d, ensure_ascii=False)}</script>\n' for d in (page, crumb))


def page_body(m: dict) -> str:
    r = catalog.record(m, PREFIX, {})
    hero = catalog.spec_hero_html([m], PREFIX, {})
    toc = [("siblings", "ラインナップの中の位置・1つ上／下との違い"), ("spec", "仕様と定価（メーカー公表値）"), ("price", "価格・購入先"), ("check", "買う前に公式資料で確かめられること")]
    if db.variants(m):
        toc.append(("variants", "派生・仕上げ違い"))
    toc += [("score", "公表情報の充実度（当サイトの機械採点）"), ("sources", "出典")]
    toc_html = "\n".join(f'        <li><a href="#{k}">{v}</a></li>' for k, v in toc)
    return f"""  <p class="crumb measure"><a href="../index.html">トップ</a> &gt; <a href="../instruments/{esc(m["group_key"])}.html">{esc(m["group_label"])}</a> &gt; <a href="../brands.html#bk-{esc(m["brand_key"])}">{esc(m["brand_label"])}</a> &gt; {esc(m["name"])}</p>
  <p class="prnote measure">{cfg.NOTICE_PR}</p>
  <div class="measure mpage">
    <p class="kicker">{esc(m["brand_label"])}<span>{esc(m["instrument_label"])}</span><span>型番 {esc(m["model"])}</span></p>
    <h1>{esc(m["name"])}<small>税込定価・仕様・隣接型番との違い（{esc(m["brand_label"])} {esc(m["instrument_label"])}）</small></h1>
{flags_caution(m)}{article_lead(m)}{keypoints_html(m, r)}
{buybar_html(m)}{hero}
    <p class="lead-p">{esc(m["brand_label"])}「{esc(m["name"])}」の税込希望小売価格と仕様を、メーカー公式ページ・日本の正規代理店・公式カタログで確認できた範囲だけ載せています。確認できなかった項目は「—（メーカー未記載）」のままにし、推測で埋めません。音の良し悪しや吹きやすさは扱いません。</p>
    <p class="meta"><span>確認日：<b>{esc(m["fetched"])}</b></span><span>出典の種類：<b>{esc(db.source_kind(m))}</b></span></p>
    <nav class="toc" aria-label="目次"><b>このページの内容</b><ol>
{toc_html}
    </ol></nav>
  </div>
  <div class="measure mpage">
    <h2 id="siblings">ラインナップの中の位置<small>（{esc(m["brand_label"])} {esc(m["instrument_label"])}・税込定価順）</small></h2>
{siblings_html(m)}
    <h2 id="spec">仕様と定価<small>（メーカー・正規代理店の公表値）</small></h2>
{render.spec_table_html(m)}
    <h2 id="price">価格・購入先</h2>
{price_html(m)}
    <h2 id="check">買う前に公式資料で確かめられること</h2>
{checklist_html(m)}
{variants_html(m)}
    <h2 id="score">公表情報の充実度<small>（当サイトの機械採点・{db.SCORE_MAX}点満点）</small></h2>
{score_section_html(m, r)}
    <h2 id="sources">出典</h2>
{sources_html(m)}
    <p class="soft">掲載内容の誤り・訂正のご依頼（メーカー・楽器店・権利者の方を含む）は<a href="../about.html#contact">このサイトについての窓口</a>までお願いします。</p>
{related_html(m)}
    <a class="totop" href="#main">↑ ページの先頭へ</a>
  </div>"""


def generate(m: dict) -> str:
    rel = f"models/{m['slug']}.html"
    r = catalog.record(m, PREFIX, {})
    title = f'{m["name"]}の定価と仕様（{m["brand_label"]} {m["instrument_label"]}）｜{cfg.SITE_NAME}'
    html = chrome.page_html(title=title, description=description_of(m, r), rel_path=rel, body=page_body(m),
                            current="models", og_type="article", extra_head=jsonld(m, r, rel), noindex=not m["is_current"])
    chrome.write_page(rel, html)
    return rel


def gen_index_page():
    rel = "models/index.html"
    secs = []
    for g, glabel, fam, _iks in db.INSTRUMENT_GROUPS:
        rows = [m for m in db.CURRENT if m["group_key"] == g]
        if not rows:
            continue
        by_brand = defaultdict(list)
        for m in rows:
            by_brand[m["brand_key"]].append(m)
        parts = []
        for bk in sorted(by_brand, key=lambda k: -len(by_brand[k])):
            lis = "\n".join(
                f'    <li><a href="{esc(m["slug"])}.html">{esc(m["name"])}</a><span class="soft">　{esc(m["instrument_label"])}／{esc(db.msrp_txt(m))}／{esc(db.txt(m, "finish"))}</span></li>'
                for m in sorted(by_brand[bk], key=lambda x: (x["msrp"] is None, x["msrp"] or 0, x["model"])))
            parts.append(f'  <h3>{esc(db.BRANDS[bk]["label"])}<small>（{len(by_brand[bk])}型番）</small></h3>\n  <ul class="mlist">\n{lis}\n  </ul>')
        secs.append(f'  <section id="g-{g}"><h2>{esc(glabel)}<small>（現行 {len(rows)} 型番・<a href="../instruments/{g}.html">一覧表へ</a>）</small></h2>\n' + "\n".join(parts) + "\n  </section>")
    n = len(db.CURRENT)
    n_old = len(db.MODELS) - n
    body = f"""  <p class="crumb measure left"><a href="../index.html">トップ</a> &gt; 型番ページ一覧</p>
  <p class="prnote measure left">{cfg.NOTICE_PR}</p>
  <div class="measure left">
    <h1>型番ページ一覧<small>（現行 {n} 型番）</small></h1>
    <p class="lead-p">現行{n}型番それぞれの税込希望小売価格・仕様・付属品・隣接型番・出典をまとめた型番ページです。楽器種→ブランドの順に、税込定価の安い順で並べています。
    絞り込みや横並び比較は<a href="../index.html#db">トップのカタログ</a>で、ブランド横断の一覧表は<a href="../instruments/index.html">楽器種別ページ</a>でご覧ください。
    生産終了・在庫限りの{n_old}型番は<a href="../discontinued.html">別の一覧</a>に分けています。</p>
    <p class="tnote">{cfg.NOTICE_PRICE} {cfg.NOTICE_NA}</p>
  </div>
  <div class="measure left">
{chr(10).join(secs)}
  </div>"""
    items = [{"@type": "ListItem", "position": i, "url": cfg.canonical_url(f"models/{m['slug']}.html"), "name": m["name"]}
             for i, m in enumerate(db.CURRENT, 1)]
    ld = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": f"型番ページ一覧（現行{n}型番）",
           "url": cfg.canonical_url(rel), "inLanguage": "ja",
           "isPartOf": {"@type": "WebSite", "name": cfg.SITE_NAME, "url": cfg.BASE_URL + "/"},
           "mainEntity": {"@type": "ItemList", "numberOfItems": n, "itemListElement": items}},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "トップ", "item": cfg.BASE_URL + "/"},
              {"@type": "ListItem", "position": 2, "name": "型番ページ一覧", "item": cfg.canonical_url(rel)}]}]
    extra = "".join(f'<script type="application/ld+json">{json.dumps(d, ensure_ascii=False)}</script>\n' for d in ld)
    chrome.write_page(rel, chrome.page_html(
        extra_head=extra, title=f"管楽器 現行{n}型番の型番ページ一覧｜{cfg.SITE_NAME}",
        description=(f"吹奏楽の管楽器 現行{n}型番の型番ページ一覧。楽器種→ブランドの順に、税込希望小売価格・仕様・付属品・隣接型番・出典をまとめたページへ進めます。"
                     "並びは税込定価の安い順です。"),
        rel_path=rel, body=body, current="models"))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    keep = set()
    for m in db.MODELS:
        keep.add(Path(generate(m)).name)
    gen_index_page()
    keep.add("index.html")
    d = chrome.SITE_DIR / "models"
    removed = 0
    for p in d.glob("*.html"):
        if p.name not in keep:
            p.unlink()
            removed += 1
    print(f"型番ページ {len(db.MODELS)} 本（現行{len(db.CURRENT)}・終了{len(db.MODELS) - len(db.CURRENT)}は noindex）＋一覧1 を生成（古いHTML {removed} 件を削除）")


if __name__ == "__main__":
    main()
