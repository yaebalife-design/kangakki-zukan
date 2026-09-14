# -*- coding: utf-8 -*-
"""記事dict（articles_data.py）→ 記事HTML（articles/{slug}.html）＋記事一覧（articles/index.html）。

執筆ルール§6の4型（A 型番ページ＝gen_model／B 型番ペア差分／C 型番一覧・世代・派生／D 値段相場・選び方）を、
共通の「ブロックDSL」で組み立てる。型ごとに別テンプレを持たず、セクションに置くブロックの並びで型を表現する。

ブロックの種類:
  {"p": "…"}                          段落（HTML可）
  {"html": "…"}                       そのまま出力
  {"note": "…"} / {"caution": "…"}    囲み
  {"fig": "brass_terms"}              figures.py の自作SVG図解
  {"spec": ("brand_key", "型番")}      1型番の縦仕様表
  {"cmp": [("brand_key","型番"), …]}   横並び比較表（違う行を強調）
  {"cards": [(…), …], "why": {型番: 文}}  型番カード
  {"lineup": {"brand": "yamaha", "group": "trumpet" | "instrument": "bb_trumpet", "current": True,
              "models": [...] | "prefix": ["YTR-8335"], "cols": ["price","key_system","material"]}}  ブランド×楽器種の一覧表（定価順）
      cols に出せる列: series/price/finish/key/material/key_system/neck/bore/bell/acc/status（既定は series,price,finish,key,material,status）
  {"variants": ("brand_key", "型番")}  その型番の派生・仕上げ違い一覧
  {"pricedist": ["saxophone", …]}     楽器種ごとの定価分布（空リストで全楽器種）
  {"minitbl": [(見出し, 値), …]}       小さな表
  {"steps": [(見出し, 本文HTML), …]}   手順
  {"list": ["…", …]}                  箇条書き
  {"buy": [("brand_key","型番"), …]}   購入導線（提携前は案内文だけ）

構造化データ: Article ＋ FAQPage ＋ BreadcrumbList。FAQPage の設問数は表示FAQと同じリストから作る（qa_site が検査）。
"""
import html as htmllib
import json
import re
import sys

import site_config as cfg
import site_chrome as chrome
import kangakki_db as db
import figures
import render
import moshimo_link
import price_data
from articles_data import ARTICLES, DRAFTS


def plain(s: str) -> str:
    return " ".join(htmllib.unescape(re.sub(r"<[^>]+>", "", s)).split())


def jp_date(iso: str) -> str:
    return iso.replace("-", ".")


