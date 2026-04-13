import pytest
from pathlib import Path
from boilergen.builder.cleanup import cleanup_file, cleanup_directory

def test_cleanup_file_basic(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("\n\nLine 1\n\n\nLine 2\n\n\n", encoding="utf-8")
    
    cleanup_file(f)
    
    # Leading/trailing stripped, triple newline collapsed to double
    # Should end with exactly one newline if not empty
    expected = "Line 1\n\nLine 2\n"
    assert f.read_text(encoding="utf-8") == expected

def test_cleanup_file_only_whitespace(tmp_path):
    f = tmp_path / "blank.txt"
    f.write_text("   \n\n   \n", encoding="utf-8")
    
    cleanup_file(f)
    
    # Should be empty string if only whitespace
    assert f.read_text(encoding="utf-8") == ""

def test_cleanup_file_no_changes_needed(tmp_path):
    f = tmp_path / "clean.txt"
    content = "Single Line\n"
    f.write_text(content, encoding="utf-8")
    
    cleanup_file(f)
    
    assert f.read_text(encoding="utf-8") == content

def test_cleanup_directory(tmp_path):
    d = tmp_path / "subdir"
    d.mkdir()
    f1 = d / "file1.txt"
    f1.write_text("\n\nF1\n\n", encoding="utf-8")
    f2 = tmp_path / "file2.txt"
    f2.write_text("\n\nF2\n\n", encoding="utf-8")
    
    cleanup_directory(tmp_path)
    
    assert f1.read_text(encoding="utf-8") == "F1\n"
    assert f2.read_text(encoding="utf-8") == "F2\n"
