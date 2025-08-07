"""Tool registration modules for Mode Manager MCP Server."""

from .chatmode_tools import register_chatmode_tools
from .instruction_tools import register_instruction_tools
from .library_tools import register_library_tools
from .remember_tools import register_remember_tools

__all__ = [
    "register_chatmode_tools",
    "register_instruction_tools",
    "register_library_tools",
    "register_remember_tools",
]


def register_all_tools() -> None:
    """Register all tools with the server."""
    register_instruction_tools()
    register_chatmode_tools()
    register_library_tools()
    register_remember_tools()
