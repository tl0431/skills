#!/usr/bin/env python3
"""Font discovery, caching, and selection for md2pdf."""

import glob
import json
import os
import platform
import sys
from pathlib import Path

import yaml

CHINESE_KEYWORDS = [
    "arial unicode", "pingfang", "yahei", "simsun", "simhei",
    "stheiti", "hiragino", "noto cjk", "notosanscjk", "source han",
    "wenquanyi", "notosanssc", "noto sans sc",
]

SCAN_PATHS = {
    "Darwin": [
        "/Library/Fonts",
        str(Path.home() / "Library/Fonts"),
        "/System/Library/Fonts",
    ],
    "Windows": ["C:\\Windows\\Fonts"],
    "Linux": [
        "/usr/share/fonts",
        str(Path.home() / ".fonts"),
        "/usr/local/share/fonts",
    ],
}

_COMPAT_CACHE: dict = {}  # path -> True/False


# ---------------------------------------------------------------------------
# Font compatibility testing
# ---------------------------------------------------------------------------

def test_font_compatibility(path: str) -> bool:
    """Try registering the font with ReportLab. Returns True if compatible."""
    if path in _COMPAT_CACHE:
        return _COMPAT_CACHE[path]
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont as _TTFont
        test_name = f"_compat_test_{abs(hash(path))}"
        p = Path(path)
        if p.suffix.lower() == ".ttc":
            pdfmetrics.registerFont(_TTFont(test_name, path, subfontIndex=0))
        else:
            pdfmetrics.registerFont(_TTFont(test_name, path))
        _COMPAT_CACHE[path] = True
        return True
    except Exception:
        _COMPAT_CACHE[path] = False
        return False


# ---------------------------------------------------------------------------
# CFF → TTF conversion (for PostScript OTF fonts not natively supported)
# ---------------------------------------------------------------------------

def _convert_cache_dir() -> Path:
    """Return (and create) the directory for converted font files."""
    d = Path.home() / ".cache" / "md2pdf" / "converted"
    try:
        d.mkdir(parents=True, exist_ok=True)
    except (PermissionError, OSError) as e:
        import sys
        print(f"警告 / Warning: cannot create font cache dir {d}: {e}", file=sys.stderr)
        raise
    return d


def convert_cff_to_ttf(src_path: str, subfont_index: int = 0) -> str | None:
    """
    Convert a CFF-based font (OTF or CFF-in-TTC) to a ReportLab-compatible TTF.

    Uses fontTools to:
      1. Extract the target subfont (for TTC files)
      2. Render each glyph into a TrueType glyf table via TTGlyphPointPen
      3. Fix the sfntVersion header so ReportLab recognises it as TrueType

    Returns the path to the converted TTF, or None if conversion fails.
    Converted files are cached in ~/.cache/md2pdf/converted/.
    """
    try:
        from fontTools.ttLib import TTFont, TTCollection
        from fontTools.pens.ttGlyphPen import TTGlyphPointPen
        from fontTools.pens.pointPen import SegmentToPointPen
        from fontTools.pens.recordingPen import RecordingPen
        from fontTools.ttLib.tables._g_l_y_f import table__g_l_y_f, Glyph
        from fontTools.ttLib.tables._l_o_c_a import table__l_o_c_a
    except ImportError:
        return None  # fonttools not available

    stem = Path(src_path).stem
    out_path = str(_convert_cache_dir() / f"{stem}_sub{subfont_index}.ttf")

    if Path(out_path).exists():
        return out_path  # already converted

    try:
        src = src_path.lower()
        if src.endswith(".ttc"):
            col = TTCollection(src_path)
            font = col.fonts[subfont_index]
        else:
            font = TTFont(src_path)

        if "CFF " not in font:
            return None  # not a CFF v1 font; CFF2 variable fonts and TrueType not handled here

        hmtx = font["hmtx"].metrics
        glyph_order = font.getGlyphOrder()
        glyph_set = font.getGlyphSet()

        # Build glyf table from CFF outlines
        glyf_table = table__g_l_y_f()
        glyf_table.glyphs = {}
        glyf_table.glyphOrder = glyph_order

        for gname in glyph_order:
            try:
                ttpen = TTGlyphPointPen(glyf_table, hmtx)
                seg_pen = SegmentToPointPen(ttpen)
                rec = RecordingPen()
                glyph_set[gname].draw(rec)
                rec.replay(seg_pen)
                glyf_table.glyphs[gname] = ttpen.glyph()
            except Exception:
                glyf_table.glyphs[gname] = Glyph()

        # Swap CFF → glyf + loca
        del font["CFF "]
        font["glyf"] = glyf_table
        font["loca"] = table__l_o_c_a()

        # Fix maxp for TrueType
        if "maxp" in font:
            font["maxp"].tableVersion = 0x00010000
            for attr in ("maxZones", "maxTwilightPoints", "maxStorage",
                         "maxFunctionDefs", "maxInstructionDefs",
                         "maxStackElements", "maxSizeOfInstructions",
                         "maxComponentElements"):
                setattr(font["maxp"], attr, 0)

        # Critical: change OTTO → TrueType header
        font.sfntVersion = "\x00\x01\x00\x00"
        font.save(out_path)
        return out_path

    except Exception:
        return None


