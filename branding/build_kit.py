#!/usr/bin/env python3
"""Build the complete, production-grade Logo Kit for YouTube Uploader Pro (Concept A: Kinetic YU)."""

import os
import re

os.makedirs("branding/master", exist_ok=True)
os.makedirs("static/img", exist_ok=True)

# -----------------------------------------------------------------------------
# 1. FINAL SYMBOL — BRAND COLOR (Electric Crimson #FF0033 on Obsidian)
# -----------------------------------------------------------------------------
# 256x256 master symbol:
# Outer U-channel chassis in deep obsidian slate #1e293b / #0f172a or solid obsidian
# Ascending arrow in vibrant electric crimson #FF0033 with gradient/accent
symbol_color = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256" role="img" aria-labelledby="title-symbol-color">
  <title id="title-symbol-color">YouTube Uploader Pro — Master Symbol</title>
  <defs>
    <linearGradient id="crimson-grad" x1="128" y1="36" x2="128" y2="160" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#FF1A4B"/>
      <stop offset="100%" stop-color="#E6002E"/>
    </linearGradient>
    <linearGradient id="chassis-grad" x1="128" y1="52" x2="128" y2="220" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#334155"/>
      <stop offset="100%" stop-color="#0F172A"/>
    </linearGradient>
  </defs>
  <!-- Outer U-channel chassis (The Queue Tray) -->
  <path fill="url(#chassis-grad)" fill-rule="evenodd" d="M36 84 L68 52 L68 164 A24 24 0 0 0 92 188 L164 188 A24 24 0 0 0 188 164 L188 52 L220 84 L220 164 A56 56 0 0 1 164 220 L92 220 A56 56 0 0 1 36 164 Z"/>
  <!-- Center Ascending Vector (The Speed Rocket) -->
  <path fill="url(#crimson-grad)" d="M128 36 L172 80 L144 80 L144 160 L112 160 L112 80 L84 80 Z"/>
</svg>
"""

# Flat brand color (pure solid fills, zero gradients for universal printing & cutting)
symbol_brand_flat = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256" role="img" aria-labelledby="title-symbol-flat">
  <title id="title-symbol-flat">YouTube Uploader Pro — Flat Brand Symbol</title>
  <!-- Outer U-channel chassis -->
  <path fill="#0F172A" fill-rule="evenodd" d="M36 84 L68 52 L68 164 A24 24 0 0 0 92 188 L164 188 A24 24 0 0 0 188 164 L188 52 L220 84 L220 164 A56 56 0 0 1 164 220 L92 220 A56 56 0 0 1 36 164 Z"/>
  <!-- Center Ascending Vector -->
  <path fill="#FF0033" d="M128 36 L172 80 L144 80 L144 160 L112 160 L112 80 L84 80 Z"/>
</svg>
"""

# Solid black master (100% monochrome black)
symbol_black = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256" role="img" aria-labelledby="title-symbol-black">
  <title id="title-symbol-black">YouTube Uploader Pro — Monochrome Black Symbol</title>
  <path fill="#000000" fill-rule="evenodd" d="M36 84 L68 52 L68 164 A24 24 0 0 0 92 188 L164 188 A24 24 0 0 0 188 164 L188 52 L220 84 L220 164 A56 56 0 0 1 164 220 L92 220 A56 56 0 0 1 36 164 Z"/>
  <path fill="#000000" d="M128 36 L172 80 L144 80 L144 160 L112 160 L112 80 L84 80 Z"/>
</svg>
"""

# Solid white reversed (for dark backgrounds)
symbol_white = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256" role="img" aria-labelledby="title-symbol-white">
  <title id="title-symbol-white">YouTube Uploader Pro — Inverted White Symbol</title>
  <path fill="#FFFFFF" fill-rule="evenodd" d="M36 84 L68 52 L68 164 A24 24 0 0 0 92 188 L164 188 A24 24 0 0 0 188 164 L188 52 L220 84 L220 164 A56 56 0 0 1 164 220 L92 220 A56 56 0 0 1 36 164 Z"/>
  <path fill="#FFFFFF" d="M128 36 L172 80 L144 80 L144 160 L112 160 L112 80 L84 80 Z"/>
</svg>
"""

