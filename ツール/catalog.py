# -*- coding: utf-8 -*-
"""図鑑UI（管楽器図鑑）：型番カード・公表項目メーター・楽器種タイル・絞り込み・比較トレイ。

嘘ゼロの実装:
  ・カードの数字は全て kangakki_db 経由（無い値は「—」）。「公表項目」は主要9項目の実値の数を機械的に数える
  ・絞り込みは 楽器種（グループ→細分）・ブランド・価格帯・現行のみ・型番名。推測で当てはめない
  ・並び順の既定はDB順（ブランド→楽器種→定価）。「公表情報の充実度」スコアは載っている情報の多さで、性能の優劣ではない
"""
import json

import site_config as cfg
import kangakki_db as db
import render
import price_data
from render import esc

MULTI_MODEL_ARTICLES = set()


def _n(v):
    return v if isinstance(v, (int, float)) else None


def record(m: dict, prefix: str, model_page: dict) -> dict:
    n, total, have = db.transparency(m)
    art = model_page.get(m["slug"]) if model_page else None
    sc, sc_items = db.score(m)
    acc = db.accessories_list(m)
    return {
        "slug": m["slug"], "name": m["name"], "model": m["model"], "brand": m["brand_key"], "brandLabel": m["brand_label"],
        "group": m["group_key"], "groupLabel": m["group_label"], "instrument": m["instrument"], "instrumentLabel": m["instrument_label"],
        "family": m["family"], "series": db.txt(m, "series"),
        "msrp": m["msrp"], "msrpTxt": db.msrp_txt(m), "msrpKind": m["msrp_kind"], "msrpDate": db.msrp_date_txt(m),
        "band": db.price_band(m), "key": db.txt(m, "key"), "finish": db.txt(m, "finish"), "material": db.material(m),
        "acc": "／".join(acc) if acc else db.txt(m, "accessories"), "accN": len(acc),
        "status": m["status"], "statusLabel": m["status_label"], "current": m["is_current"],
        "street": render.street_short(m), "url": f"{prefix}models/{m['slug']}.html",
        "article": f"{prefix}articles/{art}.html" if art else "",
        "transp": [n, total], "transpHave": have, "score": sc, "scoreMax": db.SCORE_MAX,
        "scoreItems": [[a, b, c] for a, b, c in sc_items],
        "flags": [f for f, ok in (("二次情報", m["is_secondary"]), ("仕様未確認", m["unverified"] or m["unverified_spec"])) if ok],
        "src": [{"u": u, "k": render._short_label(u, db.source_kind(m), i)} for i, u in enumerate(db.sources(m)[:2])],
        "base": db.base_model(m),
    }


def meter_html(n: int, total: int) -> str:
    segs = "".join(f'<i class="{"on" if i < n else ""}"></i>' for i in range(total))
    return (f'<div class="meter" role="img" aria-label="メーカーが公表している主要項目 {n}／{total}">'
            f'<span class="lbl">公表項目</span><span class="segs">{segs}</span><b>{n}<small>/{total}</small></b></div>')


def score_html(r: dict) -> str:
    items = "".join(f'<li><span>{esc(a)}</span><b>{b}<small>/{c}</small></b></li>' for a, b, c in r["scoreItems"])
    return (f'<details class="score"><summary><span class="lbl">公表情報の充実度</span><b>{r["score"]}<small>/{r["scoreMax"]}</small></b>'
            f'<span class="hint">内訳</span></summary><ul>{items}</ul></details>')


def _big(v_txt: str, label: str, sub: str = "") -> str:
    if v_txt.startswith("—"):
        inner = v_txt.lstrip("—").strip("（）")
        return f'<div class="num na"><b>—</b><small>{esc(label)}<em>{esc(inner)}</em></small></div>'
    cls = "num long" if len(v_txt) > 9 else "num"
    subhtml = f'<em>{esc(sub)}</em>' if sub else ""
    return f'<div class="{cls}"><b>{esc(v_txt)}</b><small>{esc(label)}{subhtml}</small></div>'


