# -*- coding: utf-8 -*-
"""トップ（＝全型番のカタログ＋絞り込み）／楽器種別ページ（instruments/）／ブランド一覧（brands.html）／
終了型番一覧（discontinued.html・noindex）／カテゴリ索引（category/）を生成する。

設計判断（2026-09-10）: ハブ＝「楽器種×ブランド×価格帯の全型番表と絞り込み」をトップに置く。
  ・楽器種ごとのブランド横断一覧（instruments/<group>.html）が「型番 一覧」「値段 相場」系の入口
  ・件数・型番数・価格の統計は全てDBから計算する（数字の手打ちなし）
  ・記事のないカテゴリは「準備中」と明示して noindex
"""
import json
import sys
from collections import defaultdict

import site_config as cfg
import site_chrome as chrome
import kangakki_db as db
import render
import catalog
import figures
import ladder
import gen_compare
import instrument_art
from articles_data import ARTICLES
from render import esc


def sorted_articles(arts=None):
    arts = ARTICLES if arts is None else arts
    return sorted(arts, key=lambda a: a["updated"], reverse=True)


def newcard_html(a: dict, prefix: str) -> str:
    cat = cfg.CATEGORY_LABELS[a["category"]]
    return f"""    <a class="newcard" href="{prefix}articles/{a['slug']}.html">
      <span class="cat">{cat}</span>
      <span class="name">{esc(a['name'])}</span>
    </a>"""


def cat_counts() -> dict:
    counts = defaultdict(int)
    for a in ARTICLES:
        counts[a["category"]] += 1
    return counts


def idx_tabs_html(prefix: str, current_key: str = "", nav_id: str = "") -> str:
    counts = cat_counts()
    tabs = []
    for key, label in cfg.CATEGORIES:
        if counts[key] == 0:
            tabs.append(f'      <span>{label}（準備中）</span>')
            continue
        cur = ' class="on" aria-current="page"' if current_key == key else ""
        tabs.append(f'      <a href="{prefix}category/{key}.html"{cur}>{label}<i>{counts[key]}</i></a>')
    idattr = f' id="{nav_id}"' if nav_id else ""
    return f'    <nav class="idx-tabs"{idattr} aria-label="記事のカテゴリ">\n' + "\n".join(tabs) + "\n    </nav>"


def jsonld(*docs) -> str:
    return "".join(f'<script type="application/ld+json">{json.dumps(d, ensure_ascii=False)}</script>\n' for d in docs)


def brandchips_html(prefix: str = "") -> str:
    counts = defaultdict(int)
    for m in db.CURRENT:
        counts[m["brand_key"]] += 1
    chips = [f'    <a href="{prefix}brands.html#bk-{k}" data-brand="{k}">{esc(db.BRANDS[k]["label"])}<i>{counts[k]}</i></a>'
             for k in sorted(counts, key=lambda k: -counts[k])]
    return '  <div class="chips">\n' + "\n".join(chips) + "\n  </div>"


def _pair_diff_txt(a: dict, b: dict) -> str:
    diff, _ = gen_compare.diff_rows(a, b)
    labels = [x[0] for x in diff if x[0] != "税込希望小売価格"]
    return ("違う項目：" + "・".join(labels[:3]) + ("…" if len(labels) > 3 else "")) if labels else "定価以外にメーカー公表値の違いなし"


def _gloss() -> str:
    return """  <details class="help gloss"><summary>用語の意味（税込希望小売価格・改定日・調子・仕上げ・シリーズ・現行／生産終了）</summary>
  <dl>
    <dt>税込希望小売価格</dt><dd>メーカー（または日本の正規代理店）が公表している定価。実際の販売価格は店ごとに違います。</dd>
    <dt>改定日・基準日</dt><dd>その定価をメーカーがいつ改定・公表したか。公式ページに記載が無い型番は「改定日はメーカー未記載」として当サイトの確認日だけを出します。</dd>
    <dt>調子</dt><dd>楽器の基準音。アルトサックスは E♭、テナーサックスやトランペットは B♭、フルートは C など。</dd>
    <dt>仕上げ</dt><dd>表面処理。ラッカー／銀メッキ／金メッキ など、メーカー表記のまま。</dd>
    <dt>シリーズ</dt><dd>メーカーがそのグレードに付けている名前（スタンダード／プロフェッショナル／カスタム、Xeno、WO など）。無い型番は「メーカー未記載」。</dd>
    <dt>現行／生産終了／在庫限り</dt><dd>メーカー・代理店ページの表記をそのまま。確認日を併記しています。</dd>
  </dl></details>"""


