# -*- coding: utf-8 -*-
"""現行機種DB（ナレッジ/現行機種DB_20260910.json ＋ _追補_他サックス11ブランド.json ＋ _訂正.json）を読み、
生成スクリプトが使える形に正規化する。**このサイトのデータの正はJSONで、コードではない。**

嘘ゼロの実装（ローカルCLAUDE.md 絶対ルール1・執筆ルール§4）:
  ・値が無いセルは空欄にせず「—（メーカー未記載）」を返す。推測での補完は一切しない
  ・研究班が仕様を取得できなかったブランド（Playtech＝サイト取得不能、Soleil＝仕様表がJS描画）は
    「—（未確認）」で区別する（「未記載」＝確認したうえで無かった、とは別）
  ・訂正JSON（当チームが一次ソースを取り直した分）は本体を上書きするが、本体JSONは書き換えない
  ・価格は「税込希望小売価格（整数）」「オープン価格」「時価」「未記載」を区別する。改定日が取れない
    行は「改定日はメーカー未記載（当サイト確認日 ○）」として断定しない

用語:
  row … JSONの1型番（dict）。CURRENT は status=="current" だけ
  NA  … 「—（メーカー未記載）」の表示文字列
"""
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

KNOWLEDGE = Path(__file__).parent.parent / "ナレッジ"
DB_JSON = KNOWLEDGE / "現行機種DB_20260910.json"
ADD_JSON = KNOWLEDGE / "現行機種DB_20260910_追補_他サックス11ブランド.json"
FIX_JSON = KNOWLEDGE / "現行機種DB_20260910_訂正.json"

NA = "—（メーカー未記載）"
UNCONFIRMED = "—（未確認）"
NA_SECONDARY = "—（楽器店ページに記載なし）"

# ── ブランド定義（DBの brand 文字列 → key）。表示名・Amazon本体掲載の確認結果（設計書§3・2026-09-10）──
BRANDS = {
    "yamaha":     {"label": "ヤマハ", "roman": "YAMAHA", "db": ["YAMAHA"], "amazon": True},
    "yanagisawa": {"label": "ヤナギサワ", "roman": "YANAGISAWA", "db": ["YANAGISAWA"], "amazon": True},
    "selmer":     {"label": "セルマー・パリ", "roman": "Henri Selmer Paris", "db": ["Henri Selmer Paris（セルマー・パリ）"], "amazon": False},
    "jupiter":    {"label": "ジュピター", "roman": "JUPITER", "db": ["JUPITER"], "amazon": False},
    "cannonball": {"label": "キャノンボール", "roman": "Cannonball", "db": ["Cannonball"], "amazon": True},
    "antigua":    {"label": "アンティグア", "roman": "Antigua", "db": ["Antigua（アンティグア）"], "amazon": True},
    "bach":       {"label": "バック", "roman": "Bach", "db": ["Bach（バック）"], "amazon": True},
    "jmichael":   {"label": "Jマイケル", "roman": "J.Michael", "db": ["J.Michael"], "amazon": True},
    "kaerntner":  {"label": "ケルントナー", "roman": "Kaerntner", "db": ["Kaerntner"], "amazon": True},
    "chateau":    {"label": "シャトー", "roman": "Chateau", "db": ["Chateau"], "amazon": None},
    "forestone":  {"label": "フォレストーン", "roman": "Forestone", "db": ["Forestone"], "amazon": None},
    "pmauriat":   {"label": "P.モーリア", "roman": "P. Mauriat", "db": ["P. Mauriat"], "amazon": None},
    "rampone":    {"label": "ランポーネ＆カッツァーニ", "roman": "Rampone & Cazzani", "db": ["Rampone & Cazzani"], "amazon": None, "secondary": True},
    "playtech":   {"label": "プレイテック", "roman": "Playtech", "db": ["Playtech"], "amazon": None, "unverified": True},
    "buffet":     {"label": "ビュッフェ・クランポン", "roman": "Buffet Crampon", "db": ["Buffet Crampon"], "amazon": True},
    "festi":      {"label": "フェスティ", "roman": "Festi", "db": ["Festi"], "amazon": None},
    "marcato":    {"label": "マルカート", "roman": "Marcato", "db": ["Marcato"], "amazon": None},
    "soleil":     {"label": "ソレイユ", "roman": "Soleil", "db": ["Soleil"], "amazon": None, "unverified_spec": True},
    "eastman":    {"label": "イーストマン", "roman": "Eastman", "db": ["Eastman"], "amazon": None},
}
AMAZON_CHECKED = "2026-09-10"      # Amazon本体掲載の有無を目視確認した日（設計書§3）
BRAND_KEY = {s: k for k, v in BRANDS.items() for s in v["db"]}

