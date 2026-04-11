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


# ---------------------------------------------------------------------------
# Tests for new functions added in April 2026
# ---------------------------------------------------------------------------

def test_font_compatibility_bundled_is_true():
    """Bundled NotoSansSC should always be ReportLab-compatible."""
    bundled = font_finder.bundled_font_path()
    assert font_finder.test_font_compatibility(bundled) is True


def test_font_compatibility_nonexistent_is_false():
    """Non-existent path should return False, not raise."""
    result = font_finder.test_font_compatibility("/nonexistent/font.ttf")
    assert result is False


def test_font_compatibility_caches_result():
    """Second call with same path should use cache (no re-test)."""
    bundled = font_finder.bundled_font_path()
    font_finder._COMPAT_CACHE.clear()
    font_finder.test_font_compatibility(bundled)
    assert bundled in font_finder._COMPAT_CACHE
    # Cache hit: result still correct
    assert font_finder._COMPAT_CACHE[bundled] is True


def test_font_format_ttf():
    assert font_finder.font_format("/fonts/MyFont.ttf") == "TTF"


def test_font_format_ttc():
    assert font_finder.font_format("/fonts/MyFont.ttc") == "TTC"


def test_font_format_otf():
    assert font_finder.font_format("/fonts/MyFont.otf") == "OTF"


def test_get_fonts_includes_bundled(tmp_path):
    """get_fonts() should always include the bundled NotoSansSC as a fallback."""
    yaml_path = tmp_path / "pdf_style.yaml"
    fonts, default = font_finder.get_fonts(str(yaml_path))
    assert any("NotoSansSC" in name for name in fonts), \
        "Bundled font should appear in font list"
    assert default is None


def test_get_fonts_all_paths_compatible(tmp_path):
    """Every font returned by get_fonts() must pass ReportLab compatibility."""
    yaml_path = tmp_path / "pdf_style.yaml"
    fonts, _ = font_finder.get_fonts(str(yaml_path))
    for name, path in fonts.items():
        assert font_finder.test_font_compatibility(path), \
            f"Font '{name}' at {path} failed ReportLab compatibility"


def test_convert_cache_dir_creates_directory():
    """_convert_cache_dir() should create and return a writable directory."""
    d = font_finder._convert_cache_dir()
    assert d.exists()
    assert d.is_dir()