def gen_top():
    s = db.stats()
    rows = db.MODELS           # 全行（現行＋終了）。既定は現行のみ表示、チェックを外すと全行
    by_cat = defaultdict(list)
    for a in sorted_articles():
        by_cat[a["category"]].append(a)
    secs = []
    for key, label in cfg.CATEGORIES:
        arts = by_cat.get(key)
        if not arts:
            continue
        cards = "\n".join(newcard_html(a, "") for a in arts)
        secs.append(f'  <section class="catsec" id="cat-{key}">\n    <h3>{label}<small>（{len(arts)}本）</small></h3>\n    <div class="newlist">\n{cards}\n    </div>\n  </section>')
    stats = f"""    <ul class="stats" aria-label="データベースの規模">
      <li><b>{s['n_current']}</b>現行型番</li>
      <li><b>{s['n_brands']}</b>ブランド</li>
      <li><b>{s['n_groups']}</b>楽器種<span class="s-hide">（木管5・金管8）</span></li>
      <li><b>{s['n_urls']}</b>出典URL<span class="s-hide">（公式・代理店・PDF）</span></li>
    </ul>"""
    articles_sec = ""
    if ARTICLES:
        articles_sec = f"""
  <h2 id="articles"><span class="secno">06</span>記事<small>（{len(ARTICLES)}本）</small></h2>
{idx_tabs_html("", "", "categories")}
{chr(10).join(secs)}"""
    # ヒーローの図＝実データ（現行全型番を楽器種×定価に散らした星図）。装飾ではなく、この図鑑の全体像を1枚で示す
    hero_viz = ladder.constellation(db.CURRENT, "", width=560)
    n_hero = sum(1 for m in db.CURRENT if m["msrp_kind"] == "price")
    pairs = gen_compare.all_pairs()
    kw = {}
    for bk, ma, mb in gen_compare.KW_PAIRS:
        try:
            a, b = db.find(bk, ma), db.find(bk, mb)
            kw[gen_compare.pair_slug(*sorted((a, b), key=lambda x: (x["msrp"] or 0)))] = True
        except KeyError:
            pass
    featured = [(a, b) for a, b in pairs if gen_compare.pair_slug(a, b) in kw][:9]
    pair_cards = "\n".join(
        f'    <a class="paircard" href="compare/{gen_compare.pair_slug(a, b)}.html"><span class="pc-b">{esc(a["brand_label"])}・{esc(a["instrument_label"])}</span>'
        f'<span class="pc-n">{esc(a["name"])} <i>vs</i> {esc(b["name"])}</span><span class="pc-p">¥{a["msrp"]:,} → ¥{b["msrp"]:,}<small>定価差 ¥{b["msrp"] - a["msrp"]:,}</small></span>'
        f'<span class="pc-d">{_pair_diff_txt(a, b)}</span></a>' for a, b in featured)
    # 相場：楽器種ごとのブランド別レンジ図（主要4楽器種）
    range_figs = []
    for g in ("saxophone", "trumpet", "clarinet", "flute", "trombone", "horn", "euphonium", "tuba"):
        grows = [m for m in db.CURRENT if m["group_key"] == g]      # 🔴 rows（カタログ全行）を上書きしない
        st = render.price_stats(grows)
        if not st["n"]:
            continue
        range_figs.append(f'  <details class="help rangefig"{" open" if g == "saxophone" else ""}><summary>{esc(db.GROUP_LABEL[g])}：定価あり{st["n"]}型番、¥{st["min"]:,}〜¥{st["max"]:,}（中央値 ¥{st["median"]:,}）</summary>'
                          + ladder.fig(ladder.brand_strip(grows, "", group_key=g), f"{db.GROUP_LABEL[g]}のブランド別の税込希望小売価格レンジ。点が各型番（押すと型番ページ）。<a href=\"instruments/{g}.html\">{db.GROUP_LABEL[g]}の一覧・型番ラダーへ</a>")
                          + "</details>")
    body = f"""  <div class="hero2">
    <div class="in">
      <div>
        <p class="kicker">吹奏楽の管楽器・現行{s['n_current']}型番・{s['n_brands']}ブランド</p>
        <p class="prnote">{cfg.NOTICE_PR}</p>
        <h1>{cfg.HERO_TITLE}</h1>
        <p class="lead">{cfg.HERO_LEAD}</p>
        <div class="cta"><a class="pri" href="#steps">マイ楽器を選ぶ →</a><a class="sec" href="compare/index.html">型番ペアの違い</a><a class="sec" href="#souba">値段の相場</a></div>
{stats}
      </div>
      <div class="art">{instrument_art.hero_art()}</div>
    </div>
  </div>
  <nav class="subnav" aria-label="ページ内"><a href="#steps">3ステップ</a><a href="#pairs">型番の違い</a><a href="#souba">相場</a><a href="#db">全型番カタログ</a><a href="#brands">ブランド</a></nav>

  <h2 id="steps"><span class="secno">01</span>はじめてのマイ楽器、3ステップで候補を絞る</h2>
  <ol class="steps3">
    <li><b>楽器を選ぶ</b><span>13楽器種から。楽器種ごとに全ブランドの現行型番と定価の分布が見られます。<a href="instruments/index.html">楽器種別の一覧 →</a></span></li>
    <li><b>予算の帯で絞る</b><span>下のカタログで「税込希望小売価格の帯」を選ぶと、その予算に入る型番だけになります。<a href="#db">カタログで絞る →</a></span></li>
    <li><b>1つ上のグレードと何が違うか見る</b><span>定価が隣り合う2型番の違いを、メーカー公表値の違う行だけで。<a href="compare/index.html">型番ペアの違い →</a></span></li>
  </ol>
{_gloss()}
{catalog.group_tiles_html(db.CURRENT, "", as_links=True)}

  <h2 id="pairs"><span class="secno">02</span>型番ペアの違い<small>（よく調べられている{len(featured)}組・全{len(pairs)}組）</small></h2>
  <p class="measure left">「YAS-280とYAS-380は何が違う？」に、メーカー公表値の違う項目と定価差だけで答えます。仕上げが違うだけの型番は「違いは仕上げと定価だけ」と分かります。</p>
  <div class="pairgrid">
{pair_cards}
  </div>
  <p class="soft"><a href="compare/index.html">同ブランド・同楽器種で定価が隣り合う全{len(pairs)}組を見る →</a></p>

  <h2 id="souba"><span class="secno">03</span>値段の相場<small>（楽器種×ブランドの税込希望小売価格レンジ）</small></h2>
  <p class="measure left">横軸は税込希望小売価格（対数目盛）。線がブランドの最低〜最高、点が各型番です。どのブランドがどの価格帯に型番を置いているか、同じ楽器種でも価格の幅がどれだけ違うかが一目で分かります。数字はメーカー・正規代理店の公表値だけです。</p>
  <div class="viz-dark"><div class="viz">{hero_viz}<p class="vz-cap">現行{n_hero}型番を楽器種×税込希望小売価格（対数軸）に散らした全体図。点の色はブランド、点を押すと型番ページ、楽器種名を押すと一覧へ。</p></div></div>
{chr(10).join(range_figs)}
  <p class="soft"><a href="instruments/index.html">13楽器種すべての相場と一覧 →</a></p>

  <h2 id="db"><span class="secno">04</span>全型番のカタログ<small>（現行{s['n_current']}型番・絞り込みと横並び比較）</small></h2>
  <p class="measure left">楽器種を押すと、その楽器種の型番だけに絞られます。ブランド・価格帯・型番名でも絞れ、カードの「比較に追加」で最大4型番を横並びにできます（違う行に色が付きます）。</p>
{catalog.tools_html(rows)}
  <details class="help"><summary>カードの見方：「公表項目」「公表情報の充実度」とは</summary><p><b>公表項目</b>は主要9項目（調子・仕上げ・材質・付属品・定価の金額・シリーズ名・機構の要点・ベル径／ボアまたはキイシステム／ネック・カタログや取説PDF）のうちメーカー・正規代理店が公表している数です。<b>公表情報の充実度</b>のスコアはそれに取扱説明書PDF・カタログPDF・改定日の明記・一次情報で確認できるかを加えた{db.SCORE_MAX}点満点で、公表情報の充実度を機械的に数えたものです。性能や音の優劣ではありません（<a href="data.html#score">基準</a>）。</p></details>
{catalog.catalog_html(rows, "", {})}
  <div id="table-view" hidden>
{render.db_table_shell(rows, "")}
  </div>
  <p class="tnote">{cfg.NOTICE_PRICE}<br>{cfg.NOTICE_NA}</p>
  <p class="soft">生産終了・在庫限りの型番（{s['n_rows'] - s['n_current']}行）は<a href="discontinued.html">終了型番の一覧</a>にも分けて保持しています。</p>
{catalog.tray_html()}

  <h2 id="brands"><span class="secno">05</span>ブランドから探す</h2>
  <p class="soft">チップを押すと上のカタログがそのブランドに絞り込まれます。各ブランドの発売元・代理店と出典の種類は<a href="brands.html">ブランド一覧</a>にまとめています。</p>
{brandchips_html()}
{articles_sec}

  <h2 id="figures"><span class="secno">{"07" if ARTICLES else "06"}</span>仕様表の読み方<small>（図解）</small></h2>
  <p class="soft">仕様表の項目がどの部位を指すか。詳しくは<a href="data.html">データの作り方</a>にあります。</p>
  <div class="figgrid">
{figures.render("woodwind_terms")}
{figures.render("brass_terms")}
  </div>
{catalog.CATALOG_JS}"""
    title = f"管楽器 現行{s['n_current']}型番の定価・仕様一覧（サックス・フルート・クラリネット・トランペット・トロンボーン…）｜{cfg.SITE_NAME}"
    website = {"@context": "https://schema.org", "@type": "WebSite", "name": cfg.SITE_NAME, "url": cfg.BASE_URL + "/", "inLanguage": "ja", "description": cfg.SITE_DESCRIPTION}
    org = {"@context": "https://schema.org", "@type": "Organization", "name": cfg.SITE_NAME, "url": cfg.BASE_URL + "/", "logo": f"{cfg.BASE_URL}/{cfg.LOGO_PNG_PATH}"}
    dataset = {"@context": "https://schema.org", "@type": "Dataset", "name": "管楽器 現行型番 定価・仕様データベース",
               "description": cfg.SITE_DESCRIPTION, "url": cfg.canonical_url("data.html"), "sameAs": cfg.BASE_URL + "/",
               "dateModified": cfg.DB_FETCHED, "inLanguage": "ja", "isAccessibleForFree": True,
               "license": cfg.canonical_url("disclaimer.html"),
               "creator": {"@type": "Organization", "name": cfg.SITE_NAME, "url": cfg.BASE_URL + "/"},
               "variableMeasured": ["税込希望小売価格（改定日つき）", "現行／生産終了", "楽器種", "シリーズ", "調子", "キイシステム", "管体材質", "ベル材質",
                                    "仕上げ", "ベル径", "ボア", "ネック", "付属品", "カタログ・取扱説明書PDF"]}
    chrome.write_page("index.html", chrome.page_html(title=title, description=cfg.SITE_DESCRIPTION, rel_path="index.html",
                                                     body=body, current="home", extra_head=jsonld(website, org, dataset)))


