import pytest
from pathlib import Path
from boilergen.core.config_manager import ConfigManager

def test_config_manager_creation(tmp_path):
    # Mock appdirs by overriding the config_dir in __init__
    # But ConfigManager uses appdirs directly.
    # I'll patch appdirs or just use a custom config_dir if I refactor it.
    
    # Let's try to patch it or just use the real one but with a unique app name.
    app_name = "boilergen_test"
    cm = ConfigManager(app_name=app_name)
    
    assert cm.config_file.exists()
    assert cm.config.has_section("TEMPLATES")

def test_resolve_template_dir_default(tmp_path):
    app_name = "boilergen_test_default"
    cm = ConfigManager(app_name=app_name)
    
    default_dir = tmp_path / "boilergen"
    resolved = cm.resolve_template_dir(str(default_dir))
    
    assert resolved == default_dir / "templates"

def test_resolve_template_dir_configured(tmp_path):
    app_name = "boilergen_test_configured"
    cm = ConfigManager(app_name=app_name)
    
    custom_dir = tmp_path / "my_templates"
    custom_dir.mkdir()
    
    cm.config.set("TEMPLATES", "TemplateLocation", str(custom_dir))
    with open(cm.config_file, "w") as f:
        cm.config.write(f)
        
    resolved = cm.resolve_template_dir(str(tmp_path / "default"))
    assert resolved == custom_dir / "templates"
