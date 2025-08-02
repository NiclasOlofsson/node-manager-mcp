"""
Mode Library Manager for browsing and installing chatmodes and instructions from a curated library.

This module handles interaction with the Mode Manager MCP Library via URL fetching.
"""

import json
import logging
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .chatmode_manager import ChatModeManager
from .instruction_manager import INSTRUCTION_FILE_EXTENSION, InstructionManager
from .simple_file_ops import FileOperationError

logger = logging.getLogger(__name__)


class LibraryManager:
    """
    Manages the Mode Manager MCP Library for browsing and installing modes/instructions.
    """

    def __init__(
        self, library_url: Optional[str] = None, prompts_dir: Optional[str] = None
    ):
        """
        Initialize the library manager.

        Args:
            library_url: URL to the library JSON file (defaults to the official Mode Manager MCP library)
            prompts_dir: Custom prompts directory for all managers (optional)
        """
        # Default to the official Mode Manager MCP library in the GitHub repository
        self.library_url = (
            library_url
            or "https://raw.githubusercontent.com/NiclasOlofsson/node-manager-mcp/refs/heads/main/library/memory-mode-library.json"
        )

        self.chatmode_manager = ChatModeManager(prompts_dir=prompts_dir)
        self.instruction_manager = InstructionManager(prompts_dir=prompts_dir)

        logger.info(f"Library manager initialized with URL: {self.library_url}")

    def _fetch_library(self) -> Dict[str, Any]:
        """
        Fetch the library JSON from the URL.

        Returns:
            Library data as dictionary

        Raises:
            FileOperationError: If library cannot be fetched
        """
        try:
            logger.info(f"Fetching library from: {self.library_url}")

            # Create request with user agent
            req = urllib.request.Request(
                self.library_url, headers={"User-Agent": "Mode-Manager-MCP/1.0"}
            )

            # Fetch the JSON data
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read()

            # Try different encodings
            for encoding in ["utf-8", "utf-8-sig", "cp1252", "latin1"]:
                try:
                    text_content = content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise FileOperationError(
                    "Could not decode library content with any supported encoding"
                )

            # Parse JSON
            library_data: Dict[str, Any] = json.loads(text_content)

            logger.info(
                f"Successfully loaded library: {library_data.get('name', 'Unknown')}"
            )
            return library_data

        except urllib.error.URLError as e:
            raise FileOperationError(
                f"Could not fetch library from {self.library_url}: {str(e)}"
            )
        except json.JSONDecodeError as e:
            raise FileOperationError(f"Invalid JSON in library: {str(e)}")
        except Exception as e:
            raise FileOperationError(f"Error fetching library: {str(e)}")

    def browse_library(
        self, category: Optional[str] = None, search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Browse the available chatmodes and instructions in the library.

        Args:
            category: Filter by category (e.g., 'development', 'testing')
            search: Search term to filter by name or description

        Returns:
            Dictionary with library information and filtered items
        """
        try:
            library = self._fetch_library()

            # Filter chatmodes
            chatmodes = library.get("chatmodes", [])
            if category:
                chatmodes = [cm for cm in chatmodes if cm.get("category") == category]
            if search:
                search_lower = search.lower()
                chatmodes = [
                    cm
                    for cm in chatmodes
                    if search_lower in cm.get("name", "").lower()
                    or search_lower in cm.get("description", "").lower()
                    or search_lower in " ".join(cm.get("tags", [])).lower()
                ]

            # Filter instructions
            instructions = library.get("instructions", [])
            if category:
                instructions = [
                    inst for inst in instructions if inst.get("category") == category
                ]
            if search:
                search_lower = search.lower()
                instructions = [
                    inst
                    for inst in instructions
                    if search_lower in inst.get("name", "").lower()
                    or search_lower in inst.get("description", "").lower()
                    or search_lower in " ".join(inst.get("tags", [])).lower()
                ]

            return {
                "library_name": library.get("name", "Mode Manager MCP Library"),
                "version": library.get("version", "1.0.0"),
                "last_updated": library.get("last_updated", "Unknown"),
                "total_chatmodes": len(library.get("chatmodes", [])),
                "total_instructions": len(library.get("instructions", [])),
                "filtered_chatmodes": len(chatmodes),
                "filtered_instructions": len(instructions),
                "chatmodes": chatmodes,
                "instructions": instructions,
                "categories": library.get("categories", []),
                "filters_applied": {"category": category, "search": search},
            }

        except Exception as e:
            raise FileOperationError(f"Error browsing library: {str(e)}")

    def get_library_item(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific item from the library by name.

        Args:
            name: Name of the chatmode or instruction

        Returns:
            Item data if found, None otherwise
        """
        try:
            library = self._fetch_library()

            # Search in chatmodes
            for chatmode in library.get("chatmodes", []):
                if chatmode.get("name") == name:
                    return {"type": "chatmode", "data": chatmode}

            # Search in instructions
            for instruction in library.get("instructions", []):
                if instruction.get("name") == name:
                    return {"type": "instruction", "data": instruction}

            return None

        except Exception as e:
            raise FileOperationError(f"Error getting library item '{name}': {str(e)}")

    def install_from_library(
        self, name: str, custom_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Install a chatmode or instruction from the library.

        Args:
            name: Name of the item to install
            custom_filename: Custom filename (optional)

        Returns:
            Installation result
        """
        try:
            # Find the item in the library
            item = self.get_library_item(name)
            if not item:
                raise FileOperationError(f"Item '{name}' not found in library")

            item_type = item["type"]
            item_data = item["data"]
            content_url = item_data.get("content_location")

            if not content_url:
                raise FileOperationError(f"No content location found for '{name}'")

            # Determine filename
            filename = (
                custom_filename
                or item_data.get("install_name")
                or f"{name}.{item_type}.md"
            )

            # Fetch the content from the URL
            logger.info(f"Fetching {item_type} content from: {content_url}")

            req = urllib.request.Request(
                content_url, headers={"User-Agent": "Mode-Manager-MCP/1.0"}
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read()

            # Try different encodings
            for encoding in ["utf-8", "utf-8-sig", "cp1252", "latin1"]:
                try:
                    file_content = content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise FileOperationError(
                    "Could not decode file content with any supported encoding"
                )

            # Install based on type
            if item_type == "chatmode":
                # Parse the content to extract frontmatter and content
                import tempfile
                from pathlib import Path

                from .simple_file_ops import parse_frontmatter_file

                # Write to temp file to parse
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".chatmode.md", delete=False, encoding="utf-8"
                ) as tmp:
                    tmp.write(file_content)
                    tmp_path = tmp.name

                try:
                    frontmatter, content_text = parse_frontmatter_file(tmp_path)

                    # Create the chatmode
                    success = self.chatmode_manager.create_chatmode(
                        filename,
                        frontmatter.get(
                            "description", item_data.get("description", "")
                        ),
                        content_text,
                        frontmatter.get("tools", []),
                    )

                    if success:
                        # Add source_url to track origin
                        updated_frontmatter = frontmatter.copy()
                        updated_frontmatter["source_url"] = content_url
                        updated_frontmatter["library_source"] = name

                        self.chatmode_manager.update_chatmode(
                            filename,
                            frontmatter=updated_frontmatter,
                            content=content_text,
                        )

                        return {
                            "status": "success",
                            "type": "chatmode",
                            "name": name,
                            "filename": filename,
                            "source_url": content_url,
                            "message": f"Successfully installed chatmode '{name}' as {filename}",
                        }
                    else:
                        raise FileOperationError(
                            f"Failed to create chatmode file: {filename}"
                        )

                finally:
                    Path(tmp_path).unlink(missing_ok=True)

            elif item_type == "instruction":
                # Parse the content to extract frontmatter and content
                import tempfile
                from pathlib import Path

                from .simple_file_ops import parse_frontmatter_file

                # Write to temp file to parse
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    suffix=INSTRUCTION_FILE_EXTENSION,
                    delete=False,
                    encoding="utf-8",
                ) as tmp:
                    tmp.write(file_content)
                    tmp_path = tmp.name

                try:
                    frontmatter, content_text = parse_frontmatter_file(tmp_path)

                    # Create the instruction
                    success = self.instruction_manager.create_instruction(
                        filename,
                        frontmatter.get(
                            "description", item_data.get("description", "")
                        ),
                        content_text,
                    )

                    if success:
                        # Add source_url to track origin
                        updated_frontmatter = frontmatter.copy()
                        updated_frontmatter["source_url"] = content_url
                        updated_frontmatter["library_source"] = name

                        self.instruction_manager.update_instruction(
                            filename,
                            frontmatter=updated_frontmatter,
                            content=content_text,
                        )

                        return {
                            "status": "success",
                            "type": "instruction",
                            "name": name,
                            "filename": filename,
                            "source_url": content_url,
                            "message": f"Successfully installed instruction '{name}' as {filename}",
                        }
                    else:
                        raise FileOperationError(
                            f"Failed to create instruction file: {filename}"
                        )

                finally:
                    Path(tmp_path).unlink(missing_ok=True)

            else:
                raise FileOperationError(f"Unknown item type: {item_type}")

        except urllib.error.URLError as e:
            raise FileOperationError(
                f"Could not fetch content from {content_url}: {str(e)}"
            )
        except Exception as e:
            raise FileOperationError(
                f"Error installing '{name}' from library: {str(e)}"
            )

    def refresh_library(self) -> Dict[str, Any]:
        """
        Refresh the library by fetching the latest version from the URL.

        Note: Without caching, this method now just fetches the library like any other operation.

        Returns:
            Updated library information
        """
        try:
            library = self._fetch_library()

            return {
                "status": "success",
                "library_name": library.get("name", "Mode Manager MCP Library"),
                "version": library.get("version", "1.0.0"),
                "last_updated": library.get("last_updated", "Unknown"),
                "total_chatmodes": len(library.get("chatmodes", [])),
                "total_instructions": len(library.get("instructions", [])),
                "message": "Library refreshed successfully",
            }

        except Exception as e:
            raise FileOperationError(f"Error refreshing library: {str(e)}")
