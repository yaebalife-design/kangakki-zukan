# -*- coding: utf-8 -*-
"""表・出典の描画部品（管楽器図鑑）。gen_index（ハブ表）・gen_model（型番ページ）・gen_article（記事内の表）で共用する。

嘘ゼロの実装:
  ・全てのセルは kangakki_db のフォーマッタ経由。値が無ければ「—（メーカー未記載）」「—（未確認）」を出す
  ・価格は「税込希望小売価格＋改定日（取れない行は『改定日はメーカー未記載』＋確認日）＋出典」の3点セット
  ・二次情報（Rampone&Cazzani）・未確認（Playtech・Soleil）・生産終了・在庫限りには行にフラグを出す
  ・ペア差分表は「値が違う行」だけを強調する（どちらが良いかは書かない）
"""
import html as htmllib
import re
import statistics

import site_config as cfg
import kangakki_db as db
import moshimo_link
import price_data


def esc(s) -> str:
    return htmllib.escape(str(s), quote=True)


def _v(s: str) -> str:
    """「—（…）」はグレー表示（文言を潰さない）。"""
    return f'<span class="na">{esc(s)}</span>' if str(s).startswith("—") else esc(s)


def cell(m: dict, key: str, unit: str = "") -> str:
    s = _v(db.txt(m, key, unit))
    if key == "key" and m.get("key_inferred") and not db.txt(m, key).startswith("—"):
        s += '<span class="src">出典の価格表に調子の記載はなく、楽器種の標準の調子です</span>'
    return s


def model_href(prefix: str, model_page: dict, m: dict) -> str:
    """型番名のリンク先。解説記事がある型番は記事、それ以外はDBから生成する型番ページ（models/）。終了型番も型番ページはある。"""
    art = model_page.get(m["slug"]) if model_page else None
    return f"{prefix}articles/{art}.html" if art else f"{prefix}models/{m['slug']}.html"


def linked_name(prefix: str, model_page: dict, m: dict, inner: str) -> str:
    return f'<a href="{model_href(prefix, model_page, m)}">{inner}</a>'


def flags_html(m: dict) -> str:
    out = ""
    if not m["is_current"]:
        out += f'<span class="flag f3" title="メーカー表記">{esc(m["status_label"])}</span>'
    if m["is_secondary"]:
        out += '<span class="flag f2" title="メーカー公式ページに到達できず楽器店ページを出典としています">二次情報</span>'
    if m["unverified"]:
        out += '<span class="flag f4" title="型番とURL以外を確認できていません">仕様未確認</span>'
    elif m["unverified_spec"]:
        out += '<span class="flag f4" title="価格以外の仕様を確認できていません">仕様未確認</span>'
    return out


# ── 価格 ──
def msrp_html(m: dict, with_src: bool = True) -> str:
    """税込希望小売価格＋改定日＋出典。3点セットを崩さない（絶対ルール3）。"""
    t = db.msrp_txt(m)
    head = f"<b>{esc(t)}</b>" if m["msrp_kind"] == "price" else _v(t) if t.startswith("—") else f"<b>{esc(t)}</b>"
    if not with_src or m["msrp_kind"] not in ("price", "open", "jika"):
        return head
    d = db.msrp_date_txt(m)
    src = db.source_kind(m)
    extra = ""
    if m["msrp_kind"] == "jika" and m.get("msrp_ref"):
        extra = (f'<span class="src">参考：代理店（野中貿易）の為替連動価格一覧では ¥{m["msrp_ref"]:,}（{esc(d) if m.get("msrp_date") else "基準日は一覧に未記載"}）。'
                 "製品ページの表記は「時価」のため、当サイトは定価として扱いません。</span>")
        return f'{head}{extra}<span class="src">出典：{esc(src)}</span>'
    if m.get("msrp_converted") and m["msrp_kind"] == "price":
        extra = (f'<span class="src">当サイト注：楽器店ページ（二次情報）の表示は税抜 ¥{round(m["msrp"] / 1.1):,}。'
                 "税込表示は当サイトが×1.10で換算した値で、メーカー・代理店の公表値ではありません。</span>")
    if m.get("msrp_is_street") and m["msrp_kind"] == "price":
        extra += ('<span class="src">当サイト注：出典ページの表記は「希望小売価格」ではなく発売元サイトが表示している価格です。'
                  "メーカーの定価としては公表されていません。</span>")
    rev = db.price_revision_txt(m)
    if rev:
        extra += f'<span class="src">価格改定の予定：{esc(rev)}。上の金額は改定前の現在価格です。</span>'
    return f'{head}<span class="src">税込／{esc(d)}／出典：{esc(src)}</span>{extra}'


