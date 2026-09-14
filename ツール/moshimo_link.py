# -*- coding: utf-8 -*-
"""購入・買取リンクの生成（管楽器図鑑）。Amazon（アソシエイト）／楽天・Yahoo!（もしも）／A8（楽器店EC・買取）。

このサイトの方針（ローカルCLAUDE.md 絶対ルール10）:
  1. 提携完了まで SHOW_AFFILIATE_LINKS=False で運用し、False の間はもしも・A8のリンクを一切出力しない。
     🔴 href="#" のダミーは絶対に置かない
  2. Amazon は **このサイト用のトラッキングID**（site_config.AMAZON_TRACKING_ID）が入るまで1本も出さない。
     入ると USE_AMAZON=True になり、規約5条文言がフッターに出る（qa_site が整合を検査）
  3. Amazon のリンク先は型番の検索結果（ASINは持たない＝スクレイピングしない・絶対ルール11）。
     本体の掲載をメーカー横断で目視確認できたブランド（kangakki_db.BRANDS["amazon"]=True）にだけ置く。
     セルマー・ジュピターは本体の掲載が無い（マウスピースのみ）ので置かない
  4. 楽天・Yahoo!は価格APIで型番一致を確認できた商品ページへの直リンク（検索結果へ逃がさない）
  5. A8 は提携が通った案件だけ site_config の A8_SHOP_LINKS／A8_KAITORI_LINKS に入れる
"""
from urllib.parse import quote

import site_config as cfg

LINK_ATTRS = ('rel="nofollow sponsored noopener" referrerpolicy="no-referrer-when-downgrade" '
              'attributionsrc target="_blank"')
PLAIN_ATTRS = 'rel="nofollow noopener" target="_blank"'


def _moshimo_href(ids: dict, target_url: str) -> str:
    return (f"//af.moshimo.com/af/c/click?a_id={ids['a_id']}&p_id={ids['p_id']}"
            f"&pc_id={ids['pc_id']}&pl_id={ids['pl_id']}&url={quote(target_url, safe='')}")


def _moshimo_impression(ids: dict) -> str:
    return (f"//i.moshimo.com/af/i/impression?a_id={ids['a_id']}&p_id={ids['p_id']}"
            f"&pc_id={ids['pc_id']}&pl_id={ids['pl_id']}")


def _require_ids(ids: dict, store: str) -> None:
    missing = [k for k, v in ids.items() if not v]
    if missing:
        raise RuntimeError(f"SHOW_AFFILIATE_LINKS=True なのに {store} のもしもID {missing} が未設定。"
                           "site_config.py に新規発行IDを設定するか、False に戻すこと（他サイトのIDの流用は厳禁）。")


def _moshimo_button(ids: dict, store: str, url: str, cls: str, label: str, note: str = "") -> str:
    if not cfg.SHOW_AFFILIATE_LINKS or not url or not ids.get("a_id"):
        return ""
    _require_ids(ids, store)
    sub = f"<small>{note}</small>" if note else ""
    return (f'<a href="{_moshimo_href(ids, url)}" class="buybtn {cls}" {LINK_ATTRS}>{label}{sub}</a>'
            f'<img src="{_moshimo_impression(ids)}" width="1" height="1" style="border:none;" alt="" loading="lazy">')


def rakuten_button(url: str, note: str = "") -> str:
    return _moshimo_button(cfg.MOSHIMO_RAKUTEN, "楽天", url, "rkt", "楽天市場で見る", note)


def yahoo_button(url: str, note: str = "") -> str:
    return _moshimo_button(cfg.MOSHIMO_YAHOO, "Yahoo!ショッピング", url, "yh", "Yahoo!ショッピングで見る", note)


def rakuten_inline(url: str, label: str = "楽天で見る") -> str:
    if not cfg.SHOW_AFFILIATE_LINKS or not url or not cfg.MOSHIMO_RAKUTEN.get("a_id"):
        return ""
    _require_ids(cfg.MOSHIMO_RAKUTEN, "楽天")
    return f'<a href="{_moshimo_href(cfg.MOSHIMO_RAKUTEN, url)}" class="shoplink" {LINK_ATTRS}>{label}</a>'


