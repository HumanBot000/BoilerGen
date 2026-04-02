import time
from enum import Enum
from pathlib import Path
from typing import Optional, Any, List


class DebugType(Enum):
    TAGS = "tags"
    INJECTIONS = "injections"
    ALL = "all"


class DebugManager:
    def __init__(self, debug_type: DebugType, debug_output: Optional[Path], log_buffer: Optional[List[str]] = None):
        self.debug_type = debug_type
        self.debug_output = debug_output
        self.log_buffer: List[str] = log_buffer if log_buffer is not None else []

    def log(self, message: str):
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] [DEBUG] {message}"
        
        # Buffer for later console display
        self.log_buffer.append(formatted_message)
        
        # Still write to file immediately if output is set
        if self.debug_output:
            try:
                with open(self.debug_output, "a", encoding="utf-8") as f:
                    f.write(formatted_message + "\n")
            except Exception:
                pass

    def get_full_log(self) -> str:
        return "\n".join(self.log_buffer)

    def state_change(self, channel: str, *args, **kwargs):
        if channel == "general":
            self.log(f"GENERAL: {args[0] if args else 'N/A'}")
        elif channel == "error":
            self.log(f"ERROR: {args[0] if args else 'N/A'}")


class TagDebugManager(DebugManager):
    def state_change(self, channel: str, *args, **kwargs):
        if channel in ["general", "error"]:
            super().state_change(channel, *args, **kwargs)
            return
            
        if channel != "tags":
            return
        
        # Can be (message,) or (tf, full_list, action, item)
        if len(args) == 1:
            self.log(f"TAG INFO: {args[0]}")
        elif len(args) >= 4:
            tf = args[0]
            action = args[2]
            item = args[3]
            self.log(f"TAG UPDATE [{action}] in {tf.destination_path}: {item}")
        else:
            self.log(f"TAG: {args}")


class InjectionDebugManager(DebugManager):
    def state_change(self, channel: str, *args, **kwargs):
        if channel in ["general", "error"]:
            super().state_change(channel, *args, **kwargs)
            return

        if channel != "injections":
            return
        
        message = args[0] if args else "Unknown injection event"
        self.log(f"INJECTION: {message}")


class AllDebugManager(DebugManager):
    def __init__(self, debug_output: Optional[Path]):
        super().__init__(DebugType.ALL, debug_output)
        # Share the log buffer with sub-managers
        self.tag_mgr = TagDebugManager(DebugType.TAGS, debug_output, self.log_buffer)
        self.inj_mgr = InjectionDebugManager(DebugType.INJECTIONS, debug_output, self.log_buffer)

    def state_change(self, channel: str, *args, **kwargs):
        if channel == "tags":
            self.tag_mgr.state_change(channel, *args, **kwargs)
        elif channel == "injections":
            self.inj_mgr.state_change(channel, *args, **kwargs)
        else:
            super().state_change(channel, *args, **kwargs)


def get_debug_manager(debug_type: Optional[DebugType], debug_output: Optional[Path]) -> Optional[DebugManager]:
    if not debug_type:
        return None
        
    if debug_type == DebugType.TAGS:
        return TagDebugManager(debug_type, debug_output)
    elif debug_type == DebugType.INJECTIONS:
        return InjectionDebugManager(debug_type, debug_output)
    elif debug_type == DebugType.ALL:
        return AllDebugManager(debug_output)
    
    return DebugManager(debug_type, debug_output)
