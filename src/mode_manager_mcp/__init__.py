"""
Mode Manager MCP Server.

This package provides an MCP server for managing VS Code chatmode files
and GitHub Copilot instructions. The server uses a singleton orchestration
pattern with tools organized in separate modules.
"""

from .simple_server import create_server

__version__ = "0.1.17"
__all__ = ["create_server"]
