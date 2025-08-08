"""Memory and remember tools for persistent AI conversations."""

import datetime
import logging
import os
from pathlib import Path
from typing import Annotated, Optional
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from fastmcp import Context
from fastmcp.prompts.prompt import Message
from mcp.types import TextContent
from pydantic import BaseModel

from ..instruction_manager import INSTRUCTION_FILE_EXTENSION
from ..server_registry import get_server_registry
from ..types import MemoryScope

logger = logging.getLogger(__name__)


def _seems_workspace_specific(memory_item: str) -> bool:
    """Check if a memory item seems to be workspace/project-specific."""
    workspace_keywords = [
        "this project",
        "this workspace",
        "this codebase",
        "this repo",
        "this repository",
        "our project",
        "our codebase",
        "our team",
        "we use",
        "we prefer",
        "project uses",
        "project requires",
        "workspace",
        "locally",
        "in this app",
        "in this application",
        "this service",
    ]

    return any(keyword in memory_item.lower() for keyword in workspace_keywords)


async def _create_user_memory(ctx: Context, memory_item: str, language: Optional[str] = None) -> dict:
    """Create user-level memory (existing behavior with language support)."""
    registry = get_server_registry()
    instruction_manager = registry.instruction_manager

    try:
        result = instruction_manager.create_memory(memory_item, scope=MemoryScope.user, language=language)
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def _create_workspace_memory(ctx: Context, memory_item: str, language: Optional[str] = None) -> dict:
    """Create workspace-level memory using the context root."""
    registry = get_server_registry()
    instruction_manager = registry.instruction_manager

    try:
        # Get the workspace root from context
        workspace_root_str: Optional[str] = None
        try:
            roots = await ctx.list_roots()
            if roots:
                # Use the first root as the workspace root
                root_uri = roots[0].uri
                parsed = urlparse(root_uri.encoded_string())
                host = "{0}{0}{mnt}{0}".format(os.path.sep, mnt=parsed.netloc)
                normpath = os.path.normpath(
                    os.path.join(host, url2pathname(unquote(parsed.path)))
                )
                workspace_root_str = normpath
        except Exception as e:
            logger.warning(f"Failed to get workspace root from context: {e}")

        logger.info(f"Using workspace root from context: {workspace_root_str}")

        # If we couldn't get a workspace root, return an error
        if workspace_root_str is None:
            return {"status": "error", "message": "Sorry, but I couldn't find the workspace root. Workspace memory requires access to the current workspace context."}

        result = instruction_manager.create_memory(memory_item, scope=MemoryScope.workspace, language=language, workspace_root=workspace_root_str)
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}


