import collections
import os
from enum import Enum
from typing import Union, List, Tuple, Optional

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


def parse_injections(yaml_data: dict, yaml_file_path: str) -> List[Injection]:
    """Parse injection definitions from YAML configuration."""
    injections = []

    for config in yaml_data.get("injections", []):
        # Parse method
        if config.get("method") == "replace":
            method = InjectionMethod.REPLACE
        else:
            method = InjectionMethod(config["method"]["insert"][0])

        injection = Injection(
            target_template_name=config["target"],
            target_file=config["at"]["file"],
            source_file=config["from"],
            target_tag=config["at"].get("tag", None),
            line=config["at"].get("line", None),
            method=method,
            injection_definition_location=os.path.dirname(yaml_file_path)
        )
        injections.append(injection)

    return injections


def find_template_file(template_files: List[TemplateFile], injection: Injection, output_path: str) -> Optional[
    TemplateFile]:
    """Find the template file that matches the injection's target file path."""
    target_path = os.path.normpath(os.path.join(output_path, injection.target_file))

    for template_file in template_files:
        candidate_path = os.path.normpath(os.path.join(output_path, template_file.destination_path))
        if candidate_path == target_path:
            return template_file
    return None


def run_injections(template_files: List[TemplateFile], run_config: RunConfig, output_path: str):
    """Execute all injections, processing them by target file to maintain consistency."""
    # Collect unique injections by target file
    visited_injections = set()
    injections_by_file = collections.defaultdict(list)

    for template_file in template_files:
        for injection in template_file.injections:
            if injection in visited_injections:
                continue
            visited_injections.add(injection)
            injections_by_file[injection.target_file].append((template_file, injection))

    # Process each target file
    for target_file_path, file_injections in injections_by_file.items():
        process_file_injections(target_file_path, file_injections, template_files, output_path)


def process_file_injections(target_file_path: str, file_injections: List[Tuple],
                            template_files: List[TemplateFile], output_path: str):
    """Process all injections for a single target file."""
    full_file_path = os.path.join(output_path, target_file_path)

    template_file_of_target = None
    for template_file in template_files:
        if os.path.normpath(template_file.destination_path) == os.path.normpath(full_file_path):
            template_file_of_target = template_file
            break
    # Read target file
    content_lines = template_file_of_target.content.splitlines()

    # Sort injections by position (line-based first, then tag-based)
    def get_injection_position(injection_tuple):
        template_file, injection = injection_tuple

        if injection.line is not None:
            return (0, injection.line)  # Line-based gets priority

        if injection.target_tag is not None:
            target_template = find_template_file(template_files, injection, output_path)
            if target_template:
                for tag in target_template.tags:
                    if str(tag.tag_identifier) == str(injection.target_tag):
                        return (1, tag.line_start)

        return (2, 0)  # Fallback

    file_injections.sort(key=get_injection_position)

    # Apply each injection
    for template_file, injection in file_injections:
        # Read source content
        source_path = os.path.join(injection.injection_definition_location, injection.source_file)
        with open(source_path, "r") as f:
            source_lines = f.read().splitlines()

        # Apply injection
        content_lines = apply_injection(content_lines, injection, source_lines, template_files, output_path)

        # Update tag positions after injection
        update_tag_positions(template_file, injection, len(source_lines), template_files, output_path)

    template_file_of_target.content = "\n".join(content_lines)


def apply_injection(content_lines: List[str], injection: Injection, source_lines: List[str],
                    template_files: List[TemplateFile], output_path: str) -> List[str]:
    """Apply a single injection to the content lines."""

    # Line-based injection
    if injection.line is not None:
        line_idx = injection.line
        method = injection.method

        if method == InjectionMethod.REPLACE:
            content_lines[line_idx:line_idx + 1] = source_lines
        elif method == InjectionMethod.BEFORE:
            content_lines[line_idx:line_idx] = source_lines
        elif method == InjectionMethod.AFTER:
            content_lines[line_idx + 1:line_idx + 1] = source_lines

        return content_lines

    # Tag-based injection
    if injection.target_tag is not None:
        target_template = find_template_file(template_files, injection, output_path)
        if not target_template:
            return content_lines

        # Find tag bounds
        tag_start, tag_end = None, None
        for tag in target_template.tags:
            if str(tag.tag_identifier) == str(injection.target_tag):
                tag_start, tag_end = tag.line_start, tag.line_end
                break

        if tag_start is None:
            return content_lines

        method = injection.method
        if method == InjectionMethod.REPLACE:
            content_lines[tag_start:tag_end] = source_lines
        elif method == InjectionMethod.BEFORE:
            content_lines[tag_start:tag_start] = source_lines
        elif method == InjectionMethod.AFTER:
            content_lines[tag_end + 1:tag_end + 1] = source_lines
        elif method == InjectionMethod.START:
            content_lines[tag_start + 1:tag_start + 1] = source_lines
        elif method == InjectionMethod.END:
            content_lines[tag_end:tag_end] = source_lines

    return content_lines


def update_tag_positions(template_file: TemplateFile, injection: Injection, source_line_count: int,
                         template_files: List[TemplateFile], output_path: str):
    """Update tag positions after an injection modifies the file structure."""
    target_template = find_template_file(template_files, injection, output_path)
    if not target_template:
        return

    # Calculate line delta
    method = injection.method
    if method == InjectionMethod.REPLACE:
        if injection.line is not None:
            line_delta = source_line_count - 1  # Replacing 1 line
        else:
            # Replacing tag content
            for tag in target_template.tags:
                if str(tag.tag_identifier) == str(injection.target_tag):
                    original_line_count = tag.line_end - tag.line_start
                    line_delta = source_line_count - original_line_count
                    break
            else:
                line_delta = 0
    else:
        line_delta = source_line_count  # Adding lines

    # Get injection position for updating tags that come after
    injection_pos = None
    if injection.line is not None:
        injection_pos = injection.line
    elif injection.target_tag is not None:
        for tag in target_template.tags:
            if str(tag.tag_identifier) == str(injection.target_tag):
                injection_pos = tag.line_start
                break

    if injection_pos is not None:
        # Update all tag positions that come after the injection
        for file in template_files:
            for tag in file.tags:
                if tag.line_start > injection_pos:
                    tag.line_start += line_delta
                if tag.line_end > injection_pos:
                    tag.line_end += line_delta
