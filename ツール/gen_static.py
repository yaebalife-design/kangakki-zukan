# -*- coding: utf-8 -*-
"""固定ページの生成（管楽器図鑑）:
  about.html / data.html / disclaimer.html / privacy.html / 404.html

嘘ゼロの適用:
  ・アクセス解析は GA4_ID が空の間は「導入していない」と書く
  ・Amazon規約5条文言はポリシーページ（disclaimer）に先行掲載し、リンクを置くまでは「提携審査後に表示」と併記
  ・型番数・充足率は kangakki_db から計算して埋める
"""
import re
import sys

import site_config as cfg
import site_chrome as chrome
import kangakki_db as db
import figures
from gen_index import newcard_html, idx_tabs_html, sorted_articles
from render import esc


def contact_html() -> str:
    if cfg.CONTACT_FORM:
        return ('<a href="contact.html">お問い合わせフォーム</a>　※メールアドレスは掲載していません。いただいた内容は運営者だけが見られる場所に届きます')
    return "お問い合わせ窓口は準備中です"


def gen_about():
    rel = "about.html"
    s = db.stats()
    desc = (f"{cfg.SITE_NAME}の運営方針。メーカー公式・日本の正規代理店・公式カタログだけを出典にする理由、"
            "税込希望小売価格と改定日の扱い、「メーカー未記載」の定義、音の良し悪しを書かない理由、訂正依頼の窓口をまとめています。")
    operator = cfg.OPERATOR_NAME or "公開時に記載します（準備中）"
    body = f"""  <p class="crumb"><a href="index.html">トップ</a> &gt; このサイトについて</p>
  <p class="prnote">{cfg.NOTICE_PR}</p>
  <div class="measure">
    <h1>このサイトについて</h1>
    <p class="meta"><span>最終改定：<b>{cfg.STATIC_UPDATED}</b></span></p>

    <h2 id="about">何をしているサイトか</h2>
    <p>「{cfg.SITE_NAME}」は、吹奏楽で使う管楽器の現行型番（{s['n_current']}型番・{s['n_brands']}ブランド・{s['n_groups']}楽器種）の税込希望小売価格と仕様を、
    <b>メーカー公式ページ・日本の正規代理店の製品ページ・公式カタログや取扱説明書のPDFだけ</b>を出典に横断できるようにした個人運営のデータベースです。</p>
    <p>読者は「YAS-280とYAS-380の違い」「トランペットの値段の相場」で調べている吹奏楽部の中高生と保護者、大人の趣味で楽器を選ぶ方、買い替えで旧楽器を手放す方を想定しています。
    <b>メーカーが公表している定価と仕様、隣り合う型番との差分</b>を並べ、ご自身で判断できる材料をそろえることが目的です。</p>

    <h2 id="policy">編集方針</h2>
    <div class="tblcard"><table class="minitbl">
      <tr><th scope="row">一次情報だけ</th><td>定価・調子・仕上げ・材質・付属品・機構は、メーカー公式ページ・日本の正規代理店の製品ページ・公式カタログPDFで確認できた値だけを書きます。楽器店ページしか見つからない型番は「二次情報」と表示します。</td></tr>
      <tr><th scope="row">価格は3点セット</th><td>「税込希望小売価格」「改定日（無い型番は『改定日はメーカー未記載』と当サイトの確認日）」「出典」を必ず並べます。「時価」「オープン価格」はメーカーの表記のままです（<a href="data.html#price">価格の扱い</a>）。</td></tr>
      <tr><th scope="row">「メーカー未記載」</th><td>確認しても記載が見つからなかった項目は空欄にせず「—（メーカー未記載）」と表示します。推測値・「約」の勝手な補完はしません（<a href="data.html#na">定義</a>）。</td></tr>
      <tr><th scope="row">音の良し悪しを書かない</th><td>音色・鳴りやすさ・吹きやすさ・上達しやすさは実証できないため書きません。書けるのは仕様・価格・メーカー表記と、メーカー・楽器店の表現の引用だけです。</td></tr>
      <tr><th scope="row">「後継」を断定しない</th><td>「後継」と書くのはメーカーが明記している場合（セルマー）だけです。他社は発売年・カタログ掲載の推移として系譜を示します。</td></tr>
      <tr><th scope="row">レビューを転載しない</th><td>通販サイトのレビュー・口コミは引用しません。実売価格は公式APIで確認できた最安値だけを、確認した店と確認日つきで載せます。</td></tr>
      <tr><th scope="row">広告の明示</th><td>アフィリエイトリンクを含むページにはPR表記を掲載します（<a href="disclaimer.html">免責事項・広告表記</a>）。</td></tr>
    </table></div>

    <h2 id="how">記事の作り方</h2>
    <p>メーカー公式サイト・正規代理店の製品ページ・公式カタログPDFから定価と仕様を収集してデータベースに整理し、表と記事を生成しています。
    掲載する数値はすべて出典URLと確認日を各ページの「出典」欄に示し、公開前に断定表現・リンク切れ・出典の有無・「メーカー未記載」の割合を機械的に検査したうえで、<b>最終確認と公開の判断は運営者が行っています</b>。体験談は載せていません。</p>

    <h2 id="operator">運営者</h2>
    <div class="tblcard"><table class="minitbl">
      <tr><th scope="row">運営形態</th><td>個人運営</td></tr>
      <tr><th scope="row">運営者名</th><td>{operator}</td></tr>
      <tr><th scope="row">運営開始</th><td>2026年9月</td></tr>
      <tr><th scope="row">お問い合わせ</th><td>{contact_html()}</td></tr>
    </table></div>

    <h2 id="contact">訂正・削除のご依頼</h2>
    <p>掲載内容に誤りがある場合、またメーカー・楽器店・権利者の方からの訂正・削除のご依頼は、上記のお問い合わせ窓口までお願いします。
    原則として3営業日以内に内容を確認し、公式の資料に照らして訂正または削除します。対応したページは最終更新日を更新します。</p>
    <p class="soft">{cfg.NOTICE_INDEPENDENT}</p>
  </div>"""
    chrome.write_page(rel, chrome.page_html(title=f"このサイトについて｜{cfg.SITE_NAME}", description=desc, rel_path=rel, body=body,
                                            current="about", extra_head=chrome.crumb_jsonld(rel, "このサイトについて")))


