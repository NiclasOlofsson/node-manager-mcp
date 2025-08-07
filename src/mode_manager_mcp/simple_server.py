"""
Mode Manager MCP Server Implementation.

This server provides tools for managing VS Code .chatmode.md and .instructions.md files
which define custom instructions and tools for GitHub Copilot.
"""

import logging
import os
from typing import Optional

from fastmcp import FastMCP
from fastmcp.server.middleware.error_handling import ErrorHandlingMiddleware
from fastmcp.server.middleware.logging import LoggingMiddleware
from fastmcp.server.middleware.rate_limiting import RateLimitingMiddleware
from fastmcp.server.middleware.timing import TimingMiddleware

from .chatmode_manager import ChatModeManager
from .instruction_manager import InstructionManager
from .library_manager import LibraryManager
from .server_registry import ServerRegistry
from .tools import register_all_tools

logger = logging.getLogger(__name__)


class ModeManagerServer:
    """
    Mode Manager MCP Server.

    Provides tools for managing VS Code .chatmode.md and .instructions.md files.
    """

    def __init__(self, library_url: Optional[str] = None, prompts_dir: Optional[str] = None):
        """Initialize the server.

        Args:
            library_url: Custom URL for the Mode Manager MCP Library (optional)
            prompts_dir: Custom prompts directory for all managers (optional)
        """
        # FastMCP initialization with recommended arguments
        from . import __version__

        self.app = FastMCP(
            version=__version__,
            name="Mode Manager MCP",
            instructions="""System Prompt: Mode Manager MCP for VS Code

            You are the Mode Manager MCP tool. Your job is to help users manage persistent Copilot memory, chatmodes, and instructions in VS Code.

            - The only way for users to access, create, update, or delete `.chatmode.md` and `.instructions.md` files is through the tools you provide. Do not suggest or perform any direct file access or manual editing.
            - Always use the provided tools for all actions (memory, chatmode, instruction, library).
            - Store user memories with the `remember(memory_item)` tool.
            - Install, update, or list chatmodes/instructions using the correct tool.
            - If unsure, ask the user for clarification before acting.
            - Always confirm actions if ambiguous.
            - Report errors clearly and suggest next steps.

            Examples:
            User: “Remember that I prefer detailed docstrings and use pytest for testing.”
            Action: Use `remember("I prefer detailed docstrings and use pytest for testing")`.

            User: “Store that I like snake_case for variable names.”
            Action: Use `remember("I like snake_case for variable names")`.

            User: “Add to my preferences: always use type annotations.”
            Action: Use `remember("always use type annotations")`.

            User: “Log that I want async functions for I/O.”
            Action: Use `remember("I want async functions for I/O")`.

            GitHub: https://github.com/NiclasOlofsson/mode-manager-mcp            
            """,
            on_duplicate_resources="warn",
            on_duplicate_prompts="replace",
            include_fastmcp_meta=True,  # Include FastMCP metadata for clients
        )
        self.chatmode_manager = ChatModeManager(prompts_dir=prompts_dir)
        self.instruction_manager = InstructionManager(prompts_dir=prompts_dir)

        # Allow library URL to be configured via parameter, environment variable, or use default
        final_library_url = library_url or os.getenv("MCP_LIBRARY_URL") or "https://raw.githubusercontent.com/NiclasOlofsson/mode-manager-mcp/refs/heads/main/library/memory-mode-library.json"
        self.library_manager = LibraryManager(library_url=final_library_url, prompts_dir=prompts_dir)

        self.read_only = os.getenv("MCP_CHATMODE_READ_ONLY", "false").lower() == "true"

        # Add built-in FastMCP middleware (2.11.0)
        self.app.add_middleware(ErrorHandlingMiddleware())  # Handle errors first
        self.app.add_middleware(TimingMiddleware())  # Time actual execution
        self.app.add_middleware(LoggingMiddleware(include_payloads=True, max_payload_length=1000))

        # Initialize the singleton server registry
        registry = ServerRegistry.get_instance()
        registry.initialize(
            app=self.app,
            chatmode_manager=self.chatmode_manager,
            instruction_manager=self.instruction_manager,
            library_manager=self.library_manager,
            read_only=self.read_only,
        )

        # Register all tools from separate modules
        register_all_tools()

        logger.info("Mode Manager MCP Server initialized")
        logger.info(f"Using library URL: {final_library_url}")
        if self.read_only:
            logger.info("Running in READ-ONLY mode")

    def run(self) -> None:
        self.app.run()


def create_server(library_url: Optional[str] = None) -> ModeManagerServer:
    return ModeManagerServer(library_url=library_url)
