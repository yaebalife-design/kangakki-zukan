# -*- coding: utf-8 -*-
"""楽器を連想させる自作のラインアート（SVG）。

  ・特定の型番・製品を写した絵ではなく、楽器種を示す汎用の線画（アイコン）。商品画像・実機画像は使わない（絶対ルール8）
  ・楽器種タイル（13種）のアイコンと、ヒーローの大きな構成（サックス＋トランペット＋フルート）
  ・線は stroke だけで描く（塗りは最小限）。色はCSSの currentColor／グラデーションで付ける
"""

# 64×64 の viewBox に収まる線画。stroke="currentColor" fill="none" を前提
ICONS = {
    "saxophone": (
        '<path d="M40 6 C28 6 22 14 24 22 C26 30 26 36 26 46 L27 88 C28 100 48 102 50 88 L52 62 C53 54 58 50 64 48" transform="scale(.6) translate(4 2)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'
        '<ellipse cx="42" cy="30.5" rx="3.2" ry="5" transform="rotate(-62 42 30.5)" stroke-width="2.2"/>'
        '<circle cx="20" cy="30" r="2" stroke-width="1.6"/><circle cx="20.5" cy="38" r="2" stroke-width="1.6"/><circle cx="21" cy="46" r="2" stroke-width="1.6"/><circle cx="21.5" cy="54" r="2" stroke-width="1.6"/>'
        '<path d="M27 8 L31 6" stroke-width="2.4" stroke-linecap="round"/>'
    ),
    "flute": (
        '<path d="M8 40 L56 16" stroke-width="4" stroke-linecap="round"/>'
        '<path d="M10 36 L14 34 M18 32 L22 30 M26 28 L30 26 M34 24 L38 22 M42 20 L46 18" stroke-width="2" stroke-linecap="round"/>'
        '<circle cx="18" cy="37.5" r="2.4" stroke-width="1.6"/><circle cx="26" cy="33.5" r="2.4" stroke-width="1.6"/><circle cx="34" cy="29.5" r="2.4" stroke-width="1.6"/><circle cx="42" cy="25.5" r="2.4" stroke-width="1.6"/>'
        '<rect x="50" y="12" width="7" height="5" rx="1.5" transform="rotate(-27 53.5 14.5)" stroke-width="1.8"/>'
    ),
    "clarinet": (
        '<path d="M32 6 L32 46" stroke-width="5" stroke-linecap="round"/>'
        '<path d="M32 46 L32 50 Q32 58 24 60 L40 60 Q32 58 32 50" stroke-width="2.4" stroke-linejoin="round" fill="none"/>'
        '<path d="M32 6 L32 2" stroke-width="2.4" stroke-linecap="round"/>'
        '<circle cx="32" cy="18" r="2.3" stroke-width="1.6"/><circle cx="32" cy="26" r="2.3" stroke-width="1.6"/><circle cx="32" cy="34" r="2.3" stroke-width="1.6"/>'
        '<path d="M26 20 L22 16 M38 28 L42 24 M26 36 L22 40" stroke-width="1.8" stroke-linecap="round"/>'
    ),
    "oboe": (
        '<path d="M32 12 L32 48" stroke-width="4" stroke-linecap="round"/>'
        '<path d="M32 48 L32 52 Q31 58 26 60 L38 60 Q33 58 32 52" stroke-width="2.2" stroke-linejoin="round"/>'
        '<path d="M32 12 L32 3" stroke-width="1.6" stroke-linecap="round"/><path d="M30 4 L34 4" stroke-width="1.6" stroke-linecap="round"/>'
        '<circle cx="32" cy="22" r="2" stroke-width="1.5"/><circle cx="32" cy="30" r="2" stroke-width="1.5"/><circle cx="32" cy="38" r="2" stroke-width="1.5"/>'
        '<path d="M27 24 L23 21 M37 32 L41 29" stroke-width="1.6" stroke-linecap="round"/>'
    ),
    "bassoon": (
        '<path d="M26 60 L26 12 Q26 6 32 6 Q38 6 38 12 L38 56" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>'
        '<path d="M38 20 Q46 18 52 10" stroke-width="2" stroke-linecap="round"/>'
        '<circle cx="26" cy="26" r="2" stroke-width="1.5"/><circle cx="26" cy="36" r="2" stroke-width="1.5"/><circle cx="38" cy="32" r="2" stroke-width="1.5"/><circle cx="38" cy="42" r="2" stroke-width="1.5"/>'
    ),
    "trumpet": (
        '<path d="M6 30 L38 30" stroke-width="3.2" stroke-linecap="round"/>'
        '<path d="M38 26 Q52 26 60 16 L60 44 Q52 34 38 34 Z" stroke-width="2.4" stroke-linejoin="round"/>'
        '<path d="M16 30 C10 30 10 40 16 40 L36 40 C42 40 42 30 36 30" stroke-width="2.2" stroke-linecap="round" fill="none"/>'
        '<path d="M22 22 L22 40 M28 22 L28 40 M34 22 L34 40" stroke-width="2.4" stroke-linecap="round"/>'
        '<path d="M20 21 L24 21 M26 21 L30 21 M32 21 L36 21" stroke-width="2.4" stroke-linecap="round"/>'
        '<path d="M3 28 L7 28 L7 32 L3 32 Z" stroke-width="1.8" stroke-linejoin="round"/>'
    ),
    "cornet": (
        '<path d="M8 30 L36 30" stroke-width="3.2" stroke-linecap="round"/>'
        '<path d="M36 26 Q48 26 56 16 L56 44 Q48 34 36 34 Z" stroke-width="2.4" stroke-linejoin="round"/>'
        '<path d="M14 30 C8 30 8 42 14 42 L34 42 C40 42 40 30 34 30" stroke-width="2.2" stroke-linecap="round" fill="none"/>'
        '<path d="M14 36 L34 36" stroke-width="2" stroke-linecap="round"/>'
        '<path d="M20 22 L20 42 M26 22 L26 42 M32 22 L32 42" stroke-width="2.4" stroke-linecap="round"/>'
        '<path d="M18 21 L22 21 M24 21 L28 21 M30 21 L34 21" stroke-width="2.4" stroke-linecap="round"/>'
    ),
    "flugelhorn": (
        '<path d="M8 32 L34 32" stroke-width="3.2" stroke-linecap="round"/>'
        '<path d="M34 26 Q46 26 58 12 L58 52 Q46 38 34 38 Z" stroke-width="2.4" stroke-linejoin="round"/>'
        '<path d="M14 32 C8 32 8 44 14 44 L32 44 C38 44 38 32 32 32" stroke-width="2.2" stroke-linecap="round" fill="none"/>'
        '<path d="M18 22 L18 44 M24 22 L24 44 M30 22 L30 44" stroke-width="2.4" stroke-linecap="round"/>'
        '<path d="M16 21 L20 21 M22 21 L26 21 M28 21 L32 21" stroke-width="2.4" stroke-linecap="round"/>'
    ),
    "horn": (
        '<circle cx="30" cy="34" r="16" stroke-width="3"/>'
        '<circle cx="30" cy="34" r="9" stroke-width="2.2"/>'
        '<path d="M42 44 Q52 50 58 60 L38 60 Q40 52 42 44 Z" stroke-width="2.2" stroke-linejoin="round"/>'
        '<path d="M14 26 L8 20" stroke-width="2.4" stroke-linecap="round"/>'
        '<path d="M26 16 L26 22 M31 15 L31 21 M36 16 L36 22" stroke-width="2.2" stroke-linecap="round"/>'
    ),
    "trombone": (
        '<path d="M6 26 L40 26 M6 34 L40 34" stroke-width="2.6" stroke-linecap="round"/>'
        '<path d="M6 26 C0 26 0 34 6 34" stroke-width="2.6" fill="none"/>'
        '<path d="M40 26 L40 22 Q52 22 62 10 L62 42 Q52 30 40 30" stroke-width="2.4" stroke-linejoin="round"/>'
        '<path d="M14 30 L30 30" stroke-width="1.8" stroke-linecap="round"/>'
        '<path d="M28 26 L28 20 L34 20 L34 26" stroke-width="2" stroke-linejoin="round"/>'
        '<path d="M44 34 L44 40 L52 40 L52 34" stroke-width="2" stroke-linejoin="round"/>'
    ),
    # 縦型の金管（ベルが上を向く）：上に広がるベル＋左下の管の輪＋右のピストン3本
    "euphonium": (
        '<path d="M22 8 Q32 4 42 8 L37 30 Q32 32 27 30 Z" stroke-width="2.4" stroke-linejoin="round"/>'
        '<ellipse cx="32" cy="8" rx="10" ry="3" stroke-width="2"/>'
        '<path d="M27 30 Q14 34 14 46 Q14 58 28 58 Q40 58 40 48 L40 38" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
        '<path d="M40 40 L58 40" stroke-width="2.6" stroke-linecap="round"/>'
        '<path d="M44 30 L44 46 M50 30 L50 46 M56 30 L56 46" stroke-width="2.4" stroke-linecap="round"/>'
        '<path d="M42 29 L46 29 M48 29 L52 29 M54 29 L58 29" stroke-width="2.4" stroke-linecap="round"/>'
    ),
    "baritone": (
        '<path d="M24 10 Q32 6 40 10 L36 30 Q32 32 28 30 Z" stroke-width="2.2" stroke-linejoin="round"/>'
        '<ellipse cx="32" cy="10" rx="8" ry="2.6" stroke-width="1.8"/>'
        '<path d="M28 30 Q16 34 16 45 Q16 56 28 56 Q38 56 38 48 L38 40" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>'
        '<path d="M38 42 L56 42" stroke-width="2.4" stroke-linecap="round"/>'
        '<path d="M43 32 L43 48 M49 32 L49 48 M55 32 L55 48" stroke-width="2.2" stroke-linecap="round"/>'
        '<path d="M41 31 L45 31 M47 31 L51 31 M53 31 L57 31" stroke-width="2.2" stroke-linecap="round"/>'
    ),
    "tuba": (
        '<path d="M16 6 Q32 0 48 6 L40 32 Q32 35 24 32 Z" stroke-width="2.6" stroke-linejoin="round"/>'
        '<ellipse cx="32" cy="6" rx="16" ry="4" stroke-width="2.2"/>'
        '<path d="M24 32 Q8 36 8 48 Q8 62 26 62 Q40 62 40 50 L40 40" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round"/>'
        '<path d="M40 42 L60 42" stroke-width="2.8" stroke-linecap="round"/>'
        '<path d="M46 30 L46 48 M52 30 L52 48 M58 30 L58 48" stroke-width="2.6" stroke-linecap="round"/>'
        '<path d="M44 29 L48 29 M50 29 L54 29 M56 29 L60 29" stroke-width="2.6" stroke-linecap="round"/>'
    ),
}


