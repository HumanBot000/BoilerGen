from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from boilergen.core.debug_manager import DebugType, get_debug_manager, DebugManager


@dataclass
class RunConfig:
    disable_dependencies: bool = False
    minimal_ui: bool = False
    clear_output: bool = False
    party_mode: bool = False
    disable_quote_parsing_for_configs : bool = False
    dry_run: bool = False
    debug_type : Optional[DebugType] = None
    debug_output : Optional[Path] = None
    debug_manager : Optional[DebugManager] = field(default=None, init=False)

    def __post_init__(self):
        if self.debug_type:
            self.debug_manager = get_debug_manager(self.debug_type, self.debug_output)
