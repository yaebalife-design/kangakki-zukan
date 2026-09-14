# -*- coding: utf-8 -*-
"""公開の一括実行（管楽器図鑑）。ドメイン取得後、これ1本で「差し替え→再生成→検査→push→デプロイ」まで通す。

    python ツール/publish.py --domain kangakki-zukan.com            # ①〜③（検査まで。pushしない）
    python ツール/publish.py --domain kangakki-zukan.com --push     # ④ GitHubへ
    python ツール/publish.py --domain kangakki-zukan.com --deploy   # ⑤ Cloudflare Pages へ
    python ツール/publish.py --check-only                           # 検査だけ

🔴 公開系（--push / --deploy）は社長の承認後にだけ実行する（ローカルCLAUDE.md 絶対ルール12）。
🔴 秘密情報検査に1件でも引っかかったら、その場で止めて push しない（マスター手順 第2章）。
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
TOOLS = ROOT / "ツール"
SITE = ROOT / "site"
GH = r"C:\Program Files\GitHub CLI\gh.exe"

# 他サイトのIDが1つでも混ざったら公開しない（絶対ルール13）。実際に使われている他サイトの値を直接書かず、形で見る
LEAK_PATTERNS = [
    (r"G-[A-Z0-9]{8,}", "GA4測定ID"),
    (r"UA-\d{4,}-\d+", "旧アナリティクスID"),
    (r"ca-pub-\d{10,}", "AdSense"),
    (r"[a-z0-9]{8,}-22\b", "AmazonトラッキングID"),
    (r"a_id=\d{6,}", "もしもa_id"),
    (r"a8mat=[A-Z0-9+]{8,}", "A8リンク"),
    (r"AKIA[0-9A-Z]{16}", "AWSキー"),
    (r"gh[pousr]_[A-Za-z0-9]{20,}", "GitHubトークン"),
    (r"sk-[A-Za-z0-9]{20,}", "APIキー"),
    # ヘッダとフッタの間に実データがある場合だけ＝鍵そのもの。PEMを剥がすコード片（contact.js）は誤検知なので除く
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----[A-Za-z0-9+/=\s]{60,}-----END", "秘密鍵"),
    (r"\b[\w.+-]+@(?!example\.)[\w-]+\.[\w.]+\b", "メールアドレス"),
]
SKIP_DIRS = {".git", "node_modules", "__pycache__"}


def run(cmd, cwd=ROOT, check=True):
    print("  $", " ".join(str(c) for c in cmd))
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.stdout.strip():
        print("   ", r.stdout.strip()[:1500])
    if r.returncode != 0:
        print("   ", (r.stderr or "").strip()[:1500])
        if check:
            sys.exit(f"🔴 失敗: {' '.join(str(c) for c in cmd)}")
    return r


def set_domain(domain: str) -> None:
    """site_config.BASE_URL を本番ドメインに差し替える。"""
    p = TOOLS / "site_config.py"
    s = p.read_text(encoding="utf-8")
    new = f'BASE_URL = "https://{domain}"'
    s2 = re.sub(r'^BASE_URL = "[^"]*"', new, s, count=1, flags=re.M)
    if s2 == s and new not in s:
        sys.exit("🔴 BASE_URL を差し替えられなかった（site_config.py の形が変わっている）")
    p.write_text(s2, encoding="utf-8")
    print(f"① BASE_URL → https://{domain}")


def build() -> None:
    print("② 再生成（build.py）")
    r = run([sys.executable, str(TOOLS / "build.py")], check=False)
    if "エラーなし" not in (r.stdout or ""):
        sys.exit("🔴 品質検査を通っていない。公開系の作業に進まないこと")


def secret_scan() -> int:
    """site/ 配下に秘密情報・他サイトのIDが混ざっていないか。1件でもあれば公開しない。"""
    print("③ 秘密情報の検査")
    hits = []
    for f in SITE.rglob("*"):
        if not f.is_file() or any(d in f.parts for d in SKIP_DIRS):
            continue
        if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".woff", ".woff2"):
            continue
        try:
            t = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pat, label in LEAK_PATTERNS:
            for m in re.finditer(pat, t):
                v = m.group(0)
                # 自サイトの正規の値・明らかな例示は除外
                if label == "メールアドレス" and ("@example" in v or v.endswith(("@2x", "@3x"))):
                    continue
                if label == "GA4測定ID" and v in ("G-XXXXXXXXXX",):
                    continue
                hits.append((f.relative_to(SITE).as_posix(), label, v[:40]))
    # 隠しファイル・鍵ファイルの混入
    for f in SITE.rglob("*"):
        if f.is_file() and (f.name.startswith(".env") or f.suffix in (".pem", ".key", ".p12")):
            hits.append((f.relative_to(SITE).as_posix(), "秘密ファイル", f.name))
    if hits:
        print(f"   🔴 {len(hits)}件の疑い:")
        for h in hits[:20]:
            print("     ", h)
    else:
        print("   ✅ 検出なし")
    return len(hits)


def git_ready(domain: str) -> None:
    """git init → 全ファイルをコミット（site/ と生成ツールを含む）。"""
    print("④ git の準備")
    if not (ROOT / ".git").exists():
        run(["git", "init", "-b", "main"])
    gitignore = ROOT / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("__pycache__/\n*.pyc\n.env\n.env.*\n*.pem\n*.key\nnode_modules/\n", encoding="utf-8")
    run(["git", "add", "-A"])
    r = run(["git", "status", "--porcelain"], check=False)
    if not (r.stdout or "").strip():
        print("   変更なし")
        return
    run(["git", "commit", "-m", f"管楽器図鑑: {domain} 向けに生成（現行864型番・記事13本）\n\n"
                                "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"], check=False)


def gh_push(repo: str) -> None:
    print("⑤ GitHub へ push")
    if not Path(GH).exists():
        sys.exit("🔴 gh が見つからない")
    r = run([GH, "auth", "status"], check=False)
    if "Logged in" not in (r.stdout or "") + (r.stderr or ""):
        sys.exit("🔴 GitHub に未ログイン。先に \"gh auth login\" を実行すること（ブラウザでの認証が要る）")
    run([GH, "repo", "create", repo, "--public", "--source", str(ROOT), "--remote", "origin", "--push"], check=False)


def cf_deploy(project: str) -> None:
    print("⑥ Cloudflare Pages へデプロイ")
    if not os.environ.get("CLOUDFLARE_API_TOKEN"):
        sys.exit("🔴 CLOUDFLARE_API_TOKEN が未設定。Cloudflareダッシュボードで Pages 編集権限のトークンを作り、\n"
                 "   環境変数に入れてから再実行すること")
    run(["npx", "--yes", "wrangler@latest", "pages", "deploy", str(SITE),
         "--project-name", project, "--branch", "main"], check=False)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", help="本番ドメイン（例 kangakki-zukan.com）")
    ap.add_argument("--repo", default="kangakki-zukan", help="GitHubリポジトリ名")
    ap.add_argument("--project", default="kangakki-zukan", help="Cloudflare Pages のプロジェクト名")
    ap.add_argument("--push", action="store_true", help="GitHubへpushする（社長承認後）")
    ap.add_argument("--deploy", action="store_true", help="Cloudflare Pagesへデプロイする（社長承認後）")
    ap.add_argument("--check-only", action="store_true", help="検査だけ")
    a = ap.parse_args()

    if a.check_only:
        sys.exit(1 if secret_scan() else 0)
    if not a.domain:
        sys.exit("--domain を指定すること")

    set_domain(a.domain)
    build()
    if secret_scan():
        sys.exit("🔴 秘密情報の疑いがあるので公開しない")
    git_ready(a.domain)
    if a.push:
        gh_push(a.repo)
    if a.deploy:
        cf_deploy(a.project)
    print("\n✅ ここまで完了。残りは社長のブラウザ作業（Pagesのカスタムドメイン接続・GA4/GSC発行）")


if __name__ == "__main__":
    main()