# Brand Crimson Mono (single ink #FF0033)
symbol_crimson = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256" role="img" aria-labelledby="title-symbol-crimson">
  <title id="title-symbol-crimson">YouTube Uploader Pro — Crimson Mono Symbol</title>
  <path fill="#FF0033" fill-rule="evenodd" d="M36 84 L68 52 L68 164 A24 24 0 0 0 92 188 L164 188 A24 24 0 0 0 188 164 L188 52 L220 84 L220 164 A56 56 0 0 1 164 220 L92 220 A56 56 0 0 1 36 164 Z"/>
  <path fill="#FF0033" d="M128 36 L172 80 L144 80 L144 160 L112 160 L112 80 L84 80 Z"/>
</svg>
"""

# App Icon (Symbol on Obsidian container with subtle 1px border and crimson accent glow)
app_icon = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256" role="img" aria-labelledby="title-app-icon">
  <title id="title-app-icon">YouTube Uploader Pro — App Icon</title>
  <defs>
    <linearGradient id="bg-grad" x1="0" y1="0" x2="256" y2="256" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#111827"/>
      <stop offset="100%" stop-color="#030712"/>
    </linearGradient>
    <linearGradient id="icon-crimson" x1="128" y1="56" x2="128" y2="180" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#FF2A55"/>
      <stop offset="100%" stop-color="#E6002E"/>
    </linearGradient>
  </defs>
  <!-- Squircle container -->
  <rect x="0" y="0" width="256" height="256" rx="56" fill="url(#bg-grad)"/>
  <rect x="1" y="1" width="254" height="254" rx="55" fill="none" stroke="#FFFFFF" stroke-opacity="0.12" stroke-width="2"/>
  <!-- Centered scaled symbol (scale 0.72, translated) -->
  <g transform="translate(36, 36) scale(0.72)">
    <path fill="#64748B" fill-rule="evenodd" d="M36 84 L68 52 L68 164 A24 24 0 0 0 92 188 L164 188 A24 24 0 0 0 188 164 L188 52 L220 84 L220 164 A56 56 0 0 1 164 220 L92 220 A56 56 0 0 1 36 164 Z"/>
    <path fill="url(#icon-crimson)" d="M128 36 L172 80 L144 80 L144 160 L112 160 L112 80 L84 80 Z"/>
  </g>
</svg>
"""

# Favicon SVG (High contrast, tight crop, pure solid geometry for 16-32px browser tabs)
favicon_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32" role="img" aria-labelledby="title-fav">
  <title id="title-fav">YouTube Uploader Pro Favicon</title>
  <rect width="32" height="32" rx="7" fill="#07090E"/>
  <!-- Scaled Kinetic YU symbol -->
  <g transform="translate(4, 4) scale(0.09375)">
    <path fill="#94A3B8" fill-rule="evenodd" d="M36 84 L68 52 L68 164 A24 24 0 0 0 92 188 L164 188 A24 24 0 0 0 188 164 L188 52 L220 84 L220 164 A56 56 0 0 1 164 220 L92 220 A56 56 0 0 1 36 164 Z"/>
    <path fill="#FF0033" d="M128 36 L172 80 L144 80 L144 160 L112 160 L112 80 L84 80 Z"/>
  </g>