def gen_data():
    rel = "data.html"
    s = db.stats()
    cols = [
        ("msrp_jpy", "税込希望小売価格", "金額・オープン価格・時価のいずれかを公表している割合。改定日の有無は下の価格の節"),
        ("key", "調子", ""),
        ("finish", "仕上げ", "メーカー表記のまま（ラッカー／銀メッキ／金メッキ 等）"),
        ("body_material", "管体材質", "木管が主。金管はベル材質の列"),
        ("bell_material", "ベル材質", "金管が主"),
        ("accessories", "付属品", "ケース・マウスピース等。型番まで書くメーカーと品目だけのメーカーがある"),
        ("series", "シリーズ名", "メーカーがグレードに付けた名前"),
        ("mechanism", "機構・仕様の要点", "キイ・トリガー・バルブ等のメーカー表記"),
        ("pdf_urls", "カタログ・取説PDF", "公式サイトで公開されているもの"),
        ("key_system", "キイシステム（木管）", "フルート・クラリネットが主"),
        ("bell_diameter_raw", "ベル径（金管）", ""),
        ("bore_raw", "ボア（金管）", ""),
        ("weight_kg", "重量", "公表率が低いため比較の列にしない"),
        ("target_level", "対象レベル", "公表率が低いため比較の列にしない"),
    ]
    trs = "\n".join(f'      <tr><th scope="row">{label}</th><td class="n">{(1 - db.na_rate(db.CURRENT, [k])) * 100:.0f}%</td><td>{note or "—"}</td></tr>'
                    for k, label, note in cols)
    n_price = sum(1 for m in db.CURRENT if m["msrp_kind"] == "price")
    n_open = sum(1 for m in db.CURRENT if m["msrp_kind"] == "open")
    n_jika = sum(1 for m in db.CURRENT if m["msrp_kind"] == "jika")
    n_dated = sum(1 for m in db.CURRENT if m.get("msrp_date"))
    n_sec = sum(1 for m in db.CURRENT if m["is_secondary"])
    n_unv = sum(1 for m in db.CURRENT if m["unverified"] or m["unverified_spec"])
    score_rows = "\n".join(f'      <tr><th scope="row">{esc(label)}</th><td>1点</td></tr>' for label, _fn in db.TRANSPARENCY_FIELDS)
    body = f"""  <p class="crumb"><a href="index.html">トップ</a> &gt; データの作り方</p>
  <p class="prnote">{cfg.NOTICE_PR}</p>
  <div class="measure">
    <h1>データの作り方・出典方針</h1>
    <p class="meta"><span>データ取得日：<b>{cfg.DB_FETCHED}</b></span><span>最終改定：<b>{cfg.STATIC_UPDATED}</b></span></p>

    <h2 id="scope">対象</h2>
    <p>吹奏楽で使う管楽器（{s['n_groups']}楽器種）のうち、メーカー公式ページ・日本の正規代理店の製品ページ・公式カタログで
    現行品と確認できた <b>{s['n_current']}型番（{s['n_brands']}ブランド）</b>を対象にしています。
    生産終了・在庫限りと表記された型番は<a href="discontinued.html">別の一覧</a>に分けて{s['n_rows'] - s['n_current']}行を保持しています。
    国産フルート専門メーカー（ムラマツ・パール・アルタス・サンキョウ・ミヤザワ）とクランポンのクラリネット本体は今後追加します。</p>

    <h2 id="sources">出典の優先順位</h2>
    <ol>
      <li><b>メーカー公式の製品ページ・仕様ページ</b>（ヤマハ・ヤナギサワ・フォレストーン等の国内メーカー、海外メーカーの日本語公式）</li>
      <li><b>公式カタログ・取扱説明書のPDF</b>（公開されているもの。ヤマハは取扱説明書とカタログの両方を回収）</li>
      <li><b>日本の正規代理店の製品ページ・価格表</b>（セルマー・バック・アンティグアは野中貿易、ジュピターはグローバル、キャノンボールはクロサワ楽器店の輸入卸、シャトーはホスコ、P.モーリアはダク）</li>
      <li><b>発売元（自社ブランド）の製品ページ</b>（Jマイケル＝マックコーポレーション、ケルントナー＝キョーリツ、フェスティ＝島村楽器、マルカート＝下倉楽器、ソレイユ＝キョーリツ）</li>
      <li><b>楽器店ページ（二次情報）</b>：正規代理店を確認できないブランドのみ（現行{n_sec}型番）。表では「二次情報」フラグを付けます</li>
    </ol>
    <p>通販サイトのレビュー・口コミは引用しません。Wikipediaも使いません。発売元のサイトを取得できず「未確認」のまま残る型番が{n_unv}型番あり、表では「仕様未確認」フラグを付けています。</p>

    <h2 id="price">価格は「税込希望小売価格＋改定日＋出典」の3点セット</h2>
    <div class="tblcard"><table class="minitbl">
      <tbody>
      <tr><th scope="row">税込希望小売価格</th>
          <td>メーカー（または日本の正規代理店）が公表している定価です。現行{s['n_current']}型番のうち<b>{n_price}型番</b>が金額を公表し、
          {n_open}型番が「オープン価格」、{n_jika}型番が「時価（お問い合わせ）」です。どちらもメーカーの表記のまま載せ、当サイトは金額を推測しません。
          実際の販売価格は店ごとに異なります。</td></tr>
      <tr><th scope="row">改定日・基準日</th>
          <td>同じ型番で定価が複数並存することがあるため（改定前後の値が各所に残る）、メーカー・代理店が公表している改定日または価格の基準日を併記します。
          公式ページに日付が無い型番は<b>「改定日はメーカー未記載」として当サイトの確認日だけを出します</b>（現行{n_dated}型番に日付あり）。研究用に閲覧した日付を改定日として書くことはしません。</td></tr>
      <tr><th scope="row">実売の最安値</th>
          <td>楽天市場・Yahoo!ショッピングの公式APIで型番一致の出品を確認できた型番だけ、いちばん安かった価格を「確認した店（モール）」「確認日」つきで載せます。
          送料・ポイント還元は含みません。「◯◯用」「専用」のマウスピース・リガチャー・ケース・リード等の部品出品は除外し、定価の40%を下限にして部品の誤検知を防いでいます。取得できない型番はこの行を出しません。</td></tr>
      </tbody>
    </table></div>

    <h2 id="band">価格帯の区分（当サイトの区分）</h2>
    <p>型番ページとカタログの絞り込みで使っている価格帯は、当サイトが税込希望小売価格を機械的に分けたものです。メーカーの分類ではなく、楽器の格付けでもありません。
    定価を公表していない型番（オープン価格・時価・未記載）は「{esc(db.PRICE_BAND_LABEL["none"])}」にまとめています。</p>
    <div class="tblcard"><table class="minitbl keep">
      <thead><tr><th scope="col">区分</th><th scope="col">税込希望小売価格</th><th scope="col">現行の型番数</th></tr></thead>
      <tbody>
{chr(10).join(f'      <tr><th scope="row">{esc(l)}</th><td>{"" if a == 0 else f"¥{a:,} 以上 "}{f"¥{b:,} 未満" if b < 10 ** 11 else ""}</td><td class="n">{sum(1 for m in db.CURRENT if db.price_band(m) == k)}</td></tr>' for k, l, a, b in db.PRICE_BANDS)}
      <tr><th scope="row">{esc(db.PRICE_BAND_LABEL["none"])}</th><td>金額の公表なし</td><td class="n">{sum(1 for m in db.CURRENT if db.price_band(m) == "none")}</td></tr>
      </tbody>
    </table></div>

    <h2 id="na">「メーカー未記載」「未確認」「二次情報」の定義</h2>
    <div class="note"><b>「—（メーカー未記載）」</b>＝メーカー公式ページ・カタログ・取扱説明書（公開されているもの）を確認したうえで、その項目の記載が見つからなかったことを示します。推測値・「約」の勝手な補完はしていません。</div>
    <div class="note"><b>「—（未確認）」</b>＝当サイトがその項目をまだ確認できていないことを示します（発売元のサイトを取得できなかった型番）。「未記載」とは区別しています。</div>
    <div class="note"><b>「二次情報」</b>＝メーカー・正規代理店の日本語ページに到達できず、楽器店ページを出典にしている型番です。数値はその表記のままです。</div>
    <p>メーカーが公表していない項目があること自体を、当サイトは判断材料として明示します。たとえば重量と対象レベルは大半のメーカーが公表していないため、比較の列にしていません。</p>

    <h2 id="fill">列ごとの公表率（現行{s['n_current']}型番）</h2>
    <div class="tblcard"><table class="minitbl keep">
      <thead><tr><th scope="col">列</th><th scope="col">公表率</th><th scope="col">備考</th></tr></thead>
      <tbody>
{trs}
      </tbody>
    </table></div>
    <p class="tnote">公表率＝メーカー・正規代理店の資料で記載を確認できた型番の割合（取得日 {cfg.DB_FETCHED}）。「未確認」の型番は未記載側に数えています。</p>

    <h2 id="generation">世代・派生・「後継」の扱い</h2>
    <p>型番のサフィックス（YTR-8335 の LA／RS／GS／WS、YAS-82Z の ZA／ZB／ZUL など）は<b>メーカーの型番表記どおり</b>に一覧化し、意味はメーカーの仕上げ欄・型番表記の引用で示します。
    「後継」と書くのは、メーカーが製品ページで前身・「後継」を明記している場合（セルマー）だけです。ヤマハ等の世代（初代／II／III）は発売年・カタログ掲載の推移として示し、断定しません。</p>

    <h2 id="score">公表情報の充実度スコアの数え方（{db.SCORE_MAX}点満点）</h2>
    <p>各型番の「公表情報の充実度」スコアは、メーカー・正規代理店が公表している情報の充実度を次の基準で機械的に数えたものです。性能や音の優劣ではありません。</p>
    <div class="tblcard"><table class="minitbl">
{score_rows}
      <tr><th scope="row">取扱説明書PDFの公開</th><td>2点</td></tr>
      <tr><th scope="row">カタログPDFの公開</th><td>1点</td></tr>
      <tr><th scope="row">価格の改定日・基準日の明記</th><td>1点</td></tr>
      <tr><th scope="row">一次情報（メーカー・正規代理店）で確認できる</th><td>1点（楽器店ページのみは0点）</td></tr>
    </table></div>
    <p class="tnote">このスコアは「買う前に公式資料で分かることの多さ」を表します。並び順の既定はスコア順ではなくブランド→楽器種→定価順です。</p>

    <h2 id="figures">仕様表の項目が指す部位</h2>
    <p>当サイトの図は仕様表の項目がどの部位を指すかを示す模式図です。</p>
{figures.woodwind_terms()}
{figures.brass_terms()}

    <h2 id="update">更新</h2>
    <p>年1回、各メーカーの製品一覧ページと価格表を確認して現行・終了と定価を更新します（ヤマハは毎年カタログを改定、価格改定は改定日つきで履歴を残します）。
    誤りに気づいた場合の窓口は<a href="about.html#contact">このサイトについて</a>にあります。</p>
  </div>"""
    chrome.write_page(rel, chrome.page_html(
        title=f"データの作り方・出典方針・「メーカー未記載」の定義｜{cfg.SITE_NAME}",
        description=(f"管楽器 現行{s['n_current']}型番のデータベースの出典方針。メーカー公式・正規代理店・カタログPDFの優先順位、税込希望小売価格と改定日の扱い、"
                     "「メーカー未記載」「未確認」「二次情報」の定義、列ごとの公表率、採点基準をまとめています。"),
        rel_path=rel, body=body, current="about"))


