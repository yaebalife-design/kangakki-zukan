# -*- coding: utf-8 -*-
"""サイト共通の <head> / ヘッダー / フッター / CSS を1箇所に集約する（管楽器図鑑）。

プロテインスキマー図鑑の site_chrome.py を土台に、配色・ロゴ・ナビ・フッター文言を本サイト用へ差し替えた。
  ・配色は真鍮（ブラス）の文脈（濃い金茶＋生成りの紙）。単一テーマ・全色を明示的に塗る
  ・GA4/GSCは未発行（ID流用禁止）。site_config で空の間はタグ自体を出力しない
  ・フッターは必須常設表記（PR／各メーカーと無関係／価格の注記／Amazon規約5条＝リンクを置く間だけ）を常に含む
  ・商品画像を持てないサイトなので、表と数値が主役になるCSSにしている
"""
import hashlib
import sys
from functools import lru_cache
from pathlib import Path

import site_config as cfg

SITE_DIR = Path(__file__).parent.parent / "site"

# (キー, ラベル, パス) — ナビの唯一の正
NAV_ITEMS = [
    ("home",   "型番を探す", "index.html"),
    ("compare", "型番の違い", "compare/index.html"),
    ("instruments", "楽器種・相場", "instruments/index.html"),
    ("brands", "ブランド", "brands.html"),
    ("models", "型番一覧", "models/index.html"),
    ("about",  "サイトについて", "about.html"),
]

FOOTER_INFO_LINKS = [
    ("contact.html",    "お問い合わせ"),
    ("about.html",      "このサイトについて"),
    ("data.html",       "データの作り方・出典方針"),
    ("privacy.html",    "プライバシーポリシー"),
    ("disclaimer.html", "免責事項・広告表記"),
]


@lru_cache(maxsize=1)
def css_version() -> str:
    """style.css の中身から作るキャッシュ破棄用の文字列（手打ちの日付だとCDNが古いCSSを返し続ける事故が起きる）。"""
    return hashlib.sha1(STYLE_CSS.encode("utf-8")).hexdigest()[:10]


