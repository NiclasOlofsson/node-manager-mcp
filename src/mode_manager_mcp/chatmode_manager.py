"""
Mode Manager for VS Code .chatmode.md files.

This module handles chatmode files which define custom chat behaviors,
tools, and instructions for VS Code Copilot.
"""

import json
import logging
import urllib.error
import urllib.request
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


class ChatModeManager:
    """
    Manages VS Code .chatmode.md files in the prompts directory.
    """

    def __init__(self, prompts_dir: Optional[Union[str, Path]] = None):
        """
        Initialize chatmode manager.

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
            f"ChatMode manager initialized with prompts directory: {self.prompts_dir}"
        )

    def list_chatmodes(self) -> List[Dict[str, Any]]:
        """
        List all .chatmode.md files in the prompts directory.

        Returns:
            List of chatmode file information
        """
        chatmodes: List[Dict[str, Any]] = []

        if not self.prompts_dir.exists():
            return chatmodes

        for file_path in self.prompts_dir.glob("*.chatmode.md"):
            try:
                frontmatter, content = parse_frontmatter_file(file_path)

                # Get preview of content (first 100 chars)
                content_preview = content.strip()[:100] if content.strip() else ""

                chatmode_info = {
                    "filename": file_path.name,
                    "name": file_path.stem.replace(".chatmode", ""),
                    "path": str(file_path),
                    "description": frontmatter.get("description", ""),
                    "tools": frontmatter.get("tools", []),
                    "frontmatter": frontmatter,
                    "content_preview": content_preview,
                    "size": file_path.stat().st_size,
                    "modified": file_path.stat().st_mtime,
                }

                chatmodes.append(chatmode_info)

            except Exception as e:
                logger.warning(f"Error reading chatmode file {file_path}: {e}")
                continue

        # Sort by name
        chatmodes.sort(key=lambda x: x["name"].lower())
        return chatmodes

    def get_chatmode(self, filename: str) -> Dict[str, Any]:
        """
        Get content and metadata of a specific chatmode file.

        Args:
            filename: Name of the .chatmode.md file

        Returns:
            Chatmode data including frontmatter and content

        Raises:
            FileOperationError: If file cannot be read
        """
        # Ensure filename has correct extension
        if not filename.endswith(".chatmode.md"):
            filename += ".chatmode.md"

        file_path = self.prompts_dir / filename

        if not file_path.exists():
            raise FileOperationError(f"Chatmode file not found: {filename}")

        try:
            frontmatter, content = parse_frontmatter_file(file_path)

            return {
                "filename": filename,
                "name": file_path.stem.replace(".chatmode", ""),
                "path": str(file_path),
                "description": frontmatter.get("description", ""),
                "tools": frontmatter.get("tools", []),
                "frontmatter": frontmatter,
                "content": content,
                "size": file_path.stat().st_size,
                "modified": file_path.stat().st_mtime,
            }

        except Exception as e:
            raise FileOperationError(f"Error reading chatmode file {filename}: {e}")

    def get_raw_chatmode(self, filename: str) -> str:
        """
        Get the raw file content of a specific chatmode file without any processing.

        Args:
            filename: Name of the .chatmode.md file

        Returns:
            Raw file content as string

        Raises:
            FileOperationError: If file cannot be read
        """
        # Ensure filename has correct extension
        if not filename.endswith(".chatmode.md"):
            filename += ".chatmode.md"

        file_path = self.prompts_dir / filename

        if not file_path.exists():
            raise FileOperationError(f"Chatmode file not found: {filename}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

        except Exception as e:
            raise FileOperationError(f"Error reading raw chatmode file {filename}: {e}")

    def create_chatmode(
        self,
        filename: str,
        description: str,
        content: str,
        tools: Optional[List[str]] = None,
    ) -> bool:
        """
        Create a new chatmode file.

        Args:
            filename: Name for the new .chatmode.md file
            description: Description of the chatmode
            content: Chatmode content/instructions
            tools: List of tools (optional)

        Returns:
            True if successful

        Raises:
            FileOperationError: If file cannot be created
        """
        # Ensure filename has correct extension
        if not filename.endswith(".chatmode.md"):
            filename += ".chatmode.md"

        file_path = self.prompts_dir / filename

        if file_path.exists():
            raise FileOperationError(f"Chatmode file already exists: {filename}")

        # Create frontmatter
        frontmatter: Dict[str, Any] = {"description": description}

        if tools:
            frontmatter["tools"] = tools

        try:
            success = write_frontmatter_file(
                file_path, frontmatter, content, create_backup=False
            )
            if success:
                logger.info(f"Created chatmode file: {filename}")
            return success

        except Exception as e:
            raise FileOperationError(f"Error creating chatmode file {filename}: {e}")

    def update_chatmode(
        self,
        filename: str,
        frontmatter: Optional[Dict[str, Any]] = None,
        content: Optional[str] = None,
    ) -> bool:
        """
        Update an existing chatmode file.

        Args:
            filename: Name of the .chatmode.md file
            frontmatter: New frontmatter (optional)
            content: New content (optional)

        Returns:
            True if successful

        Raises:
            FileOperationError: If file cannot be updated
        """
        # Ensure filename has correct extension
        if not filename.endswith(".chatmode.md"):
            filename += ".chatmode.md"

        file_path = self.prompts_dir / filename

        if not file_path.exists():
            raise FileOperationError(f"Chatmode file not found: {filename}")

        try:
            # Read current content
            current_frontmatter, current_content = parse_frontmatter_file(file_path)

            # Use provided values or keep current ones
            new_frontmatter = (
                frontmatter if frontmatter is not None else current_frontmatter
            )
            new_content = content if content is not None else current_content

            success = write_frontmatter_file(
                file_path, new_frontmatter, new_content, create_backup=True
            )
            if success:
                logger.info(f"Updated chatmode file with backup: {filename}")
            return success

        except Exception as e:
            raise FileOperationError(f"Error updating chatmode file {filename}: {e}")

    def delete_chatmode(self, filename: str) -> bool:
        """
        Delete a chatmode file with automatic backup.

        Args:
            filename: Name of the .chatmode.md file

        Returns:
            True if successful

        Raises:
            FileOperationError: If file cannot be deleted
        """
        # Ensure filename has correct extension
        if not filename.endswith(".chatmode.md"):
            filename += ".chatmode.md"

        file_path = self.prompts_dir / filename

        if not file_path.exists():
            raise FileOperationError(f"Chatmode file not found: {filename}")

        try:
            # Use safe delete which creates backup automatically
            safe_delete_file(file_path, create_backup=True)
            logger.info(f"Deleted chatmode file with backup: {filename}")
            return True

        except Exception as e:
            raise FileOperationError(f"Error deleting chatmode file {filename}: {e}")

    def update_from_source(self, filename: str) -> Dict[str, Any]:
        """
        Update a chatmode file from its source URL.

        This method fetches the latest version from the source_url in the frontmatter,
        while preserving any local tool customizations.

        Args:
            filename: Name of the .chatmode.md file

        Returns:
            Dict with update status and details

        Raises:
            FileOperationError: If file cannot be updated
        """
        # Ensure filename has correct extension
        if not filename.endswith(".chatmode.md"):
            filename += ".chatmode.md"

        file_path = self.prompts_dir / filename

        if not file_path.exists():
            raise FileOperationError(f"Chatmode file not found: {filename}")

        try:
            # Read current file
            current_frontmatter, current_content = parse_frontmatter_file(file_path)

            # Check if source_url exists
            source_url = current_frontmatter.get("source_url")
            if not source_url:
                raise FileOperationError(f"No source_url found in {filename}")

            # Fetch content from source
            logger.info(f"Fetching chatmode update from: {source_url}")

            try:
                with urllib.request.urlopen(source_url) as response:
                    raw_content = response.read()
                    # Try to decode with utf-8, fallback to other encodings if needed
                    try:
                        source_content = raw_content.decode("utf-8")
                    except UnicodeDecodeError:
                        try:
                            source_content = raw_content.decode(
                                "cp1252"
                            )  # Windows encoding
                        except UnicodeDecodeError:
                            source_content = raw_content.decode("latin1")  # Fallback
            except urllib.error.URLError as e:
                raise FileOperationError(f"Failed to fetch from {source_url}: {e}")

            # Parse source content
            try:
                # For GitHub Gist raw URLs, the content is just the file content
                if (
                    "gist.github.com" in source_url
                    or "gist.githubusercontent.com" in source_url
                ):
                    # Parse the source content as a frontmatter file
                    import tempfile

                    # Write to temp file to parse frontmatter
                    with tempfile.NamedTemporaryFile(
                        mode="w", suffix=".md", delete=False, encoding="utf-8"
                    ) as temp_file:
                        temp_file.write(source_content)
                        temp_path = Path(temp_file.name)

                    try:
                        source_frontmatter, source_body = parse_frontmatter_file(
                            temp_path
                        )
                    finally:
                        temp_path.unlink()  # Clean up temp file
                else:
                    # For other sources, assume it's already in the right format
                    raise FileOperationError(
                        f"Unsupported source URL format: {source_url}"
                    )

            except Exception as e:
                raise FileOperationError(f"Failed to parse source content: {e}")

            # Preserve local tool settings if they exist
            local_tools = current_frontmatter.get("tools")

            # Create updated frontmatter by merging source with local customizations
            updated_frontmatter = source_frontmatter.copy()
            updated_frontmatter["source_url"] = (
                source_url  # Ensure source_url is preserved
            )

            if local_tools:
                updated_frontmatter["tools"] = local_tools
                logger.info(f"Preserved local tools setting: {local_tools}")

            # Write updated file with backup
            write_frontmatter_file(
                file_path, updated_frontmatter, source_body, create_backup=True
            )

            logger.info(
                f"Successfully updated chatmode from source with backup: {filename}"
            )

            return {
                "status": "success",
                "filename": filename,
                "source_url": source_url,
                "preserved_tools": local_tools is not None,
                "message": f"Updated {filename} from source",
            }

        except FileOperationError:
            raise
        except Exception as e:
            raise FileOperationError(
                f"Error updating chatmode from source {filename}: {e}"
            )