def block_html(b: dict, a: dict, prefix: str) -> str:
    if "p" in b:
        return f'  <p>{b["p"]}</p>'
    if "html" in b:
        return "  " + b["html"]
    if "note" in b:
        return f'  <div class="note">{b["note"]}</div>'
    if "caution" in b:
        return f'  <div class="caution">{b["caution"]}</div>'
    if "fig" in b:
        return figures.render(b["fig"])
    if "spec" in b:
        return render.spec_table_html(db.find(*b["spec"]))
    if "cmp" in b:
        return (SCROLLHINT.replace("。</p>", "。色の付いた行が違う項目です。</p>")
                + render.cmp_table_html([db.find(*r) for r in b["cmp"]], prefix=prefix, fold_na=True))
    if "cards" in b:
        why = b.get("why", {})
        cards = "\n".join(render.model_card_html(db.find(*r), prefix, {}, why.get(r[1], "")) for r in b["cards"])
        return f'{cards}\n  <p class="tnote">{cfg.NOTICE_PRICE}<br>{cfg.NOTICE_NA}</p>'
    if "lineup" in b:
        f = b["lineup"]
        rows = [m for m in (db.CURRENT if f.get("current", True) else db.MODELS)
                if (not f.get("brand") or m["brand_key"] == f["brand"])
                and (not f.get("group") or m["group_key"] == f["group"])
                and (not f.get("instrument") or m["instrument"] == f["instrument"])
                and (not f.get("models") or m["model"] in f["models"])
                and (not f.get("prefix") or m["model"].startswith(tuple(f["prefix"])))]
        rows.sort(key=lambda x: (db.INSTRUMENT_ORDER.get(x["instrument"], 99), not x["is_current"], x["msrp"] is None, x["msrp"] or 0, x["model"]))
        return SCROLLHINT + render.lineup_table_html(rows, prefix, {}, caption=f.get("caption", ""), cols=f.get("cols"))
    if "variants" in b:
        m = db.find(*b["variants"])
        rows = db.variants(m) or [m]
        base = min((r["model"] for r in rows), key=len)      # YAS-82Z の派生は「YAS-82Z」（base_model は 82 で切れる）
        return SCROLLHINT + render.lineup_table_html(rows, prefix, {}, caption=f"{base} の派生・仕上げ違い")
    if "ladder" in b:
        import ladder
        f = b["ladder"]
        rows = [m for m in (db.CURRENT if f.get("current", True) else db.MODELS)
                if (not f.get("brand") or m["brand_key"] == f["brand"])
                and (not f.get("group") or m["group_key"] == f["group"])
                and (not f.get("instrument") or m["instrument"] == f["instrument"])
                and (not f.get("models") or m["model"] in f["models"])]
        me = {db.find(*r)["slug"] for r in f.get("highlight", [])}
        return ladder.fig(ladder.lineup_ladder(rows, prefix, me=me, caption=f.get("caption", "")), f.get("note", "税込希望小売価格の階段（メーカー公表値）。棒を押すと型番ページへ。"))
    if "pair" in b:
        import gen_compare
        a2, b2 = db.find(*b["pair"][0]), db.find(*b["pair"][1])
        return f'  <p class="soft"><a href="{prefix}compare/{gen_compare.pair_slug(a2, b2)}.html">{render.esc(a2["name"])}と{render.esc(b2["name"])}の差分ページ（違う行だけ・付属品の差・FAQ）</a></p>'
    if "pricedist" in b:
        keys = b["pricedist"] or [g for g, *_ in db.INSTRUMENT_GROUPS]
        groups = []
        for g in keys:
            rows = [m for m in db.CURRENT if m["group_key"] == g]
            if rows:
                groups.append((f"{db.GROUP_LABEL[g]}（{len(rows)}型番）", rows, f"{prefix}instruments/{g}.html"))
        return render.price_dist_table_html(groups, prefix)
    if "minitbl" in b:
        trs = "\n".join(f'      <tr><th scope="row">{k}</th><td>{v}</td></tr>' for k, v in b["minitbl"])
        note = f'\n  <p class="tnote">{cfg.NOTICE_NA}</p>' if any("メーカー未記載" in v for _, v in b["minitbl"]) else ""
        return f'  <div class="tblcard"><table class="minitbl">\n{trs}\n  </table></div>{note}'
    if "steps" in b:
        lis = "\n".join(f'    <li><b>{t}</b>\n      {body}</li>' for t, body in b["steps"])
        return f'  <ol class="steps">\n{lis}\n  </ol>'
    if "list" in b:
        return "  <ul>\n" + "\n".join(f"    <li>{x}</li>" for x in b["list"]) + "\n  </ul>"
    if "buy" in b:
        out = []
        for ref in b["buy"]:
            m = db.find(*ref)
            u = price_data.urls(m["slug"])
            amazon_ok = db.BRANDS[m["brand_key"]].get("amazon") is True and m["is_current"]
            row = moshimo_link.buyrow(amazon_kw=f"{m['brand_roman']} {m['model']}", rakuten_url=u.get("楽天市場", ""),
                                      yahoo_url=u.get("Yahoo!ショッピング", ""), amazon_ok=amazon_ok)
            out.append(f'  <h3>{render.esc(m["name"])}<small>　<a href="{prefix}models/{m["slug"]}.html">型番ページ</a></small></h3>\n  {row}')
        return "\n".join(out)
    raise ValueError(f'{a["slug"]}: 未知のブロック {list(b)}')


SCROLLHINT = '  <p class="scrollhint">表は横にスクロールできます。</p>\n'


def sections_html(a: dict, prefix: str) -> str:
    out = []
    for s in a["sections"]:
        out.append(f'  <h2 id="{s["id"]}">{s["h2"]}</h2>')
        for b in s["blocks"]:
            out.append(block_html(b, a, prefix))
    return "\n".join(out)


def verdict_html(a: dict) -> str:
    v = a["verdict"]
    lis = "\n".join(f"        <li>{x}</li>" for x in v["bullets"])
    return f"""    <div class="verdict">
      <div class="vhead"><span class="tab">要点</span><span class="stamp">{jp_date(a["checked"])} 確認</span></div>
      <ul>
{lis}
      </ul>
      <div class="src">{v["src"]}</div>
    </div>"""


def toc_html(a: dict) -> str:
    items = "\n".join(f'        <li><a href="#{s["id"]}">{plain(s["h2"])}</a></li>' for s in a["sections"])
    return f'    <nav class="toc" aria-label="目次">\n      <b>この記事の内容</b>\n      <ol>\n{items}\n      </ol>\n    </nav>'


