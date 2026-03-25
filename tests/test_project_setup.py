import pytest
from boilergen.builder.project_setup import sort_templates_by_dependencies
from boilergen.core.template import Template

def test_sort_templates_linear():
    t1 = Template("t1", "T1")
    t2 = Template("t2", "T2", requires=["t1"])
    t3 = Template("t3", "T3", requires=["t2"])
    
    sorted_ts = sort_templates_by_dependencies([t3, t1, t2])
    
    assert [t.id for t in sorted_ts] == ["t1", "t2", "t3"]

def test_sort_templates_branching():
    t1 = Template("t1", "T1")
    t2 = Template("t2", "T2", requires=["t1"])
    t3 = Template("t3", "T3", requires=["t1"])
    t4 = Template("t4", "T4", requires=["t2", "t3"])
    
    sorted_ts = sort_templates_by_dependencies([t4, t3, t2, t1])
    
    ids = [t.id for t in sorted_ts]
    assert ids[0] == "t1"
    assert set(ids[1:3]) == {"t2", "t3"}
    assert ids[3] == "t4"

def test_sort_templates_cyclic():
    t1 = Template("t1", "T1", requires=["t2"])
    t2 = Template("t2", "T2", requires=["t1"])
    
    with pytest.raises(ValueError, match="Cyclic dependency"):
        sort_templates_by_dependencies([t1, t2])

def test_sort_templates_missing_strict():
    t1 = Template("t1", "T1", requires=["missing"])
    
    with pytest.raises(ValueError, match="Missing dependency"):
        sort_templates_by_dependencies([t1], strict=True)

def test_sort_templates_missing_non_strict():
    t1 = Template("t1", "T1", requires=["missing"])
    
    sorted_ts = sort_templates_by_dependencies([t1], strict=False)
    assert [t.id for t in sorted_ts] == ["t1"]