def gen_disclaimer():
    rel = "disclaimer.html"
    desc = (f"{cfg.SITE_NAME}の免責事項と広告表記。Amazonアソシエイト・楽天市場・Yahoo!ショッピング・楽器店・買取サービスのアフィリエイトプログラムの利用、"
            "掲載情報の確認日と正確性、購入前の試奏、訂正依頼の窓口について。")
    pending = ("" if cfg.SHOW_AFFILIATE_LINKS else
               '<p class="soft">※楽天市場・Yahoo!ショッピング・楽器店・買取サービスのアフィリエイトプログラムは提携申請中です。承認後に購入・査定リンクを有効化します（それまでリンクは表示されません）。</p>')
    # 規約5条の文言の出し方は3段階。提携前に「収入を得ています」と断定しない一方、
    # もしもの審査は「申請時点でこの文言が載っていること」を求めるので、申請中は断定形＋注記を併記する（マスター手順 第5章）
    if cfg.USE_AMAZON:
        amazon_line = f"<p>{cfg.NOTICE_AMAZON}</p>"
    elif getattr(cfg, "AMAZON_APPLYING", False):
        amazon_line = (f"<p>{cfg.NOTICE_AMAZON}</p>"
                       '<p class="soft">※現在、Amazonアソシエイトの提携審査に申請中です。Amazonへのリンクは審査が完了してから表示します。</p>')
    else:
        amazon_line = ('<p class="soft">※Amazonアソシエイトは提携審査の申請前です。審査が完了してリンクを表示する時点で、'
                       f'「{cfg.NOTICE_AMAZON}」という規約上の表記をこの欄と全ページのフッターに掲載します。</p>')
    amazon_pending = ""
    body = f"""  <p class="crumb"><a href="index.html">トップ</a> &gt; 免責事項・広告表記</p>
  <p class="prnote">{cfg.NOTICE_PR}</p>
  <div class="measure">
    <h1>免責事項・広告表記</h1>
    <p class="meta"><span>最終改定：<b>{cfg.STATIC_UPDATED}</b></span></p>

    <h2 id="ads">広告表記</h2>
    <p><b>{cfg.NOTICE_PR}</b></p>
    {amazon_line}{amazon_pending}
    <p>当サイトは、もしもアフィリエイト（株式会社もしも）を通じて楽天市場・Yahoo!ショッピングのプログラムを、A8.net（株式会社ファンコミュニケーションズ）を通じて楽器店EC・楽器買取サービスのプログラムを利用します。
    リンク先で商品を購入・査定を申し込まれた場合、当サイトに紹介料が支払われることがあります。購入価格や査定額が変わることはありません。
    掲載する定価・仕様・出典は広告の有無に影響されません。</p>
    {pending}

    <h2 id="info">情報の取り扱いについて</h2>
    <ul>
      <li>掲載情報は、各ページに記載した<b>確認日時点</b>のメーカー・正規代理店の公表資料にもとづきます。</li>
      <li>メーカーが定価や仕様を改定した場合、当サイトの記載が追いつかないことがあります。最新情報は各メーカー公式サイトをご確認ください。</li>
      <li>税込希望小売価格は実際の販売価格ではありません。価格・在庫は変動します。最新の情報はリンク先の販売ページでご確認ください。</li>
      <li>正確な記載に努めていますが、内容の完全性を保証するものではありません。誤りに気づいた場合は訂正し、該当ページの最終更新日を更新します。</li>
      <li>リンク先の店舗・買取業者と利用者の間の取引について、当サイトは関与せず、責任を負いません。</li>
    </ul>

    <h2 id="use">楽器の選び方について</h2>
    <div class="caution">当サイトはメーカー・正規代理店が公表している定価と仕様を並べたもので、音の良し悪し・吹きやすさ・上達しやすさは判断しません。
    楽器は個体差があり、購入前の試奏を各メーカー・楽器店が推奨しています。並行輸入品・中古品はメーカー保証や修理受付の対象外になり得ます。</div>

    <h2 id="trademark">商標・メーカーとの関係</h2>
    <p>記事中の商品名・型番・ブランド名は各社の商標または登録商標です。商品を特定するための記述として使用しています。
    記事中の「」内の文言は、出典欄に示した各メーカー・代理店の資料からの引用です。</p>
    <p>{cfg.NOTICE_INDEPENDENT}</p>

    <h2 id="correction">訂正・削除のご依頼</h2>
    <p>掲載内容の訂正・削除のご依頼は<a href="about.html#contact">このサイトについての窓口</a>までお願いします。</p>
  </div>"""
    chrome.write_page(rel, chrome.page_html(title=f"免責事項・広告表記｜{cfg.SITE_NAME}", description=desc, rel_path=rel, body=body, current=""))


