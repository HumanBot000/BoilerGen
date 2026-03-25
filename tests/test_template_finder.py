import pytest
from pathlib import Path
import yaml
from boilergen.core.template_finder import (
    list_subgroups_and_templates,
    find_all_templates,
    resolve_dependencies
)

@pytest.fixture
def mock_template_structure(tmp_path):
    """Create a mock template directory structure for testing."""
    # Root
    #  ├── t1 (template)
    #  ├── group1 (subgroup)
    #  │    └── t2 (template, depends on t1)
    #  └── group2 (subgroup)
    #       └── subgroup1 (subgroup)
    #            └── t3 (template, depends on t2)
    
    # Template 1
    t1_dir = tmp_path / "t1"
    t1_dir.mkdir()
    (t1_dir / "template.yaml").write_text(yaml.dump({
        "id": "t1",
        "label": "Template 1",
        "requires": []
    }))
    
    # Group 1 / Template 2
    g1_dir = tmp_path / "group1"
    g1_dir.mkdir()
    t2_dir = g1_dir / "t2"
    t2_dir.mkdir()
    (t2_dir / "template.yaml").write_text(yaml.dump({
        "id": "t2",
        "label": "Template 2",
        "requires": ["t1"]
    }))
    
    # Group 2 / Subgroup 1 / Template 3
    g2_dir = tmp_path / "group2"
    g2_dir.mkdir()
    sg1_dir = g2_dir / "subgroup1"
    sg1_dir.mkdir()
    t3_dir = sg1_dir / "t3"
    t3_dir.mkdir()
    (t3_dir / "template.yaml").write_text(yaml.dump({
        "id": "t3",
        "label": "Template 3",
        "requires": ["t2"]
    }))
    
    return tmp_path

def test_list_subgroups_and_templates(mock_template_structure):
    subgroups, templates = list_subgroups_and_templates(str(mock_template_structure))
    
    assert "group1" in subgroups
    assert "group2" in subgroups
    assert len(templates) == 1
    assert templates[0].id == "t1"

def test_find_all_templates(mock_template_structure):
    all_templates = find_all_templates(str(mock_template_structure))
    
    assert len(all_templates) == 3
    assert "t1" in all_templates
    assert "t2" in all_templates
    assert "t3" in all_templates
    assert all_templates["t2"].requires == ["t1"]

def test_resolve_dependencies(mock_template_structure):
    all_templates = find_all_templates(str(mock_template_structure))
    
    # Select t3, should resolve t2 and t1
    required, auto = resolve_dependencies(["t3"], all_templates)
    
    assert set(required) == {"t1", "t2", "t3"}
    assert set(auto) == {"t1", "t2"}

def test_resolve_dependencies_already_selected(mock_template_structure):
    all_templates = find_all_templates(str(mock_template_structure))
    
    # Select t3 and t2 manually
    required, auto = resolve_dependencies(["t3", "t2"], all_templates)
    
    assert set(required) == {"t1", "t2", "t3"}
    assert set(auto) == {"t1"}