def try_convert_font(path: str) -> str | None:
    """
    If `path` is incompatible with ReportLab, attempt CFF→TTF conversion.
    Returns a compatible font path, or None if conversion is not possible.
    """
    p = Path(path)
    subfont_index = 0
    converted = convert_cff_to_ttf(path, subfont_index)
    if converted and test_font_compatibility(converted):
        return converted
    return None


# ---------------------------------------------------------------------------
# Font scanning
# ---------------------------------------------------------------------------

def bundled_font_path() -> str:
    """Return absolute path to the bundled NotoSansSC font."""
    here = Path(__file__).parent.parent
    return str(here / "assets" / "fonts" / "NotoSansSC-Regular.ttf")


def scan_system_fonts() -> dict:
    """Scan system font directories. Returns {display_name: path}."""
    system = platform.system()
    base_dirs = SCAN_PATHS.get(system, SCAN_PATHS["Linux"])
    found = {}
    extensions = ("*.ttf", "*.otf", "*.ttc")
    for base_dir in base_dirs:
        for ext in extensions:
            pattern = str(Path(base_dir) / "**" / ext)
            for fpath in glob.glob(pattern, recursive=True):
                name = Path(fpath).stem
                found[name] = fpath
    return found


def filter_chinese_fonts(fonts: dict) -> dict:
    """Keep only fonts whose name matches Chinese font keywords."""
    result = {}
    for name, path in fonts.items():
        lower = name.lower()
        if any(kw in lower for kw in CHINESE_KEYWORDS):
            result[name] = path
    return result


def font_format(path: str) -> str:
    """Return human-readable format label for a font path."""
    ext = Path(path).suffix.lower()
    return {"ttf": "TTF", "otf": "OTF", "ttc": "TTC"}.get(ext.lstrip("."), ext.upper())


# ---------------------------------------------------------------------------
# YAML cache
# ---------------------------------------------------------------------------

def read_yaml_cache(yaml_path: str) -> dict:
    """Read pdf_style.yaml and return its contents as dict. Returns {} if missing."""
    p = Path(yaml_path)
    if not p.exists():
        return {}
    with open(p, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


def write_yaml_cache(yaml_path: str, fonts: dict, default_font) -> None:
    """Merge fonts cache and optional default_font into pdf_style.yaml."""
    p = Path(yaml_path)
    data = read_yaml_cache(yaml_path)
    if fonts:
        existing = data.get("fonts", {})
        existing.update(fonts)
        data["fonts"] = existing
    if default_font is not None:
        data["default_font"] = default_font
    with open(p, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False)


# ---------------------------------------------------------------------------
# Main entry: get usable fonts
# ---------------------------------------------------------------------------

def get_fonts(yaml_path: str):
    """
    Return (compatible_fonts_dict, default_font_or_None).

    For each discovered Chinese font:
    - If directly compatible with ReportLab → include as-is
    - If incompatible (CFF/PostScript) → attempt CFF→TTF conversion via fonttools;
      include the converted path if successful
    Results are cached in pdf_style.yaml.
    """
    data = read_yaml_cache(yaml_path)
    cached = data.get("fonts", {})
    default = data.get("default_font")

    if cached:
        compatible = {name: path for name, path in cached.items()
                      if test_font_compatibility(path)}
        if compatible:
            return compatible, default

    # Scan system
    all_fonts = scan_system_fonts()
    chinese = filter_chinese_fonts(all_fonts)

    # Add bundled fallback
    bundled = bundled_font_path()
    if Path(bundled).exists():
        chinese["NotoSansSC (bundled)"] = bundled

    # Test each font; convert incompatible CFF fonts
    compatible = {}
    for name, path in chinese.items():
        if test_font_compatibility(path):
            compatible[name] = path
        else:
            converted = try_convert_font(path)
            if converted:
                compatible[name] = converted

    write_yaml_cache(yaml_path, compatible, default_font=None)
    return compatible, default


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    """CLI: python font_finder.py --yaml /path/to/pdf_style.yaml"""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--yaml", required=True, help="Path to pdf_style.yaml")
    args = parser.parse_args()

    fonts, default_font = get_fonts(args.yaml)
    fonts_with_meta = {
        name: {"path": path, "format": font_format(path)}
        for name, path in fonts.items()
    }
    print(json.dumps({"fonts": fonts_with_meta, "default_font": default_font},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