# ── 楽器種別ページ ──
def _group_rows(g: str, current_only: bool = True) -> list:
    return [m for m in (db.CURRENT if current_only else db.MODELS) if m["group_key"] == g]


def gen_instruments():
    prefix = "../"
    # index
    groups = []
    for g, label, fam, _iks in db.INSTRUMENT_GROUPS:
        rows = _group_rows(g)
        if rows:
            groups.append((f"{label}（{len(rows)}型番）", rows, f"{g}.html"))
    body = f"""  <p class="crumb measure left"><a href="../index.html">トップ</a> &gt; 楽器種別の一覧</p>
  <p class="prnote measure left">{cfg.NOTICE_PR}</p>
  <div class="measure left">
    <h1>楽器種別の一覧<small>（{len(groups)}楽器種・現行{len(db.CURRENT)}型番）</small></h1>
    <p class="lead-p">楽器種ごとに、全ブランドの現行型番を税込希望小売価格の順に並べた一覧表と、定価の分布（最低・中央値・最高）です。
    数字はすべてデータベース（メーカー公式・正規代理店の公表値）から集計しています。</p>
  </div>
{catalog.group_tiles_html(db.CURRENT, prefix, as_links=True)}
  <h2 id="dist">楽器種ごとの税込希望小売価格の分布<small>（現行型番・金額を公表しているもの）</small></h2>
{render.price_dist_table_html(groups)}
{figures.render("family_map")}"""
    rel = "instruments/index.html"
    chrome.write_page(rel, chrome.page_html(
        title=f"管楽器の楽器種別 型番一覧と定価の分布（{len(groups)}楽器種）｜{cfg.SITE_NAME}",
        description=(f"吹奏楽の管楽器{len(groups)}楽器種ごとに、全ブランドの現行型番を税込希望小売価格順に並べた一覧と、定価の最低・中央値・最高。"
                     "数字はメーカー公式・正規代理店の公表値から集計。"),
        rel_path=rel, body=body, current="instruments", extra_head=chrome.crumb_jsonld(rel, "楽器種別の一覧")))

    for g, label, fam, iks in db.INSTRUMENT_GROUPS:
        rows = _group_rows(g)
        if not rows:
            continue
        rel = f"instruments/{g}.html"
        # 細分（アルト／テナー…）ごとの価格分布
        sub = []
        for ik in iks:
            r2 = [m for m in rows if m["instrument"] == ik]
            if r2:
                sub.append((f"{db.INSTRUMENT_LABEL[ik]}（{len(r2)}型番）", r2, ""))
        # ブランド別の一覧表（定価順）
        by_brand = defaultdict(list)
        for m in rows:
            by_brand[m["brand_key"]].append(m)
        secs = []
        for bk in sorted(by_brand, key=lambda k: -len(by_brand[k])):
            r3 = sorted(by_brand[bk], key=lambda x: (x["instrument"], x["msrp"] is None, x["msrp"] or 0, x["model"]))
            lad = ""
            if 2 <= sum(1 for x in r3 if x["msrp_kind"] == "price") <= 60:
                lad = ladder.fig(ladder.lineup_ladder(r3, prefix, caption=f"{db.BRANDS[bk]['label']} {label} の税込希望小売価格"),
                                 f"{db.BRANDS[bk]['label']}の{label}・現行型番の税込希望小売価格の階段。棒を押すと型番ページへ。")
            secs.append(f'  <h3 id="b-{bk}">{esc(db.BRANDS[bk]["label"])}<small>（{len(r3)}型番）</small></h3>\n{lad}\n  <details class="help"><summary>{esc(db.BRANDS[bk]["label"])}の{len(r3)}型番を表で見る（仕上げ・調子・材質・現行）</summary>\n' + render.lineup_table_html(r3, prefix, {}) + "\n  </details>")
        strip = ladder.fig(ladder.brand_strip(rows, prefix, group_key=g), f"{label}のブランド別の税込希望小売価格レンジ。線がブランドの最低〜最高、点が各型番（押すと型番ページ）。")
        old = [m for m in db.MODELS if m["group_key"] == g and not m["is_current"]]
        old_html = ""
        if old:
            lis = "".join(f'<li><a href="../models/{esc(m["slug"])}.html">{esc(m["name"])}</a><span class="soft">　{esc(m["brand_label"])}／{esc(m["status_label"])}／{esc(db.msrp_txt(m))}</span></li>' for m in old)
            old_html = f'  <h2 id="old">生産終了・在庫限りの型番<small>（{len(old)}型番・メーカー表記）</small></h2>\n  <ul class="mlist">{lis}</ul>'
        n_brands = len(by_brand)
        st = render.price_stats(rows)
        dist_txt = (f'定価の金額を公表している{st["n"]}型番の範囲は ¥{st["min"]:,}〜¥{st["max"]:,}、中央値は ¥{st["median"]:,} です。' if st["n"] else "")
        arts = [a for a in ARTICLES if a.get("group") == g]
        arts_html = ""
        if arts:
            arts_html = '  <h2 id="articles">この楽器種の記事</h2>\n  <div class="newlist">\n' + "\n".join(newcard_html(a, prefix) for a in arts) + "\n  </div>"
        body = f"""  <p class="crumb measure left"><a href="../index.html">トップ</a> &gt; <a href="index.html">楽器種別の一覧</a> &gt; {esc(label)}</p>
  <p class="prnote measure left">{cfg.NOTICE_PR}</p>
  <div class="measure left">
    <h1>{instrument_art.icon(g, 40)}{esc(label)}の現行型番一覧<small>（{n_brands}ブランド・{len(rows)}型番・税込定価順）</small></h1>
    <p class="lead-p">{esc(label)}の現行{len(rows)}型番を、ブランドごとに税込希望小売価格の安い順で並べています（{esc(db.FAMILY_LABEL[fam])}楽器）。{dist_txt}
    仕様・付属品・改定日・出典は各型番ページにあります。絞り込みと横並び比較は<a href="../index.html?group={g}#db">トップのカタログ（この楽器種で絞り込み済み）</a>で。</p>
    <p class="tnote">{cfg.NOTICE_PRICE} {cfg.NOTICE_NA}</p>
  </div>
  <h2 id="range">値段の相場<small>（ブランド別の税込希望小売価格レンジ）</small></h2>
{strip}
  <h2 id="dist">税込希望小売価格の分布<small>（種類別）</small></h2>
{render.price_dist_table_html(sub)}
  <h2 id="lineup">ブランド別の型番ラダー<small>（税込定価順・棒を押すと型番ページ）</small></h2>
{chr(10).join(secs)}
{old_html}
{arts_html}"""
        crumb = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "トップ", "item": cfg.BASE_URL + "/"},
            {"@type": "ListItem", "position": 2, "name": "楽器種別の一覧", "item": cfg.canonical_url("instruments/index.html")},
            {"@type": "ListItem", "position": 3, "name": label, "item": cfg.canonical_url(rel)}]}
        items = [{"@type": "ListItem", "position": i, "url": cfg.canonical_url(f"models/{m['slug']}.html"), "name": m["name"]} for i, m in enumerate(rows, 1)]
        coll = {"@context": "https://schema.org", "@type": "CollectionPage", "name": f"{label}の現行型番一覧", "url": cfg.canonical_url(rel), "inLanguage": "ja",
                "mainEntity": {"@type": "ItemList", "numberOfItems": len(rows), "itemListElement": items}}
        brands_txt = "・".join(db.BRANDS[k]["label"] for k in sorted(by_brand, key=lambda k: -len(by_brand[k]))[:5])
        chrome.write_page(rel, chrome.page_html(
            title=f"{label} 型番一覧と定価（{n_brands}ブランド・現行{len(rows)}型番）｜{cfg.SITE_NAME}",
            description=(f"{label}の現行{len(rows)}型番（{brands_txt}ほか）を税込希望小売価格順に一覧。{dist_txt}"
                         "仕様・付属品・改定日・出典は各型番ページへ。").replace("　", "")[:135],
            rel_path=rel, body=body, current="instruments", extra_head=jsonld(coll, crumb)))


