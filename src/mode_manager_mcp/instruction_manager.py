"""
Mode Manager for VS Code .instructions.md files.

This module handles instruction files which define custom instructions
and workspace-specific AI guidance for VS Code Copilot.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .path_utils import get_vscode_prompts_directory
from .simple_file_ops import (
    FileOperationError,
    parse_frontmatter_file,
    safe_delete_file,
    write_frontmatter_file,
)

logger = logging.getLogger(__name__)


INSTRUCTION_FILE_EXTENSION = ".instructions.md"


class InstructionManager:
    def append_to_section(
        self,
        instruction_name: str,
        section_header: str,
        new_entry: str,
    ) -> bool:
        """
        Append a new entry to the end of an instruction file (fast append).

        Args:
            instruction_name: Name of the .instructions.md file
            section_header: Ignored (kept for compatibility)
            new_entry: Content to append (should include any formatting, e.g., '- ...')

        Returns:
            True if successful

        Raises:
            FileOperationError: If file cannot be updated
        """
        if not instruction_name.endswith(INSTRUCTION_FILE_EXTENSION):
            instruction_name += INSTRUCTION_FILE_EXTENSION

        file_path = self.prompts_dir / instruction_name

        if not file_path.exists():
            raise FileOperationError(f"Instruction file not found: {instruction_name}")

        try:
            with open(file_path, "a", encoding="utf-8") as f:
                # Ensure entry ends with a newline
                entry = new_entry if new_entry.endswith("\n") else new_entry + "\n"
                f.write(entry)
            logger.info(f"Appended entry to end of: {instruction_name}")
            return True
        except Exception as e:
            raise FileOperationError(
                f"Error appending entry to {instruction_name}: {e}"
            )

    """
    Manages VS Code .instructions.md files in the prompts directory.
    """

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

        logger.info(
            f"Instruction manager initialized with prompts directory: {self.prompts_dir}"
        )

    def list_instructions(self) -> List[Dict[str, Any]]:
        """
        List all .instructions.md files in the prompts directory.

        Returns:
            List of instruction file information
        """
        instructions: List[Dict[str, Any]] = []

        if not self.prompts_dir.exists():
            return instructions

        for file_path in self.prompts_dir.glob(f"*{INSTRUCTION_FILE_EXTENSION}"):
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
                }

                instructions.append(instruction_info)

            except Exception as e:
                logger.warning(f"Error reading instruction file {file_path}: {e}")
                continue

        # Sort by name
        instructions.sort(key=lambda x: x["name"].lower())
        return instructions

    def get_instruction(self, instruction_name: str) -> Dict[str, Any]:
        """
        Get content and metadata of a specific instruction file.

        Args:
            instruction_name: Name of the .instructions.md file

        Returns:
            Instruction data including frontmatter and content

        Raises:
            FileOperationError: If file cannot be read
        """

        # Ensure filename has correct extension
        if not instruction_name.endswith(INSTRUCTION_FILE_EXTENSION):
            instruction_name += INSTRUCTION_FILE_EXTENSION

        file_path = self.prompts_dir / instruction_name

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
            }

        except Exception as e:
            raise FileOperationError(
                f"Error reading instruction file {instruction_name}: {e}"
            )

    def get_raw_instruction(self, instruction_name: str) -> str:
        """
        Get the raw file content of a specific instruction file without any processing.

        Args:
            instruction_name: Name of the .instructions.md file

        Returns:
            Raw file content as string

        Raises:
            FileOperationError: If file cannot be read
        """

        # Ensure filename has correct extension
        if not instruction_name.endswith(INSTRUCTION_FILE_EXTENSION):
            instruction_name += INSTRUCTION_FILE_EXTENSION

        file_path = self.prompts_dir / instruction_name

        if not file_path.exists():
            raise FileOperationError(f"Instruction file not found: {instruction_name}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

        except Exception as e:
            raise FileOperationError(
                f"Error reading raw instruction file {instruction_name}: {e}"
            )

    def create_instruction(
        self, instruction_name: str, description: str, content: str
    ) -> bool:
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
        if not instruction_name.endswith(INSTRUCTION_FILE_EXTENSION):
            instruction_name += INSTRUCTION_FILE_EXTENSION

        file_path = self.prompts_dir / instruction_name

        if file_path.exists():
            raise FileOperationError(
                f"Instruction file already exists: {instruction_name}"
            )

        # Create frontmatter with applyTo field so instructions are actually applied
        frontmatter: Dict[str, Any] = {"applyTo": "**", "description": description}

        try:
            success = write_frontmatter_file(
                file_path, frontmatter, content, create_backup=False
            )
            if success:
                logger.info(f"Created instruction file: {instruction_name}")
            return success

        except Exception as e:
            raise FileOperationError(
                f"Error creating instruction file {instruction_name}: {e}"
            )

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
        if not instruction_name.endswith(INSTRUCTION_FILE_EXTENSION):
            instruction_name += INSTRUCTION_FILE_EXTENSION

        file_path = self.prompts_dir / instruction_name

        if not file_path.exists():
            raise FileOperationError(f"Instruction file not found: {instruction_name}")

        try:
            # Read current content
            current_frontmatter, current_content = parse_frontmatter_file(file_path)

            # Use provided values or keep current ones
            new_frontmatter = (
                frontmatter if frontmatter is not None else current_frontmatter
            )
            # If new content is provided, replace all markdown content
            if content is not None:
                new_content = content
            else:
                new_content = current_content

            success = write_frontmatter_file(
                file_path, new_frontmatter, new_content, create_backup=True
            )
            if success:
                logger.info(f"Updated instruction file with backup: {instruction_name}")
            return success

        except Exception as e:
            raise FileOperationError(
                f"Error updating instruction file {instruction_name}: {e}"
            )

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
        if not instruction_name.endswith(INSTRUCTION_FILE_EXTENSION):
            instruction_name += INSTRUCTION_FILE_EXTENSION

        file_path = self.prompts_dir / instruction_name

        if not file_path.exists():
            raise FileOperationError(f"Instruction file not found: {instruction_name}")

        try:
            # Use safe delete which creates backup automatically
            safe_delete_file(file_path, create_backup=True)
            logger.info(f"Deleted instruction file with backup: {instruction_name}")
            return True

        except Exception as e:
            raise FileOperationError(
                f"Error deleting instruction file {instruction_name}: {e}"
            )