def icon(group_key: str, size: int = 44, cls: str = "gicon") -> str:
    inner = ICONS.get(group_key)
    if not inner:
        return ""
    return (f'<svg class="{cls}" viewBox="0 0 64 64" width="{size}" height="{size}" aria-hidden="true" fill="none" stroke="currentColor">'
            f'{inner}</svg>')


def hero_art() -> str:
    """ヒーロー右側の構成：大きなサックスのラインアート＋トランペット＋フルート。真鍮のグラデーションと淡い光。実機ではない汎用の線画。"""
    return """<svg class="heroart" viewBox="0 0 560 520" aria-hidden="true" fill="none">
  <defs>
    <linearGradient id="ha-g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F7E2A6"/><stop offset=".55" stop-color="#E6B85C"/><stop offset="1" stop-color="#A8722A"/></linearGradient>
    <linearGradient id="ha-g2" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#F7E2A6" stop-opacity=".9"/><stop offset="1" stop-color="#C9A227" stop-opacity=".6"/></linearGradient>
    <radialGradient id="ha-halo" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#E6B85C" stop-opacity=".28"/><stop offset="1" stop-color="#E6B85C" stop-opacity="0"/></radialGradient>
    <filter id="ha-glow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="3.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <circle cx="330" cy="270" r="230" fill="url(#ha-halo)"/>
  <!-- フルート（背面・細い） -->
  <g class="ha-flute" stroke="url(#ha-g2)" stroke-linecap="round" opacity=".7">
    <path d="M60 430 L470 150" stroke-width="9"/>
    <path d="M100 405 L112 397 M140 378 L152 370 M180 350 L192 342 M220 323 L232 315 M260 296 L272 288 M300 268 L312 260 M340 241 L352 233 M380 214 L392 206" stroke-width="3"/>
    <g fill="none" stroke-width="2.4">
      <circle cx="124" cy="392" r="7"/><circle cx="164" cy="365" r="7"/><circle cx="204" cy="338" r="7"/><circle cx="244" cy="311" r="7"/><circle cx="284" cy="283" r="7"/><circle cx="324" cy="256" r="7"/><circle cx="364" cy="229" r="7"/><circle cx="404" cy="201" r="7"/>
    </g>
    <rect x="428" y="160" width="26" height="14" rx="4" transform="rotate(-34 441 167)" stroke-width="3"/>
  </g>
  <!-- サックス（主役） -->
  <g class="ha-sax" stroke="url(#ha-g)" stroke-linecap="round" stroke-linejoin="round" filter="url(#ha-glow)">
    <path d="M362 46 C300 46 268 84 282 128 C292 160 292 190 292 232 L296 402 C300 462 400 470 406 402 L414 300 C418 264 440 244 480 236" stroke-width="22"/>
    <path d="M362 46 C300 46 268 84 282 128 C292 160 292 190 292 232 L296 402 C300 462 400 470 406 402 L414 300 C418 264 440 244 480 236" stroke-width="10" stroke="#3B2408" opacity=".25"/>
    <ellipse cx="490" cy="236" rx="16" ry="30" transform="rotate(-70 490 236)" stroke-width="7" fill="#22150A" fill-opacity=".4"/>
    <path d="M362 46 L392 40" stroke-width="12"/>
    <path d="M332 60 L348 72" stroke-width="6"/>
    <g stroke-width="5" fill="#22150A" fill-opacity=".35">
      <circle cx="262" cy="160" r="12"/><circle cx="264" cy="196" r="12"/><circle cx="266" cy="232" r="12"/><circle cx="268" cy="268" r="12"/><circle cx="270" cy="304" r="12"/><circle cx="272" cy="340" r="12"/>
      <circle cx="326" cy="250" r="9"/><circle cx="328" cy="286" r="9"/><circle cx="330" cy="322" r="9"/>
    </g>
    <path d="M258 150 L258 350" stroke-width="4" opacity=".8"/>
    <path d="M322 240 L332 340" stroke-width="3.5" opacity=".8"/>
  </g>
  <!-- トランペット（前面・左下。ベルは2本のフレア曲線＋楕円の開口） -->
  <g class="ha-tp" stroke="url(#ha-g)" stroke-linecap="round" stroke-linejoin="round" filter="url(#ha-glow)">
    <path d="M30 452 L186 452" stroke-width="12"/>
    <path d="M186 446 C226 446 252 430 282 398" stroke-width="9"/>
    <path d="M186 458 C226 458 252 474 282 506" stroke-width="9"/>
    <ellipse cx="284" cy="452" rx="12" ry="56" stroke-width="7" fill="#22150A" fill-opacity=".45"/>
    <path d="M78 452 C54 452 54 490 78 490 L170 490 C194 490 194 452 170 452" stroke-width="8"/>
    <path d="M100 422 L100 490 M130 422 L130 490 M160 422 L160 490" stroke-width="9"/>
    <path d="M90 418 L110 418 M120 418 L140 418 M150 418 L170 418" stroke-width="9"/>
    <path d="M14 444 L30 444 L30 460 L14 460 Z" stroke-width="6"/>
  </g>
</svg>"""