# ── 楽器種の分類（DBの instrument → 表示名／グループ／木管・金管）──
INSTRUMENT_GROUPS = [
    # (group_key, 表示名, family, [instrument keys])
    ("saxophone", "サックス", "woodwind",
     ["sopranino_saxophone", "eb_sopranino_saxophone", "soprano_saxophone", "curved_soprano_saxophone",
      "alto_saxophone", "tenor_saxophone", "c_melody_saxophone", "baritone_saxophone", "bass_saxophone"]),
    ("flute", "フルート・ピッコロ", "woodwind", ["piccolo", "flute", "alto_flute", "bass_flute"]),
    ("clarinet", "クラリネット", "woodwind", ["bb_clarinet", "a_clarinet", "eb_clarinet", "alto_clarinet", "bass_clarinet"]),
    ("oboe", "オーボエ", "woodwind", ["oboe"]),
    ("bassoon", "ファゴット", "woodwind", ["bassoon"]),
    ("trumpet", "トランペット", "brass",
     ["bb_trumpet", "c_trumpet", "eb_d_trumpet", "piccolo_trumpet", "rotary_trumpet", "herald_trumpet",
      "bb_pocket_trumpet", "trumpet_gf_category", "bugle"]),
    ("cornet", "コルネット", "brass", ["cornet", "bb_cornet"]),
    ("flugelhorn", "フリューゲルホルン", "brass", ["flugelhorn", "bb_flugelhorn"]),
    ("horn", "ホルン", "brass", ["french_horn"]),
    ("trombone", "トロンボーン", "brass", ["tenor_trombone", "tenor_bass_trombone", "bass_trombone", "valve_trombone"]),
    ("euphonium", "ユーフォニアム", "brass", ["euphonium"]),
    ("baritone", "バリトン・アルトホルン", "brass", ["baritone_horn", "alto_horn"]),
    ("tuba", "チューバ", "brass", ["tuba"]),
]
GROUP_OF = {ik: g for g, _l, _f, iks in INSTRUMENT_GROUPS for ik in iks}
# 表示順（INSTRUMENT_GROUPS の定義順。文字列順だと bb より a が先に来てしまう）
INSTRUMENT_ORDER = {ik: i for i, ik in enumerate(ik2 for _g, _l, _f, iks in INSTRUMENT_GROUPS for ik2 in iks)}
GROUP_LABEL = {g: l for g, l, _f, _ in INSTRUMENT_GROUPS}
GROUP_FAMILY = {g: f for g, _l, f, _ in INSTRUMENT_GROUPS}
FAMILY_LABEL = {"woodwind": "木管", "brass": "金管"}
INSTRUMENT_LABEL = {
    "sopranino_saxophone": "ソプラニーノサックス", "eb_sopranino_saxophone": "ソプラニーノサックス",
    "soprano_saxophone": "ソプラノサックス", "curved_soprano_saxophone": "カーブドソプラノサックス",
    "alto_saxophone": "アルトサックス", "tenor_saxophone": "テナーサックス", "c_melody_saxophone": "Cメロディサックス",
    "baritone_saxophone": "バリトンサックス", "bass_saxophone": "バスサックス",
    "piccolo": "ピッコロ", "flute": "フルート", "alto_flute": "アルトフルート", "bass_flute": "バスフルート",
    "eb_clarinet": "E♭クラリネット", "bb_clarinet": "B♭クラリネット", "a_clarinet": "Aクラリネット",
    "alto_clarinet": "アルトクラリネット", "bass_clarinet": "バスクラリネット",
    "oboe": "オーボエ", "bassoon": "ファゴット",
    "bb_trumpet": "B♭トランペット", "c_trumpet": "Cトランペット", "eb_d_trumpet": "E♭/Dトランペット",
    "piccolo_trumpet": "ピッコロトランペット", "rotary_trumpet": "ロータリートランペット",
    "herald_trumpet": "ファンファーレトランペット", "bb_pocket_trumpet": "ポケットトランペット",
    "trumpet_gf_category": "G/Fトランペット", "bugle": "ビューグル",
    "cornet": "コルネット", "bb_cornet": "B♭コルネット", "flugelhorn": "フリューゲルホルン", "bb_flugelhorn": "B♭フリューゲルホルン",
    "french_horn": "ホルン", "tenor_trombone": "テナートロンボーン", "tenor_bass_trombone": "テナーバストロンボーン",
    "bass_trombone": "バストロンボーン", "valve_trombone": "バルブトロンボーン",
    "euphonium": "ユーフォニアム", "baritone_horn": "バリトン", "alto_horn": "アルトホルン", "tuba": "チューバ",
}

