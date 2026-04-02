import re
import boilergen.cli.run_config
from boilergen.builder.parser.tags import TemplateFile, TAG_OPENING_REGEX, TAG_CLOSING_REGEX


def generate_file_content_data(file: TemplateFile, run_config: boilergen.cli.run_config.RunConfig):
    text = file.content
    # Configs
    for config in sorted(file.configs, key=lambda c: c.replacement_start, reverse=True):
        start = config.replacement_start
        end = config.replacement_end
        if start > 0 and end < len(text):
            if not run_config.disable_quote_parsing_for_configs:
                if text[start - 1] in ['"', "'"] and text[end] in ['"', "'"]:
                    start -= 1
                    end += 1
        text = text[:start] + config.insertion_value + text[end:]

    # Tag removal - robust against line shifts from configs
    # We replace the entire line containing a tag with an empty string to maintain original behavior
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if re.search(TAG_OPENING_REGEX, line) or re.search(TAG_CLOSING_REGEX, line):
            lines[i] = ""
    
    file.content = "\n".join(lines)


