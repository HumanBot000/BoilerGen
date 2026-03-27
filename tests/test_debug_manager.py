import pytest
from pathlib import Path
from boilergen.core.debug_manager import DebugType, TagDebugManager, InjectionDebugManager, get_debug_manager
from boilergen.core.observable import ObservableList
from boilergen.builder.parser.tags import Tag, TemplateFile

def test_observable_list_callback():
    called = []
    def callback(lst, action, item):
        called.append((action, item))
    
    ol = ObservableList([1, 2], callback=callback)
    ol.append(3)
    ol.remove(1)
    ol[0] = 5
    
    assert ("append", 3) in called
    assert ("remove", 1) in called
    assert ("set", 5) in called

def test_debug_manager_buffering(tmp_path, capsys):
    debug_file = tmp_path / "debug.log"
    mgr = TagDebugManager(DebugType.TAGS, debug_file)
    tf = TemplateFile("content", [], [], "dest/path")
    tag = Tag("tag_id", 1, 2)
    
    mgr.state_change("tags", tf, [], "append", tag)
    
    # Check that it did NOT print to console yet
    captured = capsys.readouterr()
    assert "TAG UPDATE" not in captured.out
    
    # Check that it DID write to file
    assert debug_file.exists()
    assert "TAG UPDATE" in debug_file.read_text()
    
    # Check buffered log
    log = mgr.get_full_log()
    assert "TAG UPDATE [append] in dest/path: Tag(id='tag_id', start=1, end=2)" in log

def test_general_debug_logging():
    mgr = get_debug_manager(DebugType.TAGS, None)
    mgr.state_change("general", "Testing general log")
    assert "GENERAL: Testing general log" in mgr.get_full_log()

def test_get_debug_manager():
    assert isinstance(get_debug_manager(DebugType.TAGS, None), TagDebugManager)
    assert isinstance(get_debug_manager(DebugType.INJECTIONS, None), InjectionDebugManager)
    assert get_debug_manager(None, None) is None