STYLE_CSS = """/* ══ 管楽器図鑑 ══  単一テーマ（生成りの紙＋真鍮の金茶）。全色を明示的に塗る。表・数値が主役。 */
:root{
  --paper:#F8F6F1; --card:#FFFFFF; --ink:#2A2620; --ink-soft:#6B6258; --line:#E3DCD0;
  --brass:#8A5A17; --brass-deep:#5C3A0C; --brass-wash:#F7F0E2; --th-bg:#F1EAD9; --zebra:#FBF9F4;
  --amber-ink:#7A4A10; --amber-wash:#FBF1DD; --amber-line:#D9A44A;
  --wash:#F3EFE6; --na:#6B6258; --ok:#1E6B3A; --ng:#9B2C2C;
  --rkt:#B4433E; --amz:#8F5F22; --yh:#4A1E8A; --shop:#3B5D8A; --kaitori:#2D6B5E;
  --serif:"Shippori Mincho B1","Yu Mincho","Hiragino Mincho ProN",serif;
  --sans:"Zen Kaku Gothic New","Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif;
}
@media (prefers-reduced-motion: reduce){ *{transition:none!important} }
*{box-sizing:border-box}
body{background:var(--paper); color:var(--ink); font-family:var(--sans); font-size:16px; line-height:1.8; margin:0;
  -webkit-font-smoothing:antialiased; word-break:auto-phrase}
p,li,dd,td,th,figcaption,summary{text-wrap:pretty}
h1,h2,h3,.mc-name{text-wrap:balance}
a{color:var(--brass)}
a:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid var(--brass); outline-offset:2px; border-radius:4px}
p{margin:.5em 0}
.soft{color:var(--ink-soft); font-size:13px}
.n,.num{font-variant-numeric:tabular-nums}
.skip-link{position:absolute; left:-9999px; top:0; background:var(--card); color:var(--brass); padding:8px 14px; z-index:99}
.skip-link:focus{left:8px; top:8px; border:2px solid var(--brass)}
.visually-hidden{position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0); white-space:nowrap}
[hidden]{display:none!important}

/* ── ヘッダー ── */
header.site{background:var(--card); border-bottom:1px solid var(--line); position:sticky; top:0; z-index:20}
.site-inner{max-width:1180px; margin:0 auto; padding:10px 20px; display:flex; align-items:center; gap:20px; flex-wrap:wrap}
.logo{display:flex; align-items:center; gap:10px; text-decoration:none; color:var(--ink)}
.logo svg{display:block; flex:0 0 auto}
.logo .words{line-height:1.25}
.logo .l1{display:block; font-size:11px; letter-spacing:.24em; color:var(--ink-soft); font-weight:500}
.logo .l2{display:block; font-family:var(--serif); font-weight:700; font-size:22px; letter-spacing:.06em}
.logo .l2 em{font-style:normal; color:var(--brass)}
.logo .sub{font-size:12.5px; color:var(--ink-soft); letter-spacing:.06em; margin-left:14px; align-self:flex-end; padding-bottom:4px}
nav.tabs{margin-left:auto; display:flex; gap:4px; flex-wrap:wrap}
nav.tabs a{font-size:13.5px; font-weight:500; padding:8px 12px; white-space:nowrap; border-radius:999px; border:1px solid transparent;
  color:var(--ink-soft); text-decoration:none; min-height:44px; display:inline-flex; align-items:center}
nav.tabs a[aria-current],nav.tabs a.on{background:var(--brass-wash); color:var(--brass-deep); border-color:#E0CFA6; font-weight:700}
nav.tabs a:hover{color:var(--brass)}
@media(max-width:860px){
  .site-inner{padding:6px 14px; gap:8px}
  .logo .l1,.logo .sub{display:none}
  .logo .l2{font-size:18px; white-space:nowrap}
  nav.tabs{width:100%; margin-left:0; gap:2px; flex-wrap:nowrap; overflow-x:auto; -webkit-overflow-scrolling:touch; padding-right:22px;
    -webkit-mask-image:linear-gradient(90deg,#000 calc(100% - 26px),transparent); mask-image:linear-gradient(90deg,#000 calc(100% - 26px),transparent)}
  nav.tabs a{padding:8px 10px; font-size:12.5px}
}
main{max-width:1180px; margin:0 auto; padding:0 20px 48px}
.measure{max-width:760px; margin-left:auto; margin-right:auto}
.measure.left{margin-left:0}

/* ── 見出し ── */
h1{font-family:var(--serif); font-weight:600; font-size:26px; line-height:1.55; letter-spacing:.02em; margin:0 0 6px}
@media(min-width:700px){ h1{font-size:31px} }
@media(max-width:700px){ h1{font-size:23px} h1 br{display:none} }
h2{font-family:var(--serif); font-weight:600; font-size:20px; letter-spacing:.05em; margin:46px 0 14px; padding:0 0 8px 14px; position:relative; border-bottom:1px solid var(--line)}
@media(min-width:700px){ h2{font-size:23px} }
h2::before{content:""; position:absolute; left:0; top:.32em; width:3px; height:1.15em; background:var(--brass); border-radius:2px}
h2 small{font-family:var(--sans); font-weight:500; font-size:13px; color:var(--ink-soft); margin-left:6px}
h3{font-family:var(--serif); font-weight:600; font-size:17px; letter-spacing:.03em; margin:26px 0 8px}
h4{font-family:var(--sans); font-weight:700; font-size:14.5px; margin:18px 0 6px; color:var(--brass-deep)}
h2[id],h3[id],#tools,#catalog,#db,#cmp-out,#table-view{scroll-margin-top:84px}
.secno{display:inline-block; font-family:var(--sans); font-size:12px; letter-spacing:.14em; color:var(--brass); margin-right:10px; vertical-align:middle}

/* ══ ヒーロー ══ */
.hero2{margin:0 -20px; padding:52px 20px 44px; color:#F5EEDF; position:relative; overflow:hidden;
  background:radial-gradient(1100px 600px at 85% -20%, #A8722A 0%, #5C3A0C 40%, #22150A 100%)}
.hero2::after{content:""; position:absolute; inset:0; pointer-events:none; opacity:.12;
  background-image:linear-gradient(#fff 1px,transparent 1px),linear-gradient(90deg,#fff 1px,transparent 1px); background-size:36px 36px}
.hero2 .in{max-width:1180px; margin:0 auto; position:relative; z-index:1; display:grid; grid-template-columns:minmax(0,1.1fr) minmax(0,.9fr); gap:36px; align-items:center}
.hero2 .viz{background:linear-gradient(160deg,rgba(255,255,255,.08),rgba(255,255,255,.02)); border:1px solid rgba(255,255,255,.16); border-radius:18px; padding:14px 12px 8px; box-shadow:0 20px 50px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.12)}
.hero2 .art{position:relative; display:flex; align-items:center; justify-content:center; min-height:380px}
.heroart{width:100%; max-width:560px; height:auto; display:block; filter:drop-shadow(0 18px 30px rgba(0,0,0,.45))}
.heroart .ha-sax{animation:ha-float 7s ease-in-out infinite}
.heroart .ha-tp{animation:ha-float 9s ease-in-out infinite reverse}
.heroart .ha-flute{animation:ha-float 11s ease-in-out infinite}
@keyframes ha-float{0%,100%{transform:translateY(0)} 50%{transform:translateY(-8px)}}
@media(prefers-reduced-motion:reduce){ .heroart g{animation:none} }
@media(max-width:1000px){ .hero2 .art{min-height:0; margin-top:-8px} .heroart{max-width:340px; opacity:.9} }
.viz-dark{margin:12px 0 6px; padding:16px; border-radius:18px; background:radial-gradient(900px 400px at 80% -20%, #8A5A17 0%, #4E300A 45%, #22150A 100%); color:#F5EEDF}
.viz-dark .viz{background:transparent; border:none; box-shadow:none; padding:0}
.viz-dark .vz-cap{font-size:12.5px; color:#E6CFA0; margin:8px 4px 0}
.constellation{width:100%; height:auto; display:block}
.gicon{display:block; margin:0 auto 4px; color:var(--brass); width:46px; height:46px}
.tile .gicon{transition:transform .2s}
.tile:hover .gicon{transform:translateY(-2px) scale(1.06)}
h1 .gicon{display:inline-block; vertical-align:-10px; margin:0 8px 0 0; width:40px; height:40px}
.constellation .cs-a circle{transition:r .12s}
.constellation .cs-a:hover circle{r:5.5}
.hero2 .viz .ladder{background:transparent}
.hero2 .viz svg rect.bg{fill:transparent}
.hero2 .viz svg rect.bar{fill:#E6B85C; opacity:.92}
.hero2 .viz text{fill:#F5EEDF} .hero2 .viz .ladder line{stroke:rgba(255,255,255,.25)}
.hero2 .viz .vz-cap{font-size:12px; color:#E6CFA0; margin:6px 4px 4px; line-height:1.5}
.hero2 .viz .vz-cap a{color:#FFF}
@media(max-width:1000px){ .hero2 .in{grid-template-columns:1fr} }
/* 3ステップ */
.steps3{display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin:14px 0 6px; padding:0; list-style:none; counter-reset:s3}
.steps3 li{counter-increment:s3; background:var(--card); border:1px solid var(--line); border-radius:14px; padding:16px 18px 14px 58px; position:relative; min-height:96px}
.steps3 li::before{content:counter(s3); position:absolute; left:16px; top:16px; width:30px; height:30px; border-radius:50%; background:var(--brass); color:#fff; font-weight:700; display:flex; align-items:center; justify-content:center; font-family:var(--serif)}
.steps3 b{display:block; font-family:var(--serif); font-size:16px; margin-bottom:2px}
.steps3 span{font-size:13px; color:var(--ink-soft); line-height:1.6}
.steps3 a{font-weight:700}
@media(max-width:760px){ .steps3{grid-template-columns:1fr} }
/* ペアカード */
.pairgrid{display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:12px; margin:14px 0 6px}
.paircard{display:flex; flex-direction:column; gap:6px; background:var(--card); border:1px solid var(--line); border-radius:14px; padding:16px 18px; text-decoration:none; color:var(--ink); transition:box-shadow .15s,border-color .15s,transform .15s}
.paircard:hover{border-color:#D6BE8E; box-shadow:0 8px 22px rgba(92,58,12,.12); transform:translateY(-2px)}
.paircard .pc-b{font-size:12px; color:var(--brass-deep); letter-spacing:.06em}
.paircard .pc-n{font-family:var(--serif); font-size:18px; font-weight:600; line-height:1.4}
.paircard .pc-n i{font-style:normal; font-size:12px; color:var(--brass); margin:0 6px; letter-spacing:.1em}
.paircard .pc-p{font-variant-numeric:tabular-nums; font-size:14px; color:var(--ink)} .paircard .pc-p small{display:block; color:var(--ink-soft); font-size:12px}
.paircard .pc-d{font-size:12.5px; color:var(--ink-soft)}
/* ラダー図 */
figure.ladderfig{padding:8px 8px 12px}
figure.ladderfig svg{max-width:none; width:100%}
.ladder a{cursor:pointer} .ladder a:hover rect,.ladder a:hover circle{filter:brightness(.85)} .ladder a:focus-visible{outline:2px solid var(--brass)}
.ladder text{pointer-events:none}
@media(max-width:560px){ figure.ladderfig svg{min-width:640px} }
/* セクションの導入帯 */
.usecase{display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:12px; margin:14px 0 6px}
.usecase a{display:block; background:var(--card); border:1px solid var(--line); border-left:4px solid var(--brass); border-radius:0 12px 12px 0; padding:14px 16px; text-decoration:none; color:var(--ink); transition:box-shadow .15s}
.usecase a:hover{box-shadow:0 6px 18px rgba(92,58,12,.10)}
.usecase b{display:block; font-family:var(--serif); font-size:16px; margin-bottom:2px}
.usecase span{font-size:12.5px; color:var(--ink-soft); line-height:1.6}
.subnav{position:sticky; top:62px; z-index:15; background:rgba(248,246,241,.92); backdrop-filter:blur(6px); border-bottom:1px solid var(--line); margin:0 -20px; padding:6px 20px; display:flex; gap:4px; overflow-x:auto; -webkit-overflow-scrolling:touch}
.subnav a{font-size:13px; white-space:nowrap; padding:8px 12px; border-radius:999px; color:var(--ink-soft); text-decoration:none; min-height:40px; display:inline-flex; align-items:center}
.subnav a:hover{background:var(--brass-wash); color:var(--brass-deep)}
@media(max-width:860px){ .subnav{top:0; position:static} }
.mpage .neighbors{display:grid; grid-template-columns:1fr 1fr; gap:12px; margin:12px 0}
.mpage .neighbors a{display:block; background:var(--card); border:1px solid var(--line); border-radius:12px; padding:12px 16px; text-decoration:none; color:var(--ink)}
.mpage .neighbors a:hover{border-color:var(--brass)}
.mpage .neighbors small{display:block; color:var(--ink-soft); font-size:12px}
.mpage .neighbors b{font-family:var(--serif); font-size:16px}
.mpage .neighbors .d{color:var(--brass-deep); font-variant-numeric:tabular-nums; font-weight:700}
@media(max-width:560px){ .mpage .neighbors{grid-template-columns:1fr} }
.checklist{list-style:none; padding:0; margin:10px 0; display:grid; gap:8px}
.checklist li{background:var(--card); border:1px solid var(--line); border-radius:10px; padding:10px 14px 10px 40px; position:relative; font-size:14px}
.checklist li::before{content:"✓"; position:absolute; left:14px; top:10px; color:var(--brass); font-weight:700}
.checklist li.na::before{content:"—"; color:var(--na)}
.hero2 .kicker{color:#E6CFA0; font-size:13px; letter-spacing:.12em; margin:0 0 6px; font-weight:700}
.hero2 .prnote{color:#E9DCC3; margin:0 0 10px; font-size:12.5px}
.hero2 h1{color:#FFFFFF; font-size:30px; line-height:1.45; margin:0 0 12px; max-width:20em}
@media(min-width:900px){ .hero2 h1{font-size:38px} }
.hero2 .lead{color:#EADFCB; font-size:15.5px; max-width:46em}
.stats{display:flex; flex-wrap:wrap; gap:10px; margin:22px 0 0; padding:0; list-style:none}
.stats li{background:rgba(255,255,255,.07); border:1px solid rgba(255,255,255,.14); border-left:3px solid #E6B85C; border-radius:0 8px 8px 0; padding:8px 16px; font-size:13px; color:#EADFCB}
.stats b{display:block; font-family:var(--serif); font-size:21px; color:#FFFFFF; font-variant-numeric:tabular-nums; line-height:1.3}
.hero2 .cta{margin-top:22px; display:flex; gap:10px; flex-wrap:wrap}
.hero2 .cta a{display:inline-flex; align-items:center; min-height:46px; padding:8px 20px; border-radius:999px; font-weight:700; text-decoration:none; font-size:14.5px}
.hero2 .cta a.pri{background:#E6B85C; color:#241503}
.hero2 .cta a.sec{border:1.5px solid #E6B85C; color:#F5EEDF}
@media(max-width:860px){ .hero2{padding:24px 20px 22px} .hero2 h1{font-size:24px; line-height:1.4} .hero2 .lead{font-size:14px}
  .stats{display:grid; grid-template-columns:repeat(2,1fr); gap:6px} .stats li{padding:8px 10px} .stats b{font-size:18px} }
@media(max-width:560px){ .s-hide{display:none} .stats{grid-template-columns:repeat(3,1fr)} .stats li{font-size:11px} }

/* ── 索引タブ・チップ ── */
.idx-tabs{display:flex; flex-wrap:wrap; gap:8px 6px; margin:18px 0 4px}
.idx-tabs a,.idx-tabs span{font-size:13px; font-weight:500; text-decoration:none; color:var(--ink); background:var(--card); border:1px solid var(--line);
  border-left:3px solid var(--brass); border-radius:0 8px 8px 0; padding:8px 16px 8px 12px; min-height:44px; display:inline-flex; align-items:center}
.idx-tabs a:hover{background:var(--brass-wash)}
.idx-tabs a.on{background:var(--brass); border-color:var(--brass); color:#fff; font-weight:700}
.idx-tabs a i{font-style:normal; font-size:12px; color:var(--ink-soft); margin-left:6px}
.idx-tabs a.on i{color:#F1E3C6}
.idx-tabs span{color:var(--ink-soft); background:transparent; border-style:dashed; border-left-color:var(--line)}
.chips{display:flex; flex-wrap:wrap; gap:8px}
.chips a,.chips span{font-size:13px; padding:10px 16px; min-height:44px; display:inline-flex; align-items:center; background:var(--card); border:1px solid var(--line); border-radius:999px; color:var(--ink); text-decoration:none}
.chips a:hover{border-color:var(--brass); color:var(--brass)}
.chips i{font-style:normal; font-size:12px; color:var(--ink-soft); margin-left:6px}

/* ── 楽器種タイル ── */
.tiles{display:grid; grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); gap:10px; margin:18px 0 6px}
.tile{background:var(--card); border:1px solid var(--line); border-radius:12px; padding:12px 10px 10px; cursor:pointer; font-family:var(--sans); color:var(--brass-deep);
  text-align:center; display:flex; flex-direction:column; align-items:center; gap:3px; min-height:44px; text-decoration:none}
.tile b{font-size:14px; color:var(--ink)}
.tile small{font-size:12px; color:var(--ink-soft)}
.tile em{font-style:normal; font-size:12.5px; font-weight:700; color:var(--brass); background:var(--brass-wash); border-radius:999px; padding:1px 10px; margin-top:auto}
.tile:hover,.tile.on{border-color:var(--brass); box-shadow:0 0 0 2px var(--brass-wash)}
.tile.on{background:var(--brass-wash); border:2px solid var(--brass); box-shadow:none}
.tile.on em{background:var(--brass); color:#fff}
.tile.zero{opacity:.45}
@media(max-width:700px){ .tiles{display:flex; overflow-x:auto; scroll-snap-type:x mandatory; gap:8px; padding-bottom:6px; -webkit-overflow-scrolling:touch}
  .tiles .tile{flex:0 0 40%; scroll-snap-align:start} }

/* ══ 絞り込みツール ══ */
.dbtools{display:flex; flex-direction:column; gap:10px; margin:16px 0 10px; background:var(--card); border:1px solid var(--line); border-radius:10px; padding:14px 18px}
.dbtools,.dbtools > *{min-width:0}
.fitq{display:flex; flex-wrap:wrap; gap:10px 14px; align-items:flex-end; width:100%}
.fitq .fld,.more-in .fld{display:flex; flex-direction:column; gap:4px; flex:1 1 12em; min-width:0; max-width:22em}
.dbtools label,.dbtools .lbl{font-size:12.5px; color:var(--ink-soft); letter-spacing:.04em; font-weight:700}
.dbtools select,.dbtools input[type=search],.dbtools input[type=number]{font-family:var(--sans); font-size:14px; padding:9px 12px; min-height:44px; border:1px solid var(--line); border-radius:8px; background:var(--card); color:var(--ink); width:100%}
.fitq .fld.chk{flex:1 1 20em; max-width:100%}
.fitq .fld.chk label{display:flex; flex-wrap:wrap; align-items:center; gap:8px; min-height:44px; font-size:13.5px; color:var(--ink); font-weight:600; cursor:pointer}
.fitq .fld.chk input{width:18px; height:18px; accent-color:var(--brass)}
.fitq .fld.chk small{font-weight:400; color:var(--ink-soft)}
.fitq .tilesfld{flex:0 0 100%; max-width:100%}
.more-filters summary{cursor:pointer; font-size:13.5px; color:var(--brass); padding:8px 0 8px 1.7em; min-height:44px; display:block; position:relative; list-style:none}
.more-filters summary::before{content:"＋"; position:absolute; left:0; top:12px; font-weight:700}
.more-filters[open] summary::before{content:"−"}
.more-in{display:flex; flex-wrap:wrap; gap:10px 14px; padding:4px 0 6px}
.toolbar{display:flex; flex-wrap:wrap; align-items:center; gap:10px 14px; border-top:1px dashed var(--line); padding-top:10px}
.viewtoggle{display:inline-flex; border:1px solid var(--line); border-radius:8px; overflow:hidden}
.viewtoggle button{font-family:var(--sans); font-size:13.5px; padding:0 14px; min-height:44px; border:none; background:var(--card); color:var(--ink-soft); cursor:pointer}
.viewtoggle button.on{background:var(--brass); color:#fff; font-weight:700}
.dbtools .reset{font-size:13px; background:none; border:none; color:var(--brass); cursor:pointer; text-decoration:underline; padding:10px 4px; min-height:44px}
.toolbar .hitline{margin-left:auto; padding:5px 16px; font-size:13px; color:var(--brass-deep); background:var(--brass-wash); border:1px solid #E0CFA6; border-radius:999px}
.toolbar .hitline b{font-size:19px; color:var(--brass-deep); margin-right:2px}
@media(max-width:560px){ .fitq .fld{flex-basis:100%; max-width:none} .toolbar .hitline{width:100%; text-align:center; margin:4px 0 0} }

/* ══ カード型カタログ ══ */
.catalog{display:grid; grid-template-columns:repeat(auto-fill,minmax(290px,1fr)); gap:14px; margin:14px 0 6px}
.catalog .mcard{content-visibility:auto; contain-intrinsic-size:auto 360px}
.mcard{background:var(--card); border:1px solid var(--line); border-radius:14px; padding:16px 18px 14px; display:flex; flex-direction:column; gap:8px; box-shadow:0 1px 2px rgba(92,58,12,.05); transition:box-shadow .15s, border-color .15s}
.mcard:hover{border-color:#D6BE8E; box-shadow:0 6px 18px rgba(92,58,12,.10)}
.mcard,.mcard > *,.mc-nums,.mc-nums .num{min-width:0}
.mc-top{display:flex; justify-content:space-between; align-items:center; gap:8px; flex-wrap:wrap}
.mc-top .mk{font-size:12.5px; letter-spacing:.06em; color:var(--brass-deep); background:var(--brass-wash); border-radius:4px; padding:2px 9px; font-weight:700}
.mc-top .ins{font-size:12.5px; color:var(--ink-soft)}
.flag{display:inline-block; font-size:11.5px; font-weight:700; letter-spacing:.02em; border-radius:3px; padding:0 6px; border:1px solid currentColor; vertical-align:1px}
.flag.f2{color:#8A5A18; background:var(--amber-wash)}
.flag.f3{color:#7B3A46; background:#FBEFF1}
.flag.f4{color:#4A5A6B; background:#EEF2F5}
.mc-name{font-family:var(--serif); font-size:18.5px; margin:0; line-height:1.4; letter-spacing:.02em}
.mc-name a{color:var(--ink); text-decoration:underline; text-decoration-color:var(--brass); text-decoration-thickness:2px; text-underline-offset:4px}
.mc-name a:hover{color:var(--brass)}
.mc-sub{font-size:12.5px; color:var(--ink-soft); margin:-4px 0 0}
.mc-nums{display:grid; grid-template-columns:1.4fr .8fr 1fr; gap:8px; padding:10px 0 4px; border-top:1px dashed var(--line); border-bottom:1px dashed var(--line); align-items:start; min-height:78px}
.mc-nums .num b{display:block; font-family:var(--serif); font-size:22px; line-height:1.15; color:var(--ink); font-variant-numeric:tabular-nums; letter-spacing:-.01em; overflow-wrap:anywhere; word-break:normal}
@media(max-width:560px){ .mc-nums{grid-template-columns:1fr 1fr} .mc-nums .num:first-child{grid-column:1/-1} }
.mc-nums .num.long b{font-size:15px; line-height:1.3}
.mc-nums .num small{display:block; font-size:11.5px; color:var(--ink-soft); line-height:1.4; margin-top:2px}
.mc-nums .num small em{display:block; font-style:normal; font-size:11px; color:var(--na)}
.mc-nums .num.na b{color:var(--na); font-size:18px}
.mc-line{font-size:12.5px; color:var(--ink-soft); display:flex; flex-wrap:wrap; gap:4px 12px}
.mc-line b{color:var(--ink); font-weight:600}
.meter{display:flex; align-items:center; gap:8px; font-size:12.5px; color:var(--ink-soft)}
.meter .segs{display:flex; gap:2px; flex:1}
.meter .segs i{flex:1; height:7px; border-radius:2px; background:#EAE3D5}
.meter .segs i.on{background:#C79A4B}
.meter b{color:var(--ink); font-variant-numeric:tabular-nums; font-size:14px}
.meter b small{color:var(--ink-soft); font-size:11.5px}
.mcard .price{font-size:13px; color:var(--ink); min-height:20px}
.mcard .price small{display:block; font-size:11.5px; color:var(--ink-soft)}
.mc-actions{display:flex; justify-content:space-between; align-items:center; gap:8px 12px; margin-top:auto; padding-top:6px; font-size:13px; flex-wrap:wrap}
.mc-actions .pick{display:inline-flex; align-items:center; gap:6px; color:var(--ink-soft); cursor:pointer; min-height:44px; margin-right:auto; white-space:nowrap}
.mc-actions .pick input{width:16px; height:16px; accent-color:var(--brass)}
.mc-actions .pick small{font-weight:400}
.mc-actions .more{font-weight:700; text-decoration:none; padding:10px 0; min-height:44px; display:inline-flex; align-items:center; white-space:nowrap}
.mcard.is-strip{padding:12px 16px; gap:6px; border-color:var(--brass-wash); box-shadow:none; background:var(--zebra)}
.mcard.is-strip .mc-nums{border-bottom:none; padding-bottom:0}
.spechero{display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:14px; margin:10px 0 4px}
.spechero.n3,.spechero.n4{grid-template-columns:repeat(2,minmax(0,1fr))}
@media(max-width:560px){ .spechero.n3,.spechero.n4{grid-template-columns:1fr} }
.dbempty{background:var(--card); border:1px dashed #E0CFA6; border-radius:12px; padding:28px 22px; text-align:center; font-size:15px; color:var(--ink); margin:14px 0; line-height:1.9}
.dbmore{text-align:center; margin:10px 0 4px}
.dbmore .reset{display:inline-flex; align-items:center; min-height:44px; padding:0 22px; border:1px solid var(--brass); border-radius:999px; background:var(--card); color:var(--brass); font-weight:700; cursor:pointer; font-family:var(--sans); font-size:13.5px; text-decoration:none}
.dbmore .soft{margin-left:10px}
.dbempty .reset{display:inline-flex; align-items:center; min-height:44px; margin-top:10px; padding:0 20px; border:1px solid var(--brass); border-radius:999px; background:var(--card); color:var(--brass); font-weight:700; cursor:pointer; font-family:var(--sans); font-size:13.5px}

/* ══ 全型番の表（表ビュー・記事内の静的表） ══ */
.dbwrap{position:relative; margin:6px 0 4px; border:1px solid var(--line); border-radius:10px; background:var(--card); overflow:auto; max-height:min(80vh,900px); -webkit-overflow-scrolling:touch}
table.db{border-collapse:separate; border-spacing:0; table-layout:fixed; font-size:13px; line-height:1.6}
.db th,.db td{padding:9px 11px; text-align:left; border-bottom:1px solid var(--line); vertical-align:top; background:var(--card); overflow-wrap:anywhere}
.db thead th{position:sticky; top:0; z-index:3; font-size:12px; letter-spacing:.03em; font-weight:700; color:var(--brass-deep); background:var(--th-bg); border-bottom:2px solid #DCCBA5; white-space:nowrap}
.db tbody tr[data-even] td,.db tbody tr[data-even] .c-model{background:var(--zebra)}
.db tbody tr:hover td,.db tbody tr:hover .c-model{background:var(--brass-wash)}
.db .c-model{position:sticky; left:0; z-index:2; border-right:1px solid var(--line)}
.db thead .c-model{z-index:4}
.db .c-model b{font-weight:700; display:block; line-height:1.45}
.db .c-model .mk{display:block; font-size:12.5px; color:var(--ink-soft)}
.db .c-model a{text-decoration:none} .db .c-model a b{text-decoration:underline; text-underline-offset:2px}
.db .na,.minitbl td .na,.cmp .na{color:var(--na); font-size:12.5px; background:#F3EFE6; border-radius:3px; padding:1px 5px; box-decoration-break:clone; -webkit-box-decoration-break:clone}
.db .n{white-space:nowrap}
.db tr.hl th,.db tr.hl td{background:#FFF3D6!important}
.db .tpick{display:inline-flex; align-items:center; margin-right:6px; vertical-align:middle}
.db .tpick input{width:16px; height:16px; accent-color:var(--brass)}
.dbnote,.tnote{font-size:12.5px; color:var(--ink-soft); margin:8px 0}
.scrollhint{font-size:12.5px; color:var(--ink-soft); margin:0 0 4px}
@media(max-width:700px){ .dbwrap{margin-left:-20px; margin-right:-20px; border-radius:0; border-left:none; border-right:none} .db .c-model{font-size:12.5px} }
.dbwrap,.cmpwrap{background:linear-gradient(90deg,var(--card) 30%,rgba(255,255,255,0)) left/40px 100% no-repeat,
  linear-gradient(270deg,var(--card) 30%,rgba(255,255,255,0)) right/40px 100% no-repeat,
  radial-gradient(farthest-side at 0 50%,rgba(92,58,12,.16),transparent) left/14px 100% no-repeat,
  radial-gradient(farthest-side at 100% 50%,rgba(92,58,12,.16),transparent) right/14px 100% no-repeat, var(--card);
  background-attachment:local,local,scroll,scroll,local}

/* ── 記事・型番ページの部品 ── */
.crumb{font-size:12.5px; color:var(--ink-soft); margin:16px auto 2px}
.crumb a{color:var(--ink-soft); display:inline-block; padding:10px 2px; text-decoration:underline; text-underline-offset:2px}
.prnote{font-size:12.5px; color:var(--ink); margin:6px auto 2px}
.meta{font-size:12.5px; color:var(--ink-soft); display:flex; gap:18px; flex-wrap:wrap; margin:10px 0 16px}
.meta b{font-weight:500; font-variant-numeric:tabular-nums}
.lead-p{font-size:15px}
.mpage .kicker{margin:0 0 4px; font-size:13px; color:var(--ink-soft); letter-spacing:.04em}
.mpage .kicker span{margin-left:10px}
.mpage h1 small{display:block; font-size:16px; font-weight:500; color:var(--ink-soft); margin-top:4px}
.verdict{position:relative; background:var(--card); border:1px solid var(--brass); border-radius:10px; padding:0 22px 18px; margin:14px 0 10px; box-shadow:0 1px 3px rgba(0,0,0,.06); overflow:hidden}
.verdict .vhead{display:flex; align-items:center; justify-content:space-between; gap:10px; flex-wrap:wrap; margin:0 -22px 16px; padding:0 20px 0 0; min-height:44px; background:var(--brass-wash); border-bottom:1px solid #E0CFA6}
.verdict .tab{display:flex; align-items:center; align-self:stretch; background:var(--brass); color:#fff; font-family:var(--serif); font-weight:600; font-size:12.5px; letter-spacing:.22em; padding:0 18px; border-radius:9px 0 8px 0}
.verdict .stamp{font-size:12.5px; color:var(--brass-deep); border:1px solid var(--brass-deep); border-radius:4px; padding:2px 9px; background:#fff; white-space:nowrap}
.verdict ul{margin:0; padding-left:20px}
.verdict li{margin:7px 0; font-size:14.5px}
.verdict .src{font-size:12.5px; color:var(--ink-soft); margin-top:14px; padding-top:10px; border-top:1px dashed var(--line)}
.verdict .bigprice{font-family:var(--serif); font-size:28px; color:var(--brass-deep); font-variant-numeric:tabular-nums; margin:4px 0 2px}
.verdict .bigprice small{font-family:var(--sans); font-size:12.5px; color:var(--ink-soft); margin-left:8px; font-weight:400}
@media(max-width:560px){ .verdict{padding:0 15px 16px} .verdict .vhead{margin:0 -15px 14px} }
nav.toc{background:var(--card); border:1px solid var(--line); border-radius:10px; padding:12px 18px; margin:10px 0 6px}
nav.toc b{font-family:var(--serif); font-weight:600; font-size:13px; letter-spacing:.1em; color:var(--ink-soft)}
nav.toc ol{margin:6px 0 0; padding-left:20px; font-size:13.5px; columns:2; column-gap:24px}
nav.toc li{margin:2px 0; break-inside:avoid}
nav.toc a{color:var(--ink); text-decoration:none; border-bottom:1px dotted var(--line); display:inline; padding:5px 0; line-height:2}
@media(max-width:560px){ nav.toc ol{columns:1} }
.minitbl{border-collapse:collapse; width:100%; font-size:13.5px; background:var(--card)}
.minitbl th,.minitbl td{padding:10px 16px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top}
.minitbl tr:last-child th,.minitbl tr:last-child td{border-bottom:none}
.minitbl th{background:var(--th-bg); font-weight:700; font-size:12.5px; letter-spacing:.04em; width:11em; color:var(--brass-deep)}
.minitbl thead th{width:auto}
.minitbl td .src{display:block; font-size:12.5px; color:var(--ink-soft); margin-top:2px}
.minitbl td.n{text-align:right; white-space:nowrap}
.tblcard{position:relative; border-radius:10px; overflow-x:auto; border:1px solid var(--line); margin:14px 0 6px; -webkit-overflow-scrolling:touch}
@media(max-width:560px){
  .minitbl:not(.keep) ,.minitbl:not(.keep) tbody,.minitbl:not(.keep) tr,.minitbl:not(.keep) th,.minitbl:not(.keep) td{display:block; width:auto}
  .minitbl:not(.keep) tr{border-bottom:1px solid var(--line)}
  .minitbl:not(.keep) th{width:auto; padding:10px 14px 2px; background:transparent; border-bottom:none; color:var(--ink-soft); font-size:12.5px}
  .minitbl:not(.keep) td{padding:0 14px 12px} .minitbl:not(.keep) td.n{text-align:left}
  .minitbl:not(.keep) thead{display:none}
}
.cmpwrap{position:relative; margin:16px 0 6px; border:1px solid var(--line); border-radius:10px; background:var(--card); overflow-x:auto; -webkit-overflow-scrolling:touch}
table.cmp{border-collapse:separate; border-spacing:0; width:100%; min-width:620px; font-size:13px; line-height:1.6}
.cmp th,.cmp td{padding:10px 13px; text-align:left; border-bottom:1px solid var(--line); vertical-align:top; background:var(--card)}
.cmp thead th{font-size:12.5px; font-weight:700; color:var(--brass-deep); background:var(--th-bg); border-bottom:2px solid #DCCBA5; vertical-align:bottom}
.cmp thead th .b{display:block; font-size:12.5px; font-weight:500; color:var(--ink-soft); margin-top:2px}
.cmp tbody th{background:var(--th-bg); font-weight:700; font-size:12.5px; color:var(--brass-deep); position:sticky; left:0; z-index:2; min-width:8.5em}
.cmp tbody tr:nth-child(even) td{background:var(--zebra)}
.cmp tbody tr.diff td{background:#FFF6E0}
.cmp tbody tr.diff th{background:#F3DFB4}
.cmp tbody th .src{display:block; font-size:12.5px; color:var(--ink-soft); font-weight:400; margin-top:2px}
.cmp.ft td.n .src{display:block; font-size:11.5px; color:var(--ink-soft); margin-top:2px}
.cmp.ft{table-layout:fixed}
.cmp.ft tbody th{position:static; font-weight:600; color:var(--ink); background:var(--card)}
.cmp-sticky{max-height:75vh; overflow:auto}
.cmp-sticky .cmp thead th{position:sticky; top:0; z-index:3}
@media(max-width:560px){ .cmp tbody th{min-width:5.5em; font-size:11.5px; padding:8px} table.cmp{min-width:560px} }
.caution{background:var(--amber-wash); border-left:4px solid var(--amber-line); border-radius:0 8px 8px 0; padding:12px 18px; font-size:13px; color:var(--amber-ink); line-height:1.8; margin:12px 0}
.caution a{color:var(--amber-ink)}
.note{background:var(--brass-wash); border-left:4px solid var(--brass); border-radius:0 8px 8px 0; padding:12px 18px; font-size:13.5px; margin:14px 0}
.note b{color:var(--brass-deep)}
ol.steps{counter-reset:st; list-style:none; padding:0; margin:14px 0}
ol.steps > li{counter-increment:st; position:relative; background:var(--card); border:1px solid var(--line); border-radius:10px; padding:14px 18px 14px 58px; margin:0 0 10px}
ol.steps > li::before{content:counter(st); position:absolute; left:16px; top:14px; width:28px; height:28px; border-radius:50%; background:var(--brass); color:#fff; font-weight:700; font-size:14px; display:flex; align-items:center; justify-content:center}
ol.steps > li b{display:block; font-family:var(--serif); font-size:15.5px; margin-bottom:2px}
figure.fig{margin:20px 0; background:var(--card); border:1px solid var(--line); border-radius:10px; padding:16px}
figure.fig svg{display:block; width:100%; height:auto; max-width:620px; margin:0 auto}
figure.fig figcaption{font-size:12.5px; color:var(--ink-soft); margin-top:10px}
.fighint{display:none}
@media(max-width:560px){ figure.fig{padding:8px 4px 12px; overflow-x:auto} figure.fig svg{min-width:470px} .fighint{display:block; position:sticky; left:0; padding:0 8px} }
.figgrid{display:grid; grid-template-columns:1fr 1fr; gap:16px; margin:14px 0}
.figgrid figure{margin:0}
@media (max-width:760px){.figgrid{grid-template-columns:1fr}}
details.help{background:var(--card); border:1px solid var(--line); border-radius:10px; padding:2px 18px; margin:8px 0 12px; max-width:760px}
details.help summary{font-size:13.5px; padding:10px 0; cursor:pointer; color:var(--brass)}
details.help p{margin:0 0 12px; font-size:13.5px; color:var(--ink-soft)}
.help.gloss dl{margin:6px 0 0; display:grid; grid-template-columns:max-content 1fr; gap:6px 14px; font-size:13.5px}
.help.gloss dt{font-weight:700; color:var(--brass-deep)} .help.gloss dd{margin:0}
@media(max-width:560px){ .help.gloss dl{grid-template-columns:1fr; gap:2px} .help.gloss dd{margin:0 0 8px} }
details.score{border:1px dashed var(--line); border-radius:8px; padding:4px 10px; font-size:12.5px}
details.score summary{display:flex; align-items:center; gap:8px; cursor:pointer; list-style:none; min-height:32px}
details.score summary .lbl{color:var(--ink-soft)} details.score summary b{font-size:15px; color:var(--ink)} details.score summary b small{color:var(--ink-soft); font-size:11.5px}
details.score summary .hint{margin-left:auto; color:var(--brass); text-decoration:underline}
details.score ul{list-style:none; margin:6px 0 4px; padding:0}
details.score li{display:flex; justify-content:space-between; gap:8px; padding:3px 0; border-top:1px dotted var(--line); color:var(--ink-soft)}
details.score li b{color:var(--ink)}

/* ── 記事カード ── */
.newlist{display:grid; grid-template-columns:repeat(auto-fill,minmax(320px,1fr)); gap:10px}
.newcard{display:flex; flex-direction:column; gap:6px; align-items:flex-start; background:var(--card); border:1px solid var(--line); border-radius:10px; padding:13px 18px; text-decoration:none; color:var(--ink)}
.newcard:hover{border-color:#D6BE8E; background:var(--zebra)}
.newcard .cat{font-size:11.5px; letter-spacing:.06em; color:var(--brass-deep); background:var(--brass-wash); border-radius:4px; padding:3px 9px}
.newcard .name{font-family:var(--serif); font-weight:600; font-size:16px; line-height:1.5}
.mlist{list-style:none; margin:8px 0 16px; padding:0}
.mlist li{padding:8px 0; border-top:1px dashed var(--line); font-size:14px; line-height:1.5}
.mlist li a{font-weight:600; text-decoration:underline; text-underline-offset:3px}
.mlist li .soft{font-size:12.5px}
.mlist li.me{background:var(--brass-wash); margin:0 -8px; padding:8px}

/* ── 購入・買取リンク ── */
.buyrow{display:flex; gap:12px; flex-wrap:wrap; margin:14px 0}
.buybtn{font-family:var(--sans); font-weight:700; font-size:14px; letter-spacing:.03em; border-radius:8px; min-height:48px; padding:6px 24px; border:none; color:#fff;
  display:inline-flex; flex-direction:column; justify-content:center; align-items:flex-start; text-decoration:none}
.buybtn.amz{background:var(--amz)} .buybtn.rkt{background:var(--rkt)}
.buybtn.yh{background:var(--card); color:var(--yh); border:1.5px solid currentColor}
.buybtn.shop{background:var(--card); color:var(--shop); border:1.5px solid currentColor}
.buybtn.kaitori{background:var(--kaitori)}
.buybtn.ghost{background:var(--zebra); color:var(--ink-soft); border:1px dashed var(--line); cursor:default}
.buybtn small{font-weight:400; font-size:12.5px; letter-spacing:.02em}
@media(max-width:560px){ .buybtn{width:100%; align-items:center} }
.buynote{font-size:13px; color:var(--ink-soft); margin:8px 0 6px}
.buynote-s{margin-top:-4px}
.shoplink{font-weight:700; text-decoration:underline; text-underline-offset:3px}

/* ── FAQ・出典 ── */
details.faq{background:var(--card); border:1px solid var(--line); border-radius:10px; padding:2px 18px; margin:8px 0}
details.faq summary{font-family:var(--serif); font-weight:600; font-size:14.5px; padding:12px 0; cursor:pointer}
details.faq p{margin:0 0 14px; font-size:14px}
details.sources-wrap summary{font-size:13.5px}
ol.sources{font-size:13px; color:var(--ink-soft); line-height:1.7; padding-left:20px}
ol.sources li{margin:6px 0}
ol.sources a{word-break:break-all}
ol.sources a::after{content:" ↗"; font-size:.85em; color:var(--ink-soft)}
ol.sources .srcnote{display:block; font-size:12px; color:var(--ink-soft)}
.related{margin-top:16px}
.totop{display:inline-block; font-size:12.5px; color:var(--ink-soft); margin-top:32px; text-decoration:none; padding:4px 0}
.backtool{position:fixed; right:14px; bottom:14px; z-index:25; display:none; background:var(--brass-deep); color:#fff; border-radius:999px; padding:0 18px; min-height:46px; align-items:center; font-size:13.5px; font-weight:700; text-decoration:none; box-shadow:0 6px 18px rgba(0,0,0,.28)}
@media(max-width:860px){ .backtool.on{display:inline-flex} body.has-tray .backtool{bottom:70px} }

/* ── 比較トレイ ── */
.tray{position:fixed; left:0; right:0; bottom:0; z-index:30; background:#4E300A; color:#F5EEDF; box-shadow:0 -6px 20px rgba(0,0,0,.25)}
.tray-in{max-width:1180px; margin:0 auto; padding:10px 20px; display:flex; align-items:center; gap:12px; flex-wrap:wrap}
.tray .lbl{font-size:12.5px; color:#fff; font-weight:700; letter-spacing:.04em}
.tray .picks{display:flex; gap:8px; flex-wrap:wrap; flex:1}
.tray .picks span{background:rgba(255,255,255,.12); border-radius:999px; padding:6px 8px 6px 14px; font-size:13.5px; display:inline-flex; align-items:center; gap:6px}
.tray .picks button{border:none; background:rgba(255,255,255,.2); color:#fff; border-radius:50%; width:32px; height:32px; cursor:pointer; font-size:14px; line-height:1}
.tray .go{background:#E6B85C; color:#241503; border:none; border-radius:999px; font-weight:700; font-family:var(--sans); font-size:14px; padding:0 20px; min-height:44px; cursor:pointer}
.tray .clear{background:none; border:1px solid rgba(255,255,255,.4); color:#F5EEDF; border-radius:999px; font-family:var(--sans); font-size:13px; padding:0 14px; min-height:44px; cursor:pointer}
.cmp-out{margin-top:20px}
body.has-tray{padding-bottom:80px}
.samehide{font-size:13px; color:var(--ink-soft); display:inline-flex; align-items:center; gap:6px; min-height:44px}
@media(max-width:560px){ .tray-in{padding:8px 12px; gap:8px; flex-wrap:nowrap} .tray .picks{flex-wrap:nowrap; overflow-x:auto; gap:6px}
  .tray .picks span{font-size:12.5px; padding:4px 6px 4px 10px; white-space:nowrap} .tray .go{padding:0 12px; min-height:40px; font-size:13px; white-space:nowrap} .tray .clear{padding:0 10px; min-height:40px; font-size:12.5px} }

/* ── フッター ── */
footer.site{border-top:1px solid var(--line); background:var(--card); margin-top:56px}
.foot-inner{max-width:1180px; margin:0 auto; padding:26px 20px; font-size:12.5px; color:var(--ink-soft); line-height:2}
.foot-inner .pr{font-weight:700; color:var(--ink)}
.foot-nav{display:flex; flex-wrap:wrap; gap:6px 14px; margin:0 0 10px; padding:0 0 12px; border-bottom:1px solid var(--line)}
.foot-nav b{color:var(--ink); font-weight:500; margin-right:2px}
.foot-nav a,.foot-links a{color:var(--ink-soft); text-decoration:none; border-bottom:1px dotted var(--line); display:inline-block; padding:4px 0}
.foot-nav a:hover,.foot-links a:hover{color:var(--brass)}
.foot-links{margin:8px 0 0; display:flex; gap:16px; flex-wrap:wrap}
#ct-form [aria-invalid="true"]{border-color:#B3242C; box-shadow:0 0 0 3px rgba(179,36,44,.12)}
"""