</svg>
"""

# -----------------------------------------------------------------------------
# 2. HORIZONTAL LOCKUP — DARK MODE CONSOLE (For sidebar and navigation)
# -----------------------------------------------------------------------------
lockup_dark = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 256" width="960" height="256" role="img" aria-labelledby="title-lockup-dark">
  <title id="title-lockup-dark">YouTube Uploader Pro — Dark Console Lockup</title>
  <defs>
    <linearGradient id="ld-crimson" x1="128" y1="36" x2="128" y2="160" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#FF2A55"/>
      <stop offset="100%" stop-color="#E6002E"/>
    </linearGradient>
  </defs>
  <!-- Symbol -->
  <g id="symbol" transform="translate(26, 0)">
    <path fill="#475569" fill-rule="evenodd" d="M36 84 L68 52 L68 164 A24 24 0 0 0 92 188 L164 188 A24 24 0 0 0 188 164 L188 52 L220 84 L220 164 A56 56 0 0 1 164 220 L92 220 A56 56 0 0 1 36 164 Z"/>
    <path fill="url(#ld-crimson)" d="M128 36 L172 80 L144 80 L144 160 L112 160 L112 80 L84 80 Z"/>
  </g>
  <!-- Brand Heading -->
  <g id="brand-text" fill="#F8FAFC" transform="translate(-26, 0)">
    <!-- Y -->
    <polygon points="334,80 364,110 364,164 384,164 384,110 414,80 392,80 374,98 356,80" fill="#FF0033"/>
    <!-- T -->
    <polygon points="422,80 466,80 466,100 454,100 454,164 434,164 434,100 422,100" fill="#FF0033"/>
    <!-- Separator Dot -->
    <rect x="478" y="116" width="12" height="12" rx="3" fill="#64748B"/>
    <!-- UPLOADER -->
    <!-- U -->
    <path d="M506 80 L526 80 L526 138 A14 14 0 0 0 554 138 L554 80 L574 80 L574 138 A34 34 0 0 1 506 138 Z"/>
    <!-- P -->
    <path fill-rule="evenodd" d="M588 80 L622 80 A24 24 0 0 1 622 128 L608 128 L608 164 L588 164 Z M608 100 L620 100 A4 4 0 0 1 620 108 L608 108 Z"/>
    <!-- L -->
    <polygon points="656,80 676,80 676,144 704,144 704,164 656,164"/>
    <!-- O -->
    <path fill-rule="evenodd" d="M742 80 A42 42 0 1 1 741.9 80 Z M742 100 A22 22 0 1 0 742.1 100 Z"/>
    <!-- A -->
    <polygon points="808,80 830,80 852.5,164 830.5,164 824.5,142 813.5,142 807.5,164 785.5,164"/>
    <!-- D -->
    <path fill-rule="evenodd" d="M868 80 L894 80 A42 42 0 0 1 894 164 L868 164 Z M888 100 L894 100 A22 22 0 0 1 894 144 L888 144 Z"/>
  </g>
  <!-- Sub-badge -->
  <g id="badge" transform="translate(-26, 0)">
    <!-- PRO Tag in electric crimson -->
    <g fill="#FF0033">
      <!-- P -->
      <polygon points="334,186 348,186 348,198 340,198 340,208 334,208"/>
      <!-- R -->
      <polygon points="354,186 368,186 368,198 360,198 368,208 362,208 356,200 356,208 350,208 350,186"/>
      <!-- O -->
      <path fill-rule="evenodd" d="M382 186 A11 11 0 1 1 381.9 186 Z M382 191 A6 6 0 1 0 382.1 191 Z"/>
    </g>
    <!-- Cyan separator -->
    <rect x="404" y="196" width="20" height="3" rx="1.5" fill="#00F0FF"/>
    <!-- Subtitle text -->
    <g fill="#94A3B8">
      <polygon points="436,186 450,186 450,189 440,189 440,193 450,194 450,206 436,206 436,202 446,202 446,197 436,196"/>
      <polygon points="458,186 472,186 472,189 467,189 467,206 463,206 463,189 458,189"/>
      <path d="M478 186 L482 186 L482 199 A3 3 0 0 0 488 199 L488 186 L492 186 L492 199 A7 7 0 0 1 478 199 Z"/>
      <path fill-rule="evenodd" d="M498 186 L506 186 A10 10 0 0 1 506 206 L498 206 Z M502 190 L506 190 A6 6 0 0 1 506 202 L502 202 Z"/>
      <rect x="516" y="186" width="4" height="20"/>
      <path fill-rule="evenodd" d="M532 186 A10 10 0 1 1 531.9 186 Z M532 190 A6 6 0 1 0 532.1 190 Z"/>
    </g>
  </g>
</svg>
"""

