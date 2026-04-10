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
            for path in glob.glob(pattern, recursive=True):
                name = Path(path).stem
                found[name] = path
    return found


def filter_chinese_fonts(fonts: dict) -> dict:
    """Keep only fonts whose name matches Chinese font keywords."""
    result = {}
    for name, path in fonts.items():
        lower = name.lower()
        if any(kw in lower for kw in CHINESE_KEYWORDS):
            result[name] = path
    return result


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


def get_fonts(yaml_path: str):
    """
    Return (chinese_fonts_dict, default_font_or_None).
    Uses yaml cache if available; otherwise scans system and writes cache.
    """
    data = read_yaml_cache(yaml_path)
    cached = data.get("fonts", {})
    default = data.get("default_font")

    if cached:
        return cached, default

    # No cache — scan system
    all_fonts = scan_system_fonts()
    chinese = filter_chinese_fonts(all_fonts)

    # Add bundled font as fallback entry
    bundled = bundled_font_path()
    if Path(bundled).exists():
        chinese["NotoSansSC (bundled)"] = bundled

    write_yaml_cache(yaml_path, chinese, default_font=None)
    return chinese, default


def main():
    """CLI: python font_finder.py --yaml /path/to/pdf_style.yaml"""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--yaml", required=True, help="Path to pdf_style.yaml")
    args = parser.parse_args()

    fonts, default_font = get_fonts(args.yaml)
    print(json.dumps({"fonts": fonts, "default_font": default_font}, ensure_ascii=False))


if __name__ == "__main__":
    main()
