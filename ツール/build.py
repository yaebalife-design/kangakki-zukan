# -*- coding: utf-8 -*-
"""管楽器図鑑のサイト全体を、正しい順序で1本のコマンドで作り直す。

  python build.py            … 全生成＋検査
  python build.py --check    … 生成せず検査だけ
  python build.py --no-check … 生成だけ（基本使わない）

検査(qa_site.py)がエラーを返したら **公開系の作業に進まないこと**。
（そもそも公開・デプロイ・git init は社長承認後のみ＝ローカルルール12）
"""
import re
import subprocess
import sys
import time
from pathlib import Path

TOOLS = Path(__file__).parent
SITE = TOOLS.parent / "site"
PY = sys.executable

STEPS = [
    ("site_chrome.py", "assets/style.css・favicon"),
    ("gen_og.py",      "OG画像（assets/og/）・アイコンPNG"),
    ("gen_article.py", "記事ページ（articles/）＋記事一覧"),
    ("gen_compare.py", "型番ペア差分ページ（compare/）"),
    ("gen_model.py",   "型番ページ（models/・全型番）"),
    ("gen_index.py",   "トップ（カタログ）＋楽器種別＋ブランド一覧＋終了一覧＋カテゴリ索引"),
    ("gen_static.py",  "このサイトについて・データの作り方・免責・プライバシー・404"),
    ("gen_contact.py", "お問い合わせフォーム（contact.html）"),
]

ROBOTS_TXT = "User-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n"
HEADERS_TXT = """/*
  X-Frame-Options: SAMEORIGIN
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: geolocation=(), microphone=(), camera=()
  Content-Security-Policy: default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; script-src 'self' 'unsafe-inline' https://www.googletagmanager.com; img-src 'self' data: https://i.moshimo.com https://www.google-analytics.com; connect-src 'self' https://www.google-analytics.com https://*.google-analytics.com https://*.analytics.google.com; frame-ancestors 'self'
  X-Robots-Tag: noai, noimageai
/assets/*
  Cache-Control: public, max-age=31536000, immutable
"""
REDIRECTS_TXT = """# Cloudflare Pages の転送ルール（手書き維持。build.py は上書きしない）
# 記事を削除・統合したら「旧パス 新パス 301」を1行追加する
/index.html / 301
"""


def run(script, label):
    t0 = time.time()
    print(f"▶ {label:44} ({script})")
    r = subprocess.run([PY, script], cwd=str(TOOLS), capture_output=True, text=True, encoding="utf-8", errors="replace")
    dt = time.time() - t0
    if r.returncode != 0:
        print(f"  ❌ 失敗 (exit {r.returncode})")
        print((r.stdout or "")[-1500:])
        print((r.stderr or "")[-1500:])
        return False
    tail = [l for l in (r.stdout or "").strip().splitlines() if l.strip()]
    if tail:
        print(f"  {tail[-1].strip()[:100]}  [{dt:.1f}s]")
    return True


def gen_sitemap():
    sys.path.insert(0, str(TOOLS))
    import site_config as cfg
    from articles_data import ARTICLES

    def priority_for(rel):
        if rel == "index.html":
            return 1.0
        if rel.startswith("articles/") or rel.startswith("instruments/") or rel.startswith("compare/"):
            return 0.8
        if rel == "contact.html":
            return 0.4
        if rel in ("brands.html", "data.html") or rel.startswith("models/"):
            return 0.7
        if rel.startswith("category/"):
            return 0.6
        return 0.3

    by_slug = {a["slug"]: a for a in ARTICLES}
    all_max = max([a["updated"] for a in ARTICLES] + [cfg.DB_FETCHED])

    def lastmod_for(rel):
        if rel.startswith("articles/"):
            a = by_slug.get(rel[len("articles/"):-len(".html")])
            if a:
                return a["updated"]
        if rel.startswith("category/"):
            key = rel[len("category/"):-len(".html")]
            ds = [a["updated"] for a in ARTICLES if a["category"] == key]
            return max(ds) if ds else cfg.STATIC_UPDATED
        if rel in ("index.html", "brands.html", "data.html") or rel.startswith(("instruments/", "models/", "compare/")):
            return all_max if rel == "index.html" else cfg.DB_FETCHED
        return cfg.STATIC_UPDATED

    rows = []
    for p in sorted(SITE.rglob("*.html")):
        rel = p.relative_to(SITE).as_posix()
        h = p.read_text(encoding="utf-8")
        if re.search(r'<meta name="robots" content="[^"]*noindex', h):
            continue
        m = re.search(r'<link rel="canonical" href="([^"]+)"', h)
        if m and m.group(1).rstrip("/") != cfg.canonical_url(rel).rstrip("/"):
            continue
        rows.append((cfg.canonical_url(rel), priority_for(rel), lastmod_for(rel)))
    rows.sort(key=lambda r: (-r[1], r[0]))
    body = "\n".join(f"  <url><loc>{u}</loc><priority>{pr}</priority><lastmod>{lm}</lastmod></url>" for u, pr, lm in rows)
    (SITE / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                      f"{body}\n</urlset>\n", encoding="utf-8")
    print(f"▶ sitemap.xml: {len(rows)} URL")
    (SITE / "robots.txt").write_text(ROBOTS_TXT.format(base=cfg.BASE_URL), encoding="utf-8")
    for name, txt in (("_headers", HEADERS_TXT), ("_redirects", REDIRECTS_TXT)):
        f = SITE / name
        if not f.exists():
            f.write_text(txt, encoding="utf-8")
            print(f"▶ {name}: 新規作成")
    print("▶ robots.txt: 生成")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    args = set(sys.argv[1:])
    only_check = "--check" in args
    skip_check = "--no-check" in args
    if not only_check:
        print("=" * 64 + "\nサイトを生成\n" + "=" * 64)
        for script, label in STEPS:
            if not (TOOLS / script).exists():
                print(f"▶ {label:44} ({script})  ⚠️ ファイルが無いので飛ばす")
                continue
            if not run(script, label):
                print("\n🔴 生成に失敗したので中断した。")
                return 1
        gen_sitemap()
        print()
    if skip_check:
        print("（--no-check が指定されたので検査を飛ばした）")
        return 0
    print("=" * 64 + "\n品質検査（qa_site.py）\n" + "=" * 64)
    r = subprocess.run([PY, "qa_site.py"], cwd=str(TOOLS), capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(r.stdout)
    if r.stderr.strip():
        print(r.stderr[-1200:])
    if r.returncode != 0:
        print("🔴 検査でエラー。公開系の作業に進まないこと。")
        return 1
    print("✅ 検査を通過。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
