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

def test_all_themes_resolve():
    for name in md2pdf.THEMES:
        c = md2pdf.resolve_theme(name, {})
        assert "accent" in c and "dark" in c and "muted" in c


def test_custom_theme_uses_style_data():
    data = {"custom_accent": "#FF0000", "custom_dark": "#000000", "custom_muted": "#CCCCCC"}
    c = md2pdf.resolve_theme("custom", data)
    assert abs(c["accent"].red - 1.0) < 0.01


def test_unknown_theme_falls_back_to_navy():
    c = md2pdf.resolve_theme("nonexistent", {})
    navy = md2pdf.resolve_theme("navy", {})
    assert c["accent"].hexval() == navy["accent"].hexval()


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


def test_inline_italic():
    assert "<i>world</i>" in md2pdf.inline_to_xml("*world*", "CustomFont")


def test_inline_code():
    result = md2pdf.inline_to_xml("`code`", "CustomFont")
    assert "Courier" in result and "code" in result


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


def test_parse_paragraph():
    tokens = md2pdf.parse_markdown("Hello world")
    assert any(t["type"] == "para" and "Hello" in t["text"] for t in tokens)


def test_parse_bullet_list():
    tokens = md2pdf.parse_markdown("- item one\n- item two")
    bullets = [t for t in tokens if t["type"] == "bullet"]
    assert len(bullets) == 2
    assert bullets[0]["text"] == "item one"


def test_parse_ordered_list():
    tokens = md2pdf.parse_markdown("1. first\n2. second")
    ordered = [t for t in tokens if t["type"] == "ordered"]
    assert len(ordered) == 2


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


def test_parse_hr():
    tokens = md2pdf.parse_markdown("---")
    assert any(t["type"] == "hr" for t in tokens)


def test_parse_table():
    md = "| A | B |\n|---|---|\n| 1 | 2 |"
    tokens = md2pdf.parse_markdown(md)
    assert any(t["type"] == "table" for t in tokens)


def test_parse_blank_line():
    tokens = md2pdf.parse_markdown("a\n\nb")
    assert any(t["type"] == "blank" for t in tokens)


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
    input_md = tmp_path / "test.md"
    output_pdf = tmp_path / "test_nocover.pdf"
    input_md.write_text("# Title\n\nBody text.", encoding="utf-8")
    style_yaml = tmp_path / "style.yaml"
    style_yaml.write_text("cover: false\nheader: false\nfooter: false\n")

    md2pdf.convert(str(input_md), str(output_pdf), BUNDLED_FONT,
                   theme_name="minimal", style_path=str(style_yaml))
    assert output_pdf.exists()


def test_convert_letter_size(tmp_path):
    input_md = tmp_path / "test.md"
    output_pdf = tmp_path / "test_letter.pdf"
    input_md.write_text("# Letter\n\nContent.", encoding="utf-8")
    style_yaml = tmp_path / "style.yaml"
    style_yaml.write_text("page_size: Letter\ncover: false\n")

    md2pdf.convert(str(input_md), str(output_pdf), BUNDLED_FONT,
                   style_path=str(style_yaml))
    assert output_pdf.exists()


def test_convert_chinese_content(tmp_path):
    input_md = tmp_path / "chinese.md"
    output_pdf = tmp_path / "chinese.pdf"
    input_md.write_text(
        "# 数字生命调研报告\n\n## 简介\n\n这是一份关于**数字生命**的调研报告。\n\n- 第一点\n- 第二点\n",
        encoding="utf-8",
    )
    md2pdf.convert(str(input_md), str(output_pdf), BUNDLED_FONT, theme_name="navy")
    assert output_pdf.exists() and output_pdf.stat().st_size > 1000
