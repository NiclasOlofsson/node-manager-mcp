"""
Singleton server registry for Mode Manager MCP.

This module provides a singleton pattern for the ModeManagerServer,
allowing tool registration from multiple files while maintaining
a single server instance.
"""

from typing import Optional

from fastmcp import FastMCP

from .chatmode_manager import ChatModeManager
from .instruction_manager import InstructionManager
from .library_manager import LibraryManager


class ServerRegistry:
    """Singleton registry for the MCP server and its components."""

    _instance: Optional["ServerRegistry"] = None
    _initialized: bool = False

    def __new__(cls) -> "ServerRegistry":
        """Create or return the singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the server registry (only once)."""
        if not ServerRegistry._initialized:
            self._app: Optional[FastMCP] = None
            self._chatmode_manager: Optional[ChatModeManager] = None
            self._instruction_manager: Optional[InstructionManager] = None
            self._library_manager: Optional[LibraryManager] = None
            self._read_only: bool = False
            ServerRegistry._initialized = True

    def initialize(
        self,
        app: FastMCP,
        chatmode_manager: ChatModeManager,
        instruction_manager: InstructionManager,
        library_manager: LibraryManager,
        read_only: bool = False,
    ) -> None:
        """Initialize the registry with server components."""
        self._app = app
        self._chatmode_manager = chatmode_manager
        self._instruction_manager = instruction_manager
        self._library_manager = library_manager
        self._read_only = read_only

    @property
    def app(self) -> FastMCP:
        """Get the FastMCP app instance."""
        if self._app is None:
            raise RuntimeError("ServerRegistry not initialized. Call initialize() first.")
        return self._app

    @property
    def chatmode_manager(self) -> ChatModeManager:
        """Get the ChatModeManager instance."""
        if self._chatmode_manager is None:
            raise RuntimeError("ServerRegistry not initialized. Call initialize() first.")
        return self._chatmode_manager

    @property
    def instruction_manager(self) -> InstructionManager:
        """Get the InstructionManager instance."""
        if self._instruction_manager is None:
            raise RuntimeError("ServerRegistry not initialized. Call initialize() first.")
        return self._instruction_manager

    @property
    def library_manager(self) -> LibraryManager:
        """Get the LibraryManager instance."""
        if self._library_manager is None:
            raise RuntimeError("ServerRegistry not initialized. Call initialize() first.")
        return self._library_manager

    @property
    def read_only(self) -> bool:
        """Get the read-only mode status."""
        return self._read_only

    @classmethod
    def get_instance(cls) -> "ServerRegistry":
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (primarily for testing)."""
        cls._instance = None
        cls._initialized = False


# Convenience function to get the registry instance
def get_server_registry() -> ServerRegistry:
    """Get the singleton server registry instance."""
    return ServerRegistry.get_instance()
