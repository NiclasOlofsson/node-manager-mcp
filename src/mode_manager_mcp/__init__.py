"""
Mode Manager MCP Server.

This package provides an MCP server for managing VS Code chatmode files
and GitHub Copilot instructions.
"""

from .simple_server import create_server

__version__ = "0.1.13"
__all__ = ["create_server"]
