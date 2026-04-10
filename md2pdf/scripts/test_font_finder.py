import json, os, sys, tempfile
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent))
import font_finder

def test_scan_returns_dict():
    result = font_finder.scan_system_fonts()
    assert isinstance(result, dict)

def test_scan_keys_are_strings():
    result = font_finder.scan_system_fonts()
    for k, v in result.items():
        assert isinstance(k, str)
        assert isinstance(v, str)

def test_read_yaml_cache_empty(tmp_path):
    yaml_path = tmp_path / "pdf_style.yaml"
    result = font_finder.read_yaml_cache(str(yaml_path))
    assert result == {}

def test_write_and_read_yaml_cache(tmp_path):
    yaml_path = tmp_path / "pdf_style.yaml"
    fonts = {"PingFang SC": "/fake/path/PingFang.ttc"}
    font_finder.write_yaml_cache(str(yaml_path), fonts, default_font=None)
    result = font_finder.read_yaml_cache(str(yaml_path))
    assert result.get("fonts", {}).get("PingFang SC") == "/fake/path/PingFang.ttc"

def test_write_default_font(tmp_path):
    yaml_path = tmp_path / "pdf_style.yaml"
    font_finder.write_yaml_cache(str(yaml_path), {}, default_font="PingFang SC")
    result = font_finder.read_yaml_cache(str(yaml_path))
    assert result.get("default_font") == "PingFang SC"

def test_filter_chinese_fonts():
    all_fonts = {
        "Arial": "/fonts/Arial.ttf",
        "PingFang SC": "/fonts/PingFang.ttc",
        "NotoSansCJK": "/fonts/NotoSansCJK.ttf",
        "Helvetica": "/fonts/Helvetica.ttf",
    }
    result = font_finder.filter_chinese_fonts(all_fonts)
    assert "PingFang SC" in result
    assert "NotoSansCJK" in result
    assert "Arial" not in result
    assert "Helvetica" not in result

def test_bundled_font_exists():
    bundled = font_finder.bundled_font_path()
    assert Path(bundled).exists(), f"Bundled font not found at {bundled}"
