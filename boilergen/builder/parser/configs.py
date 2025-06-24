import re
from typing import Union
import yaml


class NotDefinedType:
    def __repr__(self):
        return "NOT_DEFINED"

    def __str__(self):
        return "NOT_DEFINED"


NOT_DEFINED = NotDefinedType()

ValueType = Union[str, bool, None, NotDefinedType]


class ValueConfig:
    def __init__(self, identifier: str, replacement_start: int, replacement_end: int,
                 in_template_value: ValueType, yaml_value: ValueType, cli_value: ValueType):
        self.identifier = identifier
        self.replacement_start = replacement_start
        self.replacement_end = replacement_end
        self.in_template_value = in_template_value
        self.yaml_value = yaml_value
        self.cli_value = cli_value

    @property
    def insertion_value(self):
        value_order = [self.cli_value, self.yaml_value, self.in_template_value]
        for value in value_order:
            if value is not NOT_DEFINED:
                return value
        return NOT_DEFINED

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"ValueConfig(identifier={self.identifier}, in_template_value={self.in_template_value}, yaml_value={self.yaml_value}, cli_value={self.cli_value})"


def extract_configs(file_content: str):
    full_pattern = re.compile(
        r'boilergen:config\s*\|\s*'
        r'([^\s|]+)'  # identifier
        r'(?:\s*\|\s*'
        r'([^"\']*(?:"[^"]*"|\'[^\']*\'[^"\']*)*)'  # value that may contain quoted strings
        r')?'
    )

    offset = 0
    configs = []

    for line_number, line in enumerate(file_content.splitlines(keepends=True), start=1):
        # Let's debug by showing what we're trying to match
        # Find outer quotes first
        in_quotes = []
        i = 0
        while i < len(line):
            if line[i] in ('"', "'"):
                quote_char = line[i]
                start_quote = i
                i += 1
                # Find end quote
                while i < len(line) and line[i] != quote_char:
                    if line[i] == '\\':  # Skip escaped characters
                        i += 2
                    else:
                        i += 1
                if i < len(line):  # Found closing quote
                    in_quotes.append((start_quote, i, quote_char, line[start_quote:i + 1]))
                i += 1
            else:
                i += 1

        # Now look for boilergen:config patterns within quotes
        for start_quote, end_quote, quote_char, quoted_content in in_quotes:
            inner_content = quoted_content[1:-1]  # Remove outer quotes
            matches = list(full_pattern.finditer(inner_content))

            for m in matches:
                # Adjust positions to account for the quote offset
                match_start = offset + start_quote + 1 + m.start()
                match_end = offset + start_quote + 1 + m.end()

                identifier = m.group(1).strip()
                raw_value = m.group(2).strip() if m.group(2) is not None else None

                interpreted_value = interpret_value(raw_value, quote_char)
                config = ValueConfig(
                    identifier=identifier,
                    replacement_start=match_start,
                    replacement_end=match_end,
                    in_template_value=interpreted_value,
                    yaml_value=NOT_DEFINED,
                    cli_value=NOT_DEFINED
                )
                configs.append(config)
        offset += len(line)

    return configs


def fetch_yaml_configs(configs: list[ValueConfig], yaml_data: dict):
    for config in configs:
        if config.identifier in yaml_data["config"]:
            config.yaml_value = yaml_data["config"][config.identifier]

def interpret_value(raw: Union[str, None, NotDefinedType], outer_quote: Union[str, None]) -> ValueType:
    """
    Interpret the raw value depending on the outer quote context.

    - If raw is None or NOT_DEFINED, return NOT_DEFINED.
    - Strip raw.
    - If outer_quote is set:
        - If raw starts and ends with matching quotes, preserve raw (including quotes).
        - Else return raw stripped (no added quotes).
    - If outer_quote is None:
        - Return raw stripped (no quotes stripped or added).
    """
    if raw is None or raw is NOT_DEFINED:
        return NOT_DEFINED

    txt = raw.strip()
    if not txt:  # Empty string case
        return txt
    if outer_quote:
        # We're inside outer quotes like "boilergen:config | debug | True"
        if len(txt) >= 2 and txt[0] == txt[-1] and txt[0] in ('"', "'"):
            # Value has explicit inner quotes: "boilergen:config | debug | 'True'" -> 'True'
            # or 'boilergen:config | host | "0.0.0.0"' -> "0.0.0.0"
            return txt
        else:
            # Value has no inner quotes: "boilergen:config | debug | True" -> True
            return txt
    else:
        # No outer quote context: just return stripped value
        return txt
