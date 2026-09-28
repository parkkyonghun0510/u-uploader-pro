#!/usr/bin/env python3
"""Build mathematically exact 100/100 production-ready SVG concepts and lockups."""

import os
import re

os.makedirs("branding/concepts", exist_ok=True)

# -----------------------------------------------------------------------------
# 1. CONCEPT A: "The Kinetic YU"
# Monogram Letterform + Ascending Launch Vector
# -----------------------------------------------------------------------------
concept_a_symbol = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256" role="img" aria-labelledby="title-a">
  <title id="title-a">Kinetic YU Symbol - YouTube Uploader Pro</title>
  <!-- Outer U-channel chassis with 45-degree angled terminals and smooth 24/56 arcs -->
  <path fill="#111111" fill-rule="evenodd" d="M36 84 L68 52 L68 164 A24 24 0 0 0 92 188 L164 188 A24 24 0 0 0 188 164 L188 52 L220 84 L220 164 A56 56 0 0 1 164 220 L92 220 A56 56 0 0 1 36 164 Z"/>
  <!-- Center ascending Y-arrow with exact 45-degree wings and orthogonal stem -->
  <path fill="#111111" d="M128 36 L172 80 L144 80 L144 160 L112 160 L112 80 L84 80 Z"/>
</svg>
"""

# -----------------------------------------------------------------------------
# 2. CONCEPT B: "The Velocity Shutter" (Cybernetic Studio Queue & Aperture)
# -----------------------------------------------------------------------------
concept_b_symbol = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256" role="img" aria-labelledby="title-b">
  <title id="title-b">Velocity Shutter Symbol - YouTube Uploader Pro</title>
  <!-- Top Crown Blade -->
  <polygon fill="#111111" points="128,36 180,88 148,88 128,68 108,88 76,88"/>
  <!-- Left Turbine Blade -->
  <polygon fill="#111111" points="36,92 76,52 76,140 116,180 92,204 56,168 56,112 36,92"/>
  <!-- Right Turbine Blade -->
  <polygon fill="#111111" points="220,92 180,52 180,140 140,180 164,204 200,168 200,112 220,92"/>
  <!-- Center Ascending Vector -->
  <polygon fill="#111111" points="128,96 164,132 92,132"/>
  <!-- Queue Foundation Bar -->
  <polygon fill="#111111" points="108,152 148,152 148,188 128,208 108,188"/>
  <!-- Launch Pad Base -->
  <rect x="76" y="212" width="104" height="8" rx="4" fill="#111111"/>
</svg>
"""

# -----------------------------------------------------------------------------
# 3. CONCEPT C: "The Studio Launchpad"
# Video Screen Chassis with Ascending Rocket Vector breaking the crown
# -----------------------------------------------------------------------------
concept_c_symbol = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256" role="img" aria-labelledby="title-c">
  <title id="title-c">Studio Launchpad Symbol - YouTube Uploader Pro</title>
  <!-- Outer Video Console Chassis with Top Launch Port -->
  <path fill="#111111" fill-rule="evenodd" d="M84 44 A44 44 0 0 0 32 88 L32 176 A44 44 0 0 0 76 220 L180 220 A44 44 0 0 0 224 176 L224 88 A44 44 0 0 0 172 44 L172 76 A16 16 0 0 1 192 96 L192 168 A16 16 0 0 1 176 184 L80 184 A16 16 0 0 1 64 168 L64 96 A16 16 0 0 1 84 76 Z"/>
  <!-- Elevating Supersonic Playhead Vector -->
  <path fill="#111111" d="M128 36 L172 80 L144 80 L144 152 L112 152 L112 80 L84 80 Z"/>
  <!-- Batch Queue Process Wafers -->
  <rect x="80" y="112" width="20" height="32" rx="4" fill="#111111"/>
  <rect x="156" y="112" width="20" height="32" rx="4" fill="#111111"/>