# ── ブランド一覧 ──
def gen_brands():
    rel = "brands.html"
    counts = defaultdict(int)
    for m in db.CURRENT:
        counts[m["brand_key"]] += 1
    keys = sorted(counts, key=lambda k: -counts[k])
    secs = []
    for k in keys:
        info = db.BRANDS[k]
        rows = [m for m in db.CURRENT if m["brand_key"] == k]
        makers = sorted({m["maker"] for m in rows})
        dists = sorted({m["distributor_jp"] for m in rows if m["distributor_jp"]})
        kinds = sorted({db.source_kind(m) for m in rows})
        groups = defaultdict(int)
        for m in rows:
            groups[m["group_key"]] += 1
        glinks = "／".join(f'<a href="instruments/{g}.html#b-{k}">{esc(db.GROUP_LABEL[g])} {n}</a>' for g, n in sorted(groups.items(), key=lambda t: -t[1]))
        amazon = {True: f"本体の掲載を確認（{db.AMAZON_CHECKED}）", False: f"本体の掲載なし・マウスピース等のみ（{db.AMAZON_CHECKED}）", None: "未確認"}[info.get("amazon")]
        n_price = sum(1 for m in rows if m["msrp_kind"] == "price")
        n_pdf = sum(1 for m in rows if m.get("pdf_urls"))
        flags = []
        if info.get("secondary"):
            flags.append("出典は楽器店ページ（二次情報）。日本の正規代理店を確認できていません")
        if info.get("unverified"):
            flags.append("発売元サイトを当サイトの環境から取得できず、型番とURL以外は未確認")
        if info.get("unverified_spec"):
            flags.append("仕様表を取得できず、価格以外は未確認")
        fl = "".join(f'<div class="caution">{esc(x)}</div>' for x in flags)
        secs.append(f"""  <section id="bk-{k}">
    <h2>{esc(info['label'])}<small>（{esc(info['roman'])}・現行 {counts[k]} 型番）</small></h2>
    {fl}
    <div class="tblcard"><table class="minitbl"><caption class="visually-hidden">{esc(info['label'])} の発売元と出典の種類</caption>
      <tr><th scope="row">メーカー</th><td>{esc("／".join(makers))}</td></tr>
      <tr><th scope="row">日本での発売元・代理店</th><td>{esc("／".join(dists)) if dists else '<span class="na">—（未確認）</span>'}</td></tr>
      <tr><th scope="row">出典の種類</th><td>{esc("／".join(kinds))}</td></tr>
      <tr><th scope="row">楽器種と型番数</th><td>{glinks}</td></tr>
      <tr><th scope="row">税込希望小売価格の金額を公表</th><td class="n">{n_price}／{counts[k]} 型番</td></tr>
      <tr><th scope="row">カタログ・取説PDFの回収</th><td class="n">{n_pdf}／{counts[k]} 型番</td></tr>
      <tr><th scope="row">Amazonでの本体の取扱</th><td>{esc(amazon)}<span class="src">ブランド単位の目視確認。型番ごとの在庫は保証しません</span></td></tr>
    </table></div>
    <p class="soft"><a href="index.html?brand={k}#db">このブランドの全型番をカタログで見る</a></p>
  </section>""")
    body = f"""  <p class="crumb measure left"><a href="index.html">トップ</a> &gt; ブランド一覧</p>
  <p class="prnote measure left">{cfg.NOTICE_PR}</p>
  <div class="measure left">
    <h1>ブランド一覧<small>（{len(keys)}ブランド）</small></h1>
    <p class="lead-p">現行型番を掲載しているブランドと、当サイトが出典にしている資料の種類（メーカー公式／日本の正規代理店／発売元公式／楽器店ページ）です。
    海外メーカーは日本の正規代理店の製品ページ・カタログを一次情報として扱い、代理店を確認できないブランドは明記しています。</p>
    <p class="tnote">{cfg.NOTICE_NA}</p>
  </div>
{brandchips_html()}
{chr(10).join(secs)}"""
    chrome.write_page(rel, chrome.page_html(
        title=f"管楽器のブランド一覧と発売元・出典の種類（{len(keys)}ブランド）｜{cfg.SITE_NAME}",
        description=(f"管楽器の現行型番を扱う{len(keys)}ブランドの一覧。各ブランドのメーカー・日本での発売元／代理店、出典の種類、"
                     "楽器種ごとの型番数、定価の公表状況、カタログPDFの回収状況を確認日つきでまとめています。"),
        rel_path=rel, body=body, current="brands", extra_head=chrome.crumb_jsonld(rel, "ブランド一覧")))


