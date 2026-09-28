# YouTube Uploader Pro — Brand Identity Guidelines

> Production identity system, specifications, color codes, and usage rules.

---

## 1. The Logo & Brand Mark

### Concept: "The Kinetic YU"
The YouTube Uploader Pro brand mark is a monolithic geometric monogram combining:
- **`Y` (YouTube)**: The upper angled arms funnel down to an arrow apex.
- **`U` (Uploader / Queue Tray)**: The outer structural U-chassis represents the local batch queue and pipeline.
- **Ascending Velocity Vector**: A supersonic upward playhead that replaces the passive horizontal play triangle with active automated upload acceleration.

```
       ▲  [Launch Vector]
     /   \
    |  ▲  |  [Y + Upload Vector]
    \     /
     \___/   [U-Chassis / Queue Tray]
```

### Master Variations
| File | Format | Optimal Context |
|---|---|---|
| [`branding/master/yt-uploader-symbol.svg`](file:///Users/mac/Downloads/youtube_uploader_selenium-master/branding/master/yt-uploader-symbol.svg) | Full Gradient | Primary digital avatar, marketing headers, splash screens |
| [`branding/master/yt-uploader-symbol-flat.svg`](file:///Users/mac/Downloads/youtube_uploader_selenium-master/branding/master/yt-uploader-symbol-flat.svg) | Solid 2-Color | Silkscreen, print, embroidery, flat UI badges |
| [`branding/master/yt-uploader-symbol-black.svg`](file:///Users/mac/Downloads/youtube_uploader_selenium-master/branding/master/yt-uploader-symbol-black.svg) | 1-Color Black | Black & white documents, receipts, thermal print |
| [`branding/master/yt-uploader-symbol-white.svg`](file:///Users/mac/Downloads/youtube_uploader_selenium-master/branding/master/yt-uploader-symbol-white.svg) | 1-Color White | Dark backgrounds, video watermarks, dark console containers |
| [`branding/master/yt-uploader-symbol-crimson.svg`](file:///Users/mac/Downloads/youtube_uploader_selenium-master/branding/master/yt-uploader-symbol-crimson.svg) | Single Brand Ink | Single-pass red printing, alerts, monochrome badges |
| [`branding/master/yt-uploader-app-icon.svg`](file:///Users/mac/Downloads/youtube_uploader_selenium-master/branding/master/yt-uploader-app-icon.svg) | Squircle Tile | macOS Dock, iOS home screen, desktop application launcher |
| [`branding/master/yt-uploader-favicon.svg`](file:///Users/mac/Downloads/youtube_uploader_selenium-master/branding/master/yt-uploader-favicon.svg) | 32px Micro-Cut | Browser tab icon, PWA icon, bookmarks |
| [`branding/master/yt-uploader-lockup-dark.svg`](file:///Users/mac/Downloads/youtube_uploader_selenium-master/branding/master/yt-uploader-lockup-dark.svg) | Horizontal Dark | Dark dashboard sidebar, terminal banner, README header |
| [`branding/master/yt-uploader-lockup-light.svg`](file:///Users/mac/Downloads/youtube_uploader_selenium-master/branding/master/yt-uploader-lockup-light.svg) | Horizontal Light | Documentation, whitepapers, executive reports |
| [`branding/master/yt-uploader-lockup-stacked.svg`](file:///Users/mac/Downloads/youtube_uploader_selenium-master/branding/master/yt-uploader-lockup-stacked.svg) | Square Lockup | Social profile headers, square cards, conference badges |

---

## 2. Clear Space & Minimum Sizes

### Clear Space Rule
Maintain a clear margin around the symbol and lockups equal to **$X$**, where **$X$** is the width of the central arrow stem ($32\text{ units}$ on the $256\text{ canvas}$, or $\approx 12.5\%$ of symbol size). No text, borders, or graphic elements should penetrate this perimeter.

```
       +-----------------------+
       |           X           |
       |     +-----------+     |
       |  X  |  SYMBOL   |  X  |
       |     +-----------+     |
       |           X           |
       +-----------------------+
```

### Minimum Reproduction Limits
| Format | Digital Screens | Print Reproduction |
|---|---|---|
| **Horizontal Lockup** | $160\text{ px}$ width | $38\text{ mm}$ width |
| **Stacked Lockup** | $96\text{ px}$ width | $24\text{ mm}$ width |
| **Master Symbol** | $24\text{ px}$ height | $6.5\text{ mm}$ height |
| **Favicon (`yt-uploader-favicon.svg`)** | $16\text{ px}$ height | N/A |

---

## 3. Official Color Palette

| Swatch | Name | HEX | RGB | HSL | Role |
|---|---|---|---|---|---|
| 🟥 | **Electric Crimson** | `#FF0033` | `255, 0, 51` | `348°, 100%, 50%` | Primary Brand Color (Ascending Vector & YT Accent) |
| 🔴 | **Crimson Hover** | `#FF2A55` | `255, 42, 85` | `348°, 100%, 58%` | Interactive Glow / Gradient Highlight |
| 🟦 | **Cyber Cyan** | `#00F0FF` | `0, 240, 255` | `184°, 100%, 50%` | Secondary Accent (Queue Status & Live Beacon) |
| ⬛ | **Obsidian Primary** | `#07090E` | `7, 9, 14` | `223°, 33%, 4%` | Command Console Background / Chassis |
| 🔲 | **Obsidian Surface** | `#0D121F` | `13, 18, 31` | `223°, 41%, 9%` | Sidebar & Card Foundation |
| ⬜ | **Pure Snow** | `#FFFFFF` | `255, 255, 255` | `0°, 0%, 100%` | Inverted Monogram & High-Contrast Typography |
| 🔘 | **Slate Subtitle** | `#94A3B8` | `148, 163, 184`| `215°, 20%, 65%` | Secondary Typography & Structural Outlines |

### Approved Combinations
- **Dark Mode Primary**: Symbol on `#07090E` or `#0D121F` (Preferred).
- **Light Mode Primary**: Symbol on `#FFFFFF` or `#F8FAFC`.
- **Pure Reversed**: White symbol on `#FF0033` (as used in app icon / buttons).
- **One-Colour Monochrome**: Solid black on white, or solid white on black.

---

## 4. Typography

- **Brand Wordmark**: Custom engineered geometric letterforms (45° angle cuts, 75° leg slopes on `A`, consistent 20px stem widths).
- **Interface Primary Font**: **Plus Jakarta Sans** (Weights: 400, 600, 700, 800)
- **Monospace / Console Font**: **JetBrains Mono** (Weights: 400, 600, 700)
- **Fallback Stack**: `system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif`

---

## 5. Usage Rules & Prohibitions (Don'ts)

- ❌ **Do not warp, stretch, or alter aspect ratios.**
- ❌ **Do not rotate the mark off-axis** (the upward velocity must always point 90° North).
- ❌ **Do not place the full-color mark on low-contrast backgrounds** (use `yt-uploader-symbol-white.svg` on dark images or `#FF0033` backdrops).
- ❌ **Do not add drop shadows, outer glows, or bevels** that alter vector silhouettes.
- ❌ **Do not substitute the master monogram with stock YouTube icons or generic cloud-upload graphics.**
