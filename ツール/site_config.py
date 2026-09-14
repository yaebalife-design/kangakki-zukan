# -*- coding: utf-8 -*-
"""サイト全体の設定を1箇所に集約する（管楽器図鑑）。

プロテインスキマー図鑑の site_config.py を土台に、本サイト用へ全面改修（2026-09-10）。

🔴 ID流用禁止（ローカルCLAUDE.md 絶対ルール13）:
  GA4 / GSC / もしも a_id / Amazonトラッキング / A8 / IndexNow Key は他サイトから絶対にコピーしない。
  社長がこのサイト用に新規発行するまで、すべて空文字のままにする。
  空文字の間は該当タグ・リンクを出力しない設計になっている（ダミー href="#" は置かない）。
"""

SITE_NAME = "管楽器図鑑"       # 2026-09-10 社長承認
SITE_NAME_EN = "KANGAKKI ZUKAN"

# 🔴 未取得。第一候補 kangakki-zukan.com（空き・J-PlatPatは社長作業）。kanngakki 表記は服部管楽器と紛れるので使わない。
# canonical / sitemap の生成にはこの予定ドメインを使う（ローカル生成のみ）。
BASE_URL = "https://kangakki-zukan.com"

TAGLINE = "吹奏楽の管楽器、現行全型番の定価と仕様を一次情報だけで。"
HERO_TITLE = "管楽器の型番・定価・仕様を、<br>メーカーの一次情報だけで。"
HERO_LEAD = ("吹奏楽で使うサックス・フルート・クラリネット・トランペット・トロンボーン・ホルン・ユーフォニアム・チューバの"
             "現行型番を、メーカー公式ページ・日本の正規代理店・公式カタログだけを出典に一覧にしています。"
             "税込希望小売価格は改定日つき、確認できなかった項目は推測で埋めず「メーカー未記載」と表示します。")
LOGO_SUB = "現行型番の定価・仕様データベース"

SITE_DESCRIPTION = ("吹奏楽で使う管楽器の現行全型番を、メーカー公式・日本の正規代理店・公式カタログだけを出典に横断できる"
                    "定価・仕様データベース。税込希望小売価格（改定日つき）・現行／生産終了・調子・仕上げ・付属品・隣接型番の差分を出典URLと確認日つきで掲載。")

# OG画像（gen_og.py が生成。商品画像は使わず文字と図形のみ）
OG_DEFAULT_PATH = "assets/og/default.png"
LOGO_PNG_PATH = "assets/icon-512.png"
OG_WIDTH, OG_HEIGHT = 1200, 630

# 運営者（🔴 公開前に社長が確定）
OPERATOR_NAME = "管楽器図鑑 編集部"
CONTACT_NOTE = ""
CONTACT_EMAIL = ""        # 使わない方針（フォーム＋スプレッドシートで受ける）
CONTACT_FORM = True       # contact.html ＋ site/functions/api/contact.js で受け取る

# ── 🔴 未発行ID（社長作業待ち。流用厳禁・空のままなら出力されない） ──
GA4_ID = ""
GSC_VERIFICATION = ""

# ── アフィリエイト（moshimo_link.py が参照） ──
# 提携完了まで False。False の間はもしも・A8のリンクを一切出力しない（href="#" は絶対に置かない）。
SHOW_AFFILIATE_LINKS = False

# もしもアフィリエイト ID 群（🔴 このサイト専用の新規a_id。他サイトからの流用厳禁）
MOSHIMO_RAKUTEN = {"a_id": "", "p_id": "", "pc_id": "", "pl_id": ""}
MOSHIMO_YAHOO = {"a_id": "", "p_id": "", "pc_id": "", "pl_id": ""}

# Amazonアソシエイト（🔴 このサイト用のトラッキングIDを新規発行。例 "kangakkizukan-22"）
AMAZON_TRACKING_ID = ""
# トラッキングIDが入るまで Amazon へのリンクは1本も出さない
USE_AMAZON = bool(AMAZON_TRACKING_ID)

# 🔴 もしもの Amazon 提携は「審査時点でポリシーページに規約5条の文言が載っていること」が条件（マスター手順 第5章・
#    2026-09-02 泡盛DBで否認事例を確認）。申請ボタンを押す直前に True にして本番へ反映すること。
#    True の間は disclaimer に断定形の文言＋「リンクは審査完了後に表示します」を併記する（リンク自体は出さない）。
AMAZON_APPLYING = False

# A8（楽器店EC・買取）。提携が通った案件だけ [("表示名", "A8のリンクURL", "種別")] を入れる。空なら出さない
A8_SHOP_LINKS = []       # 例 ("石橋楽器店で探す", "https://px.a8.net/svt/ejp?a8mat=…", "shop")
A8_KAITORI_LINKS = []    # 例 ("楽器の買取屋さん（無料査定）", "https://px.a8.net/svt/ejp?a8mat=…", "kaitori")