def register_remember_tools() -> None:
    """Register memory and remember tools with the server."""
    registry = get_server_registry()
    app = registry.app
    instruction_manager = registry.instruction_manager
    read_only = registry.read_only

    @app.tool(
        name="remember",
        description=(
            "Store user information persistently for future conversations. When users share preferences, "
            "coding standards, project details, or any context they want remembered, use this tool. "
            "Extract the key information from natural language and store it appropriately. "
            "The system automatically detects scope (user/workspace) and language specificity from context. "
            "For ambiguous cases, you will receive clarification prompts to ask the user. "
            "Examples of what to remember: coding preferences ('I like detailed docstrings'), "
            "project specifics ('This app uses PostgreSQL'), language standards ('For Python, use type hints'), "
            "workflow preferences ('Always run tests before committing'). "
            "Use only the memory_item parameter with natural language - the system handles scope detection."
        ),
        tags={"public", "memory", "remember"},
        annotations={
            "idempotentHint": True,
            "readOnlyHint": False,
            "title": "Remember",
            "parameters": {
                "memory_item": "Extract and store the key information the user wants remembered. Use natural language, preserving important details and context.",
                "scope": "Usually omit this parameter - let the system auto-detect. Only specify 'workspace' for clearly project-specific items, 'user' for personal preferences.",
                "language": "Usually omit this parameter - let the system auto-detect. Only specify when the user explicitly mentions a programming language context.",
            },
            "returns": (
                "Returns confirmation of what was stored and where (global/workspace, language-specific if applicable). "
                "If the system detects ambiguous scope, you will receive a clarification request to ask the user. "
                "Always acknowledge what was remembered and explain how it will help in future conversations."
            ),
        },
        meta={"category": "memory"},
    )
    async def remember(
        ctx: Context,
        memory_item: Annotated[str, "The information to remember"],
        scope: Annotated[str, "Memory scope: 'user' (default) or 'workspace'"] = "user",
        language: Annotated[Optional[str], "Optional programming language for language-specific memory"] = None,
    ) -> str:
        """Store a memory item with support for user/workspace scope and language-specific memory."""
        if read_only:
            return "Error: Server is running in read-only mode"
        if memory_item is None or memory_item.strip() == "":
            return "Error: No memory item provided."

        try:
            roots = await ctx.list_roots()
            logger.info(f"Available roots: {', '.join(str(r) for r in roots)} - Remembering: {memory_item} (scope: {scope}, language: {language})")
        except Exception as e:
            # Handle case where list_roots is not supported (e.g., in tests)
            logger.warning(f"Failed to get roots: {e} - Remembering: {memory_item} (scope: {scope}, language: {language})")
            roots = []

        # Validate scope and convert to enum
        try:
            scope_enum = MemoryScope(scope)
        except ValueError:
            return f"Error: Scope must be '{MemoryScope.user}' or '{MemoryScope.workspace}'."

        # If scope is ambiguous based on memory content, ask for clarification
        if scope_enum == MemoryScope.user and _seems_workspace_specific(memory_item):
            return f"The memory item '{memory_item}' seems project-specific. " f"Should this be stored as workspace memory instead? " f"Please clarify by calling remember again with scope='{MemoryScope.workspace}' if needed."

        try:
            if scope_enum == MemoryScope.user:
                result = await _create_user_memory(ctx, memory_item, language)
            else:  # workspace
                result = await _create_workspace_memory(ctx, memory_item, language)

            if result["status"] == "success":
                scope_desc = "workspace" if scope_enum == MemoryScope.workspace else "global"
                lang_desc = f" for {language}" if language else ""
                return f"Remembered: {memory_item}\n" f"Stored in {scope_desc} memory{lang_desc}.\n" f"File: {result['filename']}\n" f"This memory will be available to AI assistants when the memory instruction is active in VS Code."
            else:
                return f"Error: {result.get('message', 'Unknown error occurred')}"

        except Exception as e:
            return f"Error: Exception occurred: {str(e)}"

    @app.prompt(
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
                    """Copilot, follow these onboarding steps for Mode Managers - memory management:
                    1. Call the '#mcp_mode-manager_get_instruction' tool with instruction_name='memory'.
                    - If the file exists, retrieve its content for updating.
                    - If it does not exist, simply proceed; the memory file will be created automatically when you update.
                    2. In a casual, one question at the time, ask the user for their name, location, role, preferences, and goals. If you already have the knowelege, skipe the question. 
                    3. When finished with the questions, update the memory file with inspiration from the frontmatter structure witihin the pre-formatted block below as a guidance. 
                    You MUST merge with existing content.
                    You MUST make sure no existing content is deleted.
                    You MUST make sure nothing is duplicated:
                    ```
                    ---
                    applyTo: '**'
                    description: Personal AI memory for conversations and preferences
                    ---
                    # Personal AI Memory
                    ## Personal Context
                    - Name: <user's name>
                    - Location: <user's location>
                    - Role: <user's role>
                    ## Professional Context
                    - Team: <team structure>
                    - Goals: <main goals>
                    ## Preferences
                    - Coding: <coding preferences>
                    - Communication: <communication style>
                    ## Memories
                    - <timestamp>: Law: When instructed to add to memory or remember information, you must always use the #mcp_mode-manager_remember tool to store the memory item. You are strictly prohibited from using any alternative method, tool, or manual file editing to update memory. This rule applies in all cases, without exception.
                    ```
                    3. Call the '#mcp_mode-manager_update_instruction' tool with instruction_name='memory' and the updated content to save changes.
                    4. Call the '#mcp_mode-manager_get_instruction' tool again with instruction_name='memory' and display the full contents to the user for review.
                        - Invite the user to suggest corrections or updates if needed.
                    5. Confirm with the user that their memory is now active and will be used in all future conversations and explain the meaning of the first law you added to the memory.

                    """
                ),
            ),
        ]
