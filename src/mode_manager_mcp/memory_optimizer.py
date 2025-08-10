"""
Memory Optimization Implementation with Full Backward Compatibility.

This implementation gracefully handles existing memory files without metadata
and gradually migrates them to the new enhanced format.
"""

import datetime
import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from fastmcp import Context

from .simple_file_ops import (
    FileOperationError,
    parse_frontmatter_file,
    write_frontmatter_file,
)
from .types import MemoryScope

logger = logging.getLogger(__name__)


class MemoryOptimizer:
    """Handles memory file optimization with full backward compatibility."""

    def __init__(self, instruction_manager: Any) -> None:
        self.instruction_manager = instruction_manager

    def _get_memory_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract or initialize metadata for a memory file.

        Handles backward compatibility by providing defaults for missing metadata.
        """
        try:
            frontmatter, _ = parse_frontmatter_file(file_path)

            # Provide backward-compatible defaults for missing metadata
            metadata = {
                "lastOptimized": frontmatter.get("lastOptimized"),
                "entryCount": frontmatter.get("entryCount", 0),
                "optimizationVersion": frontmatter.get("optimizationVersion", 0),
                "autoOptimize": frontmatter.get("autoOptimize", True),  # Default to enabled
                "sizeThreshold": frontmatter.get("sizeThreshold", 50000),  # 50KB
                "entryThreshold": frontmatter.get("entryThreshold", 20),  # 20 entries
                "timeThreshold": frontmatter.get("timeThreshold", 7),  # 7 days
            }

            return metadata

        except Exception as e:
            logger.warning(f"Could not read metadata from {file_path}: {e}")
            # Return safe defaults for corrupted files
            return {
                "lastOptimized": None,
                "entryCount": 0,
                "optimizationVersion": 0,
                "autoOptimize": True,
                "sizeThreshold": 50000,
                "entryThreshold": 20,
                "timeThreshold": 7,
            }

    def _count_memory_entries(self, content: str) -> int:
        """
        Count memory entries in the content.

        Handles various formats:
        - **timestamp:** content
        - - timestamp: content
        - timestamp: content (without dashes)
        """
        patterns = [
            r"^\s*-\s*\*\*\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}\*\*:.*$",  # - **2025-08-09 10:30:** content
            r"^\s*-\s*\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:.*$",  # - 2025-08-09 10:30: content
            r"^\s*\*\*\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}\*\*:.*$",  # **2025-08-09 10:30:** content (no dash)
            r"^\s*\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:.*$",  # 2025-08-09 10:30: content (no formatting)
        ]

        total_count = 0
        lines = content.split("\n")

        for pattern in patterns:
            count = len([line for line in lines if re.match(pattern, line, re.MULTILINE)])
            total_count = max(total_count, count)  # Use the highest count found

        # Fallback: count lines starting with "- **" (most common format)
        if total_count == 0:
            fallback_count = len([line for line in lines if line.strip().startswith("- **")])
            total_count = fallback_count

        return total_count

    def _should_optimize_memory(self, file_path: Path, metadata: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Determine if memory file should be optimized.

        Returns (should_optimize, reason)
        """
        # Check if auto-optimization is disabled
        if not metadata.get("autoOptimize", True):
            return False, "Auto-optimization disabled"

        # File size check
        file_size = file_path.stat().st_size
        size_threshold = metadata.get("sizeThreshold", 50000)
        if file_size > size_threshold:
            return True, f"File size ({file_size} bytes) exceeds threshold ({size_threshold} bytes)"

        # Entry count check
        try:
            _, content = parse_frontmatter_file(file_path)
            current_entries = self._count_memory_entries(content)
            last_count = metadata.get("entryCount", 0)
            entry_threshold = metadata.get("entryThreshold", 20)

            new_entries = current_entries - last_count
            if new_entries >= entry_threshold:
                return True, f"New entries ({new_entries}) exceed threshold ({entry_threshold})"

        except Exception as e:
            logger.warning(f"Could not count entries: {e}")

        # Time-based check
        last_optimized = metadata.get("lastOptimized")
        if last_optimized:
            try:
                last_opt_time = datetime.datetime.fromisoformat(last_optimized.replace("Z", "+00:00"))
                time_threshold = metadata.get("timeThreshold", 7)  # days
                days_since = (datetime.datetime.now(datetime.timezone.utc) - last_opt_time).days

                if days_since >= time_threshold:
                    return True, f"Days since last optimization ({days_since}) exceed threshold ({time_threshold})"

            except Exception as e:
                logger.warning(f"Could not parse last optimization time: {e}")
                # If we can't parse the time, consider it old enough to optimize
                return True, "Could not determine last optimization time"
        else:
            # No last optimization time means this is an existing file without metadata
            return True, "No previous optimization recorded (legacy file)"

        return False, "No optimization criteria met"

    def _update_metadata(self, file_path: Path, content: Optional[str] = None) -> bool:
        """
        Update metadata in a memory file's frontmatter.

        Gracefully handles files with or without existing metadata.
        """
        try:
            frontmatter, body_content = parse_frontmatter_file(file_path)

            # Count current entries
            entry_count = self._count_memory_entries(body_content)

            # Update metadata while preserving existing frontmatter
            frontmatter.update(
                {
                    "lastOptimized": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "entryCount": entry_count,
                    "optimizationVersion": frontmatter.get("optimizationVersion", 0) + 1,
                }
            )

            # Set defaults for new metadata fields if they don't exist
            if "autoOptimize" not in frontmatter:
                frontmatter["autoOptimize"] = True
            if "sizeThreshold" not in frontmatter:
                frontmatter["sizeThreshold"] = 50000
            if "entryThreshold" not in frontmatter:
                frontmatter["entryThreshold"] = 20
            if "timeThreshold" not in frontmatter:
                frontmatter["timeThreshold"] = 7

            # Use provided content or keep existing body
            final_content = content if content else body_content

            return write_frontmatter_file(file_path, frontmatter, final_content, create_backup=True)

        except Exception as e:
            logger.error(f"Failed to update metadata for {file_path}: {e}")
            return False

    async def _optimize_memory_with_ai(self, ctx: Context, content: str) -> Optional[str]:
        """Safely optimize memory content using AI sampling with comprehensive error handling."""
        try:
            response = await ctx.sample(
                f"""Please optimize this AI memory file by:
                
1. **Preserve ALL information** - Do not delete any memories or important details
2. **Remove duplicates** - Consolidate identical or very similar entries
3. **Organize by sections** - Group related memories under clear headings:
   - ## Personal Context (name, location, role, etc.)
   - ## Professional Context (team, goals, projects, etc.) 
   - ## Technical Preferences (coding styles, tools, workflows)
   - ## Communication Preferences (style, feedback preferences)
   - ## Universal Laws (strict rules that must always be followed)
   - ## Policies (guidelines and standards)
   - ## Suggestions/Hints (recommendations and tips)
   - ## Memories/Facts (chronological events and information)
4. **Maintain timestamps** - Keep all original timestamps for traceability
5. **Improve formatting** - Use consistent markdown formatting
6. **Preserve frontmatter structure** - Keep the YAML header intact

Return ONLY the optimized content (including frontmatter), nothing else:

{content}""",
                temperature=0.1,  # Very low for consistency
                max_tokens=4000,
                model_preferences=["gpt-4", "claude-3-sonnet"],  # Prefer more reliable models
            )

            if response and hasattr(response, "text"):
                text_attr = getattr(response, "text", None)
                optimized_content = str(text_attr).strip() if text_attr else None

                # Basic validation - ensure we still have a memories section
                if optimized_content and ("## Memories" in optimized_content or "# Personal" in optimized_content):
                    return optimized_content
                else:
                    logger.warning("AI optimization removed essential sections, reverting to original")
                    return None
            else:
                logger.warning(f"AI optimization returned unexpected type or no text: {type(response)}")
                return None

        except Exception as e:
            logger.info(f"AI optimization failed: {e}")
            return None

    async def optimize_memory_if_needed(self, file_path: Path, ctx: Context, force: bool = False) -> Dict[str, Any]:
        """
        Main optimization method with full backward compatibility.

        Args:
            file_path: Path to memory file
            ctx: FastMCP context for AI sampling
            force: Force optimization regardless of criteria

        Returns:
            Dict with optimization results
        """
        try:
            # Get metadata (with backward compatibility)
            metadata = self._get_memory_metadata(file_path)

            # Check if optimization is needed
            if not force:
                should_optimize, reason = self._should_optimize_memory(file_path, metadata)
                if not should_optimize:
                    return {"status": "skipped", "reason": reason, "metadata": metadata}
            else:
                reason = "Forced optimization"

            # Read current content
            frontmatter, content = parse_frontmatter_file(file_path)
            full_content = f"---\n"
            for key, value in frontmatter.items():
                if isinstance(value, str) and ('"' in value or "'" in value):
                    full_content += f'{key}: "{value}"\n'
                else:
                    full_content += f"{key}: {value}\n"
            full_content += f"---\n{content}"

            logger.info(f"Starting memory optimization: {reason}")

            # Try AI optimization
            optimized_content = await self._optimize_memory_with_ai(ctx, full_content)

            if optimized_content:
                # Parse optimized content to separate frontmatter and body
                optimized_frontmatter, optimized_body = parse_frontmatter_file(Path("temp"))

                # Create temporary file to parse the optimized content
                temp_path = Path("temp_optimization.md")
                try:
                    with open(temp_path, "w", encoding="utf-8") as f:
                        f.write(optimized_content)
                    optimized_frontmatter, optimized_body = parse_frontmatter_file(temp_path)
                finally:
                    if temp_path.exists():
                        temp_path.unlink()

                # Update metadata in the optimized frontmatter
                entry_count = self._count_memory_entries(optimized_body)
                optimized_frontmatter.update(
                    {
                        "lastOptimized": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        "entryCount": entry_count,
                        "optimizationVersion": frontmatter.get("optimizationVersion", 0) + 1,
                    }
                )

                # Preserve user preferences from original frontmatter
                for key in ["autoOptimize", "sizeThreshold", "entryThreshold", "timeThreshold"]:
                    if key in frontmatter:
                        optimized_frontmatter[key] = frontmatter[key]
                    elif key not in optimized_frontmatter:
                        # Set sensible defaults for new files
                        defaults = {"autoOptimize": True, "sizeThreshold": 50000, "entryThreshold": 20, "timeThreshold": 7}
                        optimized_frontmatter[key] = defaults[key]

                # Write optimized content
                success = write_frontmatter_file(file_path, optimized_frontmatter, optimized_body, create_backup=True)

                if success:
                    logger.info(f"Memory optimization completed successfully")
                    return {"status": "optimized", "reason": reason, "method": "ai", "entries_before": metadata.get("entryCount", 0), "entries_after": entry_count, "backup_created": True}
                else:
                    return {"status": "error", "reason": "Failed to write optimized content"}
            else:
                # AI optimization failed, just update metadata
                logger.info("AI optimization unavailable, updating metadata only")
                success = self._update_metadata(file_path, content)

                return {"status": "metadata_updated", "reason": reason, "method": "metadata_only", "ai_available": False, "backup_created": success}

        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")
            return {"status": "error", "reason": str(e)}

    def get_memory_stats(self, file_path: Path) -> Dict[str, Any]:
        """
        Get statistics about a memory file.

        Returns metadata and file information for user inspection.
        """
        try:
            metadata = self._get_memory_metadata(file_path)
            frontmatter, content = parse_frontmatter_file(file_path)

            current_entries = self._count_memory_entries(content)
            file_size = file_path.stat().st_size

            # Calculate optimization eligibility
            should_optimize, reason = self._should_optimize_memory(file_path, metadata)

            return {
                "file_path": str(file_path),
                "file_size_bytes": file_size,
                "current_entries": current_entries,
                "last_optimized": metadata.get("lastOptimized"),
                "optimization_version": metadata.get("optimizationVersion", 0),
                "auto_optimize_enabled": metadata.get("autoOptimize", True),
                "size_threshold": metadata.get("sizeThreshold", 50000),
                "entry_threshold": metadata.get("entryThreshold", 20),
                "time_threshold_days": metadata.get("timeThreshold", 7),
                "optimization_eligible": should_optimize,
                "optimization_reason": reason,
                "entries_since_last_optimization": current_entries - metadata.get("entryCount", 0),
            }

        except Exception as e:
            return {"error": f"Could not read memory file stats: {e}"}