def faqs_html(a: dict) -> str:
    return "\n".join(f'  <details class="faq"><summary>{f["q"]}</summary>\n    <p>{f["a"]}</p></details>' for f in a["faqs"])


def sources_html(a: dict) -> str:
    seen, items = set(), []
    for s in a.get("sources", []):
        if s["url"] in seen:
            continue
        seen.add(s["url"])
        items.append((s["name"], s["url"], s.get("note", ""), s.get("checked", cfg.DB_FETCHED)))
    for ref in a.get("models", []) + a.get("cited_models", []):
        m = db.find(*ref)
        for u in db.sources(m)[:4]:
            if u in seen:
                continue
            seen.add(u)
            items.append((f'{m["brand_label"]}／{m["name"]}', u, "カタログ・取説PDF" if db.is_pdf(u) else db.source_kind(m), m["fetched"]))
    lis = "\n".join(f'      <li><a href="{render.esc(u)}" rel="noopener" target="_blank">{render.esc(name)}<span class="visually-hidden">（別タブで開く）</span></a>'
                    f'<span class="srcnote">{render.esc(note)}／確認日 {chk}</span></li>' for name, u, note, chk in items)
    return (f'  <details class="faq sources-wrap"><summary>出典 {len(items)} 件を表示（メーカー公式ページ・正規代理店・カタログPDF）</summary>\n'
            f'    <ol class="sources">\n{lis}\n    </ol></details>')


def related_html(a: dict) -> str:
    by_slug = {x["slug"]: x for x in ARTICLES}
    picked, seen = [], {a["slug"]}
    for s in a.get("related", []):
        if s in by_slug and s not in seen:
            seen.add(s)
            picked.append(by_slug[s])
    for x in ARTICLES:
        if len(picked) >= 4:
            break
        if x["category"] == a["category"] and x["slug"] not in seen:
            seen.add(x["slug"])
            picked.append(x)
    models = "".join(f'<li><a href="../models/{db.find(*r)["slug"]}.html">{render.esc(db.find(*r)["name"])}の型番ページ</a></li>' for r in a.get("models", []))
    cards = ""
    if picked:
        from gen_index import newcard_html
        cards = '      <div class="newlist">\n' + "\n".join(newcard_html(x, "../") for x in picked[:4]) + "\n      </div>\n"
    return f"""
    <section class="related" aria-labelledby="related-h">
      <h2 id="related-h">関連するページ</h2>
{cards}      <ul>{models}<li><a href="../category/{a['category']}.html">{cfg.CATEGORY_LABELS[a['category']]}の記事をすべて見る</a></li><li><a href="../index.html">現行全型番の表に戻る</a></li></ul>
    </section>"""


def jsonld_html(a: dict, rel_path: str) -> str:
    url = cfg.canonical_url(rel_path)
    about_url = cfg.canonical_url("about.html")
    author = ({"@type": "Person", "name": cfg.OPERATOR_NAME, "url": about_url} if cfg.OPERATOR_NAME
              else {"@type": "Organization", "name": cfg.SITE_NAME, "url": about_url})
    article = {"@context": "https://schema.org", "@type": "Article", "headline": a["title_tag"], "description": a["description"],
               "image": [f"{cfg.BASE_URL}/assets/og/{a['slug']}.png"], "datePublished": a.get("published", a["updated"]),
               "dateModified": a["updated"], "author": author,
               "publisher": {"@type": "Organization", "name": cfg.SITE_NAME, "url": cfg.BASE_URL + "/",
                             "logo": {"@type": "ImageObject", "url": f"{cfg.BASE_URL}/{cfg.LOGO_PNG_PATH}"}},
               "mainEntityOfPage": url, "inLanguage": "ja"}
    faq = {"@context": "https://schema.org", "@type": "FAQPage", "url": url,
           "mainEntity": [{"@type": "Question", "name": plain(f["q"]), "acceptedAnswer": {"@type": "Answer", "text": plain(f["a"])}} for f in a["faqs"]]}
    crumb = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "トップ", "item": cfg.BASE_URL + "/"},
        {"@type": "ListItem", "position": 2, "name": cfg.CATEGORY_LABELS[a["category"]], "item": cfg.canonical_url(f"category/{a['category']}.html")},
        {"@type": "ListItem", "position": 3, "name": plain(a["name"]), "item": url}]}
    return "".join(f'<script type="application/ld+json">{json.dumps(d, ensure_ascii=False)}</script>\n' for d in (article, faq, crumb))