def msrp_short(m: dict) -> str:
    return db.msrp_txt(m)


def street_html(m: dict) -> str:
    """実売の最安値（価格APIで取れた型番だけ）。無ければ空文字＝行を出さない。"""
    slug = m["slug"]
    p = price_data.min_yen(slug)
    if not p:
        return ""
    n = price_data.shops(slug)
    mall = price_data.malls(slug)
    where = (f"{mall}で在庫のあった{n}店舗のうち、いちばん安い価格です" if n > 1 else f"{mall}で在庫を確認できた1店舗の価格です")
    return (f'<b>{esc(p)}</b><span class="src">{where}（確認日 {esc(price_data.FETCHED)}）。'
            "送料・ポイントは含みません。価格・在庫は店ごとに違い、変動します。</span>")


def street_short(m: dict) -> str:
    return price_data.min_yen(m["slug"])


# ── 出典 ──
def _url_label(u: str) -> str:
    mm = re.match(r"https?://([^/]+)", u)
    host = mm.group(1) if mm else u
    if db.is_pdf(u):
        return host + "（PDF）"
    return host


def _short_label(u: str, kind: str, i: int) -> str:
    if db.is_pdf(u):
        return "カタログ・取説PDF"
    if "specs" in u.lower():
        return "仕様ページ"
    return kind if i == 0 else "公式2"


EXT = '<span class="visually-hidden">（別タブで開く）</span>'
SHOP_HOSTS = ("soundhouse", "shimamura", "shimokura", "sakura-gakki", "ishimori", "rakuten", "amazon", "yahoo")


def _rel(u: str) -> str:
    """メーカー・正規代理店の出典は follow（一次情報としてたどれるように）。楽器店ECだけ nofollow（点検 2026-09-13）。"""
    return "noopener nofollow" if any(hh in u for hh in SHOP_HOSTS) else "noopener"


def source_links(m: dict, short: bool = False, limit: int = 4) -> str:
    urls = db.sources(m)
    if not urls:
        return '<span class="na">—（一次情報に到達できず）</span>'
    kind = db.source_kind(m)
    if short:
        return " ".join(f'<a href="{esc(u)}" rel="{_rel(u)}" target="_blank">{esc(_short_label(u, kind, i))}{EXT}</a>'
                        for i, u in enumerate(urls[:3]))
    return " ／ ".join(f'<a href="{esc(u)}" rel="{_rel(u)}" target="_blank">{esc(_url_label(u))}{EXT}</a>' for u in urls[:limit])


# ══ ① ハブの全型番表 ══
DB_COLUMNS = [
    ("ブランド／型番", "c-model", 240),
    ("楽器種", "", 130),
    ("シリーズ", "", 150),
    ("税込希望小売価格", "", 130),
    ("改定日・基準日", "", 150),
    ("調子", "", 80),
    ("仕上げ", "", 150),
    ("材質", "", 170),
    ("付属品", "", 170),
    ("現行／終了", "", 90),
    ("出典", "", 120),
]
DB_TABLE_WIDTH = sum(w for _, _, w in DB_COLUMNS)


def _acc_cell(m: dict) -> str:
    lst = db.accessories_list(m)
    if not lst:
        return cell(m, "accessories")
    return f'<details><summary>{len(lst)}点</summary><span class="dtl">{esc("／".join(lst))}</span></details>'


def db_row_html(m: dict, prefix: str, model_page: dict, table_pick: bool = False) -> str:
    name = esc(m["name"])
    inner = linked_name(prefix, model_page, m, f"<b>{name}</b>")
    if table_pick:
        inner = f'<label class="pick tpick"><input type="checkbox" class="cmp-pick" value="{esc(m["slug"])}" aria-label="{name} を比較に追加"></label>' + inner
    d = db.msrp_date_txt(m)
    return f"""        <tr data-slug="{esc(m["slug"])}">
          <th scope="row" class="c-model">{inner}<span class="mk">{esc(m["brand_label"])}</span>{flags_html(m)}</th>
          <td>{esc(m["instrument_label"])}</td>
          <td>{cell(m, "series")}</td>
          <td class="n">{_v(db.msrp_txt(m))}</td>
          <td>{esc(d) if d else '<span class="na">—</span>'}</td>
          <td>{cell(m, "key")}</td>
          <td>{cell(m, "finish")}</td>
          <td>{_v(db.material(m))}</td>
          <td>{_acc_cell(m)}</td>
          <td>{esc(m["status_label"])}</td>
          <td>{source_links(m, short=True)}</td>
        </tr>"""