def gen_privacy():
    rel = "privacy.html"
    desc = (f"{cfg.SITE_NAME}のプライバシーポリシー。個人情報の取得の有無、アクセス解析、Amazonアソシエイト・もしもアフィリエイト・A8.netのCookie、"
            "ウェブフォントの利用、改定の告知方法について。")
    if cfg.GA4_ID:
        analytics = """    <p>当サイトは、Google LLCが提供するアクセス解析ツール「Google アナリティクス 4」を利用しています。
    トラフィックデータの収集のためにCookieを使用しますが、データは匿名で収集されており、個人を特定するものではありません。
    この機能は、お使いのブラウザでCookieを無効にすることで収集を拒否できます。詳細は<a href="https://policies.google.com/privacy?hl=ja" rel="noopener" target="_blank">Googleのプライバシーポリシー</a>および
    <a href="https://tools.google.com/dlpage/gaoptout?hl=ja" rel="noopener" target="_blank">Google アナリティクス オプトアウト アドオン</a>をご確認ください。</p>"""
    else:
        analytics = """    <p>現時点で、当サイトはアクセス解析ツールを導入していません。導入する場合は、ツール名・収集される情報・オプトアウト方法を本ページに追記します。</p>"""
    body = f"""  <p class="crumb"><a href="index.html">トップ</a> &gt; プライバシーポリシー</p>
  <p class="prnote">{cfg.NOTICE_PR}</p>
  <div class="measure">
    <h1>プライバシーポリシー</h1>
    <p class="meta"><span>制定：<b>2026-09-10</b></span><span>最終改定：<b>{cfg.STATIC_UPDATED}</b></span></p>

    <h2 id="personal">個人情報の取得について</h2>
    <p>閲覧するだけであれば、氏名・メールアドレス等の個人情報は取得していません。
    絞り込み・検索・比較の入力はお使いのブラウザの中だけで処理され、外部に送信されません。</p>
    <p><a href="contact.html">お問い合わせフォーム</a>から送信された場合のみ、次の情報を取得します。
    <b>お問い合わせの種類・内容（必須）</b>と、ご記入いただいた場合の<b>お名前・返信先メールアドレス・対象ページ</b>です。
    あわせて、迷惑送信を防ぐ目的で<b>接続元の国コード</b>と、<b>IPアドレスをハッシュ化した文字列</b>（元のIPアドレスに戻せない形）を記録します。</p>
    <p>これらは、掲載内容の訂正対応とご返信のためだけに使用し、第三者へ提供しません。
    保管先は運営者のみが参照できる表計算ファイルと、サイトを配信しているCloudflareのデータベースです。削除のご希望は同じフォームからお知らせください。</p>

    <h2 id="analytics">アクセス解析について</h2>
{analytics}

    <h2 id="affiliate">アフィリエイトプログラムとCookieについて</h2>
    <p>当サイトは、Amazonアソシエイト・プログラム（Amazon.co.jp）、もしもアフィリエイト（株式会社もしも）を通じた楽天市場・Yahoo!ショッピングのプログラム、
    A8.net（株式会社ファンコミュニケーションズ）を通じた楽器店・買取サービスのプログラムを利用します。
    アフィリエイトリンクを経由した場合、成果の計測のためにこれらの事業者によりCookie等が利用されることがあります。Cookieの取り扱いは各事業者のプライバシーポリシーをご確認ください。</p>

    <h2 id="fonts">ウェブフォントについて</h2>
    <p>当サイトは表示にGoogle Fontsを利用しています。フォントの配信のため、閲覧時にお使いの端末のIPアドレス等がGoogle LLCに送信されます。</p>

    <h2 id="revision">改定について</h2>
    <p>本ポリシーを改定した場合は、本ページで告知し、上記の最終改定日を更新します。</p>
  </div>"""
    chrome.write_page(rel, chrome.page_html(title=f"プライバシーポリシー｜{cfg.SITE_NAME}", description=desc, rel_path=rel, body=body, current=""))