def yahoo_inline(url: str, label: str = "Yahoo!で見る") -> str:
    if not cfg.SHOW_AFFILIATE_LINKS or not url or not cfg.MOSHIMO_YAHOO.get("a_id"):
        return ""
    _require_ids(cfg.MOSHIMO_YAHOO, "Yahoo!ショッピング")
    return f'<a href="{_moshimo_href(cfg.MOSHIMO_YAHOO, url)}" class="shoplink" {LINK_ATTRS}>{label}</a>'


# ── Amazon ──
def amazon_search_url(keyword: str) -> str:
    if not cfg.USE_AMAZON:
        return ""
    return f"https://www.amazon.co.jp/s?k={quote(keyword)}&tag={cfg.AMAZON_TRACKING_ID}"


def amazon_button(keyword: str, note: str = "") -> str:
    """型番の検索結果への Amazon リンク。トラッキングIDが無い間は空文字。"""
    u = amazon_search_url(keyword)
    if not u:
        return ""
    sub = f"<small>{note}</small>" if note else ""
    return f'<a href="{u}" class="buybtn amz" {LINK_ATTRS}>Amazonで探す{sub}</a>'


def amazon_inline(keyword: str, label: str = "Amazonで探す") -> str:
    u = amazon_search_url(keyword)
    return f'<a href="{u}" class="shoplink" {LINK_ATTRS}>{label}</a>' if u else ""


# ── A8（楽器店EC・買取） ──
def a8_buttons(kind: str) -> list:
    if not cfg.SHOW_AFFILIATE_LINKS:
        return []
    src = cfg.A8_SHOP_LINKS if kind == "shop" else cfg.A8_KAITORI_LINKS
    cls = "shop" if kind == "shop" else "kaitori"
    return [f'<a href="{u}" class="buybtn {cls}" {LINK_ATTRS}>{label}</a>' for label, u, _k in src if u and u != "#"]


# ── 通常リンク（アフィリエイトではない） ──
def shop_link(site: str, url: str, label: str) -> str:
    """購入先の通常リンク。楽天・Yahoo!は提携後にもしも経由へ切り替わる。Amazonは USE_AMAZON の間だけ。"""
    if not url:
        return ""
    if site == "amazon":
        return amazon_inline(url, label) if cfg.USE_AMAZON else ""
    if site == "rakuten" and cfg.SHOW_AFFILIATE_LINKS:
        return rakuten_inline(url, label)
    if site == "yahoo" and cfg.SHOW_AFFILIATE_LINKS:
        return yahoo_inline(url, label)
    if site in ("rakuten", "yahoo") and not cfg.SHOW_AFFILIATE_LINKS:
        return f'<a href="{url}" class="shoplink" {PLAIN_ATTRS}>{label}</a>'
    return f'<a href="{url}" class="shoplink" {PLAIN_ATTRS}>{label}</a>'


def buyrow(amazon_kw: str = "", rakuten_url: str = "", yahoo_url: str = "", amazon_ok: bool = False,
           notes: dict = None) -> str:
    """型番ページ用の購入導線。出せるボタンが1つも無ければ運営側の事情を書かず読者向けの1行案内だけを出す。
    ONのときは直下に価格変動の注記（NOTICE_SHOP）を添える（qa_site が検査）。"""
    notes = notes or {}
    btns = []
    if amazon_ok and amazon_kw:
        btns.append(amazon_button(amazon_kw, notes.get("amazon", "")))
    btns.append(rakuten_button(rakuten_url, notes.get("rakuten", "")))
    btns.append(yahoo_button(yahoo_url, notes.get("yahoo", "")))
    btns += a8_buttons("shop")
    btns = [b for b in btns if b]
    if not btns:
        return ('<p class="buynote">当サイトの購入リンクは準備中です。'
                '価格と在庫は各メーカーの正規取扱店と通販サイトで直接ご確認ください。</p>')
    return f'<div class="buyrow">{"".join(btns)}</div>\n<p class="tnote buynote-s">{cfg.NOTICE_SHOP}</p>'


def kaitori_row() -> str:
    """「この型番を売るなら」の買取導線。提携前は空文字（見出しごと出さない）。"""
    btns = a8_buttons("kaitori")
    if not btns:
        return ""
    return f'<div class="buyrow">{"".join(btns)}</div>\n<p class="tnote buynote-s">{cfg.NOTICE_KAITORI}</p>'
