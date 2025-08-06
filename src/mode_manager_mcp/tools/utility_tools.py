"""Utility tools for prompts, memory, and onboarding functionality."""

import datetime
import logging
from typing import Annotated

from fastmcp import Context
from fastmcp.prompts.prompt import Message
from mcp.types import TextContent
from pydantic import BaseModel

from ..instruction_manager import INSTRUCTION_FILE_EXTENSION
from ..server_registry import get_server_registry

logger = logging.getLogger(__name__)


def register_utility_tools() -> None:
    """Register utility tools (prompts, memory, onboarding) with the server."""
    registry = get_server_registry()
    app = registry.app
    instruction_manager = registry.instruction_manager
    read_only = registry.read_only

    @app.tool(
        name="get_prompts_directory",
        description="Get the path to the VS Code prompts directory.",
        tags={"public", "prompts"},
        annotations={
            "idempotentHint": True,
            "readOnlyHint": True,
            "title": "Get Prompts Directory",
            "returns": "Returns the absolute path to the VS Code prompts directory where .chatmode.md and .instructions.md files are stored.",
        },
        meta={"category": "prompts"},
    )
    def get_prompts_directory() -> str:
        """Get the path to the VS Code prompts directory."""
        try:
            return str(instruction_manager.prompts_dir)
        except Exception as e:
            return f"Error getting prompts directory: {str(e)}"

    class RememberOutput(BaseModel):
        status: str
        message: str
        memory_path: str

    @app.tool(
        name="remember",
        description=(
            "Persistently store a user memory item for future AI conversations. "
            "Use this tool to record preferences, facts, or context that should be available in all future Copilot sessions. "
            "Inputs: memory_item (string, required) — the information to remember. "
            "Output: Confirmation message if successful, or an error message if the operation fails. "
            "Example: 'Remember that I prefer detailed docstrings.'"
        ),
        tags={"public", "memory"},
        annotations={
            "idempotentHint": True,
            "readOnlyHint": False,
            "title": "Remember",
            "parameters": {"memory_item": ("String. The information to remember. This will be timestamped and appended to your memory ")},
            "returns": ("Returns a confirmation message that the memory item has been stored, or an error message if the operation failed. " "If successful, the memory will be available to AI assistants in all future conversations."),
        },
        meta={"category": "memory"},
    )
    async def remember(ctx: Context, memory_item: Annotated[str, "The information to remember"]) -> str:
        """Store a memory item in your personal AI memory for future conversations."""
        if read_only:
            return "Error: Server is running in read-only mode"
        if memory_item is None or memory_item.strip() == "":
            return "Error: No memory item provided."
        try:
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

            memory_content = instruction_manager.get_raw_instruction(memory_filename)
            # Try AI optimization if sampling is available, otherwise just append
            try:
                response = await ctx.sample(
                    """Please analyze and optimize content below for LLM compliance and effectiveness.

                Remove redundancy, clarify ambiguous rules, and ensure all laws are explicit, numbered, and clearly labeled as "Law," "Policy," or "Suggestion/Hint."
                Separate universal laws, project-specific exceptions, policies, preferences, suggestions/hints, and memories/facts.
                Ensure all rules are concise, actionable, and easy for an LLM to follow.
                Output the improved file in markdown, preserving front matter and section headers. 
                The output MUST include the following front matter at the top of the file:
                ---
                applyTo: '**'
                description: Personal AI memory for conversations and preferences
                ---
                This header must only appear once in the output.
                You must only return the content and no other text.
                This is the content I want you to analyze and optimize:
                """
                    + memory_content
                    + "\n"
                    + new_memory_entry,
                    temperature=0.2,  # Lower temperature for more repeatable outcomes
                    max_tokens=1500,
                    model_preferences="gtp-4.1",
                )
                logger.info(f"Proposed optimization for memory file\n{response}")

                if not isinstance(response, TextContent):
                    logger.error(f"AI response was not TextContent, but {type(response)}")
                    # Fallback to simple append
                    updated_content = memory_content + "\n" + new_memory_entry
                else:
                    updated_content = response.text

            except Exception as e:
                logger.info(f"AI sampling not available or failed: {e}. Using simple append.")
                # Fallback to simple append
                updated_content = memory_content + "\n" + new_memory_entry

            instruction_manager.update_instruction(memory_filename, content=updated_content)

            return f"Remembered: {memory_item}\nThis memory will be available to AI assistants when the memory instruction is active in VS Code."
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
                    """

Copilot, follow these onboarding steps for Mode Managers - memory management:
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
