# pdf_style.yaml — Field Reference

## Full schema with defaults

```yaml
# Font cache (auto-populated, do not edit manually)
fonts:
  PingFang SC: /System/Library/Fonts/PingFang.ttc
default_font: PingFang SC

# Theme: navy | forest | minimal | warm | coral | slate | purple | teal | gold | rose | midnight | olive | custom
theme: navy
# Only used when theme: custom:
custom_accent: "#1C3A5E"
custom_dark: "#1A1A2E"
custom_muted: "#888888"

# Page
page_size: A4      # A4 or Letter
margin_cm: 2.5

# Cover
cover: true
cover_title: ""    # defaults to first H1
cover_subtitle: ""
cover_meta: ""     # date, author, etc.

# Header/footer
header: true
footer: true
footer_page_number: true
```

## Theme color reference

| Theme    | Accent    | Dark      | Muted     |
|----------|-----------|-----------|-----------|
| navy     | #1C3A5E   | #1A1A2E   | #888888   |
| forest   | #2D5A27   | #1A2E1A   | #888888   |
| minimal  | #333333   | #111111   | #999999   |
| warm     | #7B4F2E   | #2E1A0E   | #999999   |
| coral    | #C0392B   | #2C1810   | #888888   |
| slate    | #4A5568   | #1A202C   | #888888   |
| purple   | #553C9A   | #1A0E2E   | #888888   |
| teal     | #2C7A7B   | #0E2E2E   | #888888   |
| gold     | #B7791F   | #2E1E0E   | #888888   |
| rose     | #B83280   | #2E0E1E   | #888888   |
| midnight | #2D3748   | #0A0A0A   | #999999   |
| olive    | #556B2F   | #1A2010   | #888888   |

## ANSI theme selector display

When showing the theme selector, print each line with actual ANSI escape codes for background color, followed by spaces, then reset. Example Python code to print the selector:

```python
THEME_ANSI = {
    "navy": "\033[44m", "forest": "\033[42m", "minimal": "\033[100m",
    "warm": "\033[43m", "coral": "\033[41m", "slate": "\033[100m",
    "purple": "\033[45m", "teal": "\033[46m", "gold": "\033[33m",
    "rose": "\033[35m", "midnight": "\033[100m", "olive": "\033[32m",
}
THEMES_LIST = [
    ("navy", "Navy", "深海军蓝，专业商务 / Deep navy, professional"),
    ("forest", "Forest", "深绿，学术自然 / Deep green, academic"),
    ("minimal", "Minimal", "黑白极简 / Black & white minimal"),
    ("warm", "Warm", "暖棕，人文学术 / Warm brown, humanities"),
    ("coral", "Coral", "珊瑚红，活力现代 / Coral red, vibrant"),
    ("slate", "Slate", "石板灰，低调稳重 / Slate grey, understated"),
    ("purple", "Purple", "深紫，科技感 / Deep purple, tech"),
    ("teal", "Teal", "青绿，清新简洁 / Teal, fresh & clean"),
    ("gold", "Gold", "金棕，高端商务 / Gold brown, premium"),
    ("rose", "Rose", "玫瑰粉，轻奢优雅 / Rose pink, elegant"),
    ("midnight", "Midnight", "午夜黑，极简暗色 / Midnight black, dark minimal"),
    ("olive", "Olive", "橄榄绿，自然沉稳 / Olive green, natural"),
]
print("请选择主题 / Select theme:")
for i, (key, name, desc) in enumerate(THEMES_LIST, 1):
    ansi = THEME_ANSI[key]
    print(f" {i:2}  {ansi}      \033[0m  {name:<10} {desc}")
print("  0             Custom      自定义 hex 颜色 / Custom hex colors")
```
