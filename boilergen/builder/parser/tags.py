import re
from typing import List

from boilergen.builder.parser.configs import ValueConfig

TAG_OPENING_REGEX = r"<<boilergen:(?!config\b)[^>\s]+"
TAG_CLOSING_REGEX = r"boilergen:(?!config\b)[^>\s]+>>"


class Tag:
    def __init__(self, tag_identifier: str, line_start: int, line_end: int):
        self.tag_identifier = tag_identifier
        self.line_start = line_start
        self.line_end = line_end

    def __repr__(self):
        return f"Tag(id='{self.tag_identifier}', start={self.line_start}, end={self.line_end})"


class TemplateFile:
    def __init__(self, content: str, tags: List[Tag], configs: List[ValueConfig], destination_path: str,
                 injections=None):
        if injections is None:
            injections = []
        self.content = content
        self.tags = tags
        self.configs = configs
        self.destination_path = destination_path
        self.injections = injections


def extract_tags(file_content: str):
    opening_tags = []
    closing_tags = []

    for line_number, line in enumerate(file_content.splitlines(), start=1):
        open_match = re.search(TAG_OPENING_REGEX, line)
        if open_match:
            identifier = open_match.group().split(":")[1]
            opening_tags.append((identifier, line_number))

        close_match = re.search(TAG_CLOSING_REGEX, line)
        if close_match:
            identifier = close_match.group().split(":")[1].rstrip(">>")
            closing_tags.append((identifier, line_number))

    tags = []
    for identifier, start_line in opening_tags:
        for i, (closing_identifier, end_line) in enumerate(closing_tags):
            if closing_identifier == identifier:
                tags.append(Tag(identifier, start_line, end_line))
                del closing_tags[i]
                break
    return tags
