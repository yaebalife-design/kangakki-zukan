# -*- coding: utf-8 -*-
"""楽天市場・Yahoo!ショッピングの公式APIで、現行型番の「実売の最安値」と在庫を取り直す（管楽器図鑑）。

  ・APIは `04_ブログ運用チーム/共通ツール/shop_api.py`（全サイト共通）。鍵は同フォルダの api_keys.py（公開対象外）
  ・スクレイピングではない（ローカルCLAUDE.md 絶対ルール11）
  ・結果は `ナレッジ/楽天価格.json` に書き、`price_data.py` 経由で表示に載る

🔴 載せてよいのは「実売の最安値＋確認した店（モール）＋確認日」まで。レビュー・出品件数は載せない。
🔴 実行前に、楽天のアプリ設定の Allowed websites に `*.kangakki-zukan.com` が入っていること（社長作業）。
   ワイルドカード登録では apex が 403 になるので www を名乗る（スキマー図鑑で実測）。

🔴 部品出品の誤検知対策（緩めないこと）:
   本体¥10万に対しマウスピース¥2万を最安値に取る事故を防ぐため、
   ① 「◯◯用／専用／対応」＋部品名、マウスピース・リガチャー・ケース・リード・ストラップ・スワブ等の語を含む出品を落とす
   ② 定価の40%（定価が無ければ一致出品の最高値の30%）を下限にする
   ③ 中古・並行輸入・レンタルを落とす（shop_api.is_used＋ここの正規表現）
   ④ 型番の完全一致（NFKC正規化・ハイフン無視）を要求し、より長い型番に当たる出品は別型番とみなす

使い方:
    python ツール/refresh_prices.py              … 現行全型番（851件・1件2〜4秒）
    python ツール/refresh_prices.py --slug xxx   … 1型番だけ
    python ツール/refresh_prices.py --yahoo-only … 楽天を呼ばず動作確認だけする
    python ツール/refresh_prices.py --brand yamaha
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import unicodedata
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "共通ツール"))

import shop_api
import kangakki_db as db

shop_api.set_site("www.kangakki-zukan.com")

OUT = HERE.parent / "ナレッジ" / "楽天価格.json"
MALL = {"rakuten": "楽天市場", "yahoo": "Yahoo!ショッピング"}

_PART = ("マウスピース|リガチャー|ケース|リード|ストラップ|スワブ|クリーナー|クロス|オイル|グリス|ネック|"
         "キャップ|スタンド|ミュート|ハーネス|ボディ|管体のみ|パーツ|部品|ラッカー塗料|バルブ|スライド|ピストン|"
         "頭部管|足部管|ベル|マウスパイプ|リガチャ|サムレスト|ネックストラップ|レッスン|教本|DVD|楽譜")
_ACCESSORY = re.compile(rf"(専用|用|対応|向け|に合う)[\s　]*[^\s　]{{0,10}}({_PART})|({_PART})(単品|のみ|セット)?[\s　]*(?:$|[（(【])")
_ACCESSORY2 = re.compile(rf"^(?:[^\s　]{{0,20}}[\s　])?({_PART})")
_DROP = re.compile(r"中古|USED|ユーズド|ジャンク|並行輸入|平行輸入|輸入品|レンタル|訳あり|アウトレット|展示品|B級|難あり", re.I)
_PROMO = re.compile(r"【[^】]*】|\[[^\]]*\]|ポイント[0-9０-９]*倍|[0-9０-９]+%|[0-9０-９]+％|送料無料|全国送料無料|セール|SALE")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "").lower()
    return re.sub(r"[\s\-‐‑–—_/／()（）\[\]【】,、.。・]+", "", s)


def query_of(m: dict) -> tuple:
    """(検索語, 一致条件)。日本語だけの型番名（セルマー）は型番として照合できないので None。"""
    model = m["model"]
    if re.search(r"[^\x00-\x7f]", model) and not re.search(r"[A-Za-z]{1,4}-?\d{2,}", model):
        return None, None
    brand = m["brand_roman"]
    kw = f"{brand} {model}"
    return kw, [norm(model)]


def _matches(title: str, tokens: list) -> bool:
    t = norm(title)
    return all(tok in t for tok in tokens)


def _drop(title: str) -> bool:
    return bool(_DROP.search(title) or _ACCESSORY.search(title) or shop_api.is_used(title))


_ALL = None


def _is_other_model(title: str, m: dict) -> bool:
    """出品名が、この型番より長い別の型番（YAS-280 に対する YAS-280S 等）をより具体的に指していないか。"""
    global _ALL
    if _ALL is None:
        _ALL = [(x["slug"], norm(x["model"])) for x in db.CURRENT if query_of(x)[0]]
    t = norm(title)
    mine = norm(m["model"])
    for slug, tok in _ALL:
        if slug != m["slug"] and len(tok) > len(mine) and tok.startswith(mine) and tok in t:
            return True
    return False


def _floor(m: dict, prices: list) -> int:
    if isinstance(m.get("msrp"), int) and m["msrp"] > 0:
        return int(m["msrp"] * 0.4)
    return int(max(prices) * 0.3) if prices else 0


def _pick(items: list, tokens: list, m: dict, name_key: str, price_key: str, url_key: str, shop_key: str) -> list:
    out = []
    for it in items:
        title = str(it.get(name_key) or "")
        try:
            price = int(it.get(price_key))
        except (TypeError, ValueError):
            continue
        clean = _PROMO.sub(" ", title)
        if price <= 0 or _drop(title) or not _matches(clean, tokens) or _is_other_model(clean, m):
            continue
        shop = it.get(shop_key) or ""
        if isinstance(shop, dict):
            shop = shop.get("name") or shop.get("sellerId") or ""
        out.append({"price": price, "title": title, "url": shop_api.strip_tracking(str(it.get(url_key) or "")), "shop": str(shop)})
    return out


def collect(m: dict, yahoo_only: bool = False) -> dict:
    kw, tokens = query_of(m)
    rec = {"slug": m["slug"], "name": m["name"], "brand": m["brand_key"], "model": m["model"], "keyword": kw}
    if not kw:
        rec.update({"shops": 0, "malls": [], "skipped": "型番が英数字でないため照合しない"})
        return rec
    found: dict[str, list] = {}
    if not yahoo_only:
        r = shop_api.rakuten_search_full(kw, hits=30)
        found["rakuten"] = _pick(r["items"], tokens, m, "itemName", "itemPrice", "itemUrl", "shopName")
    y = shop_api.yahoo_search_full(kw, hits=30)
    found["yahoo"] = _pick(y["items"], tokens, m, "name", "price", "url", "seller")
    allk = [(site, x) for site, lst in found.items() for x in lst]
    floor = _floor(m, [x["price"] for _, x in allk])
    dropped = [x for _, x in allk if x["price"] < floor]
    allk = [(s, x) for s, x in allk if x["price"] >= floor]
    rec["floor"] = floor
    if dropped:
        rec["floorで除外"] = [{"price": x["price"], "title": x["title"][:60]} for x in dropped[:5]]
    rec["shops"] = len(allk)
    rec["malls"] = sorted({MALL[s] for s, _ in allk})
    if allk:
        allk.sort(key=lambda t: t[1]["price"])
        prices = [x["price"] for _, x in allk]
        site, best = allk[0]
        rec.update({"min": prices[0], "max": prices[-1], "median": int(statistics.median(prices)),
                    "cheapest_url": best["url"], "cheapest_shop": best["shop"], "cheapest_mall": MALL[site],
                    "items": [{"mall": MALL[s], **x} for s, x in allk[:8]]})
    return rec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", default="")
    ap.add_argument("--brand", default="")
    ap.add_argument("--yahoo-only", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    models = [m for m in db.CURRENT]
    if a.slug:
        models = [m for m in models if m["slug"] == a.slug]
    if a.brand:
        models = [m for m in models if m["brand_key"] == a.brand]
    if not models:
        raise SystemExit("対象の型番がありません")

    old = {}
    if OUT.exists():
        old = {r["slug"]: r for r in json.loads(OUT.read_text(encoding="utf-8")).get("models", [])}

    rows = []
    for i, m in enumerate(models, 1):
        try:
            rec = collect(m, yahoo_only=a.yahoo_only)
        except Exception as e:
            print(f"[{i}/{len(models)}] {m['name']}  ⚠ {e}", flush=True)
            if m["slug"] in old:
                rows.append(old[m["slug"]])
            continue
        rows.append(rec)
        lo = f"¥{rec['min']:,}（{rec.get('cheapest_mall', '')}）" if rec.get("min") else "—"
        print(f"[{i}/{len(models)}] {rec['name']}  出品{rec['shops']}  最安 {lo}", flush=True)

    done = {r["slug"] for r in rows}
    for slug, rec in old.items():
        if slug not in done:
            rows.append(rec)

    OUT.write_text(json.dumps({"fetched": f"{date.today():%Y-%m-%d}",
                               "source": "楽天市場 商品検索API／Yahoo!ショッピング 商品検索API v3",
                               "models": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    got = sum(1 for r in rows if r.get("min"))
    print(f"\n最安値を取得できた型番 {got}/{len(rows)}  → {OUT}")


if __name__ == "__main__":
    main()
