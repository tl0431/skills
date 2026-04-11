"""Tests for md2pdf.py — theme system, markdown parser, PDF builder, CLI."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import md2pdf

BUNDLED_FONT = str(Path(__file__).parent.parent / "assets" / "fonts" / "NotoSansSC-Regular.ttf")


# ---------------------------------------------------------------------------
# Theme system
# ---------------------------------------------------------------------------

DISPLAYED_THEMES = ["navy", "minimal", "warm", "slate", "gold", "midnight"]


def test_all_themes_resolve():
    for name in md2pdf.THEMES:
        c = md2pdf.resolve_theme(name, {})
        assert "accent" in c and "dark" in c and "muted" in c


def test_themes_list_contains_only_displayed_themes():
    """THEMES_LIST must only include the 6 selected themes."""
    keys = [key for key, _, _ in md2pdf.THEMES_LIST]
    assert set(keys) == set(DISPLAYED_THEMES), f"Expected {DISPLAYED_THEMES}, got {keys}"


def test_themes_list_has_six_entries():
    """THEMES_LIST must have exactly 6 entries."""
    assert len(md2pdf.THEMES_LIST) == 6


def test_print_theme_selector_uses_box_style(capsys):
    """print_theme_selector output must contain box-drawing characters."""
    md2pdf.print_theme_selector()
    out = capsys.readouterr().out
    assert "┌" in out or "│" in out, "Expected box-drawing characters in theme selector"


def test_print_theme_selector_fits_in_ten_lines(capsys):
    """Theme selector output must be ≤ 10 lines to avoid UI folding."""
    md2pdf.print_theme_selector()
    out = capsys.readouterr().out
    lines = [l for l in out.splitlines() if l.strip()]
    assert len(lines) <= 10, f"Too many lines: {len(lines)}"


def test_custom_theme_uses_style_data():
    data = {"custom_accent": "#FF0000", "custom_dark": "#000000", "custom_muted": "#CCCCCC"}
    c = md2pdf.resolve_theme("custom", data)
    assert abs(c["accent"].red - 1.0) < 0.01


def test_unknown_theme_falls_back_to_navy():
    c = md2pdf.resolve_theme("nonexistent", {})
    navy = md2pdf.resolve_theme("navy", {})
    assert c["accent"].hexval() == navy["accent"].hexval()


def test_resolve_theme_returns_heading_color():
    """All themes must return heading_color key."""
    for name in list(md2pdf.THEMES.keys()) + ["navy", "custom"]:
        c = md2pdf.resolve_theme(name, {})
        assert "heading_color" in c, f"Missing heading_color for theme {name}"
        assert "separator_color" in c
        assert "table_header_bg" in c
        assert "table_header_fg" in c


def test_existing_themes_heading_color_equals_accent():
    """For non-github themes, heading_color must equal accent (backward compat)."""
    for name in ["navy", "minimal", "warm", "slate", "gold", "midnight"]:
        c = md2pdf.resolve_theme(name, {})
        assert c["heading_color"].hexval() == c["accent"].hexval(), \
            f"{name}: heading_color {c['heading_color'].hexval()} != accent {c['accent'].hexval()}"


def test_github_theme_heading_color_is_dark():
    """GitHub theme: heading_color must equal dark (#24292e), not accent (#0366d6)."""
    c = md2pdf.resolve_theme("github", {})
    assert c["heading_color"].hexval() == c["dark"].hexval()
    # accent is blue, heading is dark — they must differ
    assert c["heading_color"].hexval() != c["accent"].hexval()


def test_github_theme_separator_is_light_gray():
    """GitHub theme: separator_color must be #eaecef (light gray)."""
    c = md2pdf.resolve_theme("github", {})
    # #eaecef = rgb(234, 236, 239) ≈ Color(0.918, 0.925, 0.937)
    assert c["separator_color"].red > 0.9
    assert c["separator_color"].green > 0.9
    assert c["separator_color"].blue > 0.9


def test_github_theme_table_header_is_light_bg_dark_fg():
    """GitHub theme: table header must be light background with dark text."""
    c = md2pdf.resolve_theme("github", {})
    # Light background: all channels > 0.9
    bg = c["table_header_bg"]
    assert bg.red > 0.9 and bg.green > 0.9 and bg.blue > 0.9
    # Dark foreground: all channels < 0.2
    fg = c["table_header_fg"]
    assert fg.red < 0.2 and fg.green < 0.2 and fg.blue < 0.2


def test_hex_to_color_white():
    c = md2pdf.hex_to_color("#FFFFFF")
    assert c.red == 1.0 and c.green == 1.0 and c.blue == 1.0


def test_hex_to_color_black():
    c = md2pdf.hex_to_color("#000000")
    assert c.red == 0.0 and c.green == 0.0 and c.blue == 0.0


# ---------------------------------------------------------------------------
# Inline markdown → XML
# ---------------------------------------------------------------------------

def test_inline_bold():
    assert "<b>hello</b>" in md2pdf.inline_to_xml("**hello**", "CustomFont")


def test_inline_bold_underscore():
    assert "<b>hello</b>" in md2pdf.inline_to_xml("__hello__", "CustomFont")


def test_inline_italic():
    assert "<i>world</i>" in md2pdf.inline_to_xml("*world*", "CustomFont")


def test_inline_italic_underscore():
    assert "<i>world</i>" in md2pdf.inline_to_xml("_world_", "CustomFont")


def test_inline_bold_italic():
    result = md2pdf.inline_to_xml("***hi***", "CustomFont")
    assert "<b>" in result and "<i>" in result and "hi" in result


def test_inline_strikethrough():
    """~~text~~ must render with ReportLab strike tag."""
    result = md2pdf.inline_to_xml("~~gone~~", "CustomFont")
    assert "<strike>gone</strike>" in result


def test_inline_image_shows_alt_text():
    """![alt](url) must render as [图片: alt] placeholder, not the URL."""
    result = md2pdf.inline_to_xml("![示意图](img.png)", "CustomFont")
    assert "示意图" in result
    assert "img.png" not in result


def test_inline_code():
    result = md2pdf.inline_to_xml("`code`", "CustomFont")
    assert "CustomFont" in result and "code" in result


def test_code_block_style_uses_font_name():
    """code_block style must use the passed font, not hardcoded Courier."""
    md2pdf.register_font(BUNDLED_FONT, "CodeTestFont")
    colors = md2pdf.resolve_theme("navy", {})
    styles = md2pdf.build_styles("CodeTestFont", colors)
    assert styles["code_block"].fontName == "CodeTestFont"
    assert styles["code_inline"].fontName == "CodeTestFont"


def test_chinese_in_code_block(tmp_path):
    """Chinese text inside a fenced code block must not cause an error."""
    input_md = tmp_path / "test.md"
    output_pdf = tmp_path / "test.pdf"
    input_md.write_text(
        "# Test\n\n```\nYear 1-2 启动阶段\n    GPU 算力采购\n```\n",
        encoding="utf-8",
    )
    result = md2pdf.convert(str(input_md), str(output_pdf), BUNDLED_FONT, theme_name="navy")
    assert output_pdf.exists() and output_pdf.stat().st_size > 500


def test_inline_link_shows_text_only():
    result = md2pdf.inline_to_xml("[click here](https://example.com)", "CustomFont")
    assert "click here" in result
    assert "https" not in result


def test_inline_escapes_xml_chars():
    result = md2pdf.inline_to_xml("a & b < c > d", "CustomFont")
    assert "&amp;" in result
    assert "&lt;" in result
    assert "&gt;" in result


# ---------------------------------------------------------------------------
# Markdown parser
# ---------------------------------------------------------------------------

def test_parse_headings():
    tokens = md2pdf.parse_markdown("# H1\n## H2\n### H3")
    types = [t["type"] for t in tokens if t["type"] != "blank"]
    assert types == ["h1", "h2", "h3"]


def test_parse_h4_to_h6():
    """Parser must recognize h4, h5, h6."""
    tokens = md2pdf.parse_markdown("#### H4\n##### H5\n###### H6")
    types = [t["type"] for t in tokens if t["type"] != "blank"]
    assert types == ["h4", "h5", "h6"]


def test_h5_h6_render_to_flowables():
    """h5 and h6 tokens must produce non-empty flowables (not silently dropped)."""
    md2pdf.register_font(BUNDLED_FONT, "H56TestFont")
    colors = md2pdf.resolve_theme("navy", {})
    styles = md2pdf.build_styles("H56TestFont", colors)
    tokens = md2pdf.parse_markdown("##### Heading 5\n###### Heading 6")
    tokens = [t for t in tokens if t["type"] != "blank"]
    flowables = md2pdf.tokens_to_flowables(tokens, styles, colors, "H56TestFont")
    assert len(flowables) == 2, f"Expected 2 flowables for h5+h6, got {len(flowables)}"


def test_parse_paragraph():
    tokens = md2pdf.parse_markdown("Hello world")
    assert any(t["type"] == "para" and "Hello" in t["text"] for t in tokens)


def test_parse_bullet_list():
    tokens = md2pdf.parse_markdown("- item one\n- item two")
    bullets = [t for t in tokens if t["type"] == "bullet"]
    assert len(bullets) == 2
    assert bullets[0]["text"] == "item one"


def test_parse_nested_bullet_list():
    """Nested bullet items must have indent=1."""
    tokens = md2pdf.parse_markdown("- parent\n  - child")
    bullets = [t for t in tokens if t["type"] == "bullet"]
    assert len(bullets) == 2
    assert bullets[0]["indent"] == 0
    assert bullets[1]["indent"] == 1


def test_parse_ordered_list():
    tokens = md2pdf.parse_markdown("1. first\n2. second")
    ordered = [t for t in tokens if t["type"] == "ordered"]
    assert len(ordered) == 2


def test_parse_nested_ordered_list():
    """Nested ordered items must have indent=1."""
    tokens = md2pdf.parse_markdown("1. parent\n   1. child")
    ordered = [t for t in tokens if t["type"] == "ordered"]
    assert len(ordered) == 2
    assert ordered[0]["indent"] == 0
    assert ordered[1]["indent"] == 1


def test_parse_ordered_list_counter_reset():
    """Ordered list counter must restart at 1 after intervening paragraph."""
    tokens = md2pdf.parse_markdown("1. first\n2. second\n\nParagraph.\n\n1. restart")
    ordered = [t for t in tokens if t["type"] == "ordered"]
    assert len(ordered) == 3
    # Verify the rendered numbers reset to 1 after the paragraph break
    md2pdf.register_font(BUNDLED_FONT, "CounterTestFont")
    colors_ = md2pdf.resolve_theme("navy", {})
    styles = md2pdf.build_styles("CounterTestFont", colors_)
    from reportlab.platypus import Paragraph as RLPara
    flowables = md2pdf.tokens_to_flowables(tokens, styles, colors_, "CounterTestFont")
    texts = [f.text for f in flowables if isinstance(f, RLPara) and f.text[:2] in ("1.", "2.", "3.")]
    assert texts == ["1. first", "2. second", "1. restart"], f"Got: {texts}"


def test_parse_code_block():
    md = "```python\nprint('hi')\n```"
    tokens = md2pdf.parse_markdown(md)
    code = [t for t in tokens if t["type"] == "code_block"]
    assert len(code) == 1
    assert "print" in code[0]["text"]


def test_parse_blockquote():
    tokens = md2pdf.parse_markdown("> some quote")
    bq = [t for t in tokens if t["type"] == "blockquote"]
    assert len(bq) == 1
    assert "some quote" in bq[0]["text"]


def test_parse_multiline_blockquote():
    """Each > line becomes a separate blockquote token."""
    tokens = md2pdf.parse_markdown("> line one\n> line two")
    bq = [t for t in tokens if t["type"] == "blockquote"]
    assert len(bq) == 2
    assert "line one" in bq[0]["text"]
    assert "line two" in bq[1]["text"]


def test_parse_hr():
    tokens = md2pdf.parse_markdown("---")
    assert any(t["type"] == "hr" for t in tokens)


def test_parse_table():
    md = "| A | B |\n|---|---|\n| 1 | 2 |"
    tokens = md2pdf.parse_markdown(md)
    assert any(t["type"] == "table" for t in tokens)


def test_build_table_github_uses_light_header():
    """_build_table with github theme must use light header background, not blue."""
    md2pdf.register_font(BUNDLED_FONT, "TblGithubFont")
    colors_github = md2pdf.resolve_theme("github", {})
    styles = md2pdf.build_styles("TblGithubFont", colors_github)
    lines = ["| A | B |", "|---|---|", "| 1 | 2 |"]
    tbl = md2pdf._build_table(lines, styles, colors_github, "TblGithubFont")
    assert tbl is not None
    # Find the BACKGROUND command for row 0 in the TableStyle
    bg_cmd = None
    for cmd in tbl._bkgrndcmds:
        if cmd[0] == "BACKGROUND" and cmd[1] == (0, 0) and cmd[2] == (-1, 0):
            bg_cmd = cmd
    assert bg_cmd is not None, "No BACKGROUND command found for header row"
    header_bg = bg_cmd[3]
    # GitHub table_header_bg is #f6f8fa (light) — all channels > 0.9
    assert header_bg.red > 0.9 and header_bg.green > 0.9 and header_bg.blue > 0.9, \
        f"Expected light header bg, got {header_bg}"


def test_parse_table_multiple_data_rows():
    """Table with 3 data rows must produce token with header + 3 rows (4 total, minus separator)."""
    md = "| A | B |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |\n| 5 | 6 |"
    tokens = md2pdf.parse_markdown(md)
    table_tokens = [t for t in tokens if t["type"] == "table"]
    assert len(table_tokens) == 1
    colors = md2pdf.resolve_theme("navy", {})
    styles = md2pdf.build_styles("Helvetica", colors)
    tbl = md2pdf._build_table(table_tokens[0]["lines"], styles, colors, "Helvetica")
    assert tbl is not None
    assert len(tbl._cellvalues) == 4  # header + 3 data rows


def test_parse_image_token():
    """![alt](url) must produce an 'image' token with alt text."""
    tokens = md2pdf.parse_markdown("![示意图](img.png)")
    img = [t for t in tokens if t["type"] == "image"]
    assert len(img) == 1
    assert img[0]["alt"] == "示意图"


def test_image_flowable_shows_alt():
    """Image token → flowable must show alt text, never the URL."""
    md2pdf.register_font(BUNDLED_FONT, "ImgFlowFont")
    colors_ = md2pdf.resolve_theme("navy", {})
    styles = md2pdf.build_styles("ImgFlowFont", colors_)
    tokens = [{"type": "image", "alt": "示意图", "src": "img.png"}]
    flowables = md2pdf.tokens_to_flowables(tokens, styles, colors_, "ImgFlowFont")
    assert len(flowables) == 1
    assert "示意图" in flowables[0].text
    assert "img.png" not in flowables[0].text


def test_image_flowable_empty_alt():
    """Image token with empty alt must render [图片], never the src filename."""
    md2pdf.register_font(BUNDLED_FONT, "ImgEmptyFont")
    colors_ = md2pdf.resolve_theme("navy", {})
    styles = md2pdf.build_styles("ImgEmptyFont", colors_)
    tokens = [{"type": "image", "alt": "", "src": "secret/path.png"}]
    flowables = md2pdf.tokens_to_flowables(tokens, styles, colors_, "ImgEmptyFont")
    assert len(flowables) == 1
    assert "secret" not in flowables[0].text
    assert "path.png" not in flowables[0].text


def test_parse_blank_line():
    tokens = md2pdf.parse_markdown("a\n\nb")
    assert any(t["type"] == "blank" for t in tokens)


def test_parse_table_separator():
    """Separator row |---|---| must be skipped; table should have header + 1 data row."""
    md = "| A | B |\n|---|---|\n| 1 | 2 |"
    tokens = md2pdf.parse_markdown(md)
    table_tokens = [t for t in tokens if t["type"] == "table"]
    assert len(table_tokens) == 1
    # Register a font so build_styles works
    colors = md2pdf.resolve_theme("navy", {})
    styles = md2pdf.build_styles("Helvetica", colors)
    # _build_table must skip the separator and return exactly 2 rows
    tbl = md2pdf._build_table(table_tokens[0]["lines"], styles, colors, "Helvetica")
    assert tbl is not None
    # Table._cellvalues holds the row data
    assert len(tbl._cellvalues) == 2


# ---------------------------------------------------------------------------
# Font registration
# ---------------------------------------------------------------------------

def test_register_font_bundled():
    name = md2pdf.register_font(BUNDLED_FONT, "TestNoto")
    assert name == "TestNoto"


def test_register_font_missing_raises():
    with pytest.raises(FileNotFoundError):
        md2pdf.register_font("/nonexistent/font.ttf", "BadFont")


# ---------------------------------------------------------------------------
# Style builder
# ---------------------------------------------------------------------------

def test_build_styles_has_required_keys():
    md2pdf.register_font(BUNDLED_FONT, "StyleTestFont")
    colors = md2pdf.resolve_theme("navy", {})
    styles = md2pdf.build_styles("StyleTestFont", colors)
    for key in ("h1", "h2", "h3", "body", "bullet", "code_block", "blockquote"):
        assert key in styles


def test_build_styles_h1_uses_heading_color():
    """h1/h2/h3 styles must use heading_color, not accent."""
    md2pdf.register_font(BUNDLED_FONT, "HeadColorFont")
    colors_github = md2pdf.resolve_theme("github", {})
    styles = md2pdf.build_styles("HeadColorFont", colors_github)
    # GitHub: heading_color == dark, accent == blue — they differ
    assert styles["h1"].textColor == colors_github["heading_color"]
    assert styles["h1"].textColor != colors_github["accent"]
    assert styles["h2"].textColor == colors_github["heading_color"]
    assert styles["h3"].textColor == colors_github["heading_color"]


def test_github_theme_has_code_color():
    """github theme must have code_color key (blue for inline code)."""
    c = md2pdf.resolve_theme("github", {})
    assert "code_color" in c
    # GitHub inline code is #0550ae — blue channel dominant
    assert c["code_color"].blue > 0.5
    assert c["code_color"].red < 0.3


def test_build_styles_code_inline_uses_code_color():
    """code_inline style must use theme code_color for github theme."""
    md2pdf.register_font(BUNDLED_FONT, "CodeColorFont")
    colors_github = md2pdf.resolve_theme("github", {})
    styles = md2pdf.build_styles("CodeColorFont", colors_github)
    assert styles["code_inline"].textColor == colors_github["code_color"]


def test_existing_themes_code_color_equals_dark():
    """Non-github themes: code_color must equal dark (backward compat)."""
    for name in ["navy", "minimal", "warm"]:
        c = md2pdf.resolve_theme(name, {})
        assert c["code_color"].hexval() == c["dark"].hexval(), \
            f"{name}: code_color should equal dark"


def test_tokens_to_flowables_uses_separator_color_for_h1_hr():
    """HRFlowable after h1/h2 must use separator_color, not accent."""
    from reportlab.platypus import HRFlowable as RLHRFlowable
    md2pdf.register_font(BUNDLED_FONT, "SepColorFont")
    colors_github = md2pdf.resolve_theme("github", {})
    styles = md2pdf.build_styles("SepColorFont", colors_github)
    tokens = [{"type": "h1", "text": "Title"}]
    flowables = md2pdf.tokens_to_flowables(tokens, styles, colors_github, "SepColorFont")
    hr_flowables = [f for f in flowables if isinstance(f, RLHRFlowable)]
    assert len(hr_flowables) == 1
    # separator_color for github is #eaecef (light gray), accent is #0366d6 (blue)
    assert hr_flowables[0].color == colors_github["separator_color"]
    assert hr_flowables[0].color != colors_github["accent"]


# ---------------------------------------------------------------------------
# Full conversion (integration)
# ---------------------------------------------------------------------------

SAMPLE_MD = """# Test Document

## Introduction

This is a **bold** and *italic* paragraph with `inline code`.

### Features

- Item one
- Item two
  - Nested item

1. First
2. Second

> A blockquote here

```python
def hello():
    print("world")
```

---

| Column A | Column B |
|----------|----------|
| Cell 1   | Cell 2   |
"""


def test_convert_produces_pdf(tmp_path):
    input_md = tmp_path / "test.md"
    output_pdf = tmp_path / "test.pdf"
    input_md.write_text(SAMPLE_MD, encoding="utf-8")

    result = md2pdf.convert(
        input_path=str(input_md),
        output_path=str(output_pdf),
        font_path=BUNDLED_FONT,
        theme_name="navy",
    )
    assert Path(result).exists()
    assert Path(result).stat().st_size > 1000


def test_convert_all_themes(tmp_path):
    input_md = tmp_path / "test.md"
    input_md.write_text("# Hello\n\nWorld.", encoding="utf-8")
    for theme in md2pdf.THEMES:
        out = tmp_path / f"test_{theme}.pdf"
        md2pdf.convert(str(input_md), str(out), BUNDLED_FONT, theme)
        assert out.exists() and out.stat().st_size > 500


def test_convert_no_cover(tmp_path):
    """cover: false in yaml should skip the cover page."""
    input_md = tmp_path / "test.md"
    output_pdf = tmp_path / "test_nocover.pdf"
    input_md.write_text("# Title\n\nBody text.", encoding="utf-8")
    style_yaml = tmp_path / "style.yaml"
    style_yaml.write_text("cover: false\nheader: false\nfooter: false\n")

    md2pdf.convert(str(input_md), str(output_pdf), BUNDLED_FONT,
                   theme_name="minimal", style_path=str(style_yaml))
    assert output_pdf.exists()


def test_convert_no_cover_param_overrides_yaml(tmp_path):
    """no_cover=True flag must override cover:true in yaml."""
    input_md = tmp_path / "test.md"
    input_md.write_text("# Title\n\n" + "Para.\n\n" * 5, encoding="utf-8")
    style_yaml = tmp_path / "style.yaml"
    style_yaml.write_text("cover: true\n")

    out_with = tmp_path / "with_cover.pdf"
    out_without = tmp_path / "no_cover.pdf"

    md2pdf.convert(str(input_md), str(out_with), BUNDLED_FONT,
                   style_path=str(style_yaml), no_cover=False)
    md2pdf.convert(str(input_md), str(out_without), BUNDLED_FONT,
                   style_path=str(style_yaml), no_cover=True)

    # no_cover=True should produce a smaller (or equal) file than with cover
    assert out_with.exists() and out_without.exists()
    # Cover adds at least a PageBreak + title text, so with_cover >= no_cover
    assert out_with.stat().st_size >= out_without.stat().st_size


def test_convert_letter_size(tmp_path):
    input_md = tmp_path / "test.md"
    output_pdf = tmp_path / "test_letter.pdf"
    input_md.write_text("# Letter\n\nContent.", encoding="utf-8")
    style_yaml = tmp_path / "style.yaml"
    style_yaml.write_text("page_size: Letter\ncover: false\n")

    md2pdf.convert(str(input_md), str(output_pdf), BUNDLED_FONT,
                   style_path=str(style_yaml))
    assert output_pdf.exists()


def test_convert_github_theme(tmp_path):
    """Full PDF conversion with github theme must succeed and produce a valid file."""
    input_md = tmp_path / "github_test.md"
    output_pdf = tmp_path / "github_test.pdf"
    input_md.write_text(
        "# GitHub Style\n\n## Subheading\n\nBody text with **bold** and *italic*.\n\n"
        "| Col A | Col B |\n|-------|-------|\n| Cell 1 | Cell 2 |\n\n"
        "> A blockquote\n\n```python\nprint('hello')\n```\n\n"
        "- Bullet one\n- Bullet two\n\n---\n\n### H3 heading\n",
        encoding="utf-8",
    )
    result = md2pdf.convert(
        input_path=str(input_md),
        output_path=str(output_pdf),
        font_path=BUNDLED_FONT,
        theme_name="github",
    )
    assert output_pdf.exists()
    assert output_pdf.stat().st_size > 2000


def test_convert_chinese_content(tmp_path):
    input_md = tmp_path / "chinese.md"
    output_pdf = tmp_path / "chinese.pdf"
    input_md.write_text(
        "# 数字生命调研报告\n\n## 简介\n\n这是一份关于**数字生命**的调研报告。\n\n- 第一点\n- 第二点\n",
        encoding="utf-8",
    )
    md2pdf.convert(str(input_md), str(output_pdf), BUNDLED_FONT, theme_name="navy")
    assert output_pdf.exists() and output_pdf.stat().st_size > 1000


# ---------------------------------------------------------------------------
# CLI custom theme args
# ---------------------------------------------------------------------------

def test_cli_custom_theme(tmp_path):
    """--theme custom with --accent/--dark/--muted should produce a valid PDF."""
    import subprocess
    input_md = tmp_path / "custom.md"
    output_pdf = tmp_path / "custom.pdf"
    input_md.write_text("# Custom Theme\n\nHello world.", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable, str(Path(__file__).parent / "md2pdf.py"),
            "--input",  str(input_md),
            "--output", str(output_pdf),
            "--font",   BUNDLED_FONT,
            "--theme",  "custom",
            "--accent", "#FF0000",
            "--dark",   "#000000",
            "--muted",  "#999999",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"CLI failed:\n{result.stderr}"
    assert output_pdf.exists()
    assert output_pdf.stat().st_size > 500


# ---------------------------------------------------------------------------
# Integration: rich Chinese markdown document
# ---------------------------------------------------------------------------

def test_github_code_block_background_is_f6f8fa():
    """code_block backColor for github theme must be #f6f8fa (all channels > 0.96)."""
    md2pdf.register_font(BUNDLED_FONT, "CodeBgFont")
    colors_github = md2pdf.resolve_theme("github", {})
    styles = md2pdf.build_styles("CodeBgFont", colors_github)
    bg = styles["code_block"].backColor
    assert bg.red > 0.96 and bg.green > 0.96 and bg.blue > 0.96, \
        f"Expected #f6f8fa-ish background, got {bg}"


def test_build_styles_code_block_uses_mono_font():
    """code_block and code_inline must use mono_font_name when provided."""
    md2pdf.register_font(BUNDLED_FONT, "BodyFont2")
    md2pdf.register_font(BUNDLED_FONT, "MonoFont2")
    colors_github = md2pdf.resolve_theme("github", {})
    styles = md2pdf.build_styles("BodyFont2", colors_github, mono_font_name="MonoFont2")
    assert styles["code_block"].fontName == "MonoFont2"
    assert styles["code_inline"].fontName == "MonoFont2"


def test_integration_full_markdown(tmp_path):
    """Build PDF from a rich Chinese markdown document."""
    md_text = """# 数字生命调研报告

## 背景

这是一份**测试文档**，包含中文内容。

### 子章节

- 列表项一
- 列表项二

1. 有序列表一
2. 有序列表二

> 这是一个引用块，用于测试 callout 样式。

| 名称 | 描述 | 状态 |
|------|------|------|
| 项目A | 测试项目 | 进行中 |
| 项目B | 另一个项目 | 完成 |

---

## 结论

文档生成测试完成。
"""
    input_md = tmp_path / "integration_test.md"
    input_md.write_text(md_text, encoding="utf-8")
    out_pdf = str(tmp_path / "integration_test.pdf")

    result = md2pdf.convert(
        input_path=str(input_md),
        output_path=out_pdf,
        font_path=BUNDLED_FONT,
        theme_name="navy",
    )
    assert Path(out_pdf).exists()


def test_blockquote_flowable_is_table_with_left_bar():
    """Blockquote must render as a Table with a LINEBEFORE left border."""
    from reportlab.platypus import Table as RLTable
    md2pdf.register_font(BUNDLED_FONT, "BqFont")
    colors_github = md2pdf.resolve_theme("github", {})
    styles = md2pdf.build_styles("BqFont", colors_github)
    tokens = [{"type": "blockquote", "text": "A quote"}]
    flowables = md2pdf.tokens_to_flowables(tokens, styles, colors_github, "BqFont")
    assert len(flowables) == 1
    assert isinstance(flowables[0], RLTable), \
        f"Expected Table for blockquote, got {type(flowables[0])}"
    # Verify LINEBEFORE command exists with correct thickness and color
    tbl = flowables[0]
    linebefore_cmds = [c for c in tbl._linecmds if c[0] == "LINEBEFORE"]
    assert len(linebefore_cmds) >= 1, "Expected LINEBEFORE command for left bar"
    lb = linebefore_cmds[0]
    assert lb[3] == 4, f"Expected LINEBEFORE thickness=4, got {lb[3]}"
    assert lb[4] == colors_github["blockquote_bar"], \
        f"Expected blockquote_bar color, got {lb[4]}"


def test_table_column_alignment():
    """Table separator :---: must produce ALIGN CENTER, ---: must produce RIGHT."""
    md2pdf.register_font(BUNDLED_FONT, "TblAlignFont")
    colors_n = md2pdf.resolve_theme("navy", {})
    styles = md2pdf.build_styles("TblAlignFont", colors_n)
    lines = ["| L | C | R |", "|:---|:---:|---:|", "| a | b | c |"]
    tbl = md2pdf._build_table(lines, styles, colors_n, "TblAlignFont")
    assert tbl is not None
    # Force layout so _cellStyles is populated
    tbl.wrap(400, 600)
    # row 0 = header, col 1 = CENTER, col 2 = RIGHT
    center_found = tbl._cellStyles[0][1].alignment == "CENTER"
    right_found  = tbl._cellStyles[0][2].alignment == "RIGHT"
    assert center_found, f"Expected CENTER for col 1, got: {tbl._cellStyles[0][1].alignment}"
    assert right_found,  f"Expected RIGHT for col 2, got: {tbl._cellStyles[0][2].alignment}"