STATUS_LABEL = {"current": "現行", "discontinued": "生産終了", "stock_only": "在庫限り"}

# 価格帯（税込希望小売価格）。絞り込みと「値段相場」記事の集計に使う
PRICE_BANDS = [
    ("b1", "〜5万円", 0, 50_000),
    ("b2", "5〜10万円", 50_000, 100_000),
    ("b3", "10〜20万円", 100_000, 200_000),
    ("b4", "20〜40万円", 200_000, 400_000),
    ("b5", "40〜70万円", 400_000, 700_000),
    ("b6", "70万円〜", 700_000, 10 ** 12),
]
PRICE_BAND_LABEL = dict((k, l) for k, l, _a, _b in PRICE_BANDS)
PRICE_BAND_LABEL["none"] = "オープン価格・時価・未記載"

MEMO_WORDS = ("抽出不可", "要再確認", "app.js", "目視転記", "テキスト層", "取得不能", "タイムアウト", "urllib", "WebFetch",
              "None", "null", "パーサ", "extra_price", "JS描画", "Shopify",
              # DBの内部フィールド名（監査 2026-09-10 で57ページに露出していた）
              "msrp_jpy", "bell_diameter_mm", "bore_mm", "weight_kg", "pdf_urls", "body_material", "key_system", "target_level",
              "×1.1で算出", "正規輸入代理店明記は未確認", "依頼文",
              # 収集作業のメモ（点検 2026-09-13 で38ページに露出していた。Playtech 15・Forestone 22・ケルントナー 1）
              "要再取得", "要確認", "URLハンドル", "検索結果", "product_id", "コピー流用", "矛盾", "重複あり")