def article_body(a: dict, rel_path: str) -> str:
    prefix = "../"
    cat_label = cfg.CATEGORY_LABELS[a["category"]]
    author_meta = f'<span>確認：<b><a href="../about.html">{cfg.OPERATOR_NAME}</a></b></span>' if cfg.OPERATOR_NAME else ""
    spechero = ""
    if a.get("models"):
        import catalog
        spechero = catalog.spec_hero_html([db.find(*r) for r in a["models"][:4]], prefix, {})
    return f"""  <p class="crumb measure"><a href="../index.html">トップ</a> &gt; <a href="../category/{a['category']}.html">{cat_label}</a></p>
  <p class="prnote measure">{cfg.NOTICE_PR}</p>
  <div class="measure">
    <h1>{a['title_h1']}</h1>
{verdict_html(a)}
{spechero}
    <p class="lead-p">{a['lead']}</p>
    <p class="meta"><span>最終更新：<b>{jp_date(a['updated'])}</b></span>{author_meta}</p>
{toc_html(a)}
  </div>
  <div class="measure">
{sections_html(a, prefix)}

    <h2 id="faq">よくある質問</h2>
{faqs_html(a)}

    <h2 id="sources">この記事の出典</h2>
    <p class="tnote">{cfg.NOTICE_PRICE} {cfg.NOTICE_NA}</p>
{sources_html(a)}
    <p class="soft">当サイトは音の良し悪し・吹きやすさを書きません。仕様表の項目の意味は<a href="../data.html#figures">データの作り方</a>の図で説明しています。
    掲載内容の誤り・訂正のご依頼（メーカー・楽器店・権利者の方を含む）は<a href="../about.html#contact">このサイトについての窓口</a>までお願いします。</p>
{related_html(a)}
    <a class="totop" href="#main">↑ ページの先頭へ</a>
  </div>"""


def generate(a: dict) -> str:
    rel_path = f"articles/{a['slug']}.html"
    if "｜" in a["title_tag"]:
        raise ValueError(f"{a['slug']}: title_tag に「｜」を含めない")
    html = chrome.page_html(title=f"{a['title_tag']}｜{cfg.SITE_NAME}", description=a["description"], rel_path=rel_path,
                            body=article_body(a, rel_path), current="articles", og_type="article",
                            extra_head=jsonld_html(a, rel_path), og_image=f"assets/og/{a['slug']}.png")
    chrome.write_page(rel_path, html)
    return rel_path


def gen_articles_index():
    from gen_index import newcard_html, idx_tabs_html, sorted_articles
    rel = "articles/index.html"
    if ARTICLES:
        cards = "\n".join(newcard_html(a, "../") for a in sorted_articles())
        listing = f'  <div class="newlist">\n{cards}\n  </div>'
    else:
        listing = ('  <p class="soft">記事はこれから順に公開します。先に、全型番の定価・仕様は<a href="../index.html#db">トップのカタログ</a>と'
                   '<a href="../instruments/index.html">楽器種別の一覧</a>でご覧いただけます。</p>')
    body = f"""  <p class="crumb measure left"><a href="../index.html">トップ</a> &gt; 記事一覧</p>
  <p class="prnote measure left">{cfg.NOTICE_PR}</p>
  <div class="measure left">
    <h1>記事一覧<small>（{len(ARTICLES)}本）</small></h1>
    <p class="lead-p">型番ペアの違い（YAS-280とYAS-380 など）、ブランド×楽器種の型番一覧と世代・派生、ブランド比較、値段相場の記事です。
    本文の数値は全てデータベース（メーカー公式・正規代理店の公表値）から表として描き、優劣は書きません。</p>
  </div>
{idx_tabs_html("../", "")}
  <h2>記事<small>（{len(ARTICLES)}本）</small></h2>
{listing}"""
    chrome.write_page(rel, chrome.page_html(
        title=f"管楽器の型番比較・型番一覧・値段相場の記事一覧｜{cfg.SITE_NAME}",
        description="管楽器の型番ペアの違い、ブランド×楽器種の型番一覧と世代・派生、ブランド比較、値段相場の記事一覧。本文の数値はメーカー公式・正規代理店の公表値から表として描いています。",
        rel_path=rel, body=body, current="articles", noindex=not ARTICLES))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    for a in ARTICLES:
        generate(a)
    gen_articles_index()
    keep = {f"{a['slug']}.html" for a in ARTICLES} | {"index.html"}
    removed = 0
    d = chrome.SITE_DIR / "articles"
    if d.exists():
        for p in d.glob("*.html"):
            if p.name not in keep:
                p.unlink()
                removed += 1
    print(f"記事 {len(ARTICLES)} 本＋一覧1 を生成（未着手 {len(DRAFTS)} 本は除外・古いHTML {removed} 件を削除）")


if __name__ == "__main__":
    main()
