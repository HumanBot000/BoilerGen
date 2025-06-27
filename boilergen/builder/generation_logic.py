import os

import boilergen.cli.run_config
from boilergen.builder.parser.tags import TemplateFile


def generate_file(file: TemplateFile, run_config: boilergen.cli.run_config.RunConfig):
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

    lines = text.splitlines()
    # Tag removal
    for tag in file.tags:
        # todo run arg to remove the line instead of clearing (We need to keep track of everything because line count get's updated)
        lines[tag.line_start - 1] = ""
        lines[tag.line_end - 1] = ""
    text = "\n".join(lines)
    os.makedirs(os.path.dirname(file.destination_path), exist_ok=True)
    with open(file.destination_path,"w+") as f:
        f.write(text)

