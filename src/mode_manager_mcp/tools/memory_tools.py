"""Tools for managing memory optimization."""

from pathlib import Path
from typing import Annotated, Optional

from fastmcp import Context

from ..memory_optimizer import MemoryOptimizer
from ..server_registry import get_server_registry


def register_memory_tools() -> None:
    """Register all memory optimization tools with the server."""
    registry = get_server_registry()
    app = registry.app
    instruction_manager = registry.instruction_manager
    read_only = registry.read_only

    @app.tool(
        name="optimize_memory",
        description="Manually optimize a memory file using AI to reorganize and consolidate entries while preserving all information.",
        tags={"public", "memory"},
        annotations={
            "idempotentHint": False,
            "readOnlyHint": False,
            "title": "Optimize Memory File",
            "parameters": {
                "memory_file": "Optional path to specific memory file. If not provided, will optimize the user's main memory file.",
                "force": "Force optimization even if criteria are not met. Defaults to False.",
            },
            "returns": "Returns detailed results of the optimization process including status, entries before/after, and backup information.",
        },
        meta={
            "category": "memory",
        },
    )
    async def optimize_memory(
        ctx: Context,
        memory_file: Annotated[Optional[str], "Path to memory file to optimize"] = None,
        force: Annotated[bool, "Force optimization regardless of criteria"] = False,
    ) -> str:
        """Manually optimize a memory file using AI sampling."""
        if read_only:
            return "Error: Server is running in read-only mode"

        try:
            # Determine which file to optimize
            if memory_file:
                file_path = Path(memory_file)
                if not file_path.exists():
                    return f"Error: Memory file not found: {memory_file}"
            else:
                # Use default user memory file
                user_memory_path = instruction_manager.get_memory_file_path()
                if not user_memory_path.exists():
                    return "Error: No user memory file found to optimize"
                file_path = user_memory_path

            # Create optimizer and run optimization
            optimizer = MemoryOptimizer(instruction_manager)
            result = await optimizer.optimize_memory_if_needed(file_path, ctx, force=force)

            # Format result message
            status = result.get("status", "unknown")
            if status == "optimized":
                entries_before = result.get("entries_before", "unknown")
                entries_after = result.get("entries_after", "unknown")
                backup_created = result.get("backup_created", False)

                message = f"✅ Memory optimization completed successfully!\n"
                message += f"📊 Entries: {entries_before} → {entries_after}\n"
                message += f"🔄 Method: {result.get('method', 'ai')}\n"
                message += f"💾 Backup created: {'Yes' if backup_created else 'No'}\n"
                message += f"📝 Reason: {result.get('reason', 'Manual optimization')}"

            elif status == "metadata_updated":
                message = f"📝 Memory metadata updated (AI optimization unavailable)\n"
                message += f"💾 Backup created: {'Yes' if result.get('backup_created', False) else 'No'}\n"
                message += f"📝 Reason: {result.get('reason', 'Manual optimization')}"

            elif status == "skipped":
                message = f"⏭️ Optimization skipped: {result.get('reason', 'Unknown reason')}\n"
                message += f"💡 Use force=True to optimize anyway"

            elif status == "error":
                message = f"❌ Optimization failed: {result.get('reason', 'Unknown error')}"

            else:
                message = f"🔍 Optimization result: {status}"

            return message

        except Exception as e:
            return f"Error during memory optimization: {str(e)}"

    @app.tool(
        name="memory_stats",
        description="Get detailed statistics and optimization status for a memory file.",
        tags={"public", "memory"},
        annotations={
            "idempotentHint": True,
            "readOnlyHint": True,
            "title": "Memory File Statistics",
            "parameters": {
                "memory_file": "Optional path to specific memory file. If not provided, will show stats for the user's main memory file.",
            },
            "returns": "Returns comprehensive statistics including file size, entry count, optimization eligibility, and configuration settings.",
        },
        meta={
            "category": "memory",
        },
    )
    def memory_stats(
        memory_file: Annotated[Optional[str], "Path to memory file to analyze"] = None,
    ) -> str:
        """Get detailed statistics about a memory file."""
        try:
            # Determine which file to analyze
            if memory_file:
                file_path = Path(memory_file)
                if not file_path.exists():
                    return f"Error: Memory file not found: {memory_file}"
            else:
                # Use default user memory file
                user_memory_path = instruction_manager.get_memory_file_path()
                if not user_memory_path.exists():
                    return "No user memory file found"
                file_path = user_memory_path

            # Get stats
            optimizer = MemoryOptimizer(instruction_manager)
            stats = optimizer.get_memory_stats(file_path)

            if "error" in stats:
                return str(stats["error"])

            # Format stats message
            message = f"📊 **Memory File Statistics**\n\n"
            message += f"📁 **File**: `{stats['file_path']}`\n"
            message += f"📏 **Size**: {stats['file_size_bytes']:,} bytes\n"
            message += f"📝 **Entries**: {stats['current_entries']}\n"
            message += f"🔄 **Last Optimized**: {stats['last_optimized'] or 'Never'}\n"
            message += f"⚡ **Optimization Version**: {stats['optimization_version']}\n\n"

            message += f"⚙️ **Configuration**:\n"
            message += f"• Auto-optimize: {'✅ Enabled' if stats['auto_optimize_enabled'] else '❌ Disabled'}\n"
            message += f"• Size threshold: {stats['size_threshold']:,} bytes\n"
            message += f"• Entry threshold: {stats['entry_threshold']} new entries\n"
            message += f"• Time threshold: {stats['time_threshold_days']} days\n\n"

            message += f"🎯 **Optimization Status**:\n"
            message += f"• Eligible: {'✅ Yes' if stats['optimization_eligible'] else '❌ No'}\n"
            message += f"• Reason: {stats['optimization_reason']}\n"
            message += f"• New entries since last optimization: {stats['entries_since_last_optimization']}"

            return message

        except Exception as e:
            return f"Error getting memory stats: {str(e)}"

    @app.tool(
        name="configure_memory_optimization",
        description="Configure memory optimization settings for auto-optimization behavior.",
        tags={"public", "memory"},
        annotations={
            "idempotentHint": False,
            "readOnlyHint": False,
            "title": "Configure Memory Optimization",
            "parameters": {
                "memory_file": "Optional path to specific memory file. If not provided, will configure the user's main memory file.",
                "auto_optimize": "Enable or disable automatic optimization. True/False.",
                "size_threshold": "File size threshold in bytes for triggering optimization.",
                "entry_threshold": "Number of new entries to trigger optimization.",
                "time_threshold_days": "Number of days between optimizations.",
            },
            "returns": "Returns confirmation of updated settings.",
        },
        meta={
            "category": "memory",
        },
    )
    def configure_memory_optimization(
        memory_file: Annotated[Optional[str], "Path to memory file to configure"] = None,
        auto_optimize: Annotated[Optional[bool], "Enable/disable auto-optimization"] = None,
        size_threshold: Annotated[Optional[int], "Size threshold in bytes"] = None,
        entry_threshold: Annotated[Optional[int], "Entry count threshold"] = None,
        time_threshold_days: Annotated[Optional[int], "Time threshold in days"] = None,
    ) -> str:
        """Configure memory optimization settings."""
        if read_only:
            return "Error: Server is running in read-only mode"

        try:
            # Determine which file to configure
            if memory_file:
                file_path = Path(memory_file)
                if not file_path.exists():
                    return f"Error: Memory file not found: {memory_file}"
            else:
                # Use default user memory file
                user_memory_path = instruction_manager.get_memory_file_path()
                if not user_memory_path.exists():
                    return "Error: No user memory file found to configure"
                file_path = user_memory_path

            # Read current frontmatter
            from ..simple_file_ops import parse_frontmatter_file, write_frontmatter_file

            frontmatter, content = parse_frontmatter_file(file_path)

            # Update settings
            updated_settings = []
            if auto_optimize is not None:
                frontmatter["autoOptimize"] = auto_optimize
                updated_settings.append(f"auto_optimize: {auto_optimize}")

            if size_threshold is not None:
                frontmatter["sizeThreshold"] = size_threshold
                updated_settings.append(f"size_threshold: {size_threshold:,} bytes")

            if entry_threshold is not None:
                frontmatter["entryThreshold"] = entry_threshold
                updated_settings.append(f"entry_threshold: {entry_threshold}")

            if time_threshold_days is not None:
                frontmatter["timeThreshold"] = time_threshold_days
                updated_settings.append(f"time_threshold: {time_threshold_days} days")

            if not updated_settings:
                return "No settings provided to update. Available options: auto_optimize, size_threshold, entry_threshold, time_threshold_days"

            # Write updated frontmatter
            success = write_frontmatter_file(file_path, frontmatter, content, create_backup=True)

            if success:
                message = "✅ Memory optimization settings updated:\n"
                for setting in updated_settings:
                    message += f"• {setting}\n"
                message += f"\n💾 Backup created for safety"
                return message
            else:
                return "❌ Failed to update memory optimization settings"

        except Exception as e:
            return f"Error configuring memory optimization: {str(e)}"
