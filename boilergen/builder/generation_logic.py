import boilergen.cli.run_config
from boilergen.builder.parser.tags import TemplateFile


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

    lines = text.splitlines()
    # Tag removal
    for index, tag in enumerate(sorted(file.tags, key=lambda t: t.line_start, reverse=True)):
        lines[tag.line_start - 1] = ""
        lines[tag.line_end - 1] = ""
    
    text = "\n".join(lines)
    file.content = text


