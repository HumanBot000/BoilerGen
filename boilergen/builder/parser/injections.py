import collections
import os
from enum import Enum
from typing import Union, List

from boilergen.builder.parser.tags import TemplateFile
from boilergen.cli.run_config import RunConfig


class InjectionMethod(Enum):
    BEFORE = "above"
    AFTER = "below"
    REPLACE = "replace"
    START = "top"
    END = "bottom"


class Injection:
    def __init__(self, target_template_name: str, target_file: str, source_file: str,
                 injection_definition_location: str,
                 target_tag: Union[str, None] = None, line: Union[int, None] = None,
                 method: InjectionMethod = InjectionMethod.END):
        if target_tag is None and line is None:
            raise ValueError("Either target_tag or line must be provided")

        self.target_template = target_template_name
        self.target_file = target_file
        self.source_file = source_file
        self.target_tag = target_tag
        self.line = line
        self.injection_definition_location = injection_definition_location
        self.method = method

    def __eq__(self, other):
        return (
                isinstance(other, Injection) and
                self.target_template == other.target_template and
                self.target_file == other.target_file and
                self.source_file == other.source_file and
                self.target_tag == other.target_tag and
                self.line == other.line and
                self.injection_definition_location == other.injection_definition_location and
                self.method == other.method
        )

    def __hash__(self):
        return hash((
            self.target_template,
            self.target_file,
            self.source_file,
            self.target_tag,
            self.line,
            self.injection_definition_location,
            self.method
        ))


def parse_injections(yaml_data: dict, yaml_file_path: str) -> list[Injection]:
    injections = []
    for injection in yaml_data.get("injections", []):
        if injection.get("method") == "replace":
            method = InjectionMethod.REPLACE
        else:
            method = InjectionMethod(injection["method"]["insert"][0])
        injections.append(
            Injection(
                target_template_name=injection["target"],
                target_file=injection["at"]["file"],
                source_file=injection["from"],
                target_tag=injection["at"].get("tag", None),
                line=injection["at"].get("line", None),
                method=method,
                injection_definition_location=os.path.dirname(yaml_file_path)
            )
        )
    return injections


def get_template_file_to_injection(template_files: List[TemplateFile], injection: Injection,
                                   output_path: str) -> TemplateFile:
    full_destination_path = os.path.normpath(os.path.join(output_path, injection.target_file))
    for file in template_files:
        candidate_path = os.path.normpath(os.path.join(output_path, file.destination_path))
        if candidate_path == full_destination_path:
            return file


def run_injections(template_files: List[TemplateFile], run_config: RunConfig, output_path: str):
    visited_injections = set()
    injections_by_target_file = collections.defaultdict(list)

    for file in template_files:
        for injection in file.injections:
            if injection in visited_injections:
                continue
            visited_injections.add(injection)
            injections_by_target_file[injection.target_file].append((file, injection))

    for target_file, injections in injections_by_target_file.items():
        full_destination_path = os.path.join(output_path, target_file)

        with open(full_destination_path, "r") as f:
            content_lines = f.read().splitlines()
        edited_content_lines = content_lines.copy()

        def sort_key(pair):
            _, injection = pair
            if injection.line is not None:
                return (0, injection.line)
            else:
                for file, inj in injections:
                    if inj == injection:
                        tags = get_template_file_to_injection(template_files, inj, output_path).tags
                        for tag in tags:
                            if str(tag.tag_identifier) == str(injection.target_tag):
                                return (1, tag.line_start)
            return (2, 0)  # Fallback

        injections.sort(key=sort_key)

        for file, injection in injections:
            source_template = get_template_file_to_injection(template_files, injection, output_path)
            with open(os.path.join(injection.injection_definition_location, injection.source_file), "r") as f:
                source_lines = f.read().splitlines()

            def find_tag_bounds():
                for tag in source_template.tags:
                    if str(tag.tag_identifier) == str(injection.target_tag):
                        return tag.line_start, tag.line_end
                return None, None

            method = injection.method
            file_length_line_delta = 0

            if method == InjectionMethod.REPLACE:
                if injection.line is not None:
                    file_length_line_delta = len(edited_content_lines[injection.line:injection.line + 1]) - len(source_lines)
                    edited_content_lines[injection.line:injection.line + 1] = source_lines
                else:
                    start, end = find_tag_bounds()
                    if start is not None and end is not None:
                        file_length_line_delta = len(edited_content_lines[start:end]) - len(source_lines)
                        edited_content_lines[start:end] = source_lines

            elif method == InjectionMethod.BEFORE:
                file_length_line_delta = len(source_lines)
                if injection.line is not None:
                    edited_content_lines[injection.line:injection.line] = source_lines
                else:
                    start, _ = find_tag_bounds()
                    if start is not None:
                        edited_content_lines[start:start] = source_lines

            elif method == InjectionMethod.AFTER:
                file_length_line_delta = len(source_lines)
                if injection.line is not None:
                    edited_content_lines[injection.line + 1:injection.line + 1] = source_lines
                else:
                    _, end = find_tag_bounds()
                    if end is not None:
                        edited_content_lines[end + 1:end + 1] = source_lines

            elif method == InjectionMethod.START:
                file_length_line_delta = len(source_lines)
                start, _ = find_tag_bounds()
                if start is not None:
                    insert_pos = start + 1
                    edited_content_lines[insert_pos:insert_pos] = source_lines

            elif method == InjectionMethod.END:
                file_length_line_delta = len(source_lines)
                _, end = find_tag_bounds()
                if end is not None:
                    insert_pos = end
                    edited_content_lines[insert_pos:insert_pos] = source_lines

            start, end = find_tag_bounds()
            for tag in file.tags:
                if start is not None and tag.line_start > start:
                    tag.line_start += file_length_line_delta
                if end is not None and tag.line_end > end:
                    tag.line_end += file_length_line_delta

        with open(full_destination_path, "w") as f:
            f.write("\n".join(edited_content_lines))