def _table_head() -> tuple:
    heads = "".join(f'<th scope="col"{f" class={chr(34)}{cls}{chr(34)}" if cls else ""}>{esc(label)}</th>' for label, cls, _w in DB_COLUMNS)
    cols = "".join(f'<col style="width:{w}px">' for _l, _c, w in DB_COLUMNS)
    return heads, cols


def db_table_shell(rows: list, prefix: str) -> str:
    """トップの表ビューの外枠だけ（行はJSが埋め込みJSONから作る。851行を焼くと index.html が肥大化する）。"""
    heads, cols = _table_head()
    return f"""  <p class="scrollhint">表は横にも縦にもスクロールできます（見出し行と型番の列は固定）。列の意味は<a href="{prefix}data.html">データの作り方</a>をご覧ください。</p>
  <div class="dbwrap">
    <table class="db" id="dbtable" style="width:{DB_TABLE_WIDTH}px">
      <caption class="visually-hidden">管楽器 {len(rows)}型番の定価・仕様一覧（メーカー公表値）</caption>
      <colgroup>{cols}</colgroup>
      <thead><tr>{heads}</tr></thead>
      <tbody></tbody>
    </table>
  </div>
  <p class="dbempty" id="dbtable-empty" hidden>条件に合う型番がありません。絞り込みを減らしてください。</p>
  <p class="dbnote">{cfg.NOTICE_PRICE}<br>{cfg.NOTICE_NA}</p>"""


def db_table_html(rows: list, prefix: str, model_page: dict, table_id: str = "dbtable") -> str:
    heads, cols = _table_head()
    body = "\n".join(db_row_html(m, prefix, model_page, table_pick=(table_id == "dbtable")) for m in rows)
    return f"""  <p class="scrollhint">表は横にも縦にもスクロールできます（見出し行と型番の列は固定）。列の意味は<a href="{prefix}data.html">データの作り方</a>をご覧ください。</p>
  <div class="dbwrap">
    <table class="db" id="{table_id}" style="width:{DB_TABLE_WIDTH}px">
      <caption class="visually-hidden">管楽器 {len(rows)}型番の定価・仕様一覧（メーカー公表値）</caption>
      <colgroup>{cols}</colgroup>
      <thead><tr>{heads}</tr></thead>
      <tbody>
{body}
      </tbody>
    </table>
  </div>
  <p class="dbnote">{cfg.NOTICE_PRICE}<br>{cfg.NOTICE_NA}</p>"""


# ══ ② 1型番の縦仕様表 ══
def _pdf_cell(m: dict) -> str:
    urls = [u for u in db.sources(m) if db.is_pdf(u)]
    if not urls:
        return '<span class="na">—（公式サイトにPDFの掲載なし、または未回収）</span>'
    shown = "<br>".join(f'<a href="{esc(u)}" rel="{_rel(u)}" target="_blank">{esc(_url_label(u))}{EXT}</a>' for u in urls[:6])
    return shown + (f'<span class="src">このほか {len(urls) - 6} 件（出典欄に全て掲載）</span>' if len(urls) > 6 else "")