def gen_discontinued():
    rel = "discontinued.html"
    rows = [m for m in db.MODELS if not m["is_current"]]
    body = f"""  <p class="crumb measure left"><a href="index.html">トップ</a> &gt; 生産終了・在庫限りの型番</p>
  <p class="prnote measure left">{cfg.NOTICE_PR}</p>
  <div class="measure left">
    <h1>生産終了・在庫限りの型番<small>（{len(rows)}行）</small></h1>
    <p class="lead-p">メーカー・代理店が「生産終了」「在庫限り」と表記している型番を、現行型番の表から分けて保持しています。
    定価・仕様は掲載時点の表記のままです。買い替えで手放す型番を調べる方は各型番ページをご覧ください。</p>
    <p class="soft">このページは検索エンジンに索引させていません（現行型番の表を主にするため）。</p>
  </div>
{render.db_table_html(rows, "", {}, table_id="dbtable-old")}"""
    chrome.write_page(rel, chrome.page_html(
        title=f"生産終了・在庫限りの型番一覧｜{cfg.SITE_NAME}",
        description="メーカー・代理店が生産終了・在庫限りと表記した管楽器の型番を、定価・仕様の掲載時点の表記のまま保持しています。",
        rel_path=rel, body=body, current="home", noindex=True))


def listing_body(h1: str, intro: str, articles: list, current_key: str) -> str:
    prefix = "../"
    if articles:
        cards = "\n".join(newcard_html(a, prefix) for a in sorted_articles(articles))
        listing = f'  <div class="newlist">\n{cards}\n  </div>'
    else:
        listing = '  <p class="soft">この分類の記事はまだありません（準備中です）。</p>'
    return f"""  <p class="crumb measure left"><a href="{prefix}index.html">トップ</a> &gt; {h1}</p>
  <p class="prnote measure left">{cfg.NOTICE_PR}</p>
  <div class="measure left">
    <h1>{h1}</h1>
    <p class="lead-p">{intro}</p>
  </div>
{idx_tabs_html(prefix, current_key)}

  <h2>記事一覧<small>（{len(articles)}本）</small></h2>
{listing}
  <p class="soft" style="margin-top:18px"><a href="{prefix}index.html">現行全型番の表に戻る</a></p>"""