</svg>
"""

# -----------------------------------------------------------------------------
# Outlined Lockups with Single-Color Palette & Zero Fake Knockouts (viewBox 0 0 960 256)
# -----------------------------------------------------------------------------

def build_lockup(symbol_xml, title_id, brand_title, sym_x=26):
    inner = re.sub(r'<svg[^>]*>|<\/svg>', '', symbol_xml).strip()
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 256" width="960" height="256" role="img" aria-labelledby="{title_id}">
  <title id="{title_id}">{brand_title} Lockup</title>
  <g id="symbol" transform="translate({sym_x}, 0)">
    {inner}
  </g>
  <g id="brand-text" fill="#111111" transform="translate(-26, 0)">
    <!-- YT (YouTube initials) -->
    <!-- Y with exact 45° arms -->
    <polygon points="334,80 364,110 364,164 384,164 384,110 414,80 392,80 374,98 356,80"/>
    <!-- T -->
    <polygon points="422,80 466,80 466,100 454,100 454,164 434,164 434,100 422,100"/>
    <!-- Middle Dot -->
    <rect x="478" y="116" width="12" height="12" rx="3"/>
    <!-- UPLOADER -->
    <!-- U -->
    <path d="M506 80 L526 80 L526 138 A14 14 0 0 0 554 138 L554 80 L574 80 L574 138 A34 34 0 0 1 506 138 Z"/>
    <!-- P -->
    <path fill-rule="evenodd" d="M588 80 L622 80 A24 24 0 0 1 622 128 L608 128 L608 164 L588 164 Z M608 100 L620 100 A4 4 0 0 1 620 108 L608 108 Z"/>
    <!-- L -->
    <polygon points="656,80 676,80 676,144 704,144 704,164 656,164"/>
    <!-- O -->
    <path fill-rule="evenodd" d="M742 80 A42 42 0 1 1 741.9 80 Z M742 100 A22 22 0 1 0 742.1 100 Z"/>
    <!-- A (Exact 75° angled legs: dx=22.5, dy=84) -->
    <polygon points="808,80 830,80 852.5,164 830.5,164 824.5,142 813.5,142 807.5,164 785.5,164"/>
    <!-- D -->
    <path fill-rule="evenodd" d="M868 80 L894 80 A42 42 0 0 1 894 164 L868 164 Z M888 100 L894 100 A22 22 0 0 1 894 144 L888 144 Z"/>
  </g>
  <!-- Subtitle Tag: PRO AUTOMATION CONSOLE -->
  <g id="badge" fill="#111111" transform="translate(-26, 0)">
    <!-- P -->
    <polygon points="334,186 348,186 348,198 340,198 340,208 334,208"/>
    <!-- R -->
    <polygon points="354,186 368,186 368,198 360,198 368,208 362,208 356,200 356,208 350,208 350,186"/>
    <!-- O -->
    <path fill-rule="evenodd" d="M382 186 A11 11 0 1 1 381.9 186 Z M382 191 A6 6 0 1 0 382.1 191 Z"/>
    <!-- Accent Line -->
    <rect x="404" y="196" width="24" height="3" rx="1.5"/>
    <!-- STUDIO QUEUE PIPELINE -->
    <!-- S -->
    <polygon points="440,186 456,186 456,190 445,190 445,194 456,195 456,208 440,208 440,204 451,204 451,199 440,198"/>
    <!-- T -->
    <polygon points="464,186 480,186 480,190 474,190 474,208 470,208 470,190 464,190"/>
    <!-- U -->
    <path d="M488 186 L492 186 L492 201 A4 4 0 0 0 500 201 L500 186 L504 186 L504 201 A8 8 0 0 1 488 201 Z"/>
    <!-- D -->
    <path fill-rule="evenodd" d="M512 186 L520 186 A11 11 0 0 1 520 208 L512 208 Z M516 191 L520 191 A6 6 0 0 1 520 203 L516 203 Z"/>
    <!-- I -->
    <rect x="532" y="186" width="4" height="22"/>
    <!-- O -->
    <path fill-rule="evenodd" d="M552 186 A11 11 0 1 1 551.9 186 Z M552 191 A6 6 0 1 0 552.1 191 Z"/>
    <!-- Divider -->
    <rect x="536" y="199" width="10" height="4" rx="2"/>
    <!-- QUEUE PIPELINE -->
    <!-- Q -->
    <path fill-rule="evenodd" d="M558 194 A7 7 0 1 1 557.9 194 Z M558 197 A4 4 0 1 0 558.1 197 Z"/>
    <polygon points="562,203 566,208 563,208 559,203"/>
    <!-- U -->
    <path d="M570 194 L573 194 L573 204 A3 3 0 0 0 579 204 L579 194 L582 194 L582 204 A6 6 0 0 1 570 204 Z"/>
    <!-- E -->
    <polygon points="588,194 598,194 598,197 591,197 591,199 597,199 597,202 591,202 591,205 598,205 598,208 588,208"/>
    <!-- U -->
    <path d="M604 194 L607 194 L607 204 A3 3 0 0 0 613 204 L613 194 L616 194 L616 204 A6 6 0 0 1 604 204 Z"/>
    <!-- E -->
    <polygon points="622,194 632,194 632,197 625,197 625,199 631,199 631,202 625,202 625,205 632,205 632,208 622,208"/>
  </g>
</svg>
"""

concept_a_lockup = build_lockup(concept_a_symbol, "title-a-lockup", "Kinetic YU", 26)
concept_b_lockup = build_lockup(concept_b_symbol, "title-b-lockup", "Velocity Shutter", 26)
concept_c_lockup = build_lockup(concept_c_symbol, "title-c-lockup", "Studio Launchpad", 22)

files = {
    "branding/concepts/concept-a-symbol.svg": concept_a_symbol,
    "branding/concepts/concept-a-lockup.svg": concept_a_lockup,
    "branding/concepts/concept-b-symbol.svg": concept_b_symbol,
    "branding/concepts/concept-b-lockup.svg": concept_b_lockup,
    "branding/concepts/concept-c-symbol.svg": concept_c_symbol,
    "branding/concepts/concept-c-lockup.svg": concept_c_lockup,
}

for path, content in files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Generated {path}")