SPEC_ROWS = [
    ("ブランド・メーカー", lambda m: esc(m["brand_label"]) + (f'<span class="src">{esc(m["maker"])}</span>' if m.get("maker") else "")),
    ("日本での発売元・代理店", lambda m: cell(m, "distributor_jp")),
    ("型番", lambda m: esc(m["model"]) + (f'<span class="src">{esc(m["model_label"])}</span>' if m["model_label"] != m["model"] else "")),
    ("楽器種", lambda m: esc(m["instrument_label"]) + f'<span class="src">{esc(db.FAMILY_LABEL.get(m["family"], ""))}楽器／{esc(m["group_label"])}</span>'),
    ("シリーズ", lambda m: cell(m, "series")),
    ("現行／生産終了", lambda m: esc(m["status_label"]) + '<span class="src">メーカー・代理店の表記による（確認日 ' + esc(m["fetched"]) + "）</span>"),
    ("税込希望小売価格", lambda m: msrp_html(m)),
    ("調子", lambda m: cell(m, "key")),
    ("キイシステム", lambda m: cell(m, "key_system")),
    ("管体材質", lambda m: cell(m, "body_material")),
    ("ベル材質", lambda m: cell(m, "bell_material")),
    ("仕上げ", lambda m: cell(m, "finish")),
    ("ベル径", lambda m: cell(m, "bell_diameter_raw")),
    ("ボア", lambda m: cell(m, "bore_raw")),
    ("ネック", lambda m: cell(m, "neck_spec")),
    ("機構・仕様の要点", lambda m: cell(m, "mechanism")),
    ("付属品", lambda m: ("<br>".join(esc(x) for x in db.accessories_list(m)) if db.accessories_list(m) else cell(m, "accessories"))),
    ("高さ（メーカー表記）", lambda m: cell(m, "height_mm_raw")),
    ("前身（メーカー明記のみ）", lambda m: cell(m, "predecessor")),
    ("後継（メーカー明記のみ）", lambda m: cell(m, "successor")),
    ("カタログ・取扱説明書PDF", _pdf_cell),
    ("備考（メーカー・代理店の表記）", lambda m: (esc(db.note_public(m)) if db.note_public(m) else '<span class="na">—</span>')),
]
# 派生・仕上げ違いの一覧や比較表で「重量・対象レベル・管体材質（金管）」は比較軸にしない（絶対ルール5）


def row_label(label: str, models: list) -> str:
    """行ラベルの読み替え。
      ・クラリネットの neck_spec はヤマハ仕様表の「バレル」長（65mm 等）なので「ネック」と出さない（監査 2026-09-10）
      ・出典が「販売価格」表記の型番は「希望小売価格」と書かない（点検 2026-09-13）"""
    if label == "ネック" and models and all(x.get("group_key") == "clarinet" for x in models):
        return "バレル"
    if label == "税込希望小売価格" and models and all(x.get("msrp_is_street") for x in models):
        return "税込価格（発売元サイトの表示）"
    return label


def spec_table_html(m: dict) -> str:
    # 同じ見出し構造の表が1ページに並ぶので、読み上げ用に表の名前を付ける（点検 2026-09-13）
    cap = f'<caption class="visually-hidden">{esc(m["name"])} の仕様と定価（メーカー公表値）</caption>'
    trs = [f'      <tr><th scope="row">{esc(row_label(label, [m]))}</th><td>{fn(m)}</td></tr>' for label, fn in SPEC_ROWS]
    st = street_html(m)
    if st:
        trs.insert(7, f'      <tr><th scope="row">実売の最安値</th><td>{st}</td></tr>')
    trs.append(f'      <tr><th scope="row">出典</th><td>{source_links(m)}<span class="src">確認日 {esc(m["fetched"])}／{esc(db.source_kind(m))}</span></td></tr>')
    return (f'  <div class="tblcard"><table class="minitbl">{cap}\n{chr(10).join(trs)}\n  </table></div>\n'
            f'  <p class="tnote">{cfg.NOTICE_PRICE}<br>{cfg.NOTICE_NA}</p>')


# ══ ③ 横並び比較表（2〜4型番・違う行を強調） ══
CMP_ROWS = [
    ("楽器種", lambda m: esc(m["instrument_label"])),
    ("シリーズ", lambda m: cell(m, "series")),
    ("税込希望小売価格", lambda m: msrp_html(m)),
    ("現行／生産終了", lambda m: esc(m["status_label"])),
    ("調子", lambda m: cell(m, "key")),
    ("キイシステム", lambda m: cell(m, "key_system")),
    ("管体材質", lambda m: cell(m, "body_material")),
    ("ベル材質", lambda m: cell(m, "bell_material")),
    ("仕上げ", lambda m: cell(m, "finish")),
    ("ベル径", lambda m: cell(m, "bell_diameter_raw")),
    ("ボア", lambda m: cell(m, "bore_raw")),
    ("ネック", lambda m: cell(m, "neck_spec")),
    ("機構・仕様の要点", lambda m: cell(m, "mechanism")),
    ("付属品", lambda m: ("<br>".join(esc(x) for x in db.accessories_list(m)) if db.accessories_list(m) else cell(m, "accessories"))),
]