def collection_jsonld(rel: str, name: str, articles: list) -> str:
    items = [{"@type": "ListItem", "position": i + 1, "url": cfg.canonical_url(f"articles/{a['slug']}.html"), "name": a["name"]}
             for i, a in enumerate(sorted_articles(articles))]
    doc = {"@context": "https://schema.org", "@type": "CollectionPage", "name": name, "url": cfg.canonical_url(rel), "inLanguage": "ja",
           "mainEntity": {"@type": "ItemList", "itemListElement": items}}
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "トップ", "item": cfg.canonical_url("index.html")},
        {"@type": "ListItem", "position": 2, "name": name, "item": cfg.canonical_url(rel)}]}
    return jsonld(doc, crumbs)


def gen_categories():
    by_cat = defaultdict(list)
    for a in ARTICLES:
        by_cat[a["category"]].append(a)
    for key, label in cfg.CATEGORIES:
        arts = by_cat.get(key, [])
        h1 = f"{label}の記事"
        rel = f"category/{key}.html"
        intro = cfg.CATEGORY_INTRO.get(key, "")
        head = ""
        for sent in [s for s in (cfg.CATEGORY_INTRO.get(key) or "").split("。") if s.strip()]:
            if len(head) + len(sent) + 1 > 100:
                break
            head += sent.strip() + "。"
        chrome.write_page(rel, chrome.page_html(
            title=f"管楽器 {label}の記事一覧｜{cfg.SITE_NAME}", description=f"管楽器の{label}の記事{len(arts)}本。{head}",
            rel_path=rel, body=listing_body(h1, intro, arts, key), current="articles",
            extra_head=collection_jsonld(rel, h1, arts) if arts else "", noindex=not arts))
    live = {key for key, _ in cfg.CATEGORIES}
    d = chrome.SITE_DIR / "category"
    if d.exists():
        for p in d.glob("*.html"):
            if p.stem not in live:
                p.unlink()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    gen_top()
    gen_instruments()
    gen_brands()
    gen_discontinued()
    gen_categories()
    n_g = sum(1 for g, *_ in db.INSTRUMENT_GROUPS if _group_rows(g))
    print(f"トップ1＋楽器種{n_g}＋楽器種索引1＋ブランド一覧1＋終了一覧1＋カテゴリ{len(cfg.CATEGORIES)} ページを生成")


if __name__ == "__main__":
    main()
