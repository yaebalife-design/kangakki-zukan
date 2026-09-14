# -*- coding: utf-8 -*-
"""記事データの共通定数（確認日・DB参照キー・出典・定型文）。articles_data と記事バッチが共有する。

DB参照は (brand_key, model) のタプル。brand_key は kangakki_db.BRANDS のキー
（yamaha / yanagisawa / selmer / jupiter / cannonball / antigua / bach / jmichael / kaerntner …）。
"""

D = "2026-09-10"   # データ取得日＝確認日


def M(brand_key: str, model: str) -> tuple:
    return (brand_key, model)


# よく使う型番（記事S＝型番ペア6本・派生・型番一覧）
YAS_280 = M("yamaha", "YAS-280")
YAS_380 = M("yamaha", "YAS-380")
YAS_480 = M("yamaha", "YAS-480")
YAS_62 = M("yamaha", "YAS-62")
YTS_380 = M("yamaha", "YTS-380")
YTS_480 = M("yamaha", "YTS-480")
YCL_450 = M("yamaha", "YCL-450")
YCL_650 = M("yamaha", "YCL-650")


def src(name: str, url: str, note: str = "メーカー公式", checked: str = D) -> dict:
    return {"name": name, "url": url, "note": note, "checked": checked}


# ランキング・評価の方針（全記事共通）
NO_RANK = ("当サイトは音の良し悪し・吹きやすさ・上達しやすさを書きません。並べているのはメーカー・正規代理店が公表している"
           "税込希望小売価格と仕様（調子・仕上げ・材質・付属品・機構の要点）だけで、優劣は付けていません。")