_DATE_RE = re.compile(r"(20\d{2})[年.\-/](\d{1,2})[月.\-/](\d{1,2})日?\s*(現在|改定|改訂)")
_DATE_YM_RE = re.compile(r"(20\d{2})年(\d{1,2})月\s*(改定|改訂|現在)")


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _slug_base(model: str) -> str:
    s = unicodedata.normalize("NFKC", model).lower()
    s = s.replace("♭", "b").replace("♯", "s")
    s = re.sub(r"[（）()【】\[\]]", " ", s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def _slugify(brand_key: str, model: str) -> str:
    s = _slug_base(model)
    if len(s) < 3 or re.search(r"[^\x00-\x7f]", model):
        # 日本語を含む型番名（セルマーの「シリーズ3 B♭テナー Gold Lacquered」等）は英数字だけでは
        # 楽器種の違いが落ちて衝突するので、元の文字列のハッシュで一意にする（並び替えで変わらない安定したURL）
        h = hashlib.sha1(model.encode("utf-8")).hexdigest()[:6]
        s = f"{s}-{h}" if s else h
    return f"{brand_key}-{s}"


def _norm_model(s: str) -> str:
    return re.sub(r"[\s\-‐‑–—_/／()（）\[\]【】,、.。・]+", "", unicodedata.normalize("NFKC", s or "")).lower()


_KEYS = ("maker", "brand", "instrument", "instrument_jp", "model", "model_label", "series", "status", "key", "key_system",
         "body_material", "bell_material", "finish", "bell_diameter_mm", "bell_diameter_raw", "bore_mm", "bore_raw",
         "neck_spec", "mechanism", "accessories", "weight_kg", "weight_raw", "height_mm_raw", "msrp_jpy", "target_level",
         "pdf_urls", "pdf_manual_urls", "pdf_catalog_urls", "predecessor", "successor", "distributor_jp", "source_url",
         "spec_url", "source_type", "fetched_at", "extra_specs", "note")


def _normalize(raw: dict, origin: str) -> dict:
    r = {k: raw.get(k) for k in _KEYS}
    r["origin"] = origin
    if r["model_label"] in (None, ""):
        r["model_label"] = r["model"]
    if r["bell_diameter_raw"] in (None, "") and isinstance(r["bell_diameter_mm"], (int, float)):
        r["bell_diameter_raw"] = f"{r['bell_diameter_mm']:g}mm"
    if r["bore_raw"] in (None, "") and isinstance(r["bore_mm"], (int, float)):
        r["bore_raw"] = f"{r['bore_mm']:g}mm"
    if r["pdf_urls"] is None:
        r["pdf_urls"] = []
    return r


def _apply_fix(r: dict, fx: dict) -> None:
    for k, v in fx["updates"].items():
        if k == "note_append":          # 元の note を残したまま末尾に足す（改定日の追記など）
            r["note"] = ((r.get("note") or "").rstrip("。 ") + "。" + v) if r.get("note") else v
            continue
        r[k] = v
    u = fx.get("source_url")
    if u and u not in (r.get("source_url") or "") and u != r.get("spec_url"):
        r["fix_source_url"] = u
    if fx.get("fetched_at"):
        r["fetched_at"] = fx["fetched_at"]
    r["fixed"] = True


def load_models() -> list:
    """本体736行＋追補（本体と重複しない型番のみ）＋訂正をマージして返す。"""
    base = _load(DB_JSON)["models"]
    add = _load(ADD_JSON)["models"]
    fix = _load(FIX_JSON)
    fixes = {(f["brand"], f["model"], f.get("instrument")): f for f in fix["updates"]}
    rules = [(re.compile(r_["model_regex"]), r_) for r_ in fix.get("rules", [])]
    strip_brands = set(fix.get("note_fixes", {}).get("strip_note_date_brands", []))

    # 重複判定は2段階（点検 2026-09-13）。
    #   ・本体に同じ（ブランド＋型番）がある行は、楽器種が違っても追補を捨てる（Cannonball SC5系＝本体の curved_soprano が正）
    #   ・それ以外は（ブランド＋楽器種＋型番）で見る。Forestone の「SX GL」はアルト／テナー／バリトンに同名があり、別型番として全て残す
    base_keys = {(BRAND_KEY.get(x.get("brand")), _norm_model(x.get("model") or "")) for x in base}
    out, seen_key, seen_slug = [], set(), {}
    for origin, rows in (("本体", base), ("追補", add), ("訂正追加", fix.get("additions", []))):
        for raw in rows:
            r = _normalize(raw, origin)
            bk = BRAND_KEY.get(r["brand"])
            if not bk:
                raise KeyError(f"BRANDS に無いブランド: {r['brand']}")
            if origin != "本体" and (bk, _norm_model(r["model"])) in base_keys:
                continue                 # 本体に同じ型番がある（Cannonball 43行）→ 本体を採る
            dedupe = (bk, r["instrument"], _norm_model(r["model"]))
            if dedupe in seen_key:
                continue
            seen_key.add(dedupe)
            fx = fixes.get((r["brand"], r["model"], r["instrument"])) or fixes.get((r["brand"], r["model"], None))
            if fx:
                _apply_fix(r, fx)
            for rx, rule in rules:
                if rule["brand"] == r["brand"] and rx.search(r["model"]):
                    _apply_fix(r, rule)
            info = BRANDS[bk]
            r["brand_key"] = bk
            r["brand_label"] = info["label"]
            r["brand_roman"] = info["roman"]
            r["is_current"] = r["status"] == "current"
            r["status_label"] = STATUS_LABEL.get(r["status"], r["status"] or "")
            r["is_secondary"] = (r.get("source_type") == "shop_secondary") or bool(info.get("secondary"))
            r["unverified"] = bool(info.get("unverified"))            # 型番とURL以外を取得できていない
            r["unverified_spec"] = bool(info.get("unverified_spec"))  # 価格以外の仕様を取得できていない
            r["family"] = GROUP_FAMILY.get(GROUP_OF.get(r["instrument"], ""), "")
            r["group_key"] = GROUP_OF.get(r["instrument"], "other")
            r["group_label"] = GROUP_LABEL.get(r["group_key"], "その他")
            r["instrument_label"] = INSTRUMENT_LABEL.get(r["instrument"], r["instrument"])
            r["name"] = r["model_label"] or r["model"]
            r["fetched"] = r.get("fetched_at") or "2026-09-10"
            r["strip_note_date"] = r["brand"] in strip_brands
            # 価格表しか出典が無い行（Cannonball＝importwind プライスリスト）は、調子が表に無く楽器種から補完されている
            # （検証 2026-09-10・ファクトチェック）。値は楽器種の標準どおりだが、出典に無いことを表示側で明示する
            r["key_inferred"] = bk == "cannonball" and "pricelist" in str(r.get("source_url") or "")
            out.append(r)

    # slug は全行そろってから決める。同じ型番名が複数の楽器種にある場合（Forestone「SX GL」＝アルト／テナー／バリトン）は
    # 楽器種をURLに入れて区別する。連番だとどれがどの楽器種か分からないため
    dup = Counter(_slugify(r["brand_key"], r["model"]) for r in out)
    for r in out:
        s = _slugify(r["brand_key"], r["model"])
        if dup[s] > 1:
            s = f"{s}-{_slug_base(r['instrument']) or r['instrument']}"
        n = seen_slug.get(s, 0)
        seen_slug[s] = n + 1
        r["slug"] = s if n == 0 else f"{s}-{n + 1}"
        _price_fields(r)
    return out


# ── 価格 ──
def _price_fields(r: dict) -> None:
    v = r.get("msrp_jpy")
    note = str(r.get("note") or "")
    r["msrp"] = None
    r["msrp_ref"] = None          # 「時価」型番の参考値（代理店の為替連動価格一覧）。定価としては出さない
    r["msrp_converted"] = "×1.1で算出" in note     # 楽器店の税抜表示を当サイトが×1.10した換算値（Rampone&Cazzani・二次情報）
    # 出典が「希望小売価格」ではなく「販売価格」と書いている行（ソレイユ・フェスティ・キャノンボール一部）。定価と混ぜない（点検 2026-09-13）
    r["msrp_is_street"] = ("販売価格" in note) and ("希望小売" not in note)
    if isinstance(v, (int, float)) and v > 0 and "製品ページ表記は「時価」" in note:
        r["msrp_ref"] = int(v)
        r["msrp_kind"] = "jika"
    elif isinstance(v, (int, float)) and v > 0:
        r["msrp"] = int(v)
        r["msrp_kind"] = "price"
    elif isinstance(v, str) and v.strip().lower() in ("open", "オープン価格", "オープン"):
        r["msrp_kind"] = "open"
    elif (isinstance(v, str) and "時価" in v) or "時価" in note:
        r["msrp_kind"] = "jika"
    elif isinstance(v, str) and v.strip().lower() in ("open price",):
        r["msrp_kind"] = "open"
    elif "オープン価格" in note:
        r["msrp_kind"] = "open"
    elif r["unverified"]:
        r["msrp_kind"] = "unconfirmed"
    else:
        r["msrp_kind"] = "na"
    # 改定日・価格基準日：note に「20xx年x月x日 現在／改定」があるときだけ採る（ジュピターは研究班の閲覧日なので採らない）
    r["msrp_date"] = None
    r["msrp_date_kind"] = "unknown"
    if not r.get("strip_note_date"):
        m = _DATE_RE.search(note)
        if m:
            r["msrp_date"] = f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
            r["msrp_date_kind"] = "改定" if m.group(4) in ("改定", "改訂") else "基準日"
        else:
            m2 = _DATE_YM_RE.search(note)
            if m2:
                r["msrp_date"] = f"{int(m2.group(1)):04d}-{int(m2.group(2)):02d}"
                r["msrp_date_kind"] = "改定" if m2.group(3) in ("改定", "改訂") else "基準日"


def msrp_txt(m: dict) -> str:
    k = m["msrp_kind"]
    if k == "price":
        # 二次情報の税抜表示を当サイトが×1.1した値は、メーカー公表の税込定価と同じ見た目で表に混ぜない（点検 2026-09-13）
        if m.get("msrp_converted"):
            return f"¥{m['msrp']:,}（当サイト換算）"
        return f"¥{m['msrp']:,}（発売元サイトの表示価格）" if m.get("msrp_is_street") else f"¥{m['msrp']:,}"
    return {"open": "オープン価格", "jika": "時価（お問い合わせ）", "unconfirmed": UNCONFIRMED}.get(k, NA)


def price_revision_txt(m: dict) -> str:
    """メーカーが発表済みの『これから適用される』改定（ヤマハ 2026-10-01 など）。現在価格は据え置き、予定として示す。"""
    pr = m.get("price_revision") or {}
    if not pr.get("date") or not pr.get("msrp_jpy"):
        return ""
    def jp(x):
        y, mo, da = x.split("-")
        return f"{int(y)}年{int(mo)}月{int(da)}日"
    ann = f"（{jp(pr['announced'])}発表）" if pr.get("announced") else ""
    return f'{jp(pr["date"])}から ¥{pr["msrp_jpy"]:,}（税込）に改定されるとメーカーが公表しています{ann}'


def msrp_date_txt(m: dict) -> str:
    """改定日の表示。取れない行は断定せず「改定日はメーカー未記載」＋当サイト確認日。"""
    if m["msrp_kind"] not in ("price", "open", "jika"):
        return ""
    if m.get("msrp_date"):
        return f"{m['msrp_date_kind']} {m['msrp_date']}"
    return f"改定日はメーカー未記載（確認日 {m['fetched']}）"


def price_band(m: dict) -> str:
    # 「時価」の参考値（msrp_ref）は定価として扱わないと型番ページに書いているので、価格帯にも使わない（点検 2026-09-13）。
    # 時価・オープン価格・未記載はまとめて "none"（＝絞り込みの「オープン価格・時価・未記載」）に入れる
    p = m.get("msrp")
    if not isinstance(p, int):
        return "none"
    for k, _l, lo, hi in PRICE_BANDS:
        if lo <= p < hi:
            return k
    return "none"


# ── 表示用フォーマッタ（値が無いときは必ず NA／UNCONFIRMED を返す） ──
def _missing(m: dict) -> str:
    if m.get("unverified") or m.get("unverified_spec"):
        return UNCONFIRMED
    if m.get("is_secondary"):
        return NA_SECONDARY
    return NA


_MEMO_PAREN = re.compile(r"[（(〔\[][^（()）〔〕\[\]]*(?:" + "|".join(re.escape(w) for w in MEMO_WORDS) + r")[^（()）〔〕\[\]]*[）)〕\]]")


_CODE_PAREN = re.compile(r"[（(]\d{8,}[)）]")                       # 販売店の内部商品コード「(000000003839)」
_CITED_PAREN = re.compile(r"[（(]([^（()）]{2,60}?)と記載[)）]")       # 研究班の「（〜と記載）」→ 引用形に


_ROMAN_FIX = [(re.compile(r"(?<=\d)Ell\b"), lambda m: "EII"), (re.compile(r"Y([A-Z])-(l{2,3})(?=ベル|$|\b)"), lambda m: f"Y{m.group(1)}-" + "I" * len(m.group(2))),
              (re.compile(r"一枚取リ"), lambda m: "一枚取り")]


def norm_roman(s: str) -> str:
    """ヤマハ公式ページ側の表記ゆれ（ローマ数字 II／III が小文字エル ll／lll で載る「ASC-200Ell」「YL-lllベル」、「一枚取リ」）を
    読者向け表示だけ EII／II／III／取り に揃える。DBの値は変えない（監査 2026-09-10 #15）。"""
    for pat, rep in _ROMAN_FIX:
        s = pat.sub(rep, s)
    return s


def clean_text(s: str) -> str:
    """研究班の作業メモ（「（app.js変数 …）」「〔…目視転記…〕」）を括弧ごと落とし、
    「（〜と記載）」はメーカー・代理店表記の引用形にする。値そのものは変えない。"""
    s = _MEMO_PAREN.sub("", s)
    s = _CODE_PAREN.sub("", s)
    s = _CITED_PAREN.sub(lambda m: f"〔メーカー・代理店表記「{m.group(1)}」〕", s)
    return norm_roman(s.strip(" ・;；"))


def txt(m: dict, key: str, unit: str = "") -> str:
    v = m.get(key)
    if v is None or v == "" or v == []:
        return _missing(m)
    if isinstance(v, list):
        return "／".join(clean_text(str(x)) for x in v)
    if isinstance(v, str):
        s = clean_text(v.strip().replace("￥", "¥"))
        if s.startswith("メーカー未記載") or s.startswith("未記載"):
            return NA
        if not s:
            return _missing(m)
        return s + unit
    if isinstance(v, (int, float)):
        return f"{v:g}{unit}"
    return str(v)


def material(m: dict) -> str:
    """木管は body_material、金管は bell_material が主。両方あれば併記。"""
    b, bl = m.get("body_material"), m.get("bell_material")
    parts = []
    if b:
        b = clean_text(str(b))
        parts.append(f"管体：{b}" if not b.startswith("管体") else b)
    if bl:
        parts.append(f"ベル：{clean_text(str(bl))}")
    return "／".join(parts) if parts else _missing(m)


def accessories_list(m: dict) -> list:
    v = m.get("accessories")
    return [norm_roman(str(x)) for x in v] if isinstance(v, list) else []


def note_public(m: dict) -> str:
    """読者に見せてよい備考。社内メモ語を含む文は落とす。"""
    s = clean_text(str(m.get("note") or ""))
    out = []
    for sent in re.split(r"[；;。]\s*", s):
        sent = sent.strip()
        if not sent or any(w in sent for w in MEMO_WORDS):
            continue
        if m.get("strip_note_date") and re.search(r"20\d{2}年\d{1,2}月\d{1,2}日現在価格", sent):
            continue
        if "販売価格" in sent:          # 店頭実売の金額は載せない（価格欄の注記で出所だけ示す）
            continue
        out.append(sent)
    return "。".join(out)


def sources(m: dict) -> list:
    """出典URLのリスト（製品ページ→仕様ページ→訂正時の取り直し→PDF）。重複除去。"""
    raw = [m.get("source_url"), m.get("spec_url"), m.get("fix_source_url")] + list(m.get("pdf_urls") or [])
    out = []
    for u in raw:
        for x in str(u or "").split(" ; "):
            x = x.strip()
            if x.startswith("http") and x not in out and "rakuten" not in x and "amazon" not in x:
                out.append(x)
    return out


def source_kind(m: dict) -> str:
    return {"maker_official": "メーカー公式", "distributor_official": "日本の正規代理店（公式）",
            "pb_official": "発売元公式（自社ブランド）", "shop_secondary": "楽器店ページ（二次情報）"}.get(
        m.get("source_type") or "", "出典")


def is_pdf(u: str) -> bool:
    return u.lower().endswith(".pdf")


def base_model(m: dict) -> str:
    """派生・仕上げ違いをまとめる基本型番。YTR-8335WS→YTR-8335、A-WO10GP→A-WO10、180ML37 SP→180ML37。
    日本語名（セルマー）は空文字（まとめない）。"""
    s = unicodedata.normalize("NFKC", m["model"]).upper()
    mm = re.match(r"^([A-Z]{1,4}-?[A-Z]{0,3}\d{1,4})", s) or re.match(r"^(\d{3}[A-Z]{1,3}\d{0,3})", s)
    return mm.group(1) if mm else ""


# ── 「メーカー公表度」：主要9項目のうち実値がある数（推測なし・機械的に数える） ──
def _has(m: dict, key: str) -> bool:
    v = m.get(key)
    if v in (None, "", []):
        return False
    return not (isinstance(v, str) and v.startswith("メーカー未記載"))


def _size_spec_ok(m: dict) -> bool:
    if m["family"] == "brass":
        return _has(m, "bell_diameter_raw") or _has(m, "bore_raw")
    return _has(m, "key_system") or _has(m, "neck_spec")


TRANSPARENCY_FIELDS = [
    ("調子", lambda m: _has(m, "key")),
    ("仕上げ", lambda m: _has(m, "finish")),
    ("材質（管体またはベル）", lambda m: _has(m, "body_material") or _has(m, "bell_material")),
    ("付属品", lambda m: _has(m, "accessories")),
    ("税込希望小売価格の金額", lambda m: m["msrp_kind"] == "price"),
    ("シリーズ名", lambda m: _has(m, "series")),
    ("機構・仕様の要点", lambda m: _has(m, "mechanism")),
    ("ベル径・ボア（金管）／キイシステム・ネック（木管）", _size_spec_ok),
    ("カタログ・取扱説明書PDF", lambda m: bool(m.get("pdf_urls"))),
]
SCORE_MAX = len(TRANSPARENCY_FIELDS) + 2 + 1 + 1 + 1     # 14


def transparency(m: dict) -> tuple:
    have = [label for label, fn in TRANSPARENCY_FIELDS if fn(m)]
    return len(have), len(TRANSPARENCY_FIELDS), have


def score(m: dict) -> tuple:
    """(合計点, [(基準, 点数, 満点), ...])。性能の優劣ではなく「公表情報の充実度」。"""
    n, total, _ = transparency(m)
    manual = any("om_" in u.lower() or "manual" in u.lower() or "取説" in u for u in (m.get("pdf_manual_urls") or []) + list(m.get("pdf_urls") or []))
    catalog = bool(m.get("pdf_catalog_urls")) or any("brochure" in u.lower() or "catalog" in u.lower() for u in m.get("pdf_urls") or [])
    primary = not m["is_secondary"]
    dated = bool(m.get("msrp_date"))
    items = [
        ("公表項目の数（主要9項目）", n, total),
        ("取扱説明書PDFの公開", 2 if manual else 0, 2),
        ("カタログPDFの公開", 1 if catalog else 0, 1),
        ("価格の改定日・基準日の明記", 1 if dated else 0, 1),
        ("一次情報（メーカー・正規代理店）で確認できる", 1 if primary else 0, 1),
    ]
    return sum(p for _, p, _ in items), items


def na_rate(rows: list, fields: list) -> float:
    total = len(rows) * len(fields)
    if not total:
        return 0.0
    miss = sum(1 for r in rows for f in fields if not _has(r, f))
    return miss / total


MODELS = load_models()
CURRENT = [m for m in MODELS if m["is_current"]]
BY_SLUG = {m["slug"]: m for m in MODELS}


def find(brand_key: str, model: str) -> dict:
    """(brand_key, model完全一致) で1行を引く。無ければ例外（記事の型番タイプミスをビルドで止める）。"""
    for m in MODELS:
        if m["brand_key"] == brand_key and m["model"] == model:
            return m
    for m in MODELS:   # 表記ゆれ（全角・ハイフン・空白）を許す
        if m["brand_key"] == brand_key and _norm_model(m["model"]) == _norm_model(model):
            return m
    raise KeyError(f"DBに見つからない型番: brand={brand_key} model={model}")


def siblings(m: dict, current_only: bool = True) -> list:
    """同ブランド・同楽器種の型番を税込定価順に。定価が無い型番は末尾（型番名順）。"""
    rows = [x for x in MODELS if x["brand_key"] == m["brand_key"] and x["instrument"] == m["instrument"]
            and (x["is_current"] or not current_only)]
    return sorted(rows, key=lambda x: (x["msrp"] is None, x["msrp"] or 0, x["model"]))


def variants(m: dict) -> list:
    """同ブランド・同楽器種で基本型番が同じ型番（派生・仕上げ違い）。自分を含む。2件未満なら空。"""
    b = base_model(m)
    if not b:
        return []
    rows = [x for x in MODELS if x["brand_key"] == m["brand_key"] and x["instrument"] == m["instrument"] and base_model(x) == b]
    rows.sort(key=lambda x: (not x["is_current"], x["msrp"] is None, x["msrp"] or 0, x["model"]))
    return rows if len(rows) >= 2 else []


def stats() -> dict:
    return {
        "n_current": len(CURRENT),
        "n_rows": len(MODELS),
        "n_brands": len({m["brand_key"] for m in CURRENT}),
        "n_instruments": len({m["instrument"] for m in CURRENT}),
        "n_groups": len({m["group_key"] for m in CURRENT}),
        "n_priced": sum(1 for m in CURRENT if m["msrp_kind"] == "price"),
        "n_dated": sum(1 for m in CURRENT if m.get("msrp_date")),
        "n_urls": len({u for m in MODELS for u in sources(m)}),
    }


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    s = stats()
    print(f"全{s['n_rows']}行 / 現行{s['n_current']}型番 / {s['n_brands']}ブランド / {s['n_groups']}楽器種グループ "
          f"/ 定価あり{s['n_priced']} / 改定日あり{s['n_dated']} / 出典URL {s['n_urls']}")
    from collections import Counter
    print(Counter(m["origin"] for m in MODELS))
    print(Counter(m["brand_key"] for m in CURRENT).most_common())
    print(Counter(m["group_key"] for m in CURRENT).most_common())
    print(Counter(m["msrp_kind"] for m in CURRENT))
    print(Counter(m["msrp_date_kind"] for m in CURRENT if m["msrp_kind"] == "price"))
    for key in ("key", "finish", "accessories", "series", "mechanism"):
        print(f"  {key:12} 未記載率 {na_rate(CURRENT, [key]):.0%}")
    for m in MODELS:
        if m.get("fixed"):
            print("  訂正適用:", m["brand"], m["model"], txt(m, "key"), txt(m, "accessories"), msrp_txt(m))
    dup = [s for s, n in Counter(_slugify(m["brand_key"], m["model"]) for m in MODELS).items() if n > 1]
    print("slug衝突（連番で回避）:", len(dup), dup[:8])