# Horizontal Lockup — Light Background Master
lockup_light = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 256" width="960" height="256" role="img" aria-labelledby="title-lockup-light">
  <title id="title-lockup-light">YouTube Uploader Pro — Light Mode Lockup</title>
  <!-- Symbol -->
  <g id="symbol" transform="translate(26, 0)">
    <path fill="#0F172A" fill-rule="evenodd" d="M36 84 L68 52 L68 164 A24 24 0 0 0 92 188 L164 188 A24 24 0 0 0 188 164 L188 52 L220 84 L220 164 A56 56 0 0 1 164 220 L92 220 A56 56 0 0 1 36 164 Z"/>
    <path fill="#FF0033" d="M128 36 L172 80 L144 80 L144 160 L112 160 L112 80 L84 80 Z"/>
  </g>
  <!-- Brand Heading -->
  <g id="brand-text" fill="#0F172A" transform="translate(-26, 0)">
    <polygon points="334,80 364,110 364,164 384,164 384,110 414,80 392,80 374,98 356,80" fill="#FF0033"/>
    <polygon points="422,80 466,80 466,100 454,100 454,164 434,164 434,100 422,100" fill="#FF0033"/>
    <rect x="478" y="116" width="12" height="12" rx="3" fill="#64748B"/>
    <path d="M506 80 L526 80 L526 138 A14 14 0 0 0 554 138 L554 80 L574 80 L574 138 A34 34 0 0 1 506 138 Z"/>
    <path fill-rule="evenodd" d="M588 80 L622 80 A24 24 0 0 1 622 128 L608 128 L608 164 L588 164 Z M608 100 L620 100 A4 4 0 0 1 620 108 L608 108 Z"/>
    <polygon points="656,80 676,80 676,144 704,144 704,164 656,164"/>
    <path fill-rule="evenodd" d="M742 80 A42 42 0 1 1 741.9 80 Z M742 100 A22 22 0 1 0 742.1 100 Z"/>
    <polygon points="808,80 830,80 852.5,164 830.5,164 824.5,142 813.5,142 807.5,164 785.5,164"/>
    <path fill-rule="evenodd" d="M868 80 L894 80 A42 42 0 0 1 894 164 L868 164 Z M888 100 L894 100 A22 22 0 0 1 894 144 L888 144 Z"/>
  </g>
  <!-- Sub-badge -->
  <g id="badge" transform="translate(-26, 0)">
    <g fill="#FF0033">
      <polygon points="334,186 348,186 348,198 340,198 340,208 334,208"/>
      <polygon points="354,186 368,186 368,198 360,198 368,208 362,208 356,200 356,208 350,208 350,186"/>
      <path fill-rule="evenodd" d="M382 186 A11 11 0 1 1 381.9 186 Z M382 191 A6 6 0 1 0 382.1 191 Z"/>
    </g>
    <rect x="404" y="196" width="20" height="3" rx="1.5" fill="#FF0033"/>
    <g fill="#475569">
      <polygon points="436,186 450,186 450,189 440,189 440,193 450,194 450,206 436,206 436,202 446,202 446,197 436,196"/>
      <polygon points="458,186 472,186 472,189 467,189 467,206 463,206 463,189 458,189"/>
      <path d="M478 186 L482 186 L482 199 A3 3 0 0 0 488 199 L488 186 L492 186 L492 199 A7 7 0 0 1 478 199 Z"/>
      <path fill-rule="evenodd" d="M498 186 L506 186 A10 10 0 0 1 506 206 L498 206 Z M502 190 L506 190 A6 6 0 0 1 506 202 L502 202 Z"/>
      <rect x="516" y="186" width="4" height="20"/>
      <path fill-rule="evenodd" d="M532 186 A10 10 0 1 1 531.9 186 Z M532 190 A6 6 0 1 0 532.1 190 Z"/>
    </g>
  </g>
