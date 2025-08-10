"""
Mode Manager for VS Code .instructions.md files.

This module handles instruction files which define custom instructions
and workspace-specific AI guidance for VS Code Copilot.

Note: This file has been refactored to eliminate DRY violations.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import unquote

from .path_utils import get_vscode_prompts_directory
from .simple_file_ops import (
    FileOperationError,
    parse_frontmatter,
    parse_frontmatter_file,
    safe_delete_file,
    write_frontmatter_file,
)
from .types import LanguagePattern, MemoryScope

logger = logging.getLogger(__name__)


INSTRUCTION_FILE_EXTENSION = ".instructions.md"


class MemoryFileConfig:
    """Configuration for memory file creation."""

    def __init__(self, scope: MemoryScope, language: Optional[str] = None):
        self.scope = scope
        self.language = language

    @property
    def filename(self) -> str:
        """Generate the appropriate filename for the memory file."""
        if self.language:
            return f"memory-{self.language.lower()}{INSTRUCTION_FILE_EXTENSION}"
        return f"memory{INSTRUCTION_FILE_EXTENSION}"

    @property
    def description(self) -> str:
        """Generate the appropriate description for the memory file."""
        if self.language:
            return f"Personal AI memory for {self.language} development"
        elif self.scope == MemoryScope.workspace:
            return "Workspace-specific AI memory for this project"
        else:
            return "Personal AI memory for conversations and preferences"

    @property
    def initial_content(self) -> str:
        """Generate the initial content for the memory file."""
        title = f"# {'Workspace' if self.scope == MemoryScope.workspace else 'Personal'} AI Memory"
        if self.language:
            title += f" - {self.language.title()}"

        description = f"\nThis file contains {'workspace-specific' if self.scope == MemoryScope.workspace else 'personal'} information for AI conversations."
        if self.language:
            description += f" Specifically for {self.language} development."

        return title + description + "\n\n## Memories\n"


class InstructionManager:
    """Manages VS Code .instructions.md files in both user and workspace prompts directories."""

    def __init__(self, prompts_dir: Optional[Union[str, Path]] = None):
        """
        Initialize instruction manager.

        Args:
            prompts_dir: Custom prompts directory (default: VS Code user dir + prompts)
        """
        if prompts_dir:
            self.prompts_dir = Path(prompts_dir)
        else:
            self.prompts_dir = get_vscode_prompts_directory()

        # Ensure prompts directory exists
        self.prompts_dir.mkdir(parents=True, exist_ok=True)

        # Workspace instructions directory (current working directory + .github/instructions)
        self.workspace_prompts_dir = Path(os.getcwd()) / ".github" / "instructions"

        logger.info(f"Instruction manager initialized with prompts directory: {self.prompts_dir}")
        logger.info(f"Workspace instructions directory: {self.workspace_prompts_dir}")

    def _decode_workspace_root(self, workspace_root: Optional[str]) -> Optional[str]:
        """Decode workspace root URL if needed."""
        if workspace_root is None:
            return None
        return unquote(workspace_root) if "%" in workspace_root else workspace_root

    def _ensure_instruction_extension(self, filename: str) -> str:
        """Ensure filename has the correct .instructions.md extension."""
        return filename if filename.endswith(INSTRUCTION_FILE_EXTENSION) else filename + INSTRUCTION_FILE_EXTENSION

    def _build_workspace_instructions_path(self, workspace_root: str) -> Path:
        """Build workspace instructions directory path."""
        decoded_root = self._decode_workspace_root(workspace_root)
        if decoded_root is None:
            raise ValueError("Workspace root cannot be None")
        return Path(decoded_root) / ".github" / "instructions"

    def _get_prompts_dir(self, scope: MemoryScope = MemoryScope.user, workspace_root: Optional[str] = None) -> Path:
        """Get the appropriate prompts directory based on scope."""
        if scope == MemoryScope.workspace:
            if workspace_root:
                return self._build_workspace_instructions_path(workspace_root)
            return self.workspace_prompts_dir
        return self.prompts_dir

    def _ensure_workspace_instructions_dir(self, workspace_root: Optional[str] = None) -> None:
        """Ensure workspace instructions directory exists."""
        if workspace_root:
            workspace_dir = self._build_workspace_instructions_path(workspace_root)
            workspace_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.workspace_prompts_dir.mkdir(parents=True, exist_ok=True)

    def _get_apply_to_pattern(self, language: Optional[str] = None) -> str:
        """Get the appropriate applyTo pattern based on language."""
        if not language:
            return LanguagePattern.get_all_pattern()

        return LanguagePattern.get_pattern(language)

    def create_memory(
        self,
        memory_item: str,
        scope: MemoryScope = MemoryScope.user,
        language: Optional[str] = None,
        workspace_root: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create or append to a memory instruction file.

        Args:
            memory_item: The memory item to store
            scope: "user" or "workspace"
            language: Optional language for language-specific memory
            workspace_root: Optional workspace root path (for workspace scope)

        Returns:
            Dict with operation result details

        Raises:
            FileOperationError: If operation fails
        """
        if scope == MemoryScope.workspace:
            if workspace_root is None:
                raise FileOperationError("Workspace root is required for workspace scope memory operations")
            # Use the provided workspace root, URL-decoded in case it comes from a FileUrl
            self.workspace_prompts_dir = self._build_workspace_instructions_path(workspace_root)
            self._ensure_workspace_instructions_dir(workspace_root)

        prompts_dir = self._get_prompts_dir(scope, workspace_root)
        apply_to_pattern = self._get_apply_to_pattern(language)

        # Use MemoryFileConfig to handle file configuration
        config = MemoryFileConfig(scope, language)
        filename = config.filename
        description = config.description

        file_path = prompts_dir / filename

        # Create file if it doesn't exist
        if not file_path.exists():
            initial_content = config.initial_content

            frontmatter = {"applyTo": apply_to_pattern, "description": description}

            success = write_frontmatter_file(file_path, frontmatter, initial_content, create_backup=False)
            if not success:
                raise FileOperationError(f"Failed to create memory file: {filename}")

        # Append the memory item
        import datetime

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        new_memory_entry = f"- **{timestamp}:** {memory_item}\n"

        success = self.append_to_section(filename, "Memories", new_memory_entry, scope, workspace_root)
        if not success:
            raise FileOperationError(f"Failed to append memory to: {filename}")

        return {
            "status": "success",
            "filename": filename,
            "scope": scope,
            "language": language,
            "path": str(file_path),
            "apply_to": apply_to_pattern,
        }

    async def create_memory_with_optimization(
        self,
        memory_item: str,
        ctx: Any,  # FastMCP Context
        scope: MemoryScope = MemoryScope.user,
        language: Optional[str] = None,
        workspace_root: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Enhanced create_memory that includes smart optimization.

        Fully backward compatible with existing memory files.
        """
        # First, create/append memory using existing logic
        result = self.create_memory(memory_item, scope, language, workspace_root)

        if result["status"] == "success":
            # Try to optimize if needed
            from .memory_optimizer import MemoryOptimizer

            file_path = Path(result["path"])
            optimizer = MemoryOptimizer(self)

            optimization_result = await optimizer.optimize_memory_if_needed(file_path, ctx)

            # Add optimization info to result
            result["optimization"] = optimization_result

            # Update success message based on optimization outcome
            if optimization_result["status"] == "optimized":
                result["message"] = f"Memory added and optimized: {memory_item}"
            elif optimization_result["status"] == "metadata_updated":
                result["message"] = f"Memory added with metadata update: {memory_item}"
            else:
                result["message"] = f"Memory added: {memory_item}"

        return result

    def append_to_section(
        self,
        instruction_name: str,
        section_header: str,
        new_entry: str,
        scope: MemoryScope = MemoryScope.user,
        workspace_root: Optional[str] = None,
    ) -> bool:
        """
        Append a new entry to the end of an instruction file (fast append).

        Args:
            instruction_name: Name of the .instructions.md file
            section_header: Ignored (kept for compatibility)
            new_entry: Content to append (should include any formatting, e.g., '- ...')
            scope: "user" or "workspace" to determine which directory to use
            workspace_root: Optional workspace root path (for workspace scope)

        Returns:
            True if successful

        Raises:
            FileOperationError: If file cannot be updated
        """
        instruction_name = self._ensure_instruction_extension(instruction_name)

        prompts_dir = self._get_prompts_dir(scope, workspace_root)
        file_path = prompts_dir / instruction_name

        if not file_path.exists():
            raise FileOperationError(f"Instruction file not found: {instruction_name}")

        try:
            with open(file_path, "a", encoding="utf-8") as f:
                # Ensure entry ends with a newline
                entry = new_entry if new_entry.endswith("\n") else new_entry + "\n"
                f.write(entry)
            logger.info(f"Appended entry to end of: {file_path}")
            return True
        except Exception as e:
            raise FileOperationError(f"Error appending entry to {instruction_name}: {e}")

    def list_instructions(self, scope: MemoryScope = MemoryScope.user) -> List[Dict[str, Any]]:
        """
        List all .instructions.md files in the prompts directory.

        Args:
            scope: "user" or "workspace" to determine which directory to list

        Returns:
            List of instruction file information
        """
        instructions: List[Dict[str, Any]] = []

        prompts_dir = self._get_prompts_dir(scope)
        if not prompts_dir.exists():
            return instructions

        for file_path in prompts_dir.glob(f"*{INSTRUCTION_FILE_EXTENSION}"):
            try:
                frontmatter, content = parse_frontmatter_file(file_path)

                # Get preview of content (first 100 chars)
                content_preview = content.strip()[:100] if content.strip() else ""

                instruction_info = {
                    "filename": file_path.name,
                    "name": file_path.name.replace(INSTRUCTION_FILE_EXTENSION, ""),
                    "path": str(file_path),
                    "description": frontmatter.get("description", ""),
                    "frontmatter": frontmatter,
                    "content_preview": content_preview,
                    "size": file_path.stat().st_size,
                    "modified": file_path.stat().st_mtime,
                    "scope": scope,
                }

                instructions.append(instruction_info)

            except Exception as e:
                logger.warning(f"Error reading instruction file {file_path}: {e}")
                continue

        # Sort by name
        instructions.sort(key=lambda x: x["name"].lower())
        return instructions

    def get_instruction(self, instruction_name: str, scope: MemoryScope = MemoryScope.user) -> Dict[str, Any]:
        """
        Get content and metadata of a specific instruction file.

        Args:
            instruction_name: Name of the .instructions.md file
            scope: "user" or "workspace" to determine which directory to use

        Returns:
            Instruction data including frontmatter and content

        Raises:
            FileOperationError: If file cannot be read
        """

        # Ensure filename has correct extension
        instruction_name = self._ensure_instruction_extension(instruction_name)

        prompts_dir = self._get_prompts_dir(scope)
        file_path = prompts_dir / instruction_name

        if not file_path.exists():
            raise FileOperationError(f"Instruction file not found: {instruction_name}")

        try:
            frontmatter, content = parse_frontmatter_file(file_path)

            return {
                "instruction_name": instruction_name,
                "name": instruction_name.replace(INSTRUCTION_FILE_EXTENSION, ""),
                "path": str(file_path),
                "description": frontmatter.get("description", ""),
                "frontmatter": frontmatter,
                "content": content,
                "size": file_path.stat().st_size,
                "modified": file_path.stat().st_mtime,
                "scope": scope,
            }

        except Exception as e:
            raise FileOperationError(f"Error reading instruction file {instruction_name}: {e}")

    def get_raw_instruction(self, instruction_name: str, scope: MemoryScope = MemoryScope.user) -> str:
        """
        Get the raw file content of a specific instruction file without any processing.

        Args:
            instruction_name: Name of the .instructions.md file
            scope: "user" or "workspace" to determine which directory to use

        Returns:
            Raw file content as string

        Raises:
            FileOperationError: If file cannot be read
        """

        # Ensure filename has correct extension
        instruction_name = self._ensure_instruction_extension(instruction_name)

        prompts_dir = self._get_prompts_dir(scope)
        file_path = prompts_dir / instruction_name

        if not file_path.exists():
            raise FileOperationError(f"Instruction file not found: {instruction_name}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

        except Exception as e:
            raise FileOperationError(f"Error reading raw instruction file {instruction_name}: {e}")

    def create_instruction(self, instruction_name: str, description: str, content: str) -> bool:
        """
        Create a new instruction file.

        Args:
            instruction_name: Name for the new .instructions.md file
            description: Description of the instruction
            content: Instruction content

        Returns:
            True if successful

        Raises:
            FileOperationError: If file cannot be created
        """

        # Ensure filename has correct extension
        instruction_name = self._ensure_instruction_extension(instruction_name)

        file_path = self.prompts_dir / instruction_name

        if file_path.exists():
            raise FileOperationError(f"Instruction file already exists: {instruction_name}")

        # Create frontmatter with applyTo field so instructions are actually applied
        frontmatter: Dict[str, Any] = {"applyTo": "**", "description": description}

        try:
            success = write_frontmatter_file(file_path, frontmatter, content, create_backup=False)
            if success:
                logger.info(f"Created instruction file: {instruction_name}")
            return success

        except Exception as e:
            raise FileOperationError(f"Error creating instruction file {instruction_name}: {e}")

    def update_instruction(
        self,
        instruction_name: str,
        frontmatter: Optional[Dict[str, Any]] = None,
        content: Optional[str] = None,
    ) -> bool:
        """
        Replace the content and/or frontmatter of an instruction file.

        This method is for full rewrites. To append to a section, use append_to_section.

        Args:
            instruction_name: Name of the .instructions.md file
            frontmatter: New frontmatter (optional)
            content: New content (optional, replaces all markdown content)

        Returns:
            True if successful

        Raises:
            FileOperationError: If file cannot be updated
        """
        # Ensure filename has correct extension
        instruction_name = self._ensure_instruction_extension(instruction_name)

        file_path = self.prompts_dir / instruction_name

        if not file_path.exists():
            raise FileOperationError(f"Instruction file not found: {instruction_name}")

        try:
            # Read current content
            current_frontmatter, current_content = parse_frontmatter_file(file_path)

            if content is not None and frontmatter is None:
                # We check if the content is actually including yaml
                frontmatter, content = parse_frontmatter(content)

            # Use provided values or keep current ones
            new_frontmatter = frontmatter if frontmatter is not None else current_frontmatter
            # If new content is provided, replace all markdown content
            if content is not None:
                new_content = content
            else:
                new_content = current_content

            success = write_frontmatter_file(file_path, new_frontmatter, new_content, create_backup=True)
            if success:
                logger.info(f"Updated instruction file with backup: {instruction_name}")
            return success

        except Exception as e:
            raise FileOperationError(f"Error updating instruction file {instruction_name}: {e}")

    def delete_instruction(self, instruction_name: str) -> bool:
        """
        Delete an instruction file with automatic backup.

        Args:
            instruction_name: Name of the .instructions.md file

        Returns:
            True if successful

        Raises:
            FileOperationError: If file cannot be deleted
        """

        # Ensure filename has correct extension
        instruction_name = self._ensure_instruction_extension(instruction_name)

        file_path = self.prompts_dir / instruction_name

        if not file_path.exists():
            raise FileOperationError(f"Instruction file not found: {instruction_name}")

        try:
            # Use safe delete which creates backup automatically
            safe_delete_file(file_path, create_backup=True)
            logger.info(f"Deleted instruction file with backup: {instruction_name}")
            return True

        except Exception as e:
            raise FileOperationError(f"Error deleting instruction file {instruction_name}: {e}")

    def get_memory_file_path(self, scope: MemoryScope = MemoryScope.user, language: Optional[str] = None, workspace_root: Optional[str] = None) -> Path:
        """
        Get the path to a memory file.

        Args:
            scope: Memory scope (user or workspace)
            language: Optional language for language-specific memory
            workspace_root: Optional workspace root path (for workspace scope)

        Returns:
            Path to the memory file
        """
        prompts_dir = self._get_prompts_dir(scope, workspace_root)
        config = MemoryFileConfig(scope, language)
        return prompts_dir / config.filename