def card_html(r: dict, hero: bool = False) -> str:
    title = f'<a href="{esc(r["url"])}">{esc(r["name"])}</a>'
    flags = "".join(f'<span class="flag f2">{esc(f)}</span>' for f in r["flags"])
    if not r["current"]:
        flags += f'<span class="flag f3">{esc(r["statusLabel"])}</span>'
    price = _big(r["msrpTxt"], "税込希望小売価格", r["msrpDate"] if r["msrpKind"] == "price" else "")
    nums = f'<div class="mc-nums">{price}{_big(r["key"], "調子")}{_big(r["finish"], "仕上げ")}</div>'
    if hero:
        return f"""<article class="mcard is-strip" data-slug="{esc(r['slug'])}">
  <div class="mc-top"><span class="mk">{esc(r['brandLabel'])}</span><span class="ins">{esc(r['instrumentLabel'])}</span>{flags}</div>
  <p class="mc-name">{esc(r['name'])}</p>
  {nums}
</article>"""
    street = f'<div class="price">実売の最安値 {esc(r["street"])}<small>当サイトが確認できた最安値。送料別・変動します（確認した店と日付は型番ページ）</small></div>' if r["street"] else ""
    action = f'<a class="more" href="{esc(r["url"])}">型番ページ →</a>' + (f'<a class="more" href="{esc(r["article"])}">解説記事 →</a>' if r["article"] else "")
    pick = f'<label class="pick"><input type="checkbox" class="cmp-pick" value="{esc(r["slug"])}"> 比較に追加<small>（最大4）</small></label>'
    return f"""<article class="mcard" data-slug="{esc(r['slug'])}">
  <div class="mc-top"><span class="mk">{esc(r['brandLabel'])}</span><span class="ins">{esc(r['instrumentLabel'])}</span>{flags}</div>
  <h3 class="mc-name">{title}</h3>
  <p class="mc-sub">{esc(r['series']) if not r['series'].startswith('—') else 'シリーズ名：メーカー未記載'}</p>
  {nums}
  <div class="mc-line"><span>材質 <b>{esc(r['material'])}</b></span><span>付属品 <b>{esc(str(r['accN']) + '点') if r['accN'] else esc(r['acc'])}</b></span></div>
  {meter_html(*r['transp'])}
  {score_html(r)}
  {street}
  <div class="mc-actions">{pick}{action}</div>
</article>"""


# 埋め込みJSONに載せるキー（JSが実際に読むものだけ）。906型番をカードごとHTMLに焼くと index.html が2.7MBになるため、
# カードと表の行はJSが埋め込みJSONから描く（初期60枚＋「もっと見る」）。型番ページ・楽器種別ページ・型番一覧が静的HTMLの導線
JS_KEYS = ("slug", "name", "brand", "group", "instrument", "series", "msrp", "msrpTxt", "msrpDate", "band", "key", "finish",
           "material", "accN", "acc", "statusLabel", "current", "street", "transp", "score", "flags")
PAGE = 60


def _slim(r: dict, m: dict) -> dict:
    """埋め込みJSONの1行。ブランド名・楽器種名は辞書で引く。空・既定値のキーは落として軽くする。"""
    d = {k: r[k] for k in JS_KEYS if k in r}
    d["acc"] = "" if r["accN"] else r["acc"]              # 付属品は点数だけ（本文は型番ページ）
    d["material"] = r["material"][:40]
    d["series"] = r["series"][:40]
    d["msrpDate"] = m["msrp_date"] or ""                  # 実際の改定日だけ。無い型番はJSが「改定日はメーカー未記載（確認日）」を組む
    d["dk"] = m["msrp_date_kind"] if m.get("msrp_date") else ""
    if m["fetched"] != cfg.DB_FETCHED:
        d["fetched"] = m["fetched"]
    for k, empty in (("msrp", None), ("street", ""), ("flags", []), ("msrpDate", ""), ("dk", ""), ("acc", "")):
        if d.get(k) == empty:
            d.pop(k, None)
    if r["current"]:
        del d["current"]
        del d["statusLabel"]
    return d