</svg>
"""

# -----------------------------------------------------------------------------
# 3. STACKED VERTICAL LOCKUP (Square 384 x 384 for billboards, avatars, docs)
# -----------------------------------------------------------------------------
lockup_stacked = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 384" width="384" height="384" role="img" aria-labelledby="title-lockup-stacked">
  <title id="title-lockup-stacked">YouTube Uploader Pro — Stacked Lockup</title>
  <!-- Centered Symbol (scale 0.85, top aligned) -->
  <g transform="translate(83, 28) scale(0.85)">
    <path fill="#0F172A" fill-rule="evenodd" d="M36 84 L68 52 L68 164 A24 24 0 0 0 92 188 L164 188 A24 24 0 0 0 188 164 L188 52 L220 84 L220 164 A56 56 0 0 1 164 220 L92 220 A56 56 0 0 1 36 164 Z"/>
    <path fill="#FF0033" d="M128 36 L172 80 L144 80 L144 160 L112 160 L112 80 L84 80 Z"/>
  </g>
  <!-- Stacked Wordmark -->
  <!-- YT UPLOADER -->
  <g transform="translate(68, 256) scale(0.42)" fill="#0F172A">
    <!-- Y -->
    <polygon points="0,0 30,30 30,84 50,84 50,30 80,0 58,0 40,18 22,0" fill="#FF0033"/>
    <!-- T -->
    <polygon points="88,0 132,0 132,20 120,20 120,84 100,84 100,20 88,20" fill="#FF0033"/>
    <!-- Separator Dot -->
    <rect x="144" y="36" width="12" height="12" rx="3" fill="#64748B"/>
    <!-- UPLOADER -->
    <path d="M172 0 L192 0 L192 58 A14 14 0 0 0 220 58 L220 0 L240 0 L240 58 A34 34 0 0 1 172 58 Z"/>
    <path fill-rule="evenodd" d="M254 0 L288 0 A24 24 0 0 1 288 48 L274 48 L274 84 L254 84 Z M274 20 L286 20 A4 4 0 0 1 286 28 L274 28 Z"/>
    <polygon points="322,0 342,0 342,64 370,64 370,84 322,84"/>
    <path fill-rule="evenodd" d="M408 0 A42 42 0 1 1 407.9 0 Z M408 20 A22 22 0 1 0 408.1 20 Z"/>
    <polygon points="474,0 496,0 518.5,84 496.5,84 490.5,62 479.5,62 473.5,84 451.5,84"/>
    <path fill-rule="evenodd" d="M534 0 L560 0 A42 42 0 0 1 560 84 L534 84 Z M554 20 L560 20 A22 22 0 0 1 560 64 L554 64 Z"/>
  </g>
  <!-- Subtitle Tag (Clean outlined vector, zero live text) -->
  <g transform="translate(132, 310)" fill="#FF0033">
    <!-- P -->
    <polygon points="16,4 28,4 28,14 22,14 22,22 16,22"/>
    <!-- R -->
    <polygon points="32,4 44,4 44,14 38,14 44,22 39,22 34,15 34,22 28,22 28,4"/>
    <!-- O -->
    <path fill-rule="evenodd" d="M56 4 A9 9 0 1 1 55.9 4 Z M56 8 A5 5 0 1 0 56.1 8 Z"/>
    <!-- Dot -->
    <rect x="70" y="11" width="4" height="4" fill="#64748B"/>
    <!-- STUDIO -->
    <polygon points="80,4 92,4 92,7 84,7 84,11 92,12 92,22 80,22 80,19 88,19 88,15 80,14" fill="#0F172A"/>
    <polygon points="96,4 108,4 108,7 103,7 103,22 100,22 100,7 96,7" fill="#0F172A"/>
  </g>
</svg>
"""

# Map output files
files = {
    "branding/master/yt-uploader-symbol.svg": symbol_color,
    "branding/master/yt-uploader-symbol-flat.svg": symbol_brand_flat,
    "branding/master/yt-uploader-symbol-black.svg": symbol_black,
    "branding/master/yt-uploader-symbol-white.svg": symbol_white,
    "branding/master/yt-uploader-symbol-crimson.svg": symbol_crimson,
    "branding/master/yt-uploader-app-icon.svg": app_icon,
    "branding/master/yt-uploader-favicon.svg": favicon_svg,
    "branding/master/yt-uploader-lockup-dark.svg": lockup_dark,
    "branding/master/yt-uploader-lockup-light.svg": lockup_light,
    "branding/master/yt-uploader-lockup-stacked.svg": lockup_stacked,

    # Deploy into web application static assets
    "static/img/logo.svg": symbol_color,
    "static/img/logo-white.svg": symbol_white,
    "static/img/logo-dark.svg": lockup_dark,
    "static/img/logo-light.svg": lockup_light,
    "static/img/favicon.svg": favicon_svg,
    "static/img/apple-touch-icon.svg": app_icon,
}

for path, content in files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"Exported: {path}")

# Generate site.webmanifest
webmanifest = """{
  "name": "YouTube Uploader Pro",
  "short_name": "YT Uploader",
  "description": "Intelligent automated YouTube video uploader and queue scheduler",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#07090e",
  "theme_color": "#ff0033",
  "icons": [
    {
      "src": "/static/img/favicon.svg",
      "sizes": "any",
      "type": "image/svg+xml"
    },
    {
      "src": "/static/img/apple-touch-icon.svg",
      "sizes": "256x256",
      "type": "image/svg+xml",
      "purpose": "any maskable"
    }
  ]
}
"""
with open("static/site.webmanifest", "w", encoding="utf-8") as f:
    f.write(webmanifest)
print("Exported: static/site.webmanifest")