def gen_404():
    rel = "404.html"
    recent = "\n".join(newcard_html(a, "") for a in sorted_articles()[:5])
    arts = f'  <h2>記事</h2>\n  <div class="newlist">\n{recent}\n  </div>' if recent else ""
    body = f"""  <div class="measure" style="padding-top:46px">
    <p class="prnote">{cfg.NOTICE_PR}</p>
    <h1>ページが見つかりません</h1>
    <p>お探しのページは移動または削除された可能性があります。
    <a href="index.html">トップページ</a>の全型番の表、<a href="instruments/index.html">楽器種別の一覧</a>、または下の分類からお探しください。</p>
  </div>
{idx_tabs_html("", "")}
{arts}"""
    html = chrome.page_html(title=f"ページが見つかりません｜{cfg.SITE_NAME}", description="お探しのページは見つかりませんでした。",
                            rel_path=rel, body=body, current="", noindex=True)
    html = re.sub(r'(href|src)="(?!https?:|//|#|/|mailto:)([^"]+)"', r'\1="/\2"', html)
    html = html.replace('href="/index.html"', 'href="/"')
    chrome.write_page(rel, html)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    gen_about()
    gen_data()
    gen_disclaimer()
    gen_privacy()
    gen_404()
    print("固定ページ 5枚を生成")


if __name__ == "__main__":
    main()