def catalog_html(rows: list, prefix: str, model_page: dict) -> str:
    recs = [record(m, prefix, model_page) for m in rows]
    dic = {"brand": {k: v["label"] for k, v in db.BRANDS.items()}, "instrument": db.INSTRUMENT_LABEL, "fetched": cfg.DB_FETCHED}
    data = json.dumps({"dic": dic, "models": [_slim(r, m) for r, m in zip(recs, rows)]}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    n_cur = sum(1 for r in recs if r["current"])
    # JSが無い環境向けの静的な導線（カード本体はJSが描く）
    fallback = (f'<noscript><p class="dbempty">カタログの絞り込みにはJavaScriptが必要です。'
                f'全型番は<a href="{prefix}models/index.html">型番ページ一覧</a>と<a href="{prefix}instruments/index.html">楽器種別の一覧</a>からご覧ください。</p></noscript>')
    return (f'{fallback}\n<div class="catalog" id="catalog" data-page="{PAGE}" data-score-max="{db.SCORE_MAX}"></div>\n'
            f'<p class="dbempty" id="catalog-empty" hidden>条件に合う型番がありません。<br>'
            f'<button type="button" class="reset" data-reset>絞り込みを解除して現行{n_cur}型番を表示</button></p>\n'
            f'<p class="dbmore" id="catalog-more" hidden><button type="button" class="reset" id="catalog-more-btn">さらに表示</button><span class="soft" id="catalog-more-n"></span></p>\n'
            f'<script id="models-json" type="application/json" data-note="{esc(cfg.NOTICE_PRICE + " " + cfg.NOTICE_NA)}">{data}</script>')


def spec_hero_html(models: list, prefix: str, model_page: dict) -> str:
    cards = "\n".join(card_html(record(m, prefix, model_page), hero=True) for m in models)
    return f'<div class="spechero n{len(models)}">\n{cards}\n</div>'


def group_tiles_html(rows: list, prefix: str = "", as_links: bool = False) -> str:
    import instrument_art
    tiles = []
    for g, label, fam, _iks in db.INSTRUMENT_GROUPS:
        n = sum(1 for m in rows if m["group_key"] == g and m["is_current"])   # 既定が「現行型番だけ」なので現行で数える
        if n == 0:
            continue
        inner = f'{instrument_art.icon(g, 46)}<b>{esc(label)}</b><small>{esc(db.FAMILY_LABEL[fam])}楽器</small><em data-count="{g}">{n}型番</em>'
        if as_links:
            tiles.append(f'    <a class="tile" href="{prefix}instruments/{g}.html">{inner}</a>')
        else:
            tiles.append(f'    <button type="button" class="tile" data-group="{g}" aria-pressed="false">{inner}</button>')
    return '  <div class="tiles" role="group" aria-label="楽器種（押して選ぶ・もう一度押すと解除）">\n' + "\n".join(tiles) + "\n  </div>"


def tools_html(rows: list) -> str:
    brands = sorted({m["brand_key"] for m in rows}, key=lambda k: -sum(1 for m in rows if m["brand_key"] == k))
    brand_opts = "".join(f'<option value="{k}">{esc(db.BRANDS[k]["label"])}（{sum(1 for m in rows if m["brand_key"] == k and m["is_current"])}）</option>' for k in brands)
    band_opts = "".join(f'<option value="{k}">{esc(l)}（{sum(1 for m in rows if db.price_band(m) == k and m["is_current"])}）</option>' for k, l, _a, _b in db.PRICE_BANDS)
    band_opts += f'<option value="none">{esc(db.PRICE_BAND_LABEL["none"])}（{sum(1 for m in rows if db.price_band(m) == "none" and m["is_current"])}）</option>'
    inst_opts = "".join(f'<option value="{ik}" data-group="{g}">{esc(db.INSTRUMENT_LABEL[ik])}（{sum(1 for m in rows if m["instrument"] == ik and m["is_current"])}）</option>'
                        for g, _l, _f, iks in db.INSTRUMENT_GROUPS for ik in iks if any(m["instrument"] == ik for m in rows))
    n_old = sum(1 for m in rows if not m["is_current"])
    return f"""  <div class="dbtools" role="search" id="tools">
    <div class="fitq">
      <div class="fld tilesfld"><span class="lbl">楽器種<small>（再度押すと解除。数字は現行型番の数）</small></span>
{group_tiles_html(rows)}
      </div>
      <select id="f-group" hidden aria-hidden="true" tabindex="-1"><option value="">指定しない</option>{"".join(f'<option value="{g}">{esc(l)}</option>' for g, l, _f, _ in db.INSTRUMENT_GROUPS)}</select>
      <div class="fld"><label for="f-instrument">楽器種をさらに絞る</label><select id="f-instrument"><option value="">すべて</option>{inst_opts}</select></div>
      <div class="fld"><label for="f-brand">ブランド</label><select id="f-brand"><option value="">すべて</option>{brand_opts}</select></div>
      <div class="fld"><label for="f-band">税込希望小売価格の帯</label><select id="f-band"><option value="">すべて</option>{band_opts}</select></div>
      <div class="fld chk"><label for="f-current"><input type="checkbox" id="f-current" checked> 現行型番だけ<small>（外すと生産終了・在庫限り{n_old}型番も表示）</small></label></div>
    </div>
    <details class="more-filters" id="more-filters">
      <summary>型番名で探す・並び順を変える</summary>
      <div class="more-in">
        <div class="fld"><label for="f-q">型番名・シリーズ名で探す</label><input type="search" id="f-q" placeholder="YAS-280、Xeno、WO1 など" autocomplete="off"></div>
        <div class="fld"><label for="f-sort">並び順</label><select id="f-sort"><option value="">ブランド→楽器種→定価順</option><option value="price-asc">税込定価が安い順</option><option value="price-desc">税込定価が高い順</option><option value="transp-desc">公表項目が多い順</option><option value="score-desc">公表情報の充実度が高い順</option></select></div>
      </div>
    </details>
    <div class="toolbar">
      <div class="viewtoggle" role="group" aria-label="表示切替"><button type="button" class="on" data-view="cards" aria-pressed="true">カード</button><button type="button" data-view="table" aria-pressed="false">表（全項目）</button></div>
      <button type="button" class="reset" id="f-reset">絞り込みを解除</button>
      <p class="hitline" id="f-hit" aria-live="polite"><b>{sum(1 for m in rows if m["is_current"])}</b> 型番を表示中</p>
    </div>
  </div>"""


def tray_html() -> str:
    return """  <a class="backtool" href="#db">絞り込みへ戻る</a>
  <div class="tray" id="tray" hidden>
    <div class="tray-in">
      <span class="lbl" id="tray-lbl">比較</span>
      <div class="picks" id="tray-picks"></div>
      <button type="button" class="go" id="tray-go">横並びで比較</button>
      <button type="button" class="clear" id="tray-clear">解除</button>
    </div>
  </div>
  <section class="cmp-out" id="cmp-out" hidden aria-labelledby="cmp-out-h">
    <h2 id="cmp-out-h">選んだ型番の比較<small>（メーカー公表値・違う行に色）</small></h2>
    <label class="samehide"><input type="checkbox" id="cmp-samehide"> 値が同じ行を隠す</label>
    <span class="samehide-n" id="cmp-samehide-n" aria-live="polite"></span>
    <div id="cmp-out-body"></div>
  </section>"""


CATALOG_JS = r"""<script>
(function(){
  var dataEl = document.getElementById('models-json');
  if(!dataEl) return;
  var PACK = JSON.parse(dataEl.textContent), DIC = PACK.dic, MODELS = PACK.models;
  MODELS.forEach(function(m){
    m.url = 'models/'+m.slug+'.html'; m.brandLabel = DIC.brand[m.brand] || m.brand; m.instrumentLabel = DIC.instrument[m.instrument] || m.instrument;
    if(m.msrp===undefined) m.msrp=null; if(!m.street) m.street=''; if(!m.flags) m.flags=[]; if(!m.acc) m.acc='';
    if(m.current===undefined){ m.current = true; m.statusLabel = '現行'; }
    m.msrpDate = m.msrpDate ? (m.dk+' '+m.msrpDate) : (m.msrpTxt.charAt(0)==='—' ? '' : '改定日はメーカー未記載（確認日 '+(m.fetched||DIC.fetched)+'）');
  });
  var NOTE = dataEl.getAttribute('data-note') || '';
  var byId = {}; MODELS.forEach(function(m){ byId[m.slug] = m; });
  var $ = function(id){ return document.getElementById(id); };
  var f = {group:$('f-group'), instrument:$('f-instrument'), brand:$('f-brand'), band:$('f-band'), current:$('f-current'), q:$('f-q'), sort:$('f-sort')};
  var hit = $('f-hit'), empty = $('catalog-empty'), tempty = $('dbtable-empty');
  var catalog = $('catalog'), tableView = $('table-view'), more = $('catalog-more'), moreBtn = $('catalog-more-btn'), moreN = $('catalog-more-n');
  var PAGE = parseInt(catalog.getAttribute('data-page') || '60', 10), SCORE_MAX = catalog.getAttribute('data-score-max') || '';
  var shown = PAGE;
  var rows = [];
  var tiles = Array.prototype.slice.call(document.querySelectorAll('.tiles .tile[data-group]'));
  var instOpts = f.instrument ? Array.prototype.slice.call(f.instrument.options) : [];
  function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
  function naSpan(t){ return String(t).indexOf('—')===0 ? '<span class="na">'+esc(t)+'</span>' : esc(t); }
  function big(v, label, sub){
    if(String(v).indexOf('—')===0){ var inner = String(v).replace(/^—/,'').replace(/^（|）$/g,''); return '<div class="num na"><b>—</b><small>'+esc(label)+'<em>'+esc(inner)+'</em></small></div>'; }
    var cls = String(v).length > 9 ? 'num long' : 'num';
    return '<div class="'+cls+'"><b>'+esc(v)+'</b><small>'+esc(label)+(sub?'<em>'+esc(sub)+'</em>':'')+'</small></div>';
  }
  function meter(n, total){ var s=''; for(var i=0;i<total;i++){ s += '<i class="'+(i<n?'on':'')+'"></i>'; } return '<div class="meter" role="img" aria-label="メーカーが公表している主要項目 '+n+'／'+total+'"><span class="lbl">公表項目</span><span class="segs">'+s+'</span><b>'+n+'<small>/'+total+'</small></b></div>'; }
  function cardHtml(m){
    var flags = (m.flags||[]).map(function(x){ return '<span class="flag f2">'+esc(x)+'</span>'; }).join('') + (m.current?'':'<span class="flag f3">'+esc(m.statusLabel)+'</span>');
    var nums = '<div class="mc-nums">'+big(m.msrpTxt, '税込希望小売価格', (m.msrp!=null? m.msrpDate : ''))+big(m.key,'調子')+big(m.finish,'仕上げ')+'</div>';
    var acc = m.accN ? m.accN+'点' : m.acc;
    var street = m.street ? '<div class="price">実売の最安値 '+esc(m.street)+'<small>当サイトが確認できた最安値。送料別・変動します（確認した店と日付は型番ページ）</small></div>' : '';
    var series = String(m.series).indexOf('—')===0 ? 'シリーズ名：メーカー未記載' : esc(m.series);
    return '<article class="mcard" data-slug="'+esc(m.slug)+'">'
      + '<div class="mc-top"><span class="mk">'+esc(m.brandLabel)+'</span><span class="ins">'+esc(m.instrumentLabel)+'</span>'+flags+'</div>'
      + '<h3 class="mc-name"><a href="'+esc(m.url)+'">'+esc(m.name)+'</a></h3><p class="mc-sub">'+series+'</p>'+nums
      + '<div class="mc-line"><span>材質 <b>'+esc(m.material)+'</b></span><span>付属品 <b>'+esc(acc)+'</b></span></div>'
      + meter(m.transp[0], m.transp[1])
      + '<div class="meter"><span class="lbl">公表情報の充実度</span><b>'+m.score+'<small>/'+SCORE_MAX+'</small></b><span class="soft">公表情報の充実度</span></div>'
      + street
      + '<div class="mc-actions"><label class="pick"><input type="checkbox" class="cmp-pick" value="'+esc(m.slug)+'"> 比較に追加<small>（最大4）</small></label><a class="more" href="'+esc(m.url)+'">型番ページ →</a></div>'
      + '</article>';
  }
  function norm(s){ s=(s||'').normalize('NFKC').toLowerCase().replace(/[\s　・\-ー_]/g,''); return s.replace(/[ぁ-ゖ]/g,function(c){return String.fromCharCode(c.charCodeAt(0)+0x60);}); }
  function visible(m, groupOverride){
    var g = (groupOverride===undefined) ? f.group.value : groupOverride;
    if(f.current && f.current.checked && !m.current) return false;
    if(g && m.group!==g) return false;
    if(f.instrument.value && m.instrument!==f.instrument.value) return false;
    if(f.brand.value && m.brand!==f.brand.value) return false;
    if(f.band.value && m.band!==f.band.value) return false;
    var text = norm(f.q.value);
    if(text && norm(m.name+' '+m.model+' '+m.brandLabel+' '+m.series+' '+m.instrumentLabel).indexOf(text)===-1) return false;
    return true;
  }
  function sortKey(m){
    var s = f.sort.value;
    if(s==='price-asc') return (m.msrp==null?1e12:m.msrp);
    if(s==='price-desc') return -(m.msrp==null?-1:m.msrp);
    if(s==='transp-desc') return -m.transp[0];
    if(s==='score-desc') return -m.score;
    return 0;
  }
  function syncInstOptions(){
    var g = f.group.value;
    instOpts.forEach(function(o){ if(!o.value) return; o.hidden = !!g && o.getAttribute('data-group')!==g; });
    if(g && f.instrument.value){ var cur = f.instrument.options[f.instrument.selectedIndex]; if(cur && cur.getAttribute('data-group')!==g) f.instrument.value=''; }
  }
  function apply(keepShown){
    syncInstOptions();
    if(!keepShown) shown = PAGE;
    var order = MODELS.slice();
    if(f.sort.value){ var idx={}; MODELS.forEach(function(m,i){idx[m.slug]=i;}); order.sort(function(a,b){ var ka=sortKey(a), kb=sortKey(b); return ka!==kb? ka-kb : idx[a.slug]-idx[b.slug]; }); }
    var vis = order.filter(function(m){ return visible(m); }), n = vis.length;   // filter に直接渡すと第2引数(index)が groupOverride に入る
    var keepPicks = {}; picks.forEach(function(s){ keepPicks[s]=true; });
    catalog.innerHTML = vis.slice(0, shown).map(cardHtml).join('');
    Array.prototype.forEach.call(catalog.querySelectorAll('.cmp-pick'), function(cb){ cb.checked = !!keepPicks[cb.value]; cb.disabled = picks.length>=4 && !cb.checked; });
    if(more){ more.hidden = n <= shown; if(moreN) moreN.textContent = ' 表示 '+Math.min(shown,n)+' / '+n+' 型番'; }
    var tb = document.querySelector('#dbtable tbody');
    if(tb && rows.length){ order.forEach(function(m){ var r = document.querySelector('#dbtable tr[data-slug="'+m.slug+'"]'); if(r){ r.hidden = !visible(m); tb.appendChild(r); } }); }
    var ev = 0; rows.forEach(function(r){ if(!r.hidden){ ev++; if(ev%2===0){ r.setAttribute('data-even',''); } else { r.removeAttribute('data-even'); } } });
    if(hit) hit.innerHTML = '<b>'+n+'</b> 型番を表示中';
    if(empty) empty.hidden = n!==0 || (tableView && !tableView.hidden);
    if(tempty) tempty.hidden = n!==0;
    tiles.forEach(function(x){ var g = x.getAttribute('data-group'); var on = g===f.group.value && !!f.group.value; x.classList.toggle('on', on); x.setAttribute('aria-pressed', on?'true':'false');
      var cnt = 0; MODELS.forEach(function(m){ if(visible(m, g)) cnt++; }); var em = x.querySelector('[data-count]'); if(em){ em.textContent = cnt+'型番'; }
      x.classList.toggle('zero', cnt===0 && !on); });
  }
  Object.keys(f).forEach(function(k){ if(f[k]) f[k].addEventListener(f[k].tagName==='INPUT' && f[k].type!=='checkbox' ?'input':'change', function(){ apply(false); }); });
  function resetAll(){
    Object.keys(f).forEach(function(k){ if(!f[k]) return; if(f[k].type==='checkbox'){ f[k].checked = (k==='current'); } else { f[k].value=''; } });
    picks = []; renderTray(); apply();
  }
  var rs = $('f-reset'); if(rs) rs.addEventListener('click', resetAll);
  if(moreBtn) moreBtn.addEventListener('click', function(){ shown += PAGE; apply(true); });
  Array.prototype.forEach.call(document.querySelectorAll('[data-reset]'), function(b){ b.addEventListener('click', resetAll); });
  tiles.forEach(function(b){ b.addEventListener('click', function(){ var g = b.getAttribute('data-group'); f.group.value = (f.group.value===g) ? '' : g; apply(); }); });
  Array.prototype.forEach.call(document.querySelectorAll('.chips a[data-brand]'), function(c){ c.addEventListener('click', function(e){ e.preventDefault(); f.brand.value=c.getAttribute('data-brand'); apply(); $('db').scrollIntoView({behavior:'smooth'}); }); });
  // 表ビューの行は、カードと同じ埋め込みJSONから最初に開いたときだけ作る（851行をHTMLに焼くと肥大化する）
  var tableBuilt = false;
  function buildTable(){
    if(tableBuilt) return;
    var tb = document.querySelector('#dbtable tbody');
    if(!tb) { tableBuilt = true; return; }
    tb.innerHTML = MODELS.map(function(m){
      var nm = '<a href="'+esc(m.url)+'"><b>'+esc(m.name)+'</b></a>';
      var flags = (m.flags||[]).map(function(x){ return '<span class="flag f2">'+esc(x)+'</span>'; }).join('') + (m.current?'':'<span class="flag f3">'+esc(m.statusLabel)+'</span>');
      var pick = '<label class="pick tpick"><input type="checkbox" class="cmp-pick" value="'+esc(m.slug)+'" aria-label="'+esc(m.name)+' を比較に追加"></label>';
      var acc = m.accN ? esc(m.accN+'点（型番ページに内訳）') : '<span class="na">'+esc(m.acc)+'</span>';
      var src = '<a href="'+esc(m.url)+'#sources">型番ページの出典欄</a>';
      return '<tr data-slug="'+esc(m.slug)+'">'
        + '<th scope="row" class="c-model">'+pick+nm+'<span class="mk">'+esc(m.brandLabel)+'</span>'+flags+'</th>'
        + '<td>'+esc(m.instrumentLabel)+'</td><td>'+naSpan(m.series)+'</td>'
        + '<td class="n">'+naSpan(m.msrpTxt)+'</td><td>'+(m.msrpDate?esc(m.msrpDate):'<span class="na">—</span>')+'</td>'
        + '<td>'+naSpan(m.key)+'</td><td>'+naSpan(m.finish)+'</td><td>'+naSpan(m.material)+'</td>'
        + '<td>'+acc+'</td><td>'+esc(m.statusLabel)+'</td><td>'+src+'</td></tr>';
    }).join('');
    rows = Array.prototype.slice.call(document.querySelectorAll('#dbtable tbody tr'));
    tableBuilt = true;
  }
  function setView(v){
    if(v==='table') buildTable();
    Array.prototype.forEach.call(document.querySelectorAll('.viewtoggle button'), function(x){ var on = x.getAttribute('data-view')===v; x.classList.toggle('on', on); x.setAttribute('aria-pressed', on?'true':'false'); });
    if(catalog) catalog.hidden = v!=='cards';
    if(tableView) tableView.hidden = v!=='table';
    try{ localStorage.setItem('kgz-view', v); }catch(e){}
    apply();
  }
  Array.prototype.forEach.call(document.querySelectorAll('.viewtoggle button'), function(b){ b.addEventListener('click', function(){ setView(b.getAttribute('data-view')); }); });
  // 比較トレイ（最大4）
  var picks = [], tray=$('tray'), trayPicks=$('tray-picks'), trayLbl=$('tray-lbl'), out=$('cmp-out'), outBody=$('cmp-out-body');
  // 表ビューの復元は picks の宣言より後（前だと apply() 内の picks 参照で例外になり catch に握り潰される・点検 2026-09-13）
  try{ if(localStorage.getItem('kgz-view')==='table') setView('table'); }catch(e){}
  function syncBodyPad(){ document.body.style.paddingBottom = (tray && !tray.hidden) ? (tray.offsetHeight + 12) + 'px' : ''; }
  function renderTray(){
    if(!tray) return;
    tray.hidden = picks.length===0;
    document.body.classList.toggle('has-tray', picks.length>0);
    trayLbl.textContent = '比較 '+picks.length+'/4';
    trayPicks.innerHTML = picks.map(function(s){ return '<span>'+esc(byId[s].name)+' <button type="button" aria-label="'+esc(byId[s].name)+' を解除" data-rm="'+s+'">×</button></span>'; }).join('');
    Array.prototype.forEach.call(trayPicks.querySelectorAll('[data-rm]'), function(b){ b.addEventListener('click', function(){ unpick(b.getAttribute('data-rm')); }); });
    Array.prototype.forEach.call(document.querySelectorAll('.cmp-pick'), function(cb){ cb.checked = picks.indexOf(cb.value)!==-1; cb.disabled = picks.length>=4 && !cb.checked; });
    if(picks.length===0 && out){ out.hidden=true; }
    syncBodyPad();
  }
  function unpick(s){ picks = picks.filter(function(x){ return x!==s; }); renderTray(); if(out && !out.hidden){ if(picks.length) renderCompare(); } }
  document.addEventListener('change', function(ev){
    var cb = ev.target;
    if(!cb || !cb.classList || !cb.classList.contains('cmp-pick')) return;
    if(cb.checked){ if(picks.length>=4){ cb.checked=false; return; } if(picks.indexOf(cb.value)===-1) picks.push(cb.value); }
    else { picks = picks.filter(function(x){ return x!==cb.value; }); }
    renderTray();
  });
  window.addEventListener('resize', syncBodyPad);
  var ROWS = [['楽器種','instrumentLabel'],['シリーズ','series'],['税込希望小売価格','msrpTxt'],['改定日・基準日','msrpDate'],['現行／終了','statusLabel'],['調子','key'],['仕上げ','finish'],['材質','material'],['付属品','accTxt'],['実売の最安値','street'],['公表項目','transp'],['公表情報の充実度','scoreTxt']];
  function cellTxt(m, key){ if(key==='scoreTxt') return m.score+' / '+SCORE_MAX+' 点'; if(key==='accTxt') return m.accN ? m.accN+'点（内訳は型番ページ）' : m.acc; var v = m[key]; if(v==null||v==='') return key==='street' ? '—（当サイト未取得）' : (key==='msrpDate' ? '—' : '—（未確認）'); if(Array.isArray(v)) return v[0]+' / '+v[1]+' 項目'; return String(v); }
  function td(s){ return s.charAt(0)==='—' ? '<td><span class="na">'+esc(s)+'</span></td>' : '<td>'+esc(s)+'</td>'; }
  function renderCompare(){
    if(!out) return;
    var ms = picks.map(function(s){ return byId[s]; });
    var same = $('cmp-samehide') && $('cmp-samehide').checked;
    var head = ms.map(function(m){ return '<th scope="col"><a href="'+m.url+'">'+esc(m.name)+'</a><span class="b">'+esc(m.brandLabel)+'</span></th>'; }).join('');
    var nd = 0;
    var body = ROWS.map(function(r){ var vals = ms.map(function(m){ return cellTxt(m, r[1]); });
      var allSame = ms.length>1 && vals.every(function(v){ return v===vals[0]; });
      if(same && allSame) return '';
      if(!allSame && ms.length>1) nd++;
      return '<tr'+(!allSame && ms.length>1 ? ' class="diff"':'')+'><th scope="row">'+r[0]+'</th>'+vals.map(td).join('')+'</tr>'; }).join('');
    var src = '<tr><th scope="row">出典</th>'+ms.map(function(m){ return '<td><a href="'+esc(m.url)+'#sources">型番ページの出典欄</a></td>'; }).join('')+'</tr>';
    outBody.innerHTML = '<div class="cmpwrap cmp-sticky"><table class="cmp"><caption class="visually-hidden">選んだ型番の比較</caption><thead><tr><th scope="col"><span class="visually-hidden">項目</span></th>'+head+'</tr></thead><tbody>'+body+src+'</tbody></table></div><p class="tnote">色の付いた行がメーカー公表値の違う項目です（'+nd+'項目）。'+esc(NOTE)+'</p>';
    out.hidden = false; out.scrollIntoView({behavior:'smooth'});
  }
  var go=$('tray-go'); if(go) go.addEventListener('click', renderCompare);
  var cl=$('tray-clear'); if(cl) cl.addEventListener('click', function(){ picks=[]; renderTray(); });
  var sh=$('cmp-samehide'); if(sh) sh.addEventListener('change', function(){ if(picks.length) renderCompare(); });
  // URLの ?group= / ?brand= で初期絞り込み（楽器種ページ・ブランド一覧からの導線）
  try{ var sp = new URLSearchParams(location.search); if(sp.get('group')) f.group.value = sp.get('group'); if(sp.get('brand')) f.brand.value = sp.get('brand'); }catch(e){}
  apply();
  // 「絞り込みへ戻る」は、カタログの絞り込み欄より下までスクロールしたときだけ出す（最初から出ていると意味が通らない）
  var back = document.querySelector('.backtool'), tools = $('tools');
  if(back && tools){
    var upd = function(){ back.classList.toggle('on', tools.getBoundingClientRect().bottom < 0); };
    upd(); window.addEventListener('scroll', upd, {passive:true}); window.addEventListener('resize', upd);
  }
})();
</script>"""


def hero_svg() -> str:
    """ヒーロー背景の抽象図形（管の輪郭と音孔の並び）。実機ではない。"""
    holes = "".join(f'<circle cx="{60 + i * 26}" cy="{120 - (i % 2) * 6}" r="{5 + (i % 3)}" fill="#F5EEDF" opacity=".8"/>' for i in range(7))
    return f"""<svg class="herosvg" viewBox="0 0 280 200" aria-hidden="true">
  <path d="M20 120 h180 l60 -50 v100 l-60 -50" fill="none" stroke="#F5EEDF" stroke-width="2.5" stroke-linejoin="round"/>
  <path d="M20 108 h175" stroke="#F5EEDF" stroke-width="1.2" opacity=".6"/>
  <path d="M20 132 h175" stroke="#F5EEDF" stroke-width="1.2" opacity=".6"/>
  <path d="M260 70 q28 50 0 100" fill="none" stroke="#E6B85C" stroke-width="2"/>
  {holes}
</svg>"""