def logo_svg() -> str:
    """ベル（朝顔）を線画にしたアイコン。実機の再現ではない。"""
    return ('<svg width="28" height="28" viewBox="0 0 28 28" aria-hidden="true">'
            '<path d="M3 13.5 h11 l7 -7 v15 l-7 -7 h-11 z" fill="#FFFFFF" stroke="#8A5A17" stroke-width="1.6" stroke-linejoin="round"/>'
            '<path d="M21 6.5 q5 7.5 0 15" fill="none" stroke="#8A5A17" stroke-width="1.6"/>'
            '<circle cx="6.5" cy="13.5" r="1.2" fill="#8A5A17"/><circle cx="10" cy="13.5" r="1.2" fill="#8A5A17"/></svg>')


def head_html(title, description, rel_path, og_type="website", extra="", noindex=False, og_image=None):
    prefix = "../" * rel_path.count("/")
    canonical = cfg.canonical_url(rel_path)
    robots = '<meta name="robots" content="noindex,follow">\n' if noindex else ""
    canon_tags = "" if noindex else (f'<link rel="canonical" href="{canonical}">\n'
                                     f'<meta property="og:url" content="{canonical}">\n')
    og_img_url = cfg.BASE_URL + "/" + (og_image or cfg.OG_DEFAULT_PATH)
    og_img_tags = (f'<meta property="og:image" content="{og_img_url}">\n'
                   f'<meta property="og:image:width" content="{cfg.OG_WIDTH}">\n'
                   f'<meta property="og:image:height" content="{cfg.OG_HEIGHT}">\n'
                   f'<meta name="twitter:image" content="{og_img_url}">\n')
    icons = (f'<link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml">\n'
             f'<link rel="apple-touch-icon" href="{prefix}assets/apple-touch-icon.png">\n')
    gsc = f'<meta name="google-site-verification" content="{cfg.GSC_VERIFICATION}">\n' if cfg.GSC_VERIFICATION else ""
    ga4 = ""
    if cfg.GA4_ID:
        ga4 = (f'<script async src="https://www.googletagmanager.com/gtag/js?id={cfg.GA4_ID}"></script>\n'
               "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());"
               f"gtag('config','{cfg.GA4_ID}');</script>\n")
    return f"""<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{gsc}{robots}<title>{title}</title>
<meta name="description" content="{description}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Shippori+Mincho+B1:wght@600;700&family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap">
<link rel="stylesheet" href="{prefix}assets/style.css?v={css_version()}">
{icons}{canon_tags}<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{cfg.SITE_NAME}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:locale" content="ja_JP">
{og_img_tags}<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">
{ga4}{extra}</head>"""