def _plain(s: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", " ", s).split())


def cmp_table_html(models: list, rows=None, highlight: bool = True, prefix: str = "../", fold_na: bool = False) -> str:
    """fold_na=True（記事用）: 全型番が「メーカー未記載」の行は表から外し、表の下に項目名だけまとめて示す。"""
    rows = rows or CMP_ROWS
    heads = "".join(f'<th scope="col"><a href="{prefix}models/{esc(m["slug"])}.html">{esc(m["name"])}</a>'
                    f'<span class="b">{esc(m["brand_label"])}</span></th>' for m in models)
    body, n_diff, folded = [], 0, []
    for label, fn in rows:
        label = row_label(label, models)
        cells = [fn(m) for m in models]
        plain = [_plain(re.sub(r'<span class="src">.*?</span>', "", c)) for c in cells]
        if fold_na and all(p.startswith("—") for p in plain):
            folded.append(label)
            continue
        diff = highlight and len(models) > 1 and len(set(plain)) > 1
        n_diff += diff
        cls = ' class="diff"' if diff else ""
        body.append(f'        <tr{cls}><th scope="row">{esc(label)}{"<span class=src>違いあり</span>" if diff else ""}</th>' + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
    src_cells = "".join(f"<td>{source_links(m, short=True)}<span class='src'>確認日 {esc(m['fetched'])}</span></td>" for m in models)
    body.append(f'        <tr><th scope="row">出典</th>{src_cells}</tr>')
    names = "・".join(m["name"] for m in models)
    note = (f"色の付いた行がメーカー公表値の違う項目です（{n_diff}項目）。同じ値の行は違いなし。" if highlight and len(models) > 1 else "")
    if folded:
        note += f"メーカー未記載のため省いた項目：{esc('・'.join(folded))}。"
    return f"""  <div class="cmpwrap">
    <table class="cmp">
      <caption class="visually-hidden">{esc(names)} の仕様・定価の比較（メーカー公表値）</caption>
      <thead><tr><th scope="col"><span class="visually-hidden">項目</span></th>{heads}</tr></thead>
      <tbody>
{chr(10).join(body)}
      </tbody>
    </table>
  </div>
  <p class="tnote">{note}{cfg.NOTICE_PRICE}<br>{cfg.NOTICE_NA}</p>"""


# ══ ④ 派生・同ブランド同楽器種の一覧（定価順） ══
# 一覧表に出せる列（記事から cols で選ぶ。既定は LINEUP_COLS_DEFAULT）
LINEUP_COLS = {
    "series":     ("シリーズ", "12%", lambda m: cell(m, "series")),
    "price":      ("税込希望小売価格", "23%", lambda m: f'{_v(db.msrp_txt(m))}<span class="src">{esc(db.msrp_date_txt(m))}</span>'),
    "finish":     ("仕上げ", None, lambda m: cell(m, "finish")),
    "key":        ("調子", "5em", lambda m: cell(m, "key")),
    "material":   ("材質", None, lambda m: _v(db.material(m))),
    "key_system": ("キイシステム", None, lambda m: cell(m, "key_system")),
    "neck":       ("ネック", None, lambda m: cell(m, "neck_spec")),
    "bore":       ("ボア", None, lambda m: cell(m, "bore_raw")),
    "bell":       ("ベル材質", None, lambda m: cell(m, "bell_material")),
    "acc":        ("付属品", "7em", lambda m: _acc_cell(m)),
    "status":     ("現行", "5em", lambda m: esc(m["status_label"])),
}
LINEUP_COLS_DEFAULT = ["series", "price", "finish", "key", "material", "status"]


def lineup_table_html(rows: list, prefix: str, model_page: dict, me: str = "", caption: str = "", cols=None) -> str:
    """ブランド×楽器種の型番一覧。cols で列を選べる（記事の本文で触れている項目を表に出すため）。"""
    keys = [k for k in (cols or LINEUP_COLS_DEFAULT) if k in LINEUP_COLS]
    trs = []
    for m in rows:
        cls = ' class="me"' if m["slug"] == me else ""
        name = esc(m["name"]) if m["slug"] == me else linked_name(prefix, model_page, m, esc(m["name"]))
        tds = "".join(f'<td{" class=\"n\"" if k == "price" else ""}>{LINEUP_COLS[k][2](m)}</td>' for k in keys)
        trs.append(f'      <tr{cls}><th scope="row">{name}{flags_html(m)}<span class="src">{esc(m["instrument_label"])}</span></th>{tds}</tr>')
    cap = (f"<caption>{esc(caption)}</caption>" if caption
           else f'<caption class="visually-hidden">{esc(rows[0]["brand_label"]) if rows else ""} の型番一覧（税込定価順・メーカー公表値）</caption>')
    colgroup = '<col style="width:22%">' + "".join(
        (f'<col style="width:{LINEUP_COLS[k][1]}">' if LINEUP_COLS[k][1] else "<col>") for k in keys)
    heads = "".join(f'<th scope="col">{esc(LINEUP_COLS[k][0])}</th>' for k in keys)
    return f"""  <div class="cmpwrap">
    <table class="cmp ft">{cap}
      <colgroup>{colgroup}</colgroup>
      <thead><tr><th scope="col">型番</th>{heads}</tr></thead>
      <tbody>
{chr(10).join(trs)}
      </tbody>
    </table>
  </div>
  <p class="tnote">{cfg.NOTICE_PRICE}<br>{cfg.NOTICE_NA}</p>"""


# ══ ⑤ 楽器種ごとの定価分布（値段相場記事・楽器種ページ用。数字は毎回DBから数える） ══
def price_stats(rows: list) -> dict:
    ps = sorted(m["msrp"] for m in rows if m["msrp_kind"] == "price")
    if not ps:
        return {"n": 0}
    return {"n": len(ps), "min": ps[0], "median": int(statistics.median(ps)), "max": ps[-1],
            "n_other": sum(1 for m in rows if m["msrp_kind"] != "price")}


def price_dist_table_html(groups: list, prefix: str = "") -> str:
    """groups: [(見出し, rows, href)]"""
    trs = []
    for label, rows, href in groups:
        s = price_stats(rows)
        name = f'<a href="{esc(href)}">{esc(label)}</a>' if href else esc(label)
        if not s["n"]:
            trs.append(f'      <tr><th scope="row">{name}</th><td class="n">0</td><td colspan="3"><span class="na">—（定価の金額を公表している現行型番なし）</span></td></tr>')
            continue
        trs.append(f'      <tr><th scope="row">{name}</th><td class="n">{s["n"]}</td><td class="n">¥{s["min"]:,}</td>'
                   f'<td class="n">¥{s["median"]:,}</td><td class="n">¥{s["max"]:,}</td></tr>')
    return f"""  <div class="tblcard"><table class="minitbl keep">
      <thead><tr><th scope="col">楽器種</th><th scope="col">定価あり</th><th scope="col">最低</th><th scope="col">中央値</th><th scope="col">最高</th></tr></thead>
      <tbody>
{chr(10).join(trs)}
      </tbody></table></div>
  <p class="tnote">当サイトのデータベースにある現行型番のうち、税込希望小売価格の金額をメーカー・正規代理店が公表しているものだけを数えています（オープン価格・時価は除く）。{cfg.NOTICE_PRICE}</p>"""


# ══ ⑥ 型番カード（記事内・縦表） ══
def model_card_html(m: dict, prefix: str, model_page: dict, why: str = "") -> str:
    name = esc(m["name"])
    title = linked_name(prefix, model_page, m, name)
    body = [
        f'<tr><th scope="row">ブランド</th><td>{esc(m["brand_label"])}</td></tr>',
        f'<tr><th scope="row">楽器種</th><td>{esc(m["instrument_label"])}</td></tr>',
        f'<tr><th scope="row">シリーズ</th><td>{cell(m, "series")}</td></tr>',
        f'<tr><th scope="row">税込希望小売価格</th><td>{msrp_html(m)}</td></tr>',
        f'<tr><th scope="row">調子</th><td>{cell(m, "key")}</td></tr>',
        f'<tr><th scope="row">仕上げ</th><td>{cell(m, "finish")}</td></tr>',
        f'<tr><th scope="row">材質</th><td>{_v(db.material(m))}</td></tr>',
        f'<tr><th scope="row">付属品</th><td>{("<br>".join(esc(x) for x in db.accessories_list(m)) if db.accessories_list(m) else cell(m, "accessories"))}</td></tr>',
        f'<tr><th scope="row">現行／生産終了</th><td>{esc(m["status_label"])}</td></tr>',
        f'<tr><th scope="row">出典</th><td>{source_links(m)}<span class="src">確認日 {esc(m["fetched"])}</span></td></tr>',
    ]
    st = street_html(m)
    if st:
        body.insert(4, f'<tr><th scope="row">実売の最安値</th><td>{st}</td></tr>')
    note = f'\n  <p>{why}</p>' if why else ""
    return (f'  <h3 id="m-{esc(m["slug"])}">{title}{flags_html(m)}</h3>{note}\n'
            f'  <div class="tblcard"><table class="minitbl" aria-labelledby="m-{esc(m["slug"])}">\n    '
            + "\n    ".join(body) + "\n  </table></div>\n")
