# -*- coding: utf-8 -*-
"""実売価格の読み出し口（管楽器図鑑）。

refresh_prices.py（楽天・Yahoo!の公式API）が ナレッジ/楽天価格.json を作っていればそれを使う。
無ければ何も返さない＝表示は「実売の最安値」行自体を出さない（未取得の行を681ページに並べない）。

🔴 このサイトが載せてよいのは「実売の最安値＋確認した店（モール）＋確認日」まで。レビューや出品件数は載せない。
"""
from __future__ import annotations

import json
from pathlib import Path

_NAV = Path(__file__).parent.parent / "ナレッジ"
_F = _NAV / "楽天価格.json"

_DATA: dict = {}
FETCHED: str = ""
SOURCE: str = ""

if _F.exists():
    try:
        _raw = json.loads(_F.read_text(encoding="utf-8"))
        FETCHED = _raw.get("fetched", "")
        SOURCE = _raw.get("source", "")
        _DATA = {r["slug"]: r for r in _raw.get("models", []) if r.get("shops")}
    except Exception:
        _DATA = {}

HAS_API = bool(_DATA)


def of(slug: str) -> dict:
    return _DATA.get(slug, {})


def min_yen(slug: str) -> str:
    r = _DATA.get(slug)
    return f"¥{r['min']:,}" if r and r.get("min") else ""


def min_int(slug: str):
    r = _DATA.get(slug)
    return r.get("min") if r else None


def shops(slug: str) -> int:
    return _DATA.get(slug, {}).get("shops", 0)


def malls(slug: str) -> str:
    ms = _DATA.get(slug, {}).get("malls") or []
    return "と".join(ms) if ms else "楽天市場"


def cheapest(slug: str) -> dict:
    """{"url","shop","mall"}（最安の出品）。無ければ空dict。"""
    r = _DATA.get(slug) or {}
    if not r.get("cheapest_url"):
        return {}
    return {"url": r["cheapest_url"], "shop": r.get("cheapest_shop", ""), "mall": r.get("cheapest_mall", "")}


def urls(slug: str) -> dict:
    """モールごとの代表URL（最安の出品）。{"楽天市場": url, "Yahoo!ショッピング": url}"""
    out = {}
    for it in (_DATA.get(slug) or {}).get("items", []):
        out.setdefault(it.get("mall", ""), it.get("url", ""))
    return out


def available(slug: str) -> bool:
    return bool(_DATA.get(slug, {}).get("shops"))