def header_html(rel_path, current=""):
    prefix = "../" * rel_path.count("/")
    links = []
    for key, label, path in NAV_ITEMS:
        aria = (' aria-current="page"' if path == rel_path else ' class="on"') if key == current else ""
        links.append(f'      <a href="{prefix}{path}"{aria}>{label}</a>')
    return f"""<a class="skip-link" href="#main">本文へスキップ</a>
<header class="site">
  <div class="site-inner">
    <a class="logo" href="{prefix}index.html" aria-label="{cfg.SITE_NAME} トップへ">
      {logo_svg()}
      <span class="words">
        <span class="l1">{cfg.SITE_NAME_EN}</span>
        <span class="l2">管楽器<em>図鑑</em></span>
      </span>
      <span class="sub">{cfg.LOGO_SUB}</span>
    </a>
    <nav class="tabs" aria-label="メインメニュー">
{chr(10).join(links)}
    </nav>
  </div>
</header>"""


def _footer_nav(prefix: str) -> str:
    from articles_data import ARTICLES
    counts = {}
    for a in ARTICLES:
        counts[a["category"]] = counts.get(a["category"], 0) + 1
    cats = " ".join(f'<a href="{prefix}category/{k}.html">{l}</a>' for k, l in cfg.CATEGORIES if counts.get(k))
    cat_html = f'<div class="foot-nav"><b>記事</b> {cats}</div>\n    ' if cats else ""
    return (f'{cat_html}<div class="foot-nav"><b>データ</b> '
            f'<a href="{prefix}index.html">型番を探す</a> '
            f'<a href="{prefix}compare/index.html">型番ペアの違い</a> '
            f'<a href="{prefix}instruments/index.html">楽器種別の一覧</a> '
            f'<a href="{prefix}brands.html">ブランド一覧</a> '
            f'<a href="{prefix}models/index.html">型番ページ一覧</a> '
            f'<a href="{prefix}data.html">データの作り方・出典方針</a></div>')


