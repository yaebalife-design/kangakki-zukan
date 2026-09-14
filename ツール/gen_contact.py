# -*- coding: utf-8 -*-
"""contact.html ＝ お問い合わせフォームを生成する（Gin-DB・スキマー図鑑と同方式）。

■ 前提
  「メールアドレスは一切出さない。受け取りはスプレッドシートで管理する」
  → ブラウザが話す相手は このサイトの /api/contact だけ。
     送信先（スプレッドシートID・サービスアカウント鍵）は Cloudflare の暗号化シークレットにしか無く、
     HTML にも JS にもリポジトリにも書かれていない。mailto: リンクも置かない。
  受け口 site/functions/api/contact.js はスキマー図鑑のものを複製して使う（公開時に社長がシークレットを設定）。

■ スパム対策（受け口と対）
  1. ハニーポット  2. 表示から3秒未満の送信は機械とみなす  3. 同一IPの回数制限（受け口側・IPはハッシュ化）
  4. Cloudflare Turnstile は環境変数を入れれば有効になる（未設定なら素通し）
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import site_config as cfg
import site_chrome as chrome

KINDS = [
    ("掲載している定価・仕様・出典の誤り", "税込希望小売価格・改定日・調子・仕上げ・付属品・出典URLなどが実際と違う"),
    ("型番の追加・生産終了のご連絡", "掲載されていない現行型番、終了した型番のお知らせ"),
    ("メーカー・楽器店・権利者の方からのご依頼", "掲載内容の訂正・削除のご依頼"),
    ("その他", "上記にあてはまらないもの"),
]

CSS = """<style>
.ct{max-width:720px}
.ct-field{margin:0 0 22px}
.ct-field > label{display:block; font-weight:700; font-size:14px; margin:0 0 6px; color:var(--ink)}
.ct-req{font-size:11px; font-weight:700; color:#fff; background:var(--brass-deep); border-radius:4px; padding:2px 7px; margin-left:8px; vertical-align:1px}
.ct-opt{font-size:11.5px; font-weight:400; color:var(--ink-soft); margin-left:8px}
.ct-help{font-size:12.5px; color:var(--ink-soft); line-height:1.75; margin:0 0 8px}
.ct-field input[type=text],.ct-field input[type=email],.ct-field select,.ct-field textarea{
  width:100%; font-family:var(--sans); font-size:16px; padding:12px 14px; border:1.5px solid var(--line); border-radius:10px; background:var(--card); color:var(--ink)}
.ct-field textarea{min-height:190px; line-height:1.85; resize:vertical}
.ct-field :focus{outline:none; border-color:var(--brass); box-shadow:0 0 0 3px var(--brass-wash)}
.ct-err{display:none; font-size:12.5px; color:#B3242C; font-weight:700; margin-top:6px}
.ct-err.on{display:block}
.ct-hp{position:absolute; left:-9999px; width:1px; height:1px; overflow:hidden}
.ct-send{font-family:var(--sans); font-weight:700; font-size:15px; letter-spacing:.03em; background:var(--brass-deep); color:#fff; border:none; border-radius:10px; min-height:52px; padding:0 34px; cursor:pointer}
.ct-send[disabled]{opacity:.5; cursor:default}
.ct-msg{margin-top:16px; padding:14px 16px; border-radius:10px; font-size:14px; line-height:1.8; display:none}
.ct-msg.on{display:block}
.ct-msg.ok{background:var(--brass-wash); border:1px solid var(--brass); color:var(--brass-deep)}
.ct-msg.ng{background:#FDF1F1; border:1px solid #E2B4B4; color:#8A2A2A}
</style>"""


def _js() -> str:
    return """<script>
(function(){
  var f = document.getElementById('ct-form');
  if(!f) return;
  var shown = Date.now();
  var btn = document.getElementById('ct-send');
  var msg = document.getElementById('ct-msg');
  function show(kind, text){ msg.className = 'ct-msg on ' + kind; msg.textContent = text; }
  function err(id, on){ var e = document.getElementById(id); if(!e) return;
    e.className = 'ct-err' + (on?' on':'');
    var fld = e.previousElementSibling;
    if(fld && fld.tagName !== 'P'){ if(on){ fld.setAttribute('aria-invalid','true'); } else { fld.removeAttribute('aria-invalid'); } } }
  f.addEventListener('submit', function(ev){
    ev.preventDefault();
    var kind = f.kind.value, message = f.message.value.trim(), email = f.email.value.trim();
    var bad = false;
    err('e-kind', !kind); if(!kind) bad = true;
    err('e-message', message.length < 10); if(message.length < 10) bad = true;
    var okMail = !email || /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email);
    err('e-email', !okMail); if(!okMail) bad = true;
    if(bad){
      show('ng', '入力内容をご確認ください。');
      var e1 = document.querySelector('.ct-err.on');
      if(e1){ var fld = e1.previousElementSibling;
        if(fld){ fld.setAttribute('aria-invalid','true'); fld.focus({preventScroll:true}); fld.scrollIntoView({block:'center', behavior:'smooth'}); } }
      return; }
    btn.disabled = true; show('ok', '送信しています…');
    fetch('/api/contact', {
      method: 'POST', headers: {'content-type': 'application/json'},
      body: JSON.stringify({ kind: kind, name: f.name_.value, email: email, url: f.url.value, message: message, hp: f.hp.value, elapsed: Date.now() - shown })
    }).then(function(r){ return r.json().then(function(d){ return {s:r.status, d:d}; }); })
      .then(function(x){
        if(x.d && x.d.ok){ f.reset(); show('ok', 'お送りいただきありがとうございます。内容を確認し、必要な場合は訂正のうえ掲載ページの最終更新日を更新します。'); }
        else { btn.disabled = false; show('ng', (x.d && x.d.message) || '送信できませんでした。時間をおいてお試しください。'); }
      })
      .catch(function(){ btn.disabled = false; show('ng', '通信に失敗しました。時間をおいてお試しください。'); });
  });
})();
</script>"""


def body_html() -> str:
    opts = "".join(f'<option value="{k}">{k}（{d}）</option>' for k, d in KINDS)
    return f"""  <p class="crumb measure"><a href="index.html">トップ</a> &gt; お問い合わせ</p>
  <p class="prnote measure">{cfg.NOTICE_PR}</p>
  <div class="measure ct">
    <h1>お問い合わせ・訂正のご依頼</h1>
    <p class="lead-p">掲載している定価・仕様の誤り、型番の追加・生産終了のご連絡、メーカー・楽器店・権利者の方からの訂正・削除のご依頼を受け付けています。
    当サイトはメーカー公式ページ・正規代理店・公式カタログで確認できた値だけを載せているため、<b>元の資料と食い違っている箇所</b>のご指摘がもっとも助かります。</p>

    <div class="note">
      <b>いただいた内容の扱い</b><br>
      内容を確認し、公式の資料に照らして訂正または削除します。対応したページは最終更新日を更新します。
      原則として3営業日以内に確認します。返信が必要な場合のみメールアドレスをご記入ください（任意）。
      いただいた情報は訂正対応の目的だけに使い、第三者へ提供しません（<a href="privacy.html">プライバシーポリシー</a>）。
    </div>

    <form id="ct-form" novalidate>
      <div class="ct-field">
        <label for="ct-kind">お問い合わせの種類<span class="ct-req">必須</span></label>
        <select id="ct-kind" name="kind" required aria-describedby="e-kind">
          <option value="">選択してください</option>
          {opts}
        </select>
        <p class="ct-err" id="e-kind">種類をお選びください。</p>
      </div>
      <div class="ct-field">
        <label for="ct-url">対象のページ<span class="ct-opt">任意</span></label>
        <p class="ct-help">誤りを見つけたページのURL、または型番をご記入ください。</p>
        <input type="text" id="ct-url" name="url" maxlength="500" autocomplete="off" placeholder="例：YAS-280 の型番ページ">
      </div>
      <div class="ct-field">
        <label for="ct-message">内容<span class="ct-req">必須</span></label>
        <p class="ct-help">できれば「どの項目が」「正しくは何か」「その根拠（メーカーページ・カタログのどこか）」を添えていただけると、確認が早く進みます。</p>
        <textarea id="ct-message" name="message" maxlength="4000" required aria-describedby="e-message" placeholder="例：税込希望小売価格が¥◯◯と書かれていますが、メーカーの製品ページでは¥△△です。"></textarea>
        <p class="ct-err" id="e-message">10文字以上でご記入ください。</p>
      </div>
      <div class="ct-field">
        <label for="ct-name">お名前・会社名<span class="ct-opt">任意</span></label>
        <input type="text" id="ct-name" name="name_" maxlength="100" autocomplete="name">
      </div>
      <div class="ct-field">
        <label for="ct-email">返信先メールアドレス<span class="ct-opt">任意</span></label>
        <p class="ct-help">返信が必要な場合のみご記入ください。訂正の連絡だけであれば空欄で構いません。</p>
        <input type="email" id="ct-email" name="email" maxlength="200" autocomplete="email" inputmode="email" aria-describedby="e-email">
        <p class="ct-err" id="e-email">メールアドレスの形式をご確認ください。</p>
      </div>
      <div class="ct-hp" aria-hidden="true">
        <label for="ct-hp">この欄は入力しないでください</label>
        <input type="text" id="ct-hp" name="hp" tabindex="-1" autocomplete="off">
      </div>
      <button type="submit" class="ct-send" id="ct-send">送信する</button>
      <div class="ct-msg" id="ct-msg" role="status" aria-live="polite"></div>
    </form>

    <p class="tnote">このフォームの送信内容は当サイトの受け口だけに送られます。
    掲載しているデータの作り方は<a href="data.html">データの作り方・出典方針</a>、運営方針は<a href="about.html">このサイトについて</a>をご覧ください。</p>
  </div>"""


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    rel = "contact.html"
    html = chrome.page_html(
        title=f"お問い合わせ・訂正のご依頼｜{cfg.SITE_NAME}",
        description=("管楽器図鑑への、掲載している定価・仕様の誤りのご指摘、型番の追加・生産終了のご連絡、"
                     "メーカー・楽器店・権利者の方からの訂正・削除のご依頼の受付フォームです。返信先の記入は任意です。"),
        rel_path=rel, body=body_html(), current="about", extra_head=CSS)
    html = html.replace("</body>", _js() + "\n</body>")
    chrome.write_page(rel, html)
    print("お問い合わせフォーム 1ページを生成")


if __name__ == "__main__":
    main()
