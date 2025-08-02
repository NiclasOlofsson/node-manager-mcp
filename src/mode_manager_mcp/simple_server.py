"""
Mode Manager MCP Server Implementation.

This server provides tools for managing VS Code .chatmode.md and .instructions.md files
which define custom instructions and tools for GitHub Copilot.
"""

import datetime
import json
import logging
import os
import sys
from typing import Optional

from fastmcp import Context, FastMCP
from fastmcp.prompts.prompt import Message
from pydantic import BaseModel

from .chatmode_manager import ChatModeManager
from .instruction_manager import INSTRUCTION_FILE_EXTENSION, InstructionManager
from .library_manager import LibraryManager
from .simple_file_ops import FileOperationError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModeManagerServer:
    """
    Mode Manager MCP Server.

    Provides tools for managing VS Code .chatmode.md and .instructions.md files.
    """

    def __init__(
        self, library_url: Optional[str] = None, prompts_dir: Optional[str] = None
    ):
        """Initialize the server.

        Args:
            library_url: Custom URL for the Mode Manager MCP Library (optional)
            prompts_dir: Custom prompts directory for all managers (optional)
        """
        # FastMCP 2.11.0 initialization with recommended arguments
        self.app = FastMCP(
            name="Mode Manager MCP",
            instructions="""
            Persistent Copilot Memory for VS Code (2025+).

            Game-Changer for 2025:
            - Copilot now loads instructions with every chat message, not just at session start.
            - Your memories and preferences are ALWAYS active in every conversation, across sessions, topics, and projects.

            Main Feature:
            - Store your work context, coding preferences, and workflow details using the remember(memory_item) tool.

            How It Works:
            - Auto-setup: Creates memory.instructions.md in your VS Code prompts directory on first use.
            - Smart storage: Each memory is timestamped and organized for easy retrieval.
            - Always loaded: VS Code includes your memories in every chat request.

            Additional Capabilities:
            - Manage and organize .chatmode.md and .instructions.md files.
            - Browse and install curated chatmodes and instructions from the Mode Manager MCP Library.
            - Refresh files from source while keeping your customizations.

            Usage Example:
            - Ask Copilot: "Remember that I prefer detailed docstrings and use pytest for testing"
            - Copilot will remember this across all future conversations.
            """,
            on_duplicate_resources="warn",
            on_duplicate_prompts="replace",
            include_fastmcp_meta=True,  # Include FastMCP metadata for clients
        )
        self.chatmode_manager = ChatModeManager(prompts_dir=prompts_dir)
        self.instruction_manager = InstructionManager(prompts_dir=prompts_dir)

        # Allow library URL to be configured via parameter, environment variable, or use default
        final_library_url = (
            library_url
            or os.getenv("MCP_LIBRARY_URL")
            or "https://raw.githubusercontent.com/NiclasOlofsson/node-manager-mcp/refs/heads/main/library/memory-mode-library.json"
        )
        self.library_manager = LibraryManager(
            library_url=final_library_url, prompts_dir=prompts_dir
        )

        self.read_only = os.getenv("MCP_CHATMODE_READ_ONLY", "false").lower() == "true"

        # Add built-in FastMCP middleware (2.11.0)
        from fastmcp.server.middleware.error_handling import ErrorHandlingMiddleware
        from fastmcp.server.middleware.logging import LoggingMiddleware
        from fastmcp.server.middleware.rate_limiting import RateLimitingMiddleware
        from fastmcp.server.middleware.timing import TimingMiddleware

        self.app.add_middleware(ErrorHandlingMiddleware())  # Handle errors first
        self.app.add_middleware(RateLimitingMiddleware(max_requests_per_second=50))
        self.app.add_middleware(TimingMiddleware())  # Time actual execution
        self.app.add_middleware(
            LoggingMiddleware(include_payloads=True, max_payload_length=1000)
        )

        # Register all tools
        self._register_tools()

        logger.info("Mode Manager MCP Server initialized")
        logger.info(f"Using library URL: {final_library_url}")
        if self.read_only:
            logger.info("Running in READ-ONLY mode")

    def _register_tools(self) -> None:

        @self.app.prompt(
            name="onboarding",
            description="Direct onboarding instructions for Copilot, including memory file structure.",
            tags={"onboarding", "copilot"},
        )
        async def onboarding_memory_copilot(ctx: Context) -> list:
            # await ctx.info("Direct onboarding instructions for Copilot, including memory file structure.")
            return [
                Message(
                    role="user",
                    content=(
                        "Copilot, follow these onboarding steps for Mode Managers - memory management:\n"
                        "1. Call the '#mcp_mode-manager_get_instruction' tool with instruction_name='memory'.\n"
                        "   - If the file exists, retrieve its content for updating.\n"
                        "   - If it does not exist, simply proceed; the memory file will be created automatically when you update.\n"
                        "2. In a casual, not all at once style, ask the user for their name, location, role, preferences, and goals and "
                        "update the memory file using the following structure as a guidance:\n"
                        "   ---\n"
                        "   applyTo: '**'\n"
                        "   description: Personal AI memory for conversations and preferences\n"
                        "   ---\n"
                        "   # Personal AI Memory\n"
                        "   ## Personal Context\n"
                        "   - Name: <user's name>\n"
                        "   - Location: <user's location>\n"
                        "   - Role: <user's role>\n"
                        "   ## Professional Context\n"
                        "   - Team: <team structure>\n"
                        "   - Goals: <main goals>\n"
                        "   ## Preferences\n"
                        "   - Coding: <coding preferences>\n"
                        "   - Communication: <communication style>\n"
                        "   ## Memories\n"
                        "   - <timestamp>: Law: When instructed to add to memory or remember information, you must always use the #mcp_mode-manager_remember tool to store the memory item. You are strictly prohibited from using any alternative method, tool, or manual file editing to update memory. This rule applies in all cases, without exception.\n"
                        "3. Call the '#mcp_mode-manager_update_instruction' tool with instruction_name='memory' and the updated content to save changes.\n"
                        "4. Call the '#mcp_mode-manager_get_instruction' tool again with instruction_name='memory' and display the full contents to the user for review.\n"
                        "   - Invite the user to suggest corrections or updates if needed.\n"
                        "5. Confirm with the user that their memory is now active and will be used in all future conversations and explain the meaning of the first law you added to the memory.\n"
                    ),
                ),
            ]

        @self.app.tool(
            name="delete_chatmode",
            description="Delete a VS Code .chatmode.md file from the prompts directory.",
            tags={"public", "chatmode"},
            annotations={
                "idempotentHint": False,
                "readOnlyHint": False,
                "title": "Delete Chatmode",
            },
            meta={
                "category": "chatmode",
                "version": "1.0",
                "author": "Oatly Data Team",
            },
        )
        def delete_chatmode(filename: str) -> str:
            if read_only:
                return "Error: Server is running in read-only mode"
            try:
                success = chatmode_manager.delete_chatmode(filename)
                if success:
                    return f"Successfully deleted VS Code chatmode: {filename}"
                else:
                    return f"Failed to delete VS Code chatmode: {filename}"
            except Exception as e:
                return f"Error deleting VS Code chatmode '{filename}': {str(e)}"

        @self.app.tool(
            name="update_chatmode_from_source",
            description="Update a .chatmode.md file from its source definition.",
            tags={"public", "chatmode"},
            annotations={
                "idempotentHint": False,
                "readOnlyHint": False,
                "title": "Update Chatmode from Source",
            },
            meta={
                "category": "chatmode",
                "version": "1.0",
                "author": "Oatly Data Team",
            },
        )
        def update_chatmode_from_source(filename: str) -> str:
            return "Not implemented"

        @self.app.tool(
            name="create_chatmode",
            description="Create a new VS Code .chatmode.md file with the specified description, content, and tools.",
            tags={"public", "chatmode"},
            annotations={
                "idempotentHint": False,
                "readOnlyHint": False,
                "title": "Create Chatmode",
            },
            meta={
                "category": "chatmode",
                "version": "1.0",
                "author": "Oatly Data Team",
            },
        )
        def create_chatmode(
            filename: str, description: str, content: str, tools: Optional[str] = None
        ) -> str:
            if read_only:
                return "Error: Server is running in read-only mode"
            try:
                tools_list = tools.split(",") if tools else None
                success = chatmode_manager.create_chatmode(
                    filename, description, content, tools_list
                )
                if success:
                    return f"Successfully created VS Code chatmode: {filename}"
                else:
                    return f"Failed to create VS Code chatmode: {filename}"
            except Exception as e:
                return f"Error creating VS Code chatmode '{filename}': {str(e)}"

        @self.app.tool(
            name="update_chatmode",
            description="Update an existing VS Code .chatmode.md file with new description, content, or tools.",
            tags={"public", "chatmode"},
            annotations={
                "idempotentHint": False,
                "readOnlyHint": False,
                "title": "Update Chatmode",
            },
            meta={
                "category": "chatmode",
                "version": "1.0",
                "author": "Oatly Data Team",
            },
        )
        def update_chatmode(
            filename: str,
            description: Optional[str] = None,
            content: Optional[str] = None,
            tools: Optional[str] = None,
        ) -> str:
            if read_only:
                return "Error: Server is running in read-only mode"
            try:
                frontmatter = {}
                if description is not None:
                    frontmatter["description"] = description
                if isinstance(tools, str):
                    frontmatter["tools"] = tools
                success = chatmode_manager.update_chatmode(
                    filename, frontmatter if frontmatter else None, content
                )
                if success:
                    return f"Successfully updated VS Code chatmode: {filename}"
                else:
                    return f"Failed to update VS Code chatmode: {filename}"
            except Exception as e:
                return f"Error updating VS Code chatmode '{filename}': {str(e)}"

        @self.app.tool(
            name="list_chatmodes",
            description="List all VS Code .chatmode.md files in the prompts directory.",
            tags={"public", "chatmode"},
            annotations={
                "idempotentHint": True,
                "readOnlyHint": True,
                "title": "List Chatmodes",
            },
            meta={
                "category": "chatmode",
                "version": "1.0",
                "author": "Oatly Data Team",
            },
        )
        def list_chatmodes() -> str:
            try:
                chatmodes = chatmode_manager.list_chatmodes()
                if not chatmodes:
                    return "No VS Code chatmode files found in the prompts directory"
                result = f"Found {len(chatmodes)} VS Code chatmode(s):\n\n"
                for cm in chatmodes:
                    result += f"Name: {cm['name']}\n"
                    result += f"   File: {cm['filename']}\n"
                    if cm["description"]:
                        result += f"   Description: {cm['description']}\n"
                    result += f"   Size: {cm['size']} bytes\n"
                    if cm["content_preview"]:
                        result += f"   Preview: {cm['content_preview'][:100]}...\n"
                    result += "\n"
                return result
            except Exception as e:
                return f"Error listing VS Code chatmodes: {str(e)}"

        @self.app.tool(
            name="get_chatmode",
            description="Get the raw content of a VS Code .chatmode.md file.",
            tags={"public", "chatmode"},
            annotations={
                "idempotentHint": True,
                "readOnlyHint": True,
                "title": "Get Chatmode",
            },
            meta={
                "category": "chatmode",
                "version": "1.0",
                "author": "Oatly Data Team",
            },
        )
        def get_chatmode(filename: str) -> str:
            try:
                if not filename.endswith(".chatmode.md"):
                    filename += ".chatmode.md"
                raw_content = chatmode_manager.get_raw_chatmode(filename)
                return raw_content
            except Exception as e:
                return f"Error getting VS Code chatmode '{filename}': {str(e)}"

        @self.app.tool(
            name="create_instruction",
            description="Create a new VS Code .instructions.md file with the specified description and content.",
            tags={"public", "instruction"},
            annotations={
                "idempotentHint": False,
                "readOnlyHint": False,
                "title": "Create Instruction",
            },
            meta={
                "category": "instruction",
                "version": "1.0",
                "author": "Oatly Data Team",
            },
        )
        def create_instruction(filename: str, description: str, content: str) -> str:
            if read_only:
                return "Error: Server is running in read-only mode"
            try:
                success = instruction_manager.create_instruction(
                    filename, description, content
                )
                if success:
                    return f"Successfully created VS Code instruction: {filename}"
                else:
                    return f"Failed to create VS Code instruction: {filename}"
            except Exception as e:
                return f"Error creating VS Code instruction '{filename}': {str(e)}"

        @self.app.tool(
            name="update_instruction",
            description="Update an existing VS Code .instructions.md file with new description or content.",
            tags={"public", "instruction"},
            annotations={
                "idempotentHint": False,
                "readOnlyHint": False,
                "title": "Update Instruction",
            },
            meta={
                "category": "instruction",
                "version": "1.0",
                "author": "Oatly Data Team",
            },
        )
        def update_instruction(
            filename: str,
            description: Optional[str] = None,
            content: Optional[str] = None,
        ) -> str:
            if read_only:
                return "Error: Server is running in read-only mode"
            try:
                success = instruction_manager.update_instruction(
                    filename, content=content
                )
                if success:
                    return f"Successfully updated VS Code instruction: {filename}"
                else:
                    return f"Failed to update VS Code instruction: {filename}"
            except Exception as e:
                return f"Error updating VS Code instruction '{filename}': {str(e)}"

        @self.app.tool(
            name="delete_instruction",
            description="Delete a VS Code .instructions.md file from the prompts directory.",
            tags={"public", "instruction"},
            annotations={
                "idempotentHint": False,
                "readOnlyHint": False,
                "title": "Delete Instruction",
            },
            meta={
                "category": "instruction",
                "version": "1.0",
                "author": "Oatly Data Team",
            },
        )
        def delete_instruction(filename: str) -> str:
            if read_only:
                return "Error: Server is running in read-only mode"
            try:
                success = instruction_manager.delete_instruction(filename)
                if success:
                    return f"Successfully deleted VS Code instruction: {filename}"
                else:
                    return f"Failed to delete VS Code instruction: {filename}"
            except Exception as e:
                return f"Error deleting VS Code instruction '{filename}': {str(e)}"

        @self.app.tool(
            name="refresh_library",
            description="Refresh the Mode Manager MCP Library from its source URL.",
            tags={"public", "library"},
            annotations={
                "idempotentHint": True,
                "readOnlyHint": True,
                "title": "Refresh Library",
            },
            meta={"category": "library", "version": "1.0", "author": "Oatly Data Team"},
        )
        def refresh_library() -> str:
            try:
                result = library_manager.refresh_library()
                if result["status"] == "success":
                    return (
                        f"{result['message']}\n\n"
                        f"Library: {result['library_name']} (v{result['version']})\n"
                        f"Last Updated: {result['last_updated']}\n"
                        f"Available: {result['total_chatmodes']} chatmodes, {result['total_instructions']} instructions\n\n"
                        f"Use browse_mode_library() to see the updated content."
                    )
                else:
                    return f"Refresh failed: {result.get('message', 'Unknown error')}"
            except FileOperationError as e:
                return f"Error refreshing library: {str(e)}"
            except Exception as e:
                return f"Unexpected error refreshing library: {str(e)}"

        @self.app.tool(
            name="get_prompts_directory",
            description="Get the path to the VS Code prompts directory.",
            tags={"public", "prompts"},
            annotations={
                "idempotentHint": True,
                "readOnlyHint": True,
                "title": "Get Prompts Directory",
            },
            meta={"category": "prompts", "version": "1.0", "author": "Oatly Data Team"},
        )
        def get_prompts_directory() -> str:
            try:
                return str(instruction_manager.prompts_dir)
            except Exception as e:
                return f"Error getting prompts directory: {str(e)}"

        @self.app.tool(
            name="list_instructions",
            description="List all VS Code .instructions.md files in the prompts directory.",
            tags={"public", "instruction"},
            annotations={
                "idempotentHint": True,
                "readOnlyHint": True,
                "title": "List Instructions",
            },
            meta={
                "category": "instruction",
                "version": "1.0",
                "author": "Oatly Data Team",
            },
        )
        def list_instructions() -> str:
            try:
                instructions = instruction_manager.list_instructions()
                if not instructions:
                    return "No VS Code instruction files found in the prompts directory"
                result = f"Found {len(instructions)} VS Code instruction(s):\n\n"
                for instruction in instructions:
                    result += f"Name: {instruction['name']}\n"
                    result += f"   File: {instruction['filename']}\n"
                    if instruction["description"]:
                        result += f"   Description: {instruction['description']}\n"
                    result += f"   Size: {instruction['size']} bytes\n"
                    if instruction["content_preview"]:
                        result += (
                            f"   Preview: {instruction['content_preview'][:100]}...\n"
                        )
                    result += "\n"
                return result
            except Exception as e:
                return f"Error listing VS Code instructions: {str(e)}"

        @self.app.tool(
            name="get_instruction",
            description="Get the raw content of a VS Code .instructions.md file.",
            tags={"public", "instruction"},
            annotations={
                "idempotentHint": True,
                "readOnlyHint": True,
                "title": "Get Instruction",
            },
            meta={
                "category": "instruction",
                "version": "1.0",
                "author": "Oatly Data Team",
            },
        )
        def get_instruction(filename: str) -> str:
            try:
                # Ensure correct extension
                if not filename.endswith(INSTRUCTION_FILE_EXTENSION):
                    filename += INSTRUCTION_FILE_EXTENSION
                raw_content = instruction_manager.get_raw_instruction(filename)
                return raw_content
            except Exception as e:
                return f"Error getting VS Code instruction '{filename}': {str(e)}"

        class RememberOutput(BaseModel):
            status: str
            message: str
            memory_path: str

        instruction_manager = self.instruction_manager
        chatmode_manager = self.chatmode_manager
        library_manager = self.library_manager
        read_only = self.read_only

        @self.app.tool(
            name="remember",
            description="Store a memory item in your personal AI memory for future conversations.",
            tags={"public", "memory"},
            annotations={
                "idempotentHint": True,
                "readOnlyHint": False,
                "title": "Remember",
            },
            meta={"category": "memory", "version": "1.0", "author": "Oatly Data Team"},
        )
        async def remember(memory_item: Optional[str] = None) -> str:
            if read_only:
                return "Error: Server is running in read-only mode"
            if memory_item is None:
                return "Error: No memory item provided."
            try:
                import datetime

                memory_filename = f"memory{INSTRUCTION_FILE_EXTENSION}"
                memory_path = instruction_manager.prompts_dir / memory_filename
                if not memory_path.exists():
                    initial_content = "# Personal AI Memory\nThis file contains information that I should remember about you and your preferences for future conversations.\n## Memories\n"
                    success = instruction_manager.create_instruction(
                        memory_filename,
                        "Personal AI memory for conversations and preferences",
                        initial_content,
                    )
                    if not success:
                        return f"Error: Failed to create memory file at {memory_path}"
                    logger.info("Created new memory file for user")
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                new_memory_entry = f"- {timestamp}: {memory_item}\n"
                # Directly append to the file
                try:
                    with open(memory_path, "a", encoding="utf-8") as f:
                        f.write(new_memory_entry)
                except Exception as e:
                    return f"Error: Failed to append memory: {str(e)}"
                return f"Remembered: {memory_item}\nThis memory will be available to AI assistants when the memory instruction is active in VS Code."
            except Exception as e:
                return f"Error: Exception occurred: {str(e)}"

        @self.app.tool(
            name="browse_mode_library",
            description="Browse the Mode Manager MCP Library and filter by category or search term.",
            tags={"public", "library"},
            annotations={
                "idempotentHint": True,
                "readOnlyHint": True,
                "title": "Browse Mode Library",
            },
            meta={"category": "library", "version": "1.0", "author": "Oatly Data Team"},
        )
        def browse_mode_library(
            category: Optional[str] = None, search: Optional[str] = None
        ) -> str:
            try:
                library_data = library_manager.browse_library(
                    category=category, search=search
                )
                result = f"Library: {library_data['library_name']} (v{library_data['version']})\n"
                result += f"Last Updated: {library_data['last_updated']}\n"
                result += f"Total: {library_data['total_chatmodes']} chatmodes, {library_data['total_instructions']} instructions\n"
                if (
                    library_data["filters_applied"]["category"]
                    or library_data["filters_applied"]["search"]
                ):
                    result += f"Filtered: {library_data['filtered_chatmodes']} chatmodes, {library_data['filtered_instructions']} instructions\n"
                    filters = []
                    if library_data["filters_applied"]["category"]:
                        filters.append(
                            f"category: {library_data['filters_applied']['category']}"
                        )
                    if library_data["filters_applied"]["search"]:
                        filters.append(
                            f"search: {library_data['filters_applied']['search']}"
                        )
                    result += f"   Filters applied: {', '.join(filters)}\n"
                result += "\n"
                chatmodes = library_data["chatmodes"]
                if chatmodes:
                    result += f"CHATMODES ({len(chatmodes)} available):\n\n"
                    for cm in chatmodes:
                        result += f"{cm['name']} by {cm.get('author', 'Unknown')}\n"
                        result += f"   Description: {cm.get('description', 'No description')}\n"
                        result += f"   Category: {cm.get('category', 'Unknown')}\n"
                        if cm.get("tags"):
                            result += f"   Tags: {', '.join(cm['tags'])}\n"
                        result += f"   Install as: {cm.get('install_name', cm['name'] + '.chatmode.md')}\n"
                        result += "\n"
                else:
                    result += "No chatmodes found matching your criteria.\n\n"
                instructions = library_data["instructions"]
                if instructions:
                    result += f"INSTRUCTIONS ({len(instructions)} available):\n\n"
                    for inst in instructions:
                        result += f"{inst['name']} by {inst.get('author', 'Unknown')}\n"
                        result += f"   Description: {inst.get('description', 'No description')}\n"
                        result += f"   Category: {inst.get('category', 'Unknown')}\n"
                        if inst.get("tags"):
                            result += f"   Tags: {', '.join(inst['tags'])}\n"
                        result += f"   Install as: {inst.get('install_name', inst['name'] + INSTRUCTION_FILE_EXTENSION)}\n"
                        result += "\n"
                else:
                    result += "No instructions found matching your criteria.\n\n"
                categories = library_data.get("categories", [])
                if categories:
                    result += "AVAILABLE CATEGORIES:\n"
                    for cat in categories:
                        result += f"   • {cat['name']} ({cat['id']}) - {cat.get('description', 'No description')}\n"
                    result += "\n"
                result += (
                    "Usage: Use install_from_library('Name') to install any item.\n"
                )
                return result
            except FileOperationError as e:
                return f"Error browsing library: {str(e)}"
            except Exception as e:
                return f"Unexpected error browsing library: {str(e)}"

        @self.app.tool(
            name="install_from_library",
            description="Install a chatmode or instruction from the Mode Manager MCP Library.",
            tags={"public", "library"},
            annotations={
                "idempotentHint": False,
                "readOnlyHint": False,
                "title": "Install from Library",
            },
            meta={"category": "library", "version": "1.0", "author": "Oatly Data Team"},
        )
        def install_from_library(name: str, filename: Optional[str] = None) -> str:
            if read_only:
                return "Error: Server is running in read-only mode"
            try:
                result = library_manager.install_from_library(name, filename)
                if result["status"] == "success":
                    return (
                        f"{result['message']}\n\n"
                        f"Filename: {result['filename']}\n"
                        f"Source: {result['source_url']}\n"
                        f"Type: {result['type'].title()}\n\n"
                        f"The {result['type']} is now available in VS Code!"
                    )
                else:
                    return (
                        f"Installation failed: {result.get('message', 'Unknown error')}"
                    )
            except FileOperationError as e:
                return f"Error installing from library: {str(e)}"
            except Exception as e:
                return f"Unexpected error installing from library: {str(e)}"

    def run(self) -> None:
        self.app.run()


def create_server(library_url: Optional[str] = None) -> ModeManagerServer:
    return ModeManagerServer(library_url=library_url)