def footer_html(rel_path):
    """必須常設表記を必ず含むフッター。qa_site.py が存在を検査する。"""
    prefix = "../" * rel_path.count("/")
    info = " ／ ".join(f'<a href="{prefix}{p}">{l}</a>' for p, l in FOOTER_INFO_LINKS)
    amazon = f"{cfg.NOTICE_AMAZON}<br>\n    " if cfg.USE_AMAZON else ""
    return f"""<footer class="site">
  <div class="foot-inner">
    {_footer_nav(prefix)}
    <span class="pr">{cfg.NOTICE_PR}</span><br>
    {amazon}{cfg.NOTICE_INDEPENDENT}<br>
    {cfg.NOTICE_PRICE}<br>
    <span class="foot-links">{info}</span>
    <div style="margin-top:6px">© 2026 {cfg.SITE_NAME}</div>
  </div>
</footer>"""


def crumb_jsonld(rel_path: str, name: str) -> str:
    import json as _json
    d = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "トップ", "item": cfg.BASE_URL + "/"},
        {"@type": "ListItem", "position": 2, "name": name, "item": cfg.canonical_url(rel_path)}]}
    return f'<script type="application/ld+json">{_json.dumps(d, ensure_ascii=False)}</script>\n'


def page_html(title, description, rel_path, body, current="", og_type="website", extra_head="", noindex=False, og_image=None):
    return f"""<!doctype html>
<html lang="ja">
{head_html(title, description, rel_path, og_type, extra_head, noindex, og_image)}
<body>
{header_html(rel_path, current)}
<main id="main">
{body}
</main>
{footer_html(rel_path)}
</body>
</html>
"""


def write_page(rel_path, html):
    out = SITE_DIR / rel_path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")


def write_assets():
    out = SITE_DIR / "assets" / "style.css"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(STYLE_CSS, encoding="utf-8")
    fav = ('<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 28 28">'
           '<rect width="28" height="28" fill="#F8F6F1"/>'
           '<path d="M3 13.5 h11 l7 -7 v15 l-7 -7 h-11 z" fill="#FFFFFF" stroke="#8A5A17" stroke-width="1.6" stroke-linejoin="round"/>'
           '<path d="M21 6.5 q5 7.5 0 15" fill="none" stroke="#8A5A17" stroke-width="1.6"/>'
           '<circle cx="6.5" cy="13.5" r="1.2" fill="#8A5A17"/><circle cx="10" cy="13.5" r="1.2" fill="#8A5A17"/></svg>')
    (SITE_DIR / "assets" / "favicon.svg").write_text(fav, encoding="utf-8")
    print(f"assets/style.css を書き出した（{len(STYLE_CSS.splitlines())}行）＋ favicon.svg")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    write_assets()