# ── カテゴリ定義（key, 表示名）。記事の category はこの key を使う ──
CATEGORIES = [
    ("pair",    "型番ペアの違い"),
    ("lineup",  "型番一覧・世代・派生"),
    ("brand",   "ブランド比較"),
    ("price",   "値段相場"),
    ("choose",  "選び方"),
]
CATEGORY_LABELS = dict(CATEGORIES)

CATEGORY_INTRO = {
    "pair": ("「YAS-280とYAS-380の違い」のように、隣り合うグレードの2型番をメーカー公表の仕様と税込希望小売価格で1表に並べます。"
             "違う行だけを強調し、どちらが良いかは書きません（音の良し悪し・吹きやすさは当サイトでは扱いません）。"),
    "lineup": ("ブランド×楽器種の現行全型番を定価順に並べ、世代の切り替わり（発売年・カタログ掲載の推移）と派生サフィックスの意味を"
               "メーカー表記の引用で示します。「後継」と書けるのはメーカーが明記しているセルマーだけです。"),
    "brand": ("ヤマハ・ヤナギサワ・セルマーのように、同じ価格帯にある型番をブランドをまたいで対応表にします。"
              "並べるのは定価・仕上げ・付属品・出典で、優劣は付けません。"),
    "price": ("楽器種ごとの税込希望小売価格の分布をデータベースから集計します。シリーズ（スタンダード／プロ／カスタム）ごとの価格帯と、"
              "中古・並行輸入の注意（一次情報）をまとめ、売るときの導線も置きます。"),
    "choose": ("吹奏楽部のマイ楽器を買う直前に迷う点を、型番とメーカー名を軸に整理します。判断材料はメーカー公表の仕様・価格・付属品だけです。"),
}

# ── 必須常設表記（ローカルCLAUDE.md 絶対ルール9 / 執筆ルール§1。qa_site.py が全ページで検査） ──
# 🔴 PR表記は「実際に広告リンクを出しているか」で切り替える。提携前に「広告を含みます」と書くと事実と食い違う（点検 2026-09-13）
HAS_AFFILIATE = SHOW_AFFILIATE_LINKS or USE_AMAZON
NOTICE_PR = ("【PR】当サイトの記事にはアフィリエイト広告（Amazon・楽天市場・楽器店・買取サービス）を含みます。" if HAS_AFFILIATE else
             "【広告について】当サイトは現在アフィリエイト広告を掲載していません。提携が完了したページには【PR】と表示します。")
NOTICE_AMAZON = f"Amazonのアソシエイトとして、{SITE_NAME}は適格販売により収入を得ています。"
NOTICE_PRICE = ("価格はメーカーが公表している税込希望小売価格です（改定日・出典を併記）。"
                "「時価」「オープン価格」はメーカーの表記のままです。実際の販売価格は店ごとに異なります。")
NOTICE_NA = ("「—（メーカー未記載）」は、メーカー公式ページ・カタログ・取扱説明書を確認したうえでその項目の記載が"
             "見つからなかったことを示します（推測では埋めていません）。「—（未確認）」は当サイトがまだ確認できていない項目です。")
# 服部管楽器（kanngakki.jp）など実在の楽器店と業態が紛れないよう、販売・買取をしないことも明示する（名称調査 2026-09-15）
NOTICE_INDEPENDENT = ("当サイトは各メーカー・楽器店・買取業者とは無関係の情報サイトです。"
                      "当サイト自身は楽器の販売・買取・修理を行っていません。"
                      "仕様・価格は各社の公式ページ・カタログ（出典欄）に基づきます。"
                      "楽器は個体差があり、購入前の試奏を各メーカー・楽器店が推奨しています。")
NOTICE_KAITORI = "査定額は楽器の状態・年式・付属品で変わります。複数社の査定を比べることをおすすめします。"
# 購入リンク行の直下（提携後）
NOTICE_SHOP = "価格・在庫は変動します。最新の価格と付属品はリンク先の商品ページとメーカー公式ページでご確認ください。"
# 並行輸入・中古（絶対ルール6。断定しない・一次情報を示す）
NOTICE_PARALLEL = ("並行輸入品・中古品は、メーカー保証や修理受付の対象外になり得ます。"
                   'たとえばヤナギサワは模倣品・並行輸入品について<a href="https://www.yanagisawasax.co.jp/information/view/741" rel="noopener" target="_blank">公式サイトで告知</a>しています（2023-02-21）。'
                   "購入前に販売店とメーカーの案内をご確認ください。")

STATIC_UPDATED = "2026-09-10"   # 固定ページの最終改定日
DB_FETCHED = "2026-09-10"       # データベースの取得日


def canonical_path(rel_path: str) -> str:
    """相対パス→本番のpretty URL（Cloudflare Pages仕様）"""
    if rel_path == "index.html":
        return "/"
    if rel_path.endswith("/index.html"):
        return "/" + rel_path[: -len("index.html")]
    if rel_path.endswith(".html"):
        return "/" + rel_path[: -len(".html")]
    return "/" + rel_path


def canonical_url(rel_path: str) -> str:
    return BASE_URL + canonical_path(rel_path)
