import re
from typing import List, Union, Optional, Callable, Any
from boilergen.builder.parser.configs import ValueConfig
from boilergen.core.observable import ObservableList

TAG_OPENING_REGEX = r"<<boilergen:(?!config\b)([a-zA-Z0-9_-]+)"
TAG_CLOSING_REGEX = r"boilergen:(?!config\b)([a-zA-Z0-9_-]+)>>"


class Tag:
    def __init__(self, tag_identifier: str, line_start: int, line_end: int):
        self.tag_identifier = tag_identifier
        self.line_start = line_start
        self.line_end = line_end

    def __repr__(self):
        return f"Tag(id='{self.tag_identifier}', start={self.line_start}, end={self.line_end})"


class TemplateFile:
    def __init__(self, content: str, tags: List[Tag], configs: List[ValueConfig], destination_path: str,
                 injections=None, tag_change_callback: Optional[Callable[[Any,Any,Any], None]] = None):
        if injections is None:
            injections = []
        self.content = content
        self.tag_change_callback = tag_change_callback
        self._tags = ObservableList(tags, callback=self.on_tags_changed)
        self.configs = configs
        self.destination_path = destination_path
        self.injections = injections
        
        # Notify about initial scan if tags exist
        if tags:
            for tag in tags:
                self.on_tags_changed(self._tags, "scanned", tag)

    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, value: Union[List[Tag], ObservableList]):
        if isinstance(value, ObservableList):
            self._tags = value
            self._tags._callback = self.on_tags_changed
        else:
            self._tags = ObservableList(value, callback=self.on_tags_changed)
        
        # Notify about refreshed tags
        for tag in self._tags:
            self.on_tags_changed(self._tags, "refreshed", tag)

    def on_tags_changed(self, *args):
        if self.tag_change_callback:
            self.tag_change_callback(self, *args)

def extract_tags(file_content: str, debug_manager=None):
    opening_tags = []
    closing_tags = []

    for line_number, line in enumerate(file_content.splitlines(), start=1):
        open_match = re.search(TAG_OPENING_REGEX, line)
        if open_match:
            identifier = open_match.group(1)
            opening_tags.append((identifier, line_number))

        close_match = re.search(TAG_CLOSING_REGEX, line)
        if close_match:
            identifier = close_match.group(1)
            closing_tags.append((identifier, line_number))

    tags = []
    for identifier, start_line in opening_tags:
        for i, (closing_identifier, end_line) in enumerate(closing_tags):
            if closing_identifier == identifier:
                tags.append(Tag(identifier, start_line, end_line))
                del closing_tags[i]
                break
    
    if debug_manager:
        debug_manager.state_change("tags", f"Scanned content and found {len(tags)} tags")
        for tag in tags:
            debug_manager.state_change("tags", f"Found tag: {tag}")
            
    return tags
