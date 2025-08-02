<picture>
  <source media="(prefers-color-scheme: dark)" srcset="logo-dark-theme.svg">
  <source media="(prefers-color-scheme: light)" srcset="logo-light-theme.svg">
  <img alt="GitHub Copilot Memory Tool" src="https://raw.githubusercontent.com/NiclasOlofsson/mode-manager-mcp/refs/heads/main/logo-light-theme.svg" width="800">
</picture>

# GitHub Copilot Memory Tool

**Finally, Copilot that actually remembers you.**

Perfect timing for 2025: VS Code now loads instructions with every message. This tool gives Copilot **persistent memory** across all your conversations.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## Why This Matters Now

**2025 Game Changer**: VS Code's new behavior loads custom instructions with **every chat request** (not just session start). This means:

- **Your memories are ALWAYS active** in every conversation  
- **No more repeating context** when you start new chats
- **Copilot truly knows you** across sessions, topics, and projects
- **Perfect timing** - built for the new instruction loading behavior

## See It In Action

**Before this tool:**
> *"Hey Copilot, write me a Python function..."*  
> Copilot: *Gives generic Python code*

**After using `remember`:**
> You: *"Remember I'm a senior data architect at Oatly, prefer type hints, and use Black formatting"*  
> Next conversation: *"Write me a Python function..."*  
> Copilot: *Generates perfectly styled code with type hints, following your exact preferences*

## Dead Simple to Use

**One command does everything:**

```
Ask Copilot: "Remember that I prefer detailed docstrings and use pytest for testing"
```

That's it. Copilot now knows this **forever**, across all future conversations.

### What You Can Remember:
- **Work context** - Your role, company, current projects
- **Coding preferences** - Languages, frameworks, style guides  
- **Project details** - Architecture decisions, naming conventions
- **Personal workflow** - How you like to work, debug, test

## How It Works Behind the Scenes

1. **Auto-setup** - Creates `memory.instructions.md` in your VS Code prompts directory on first use
2. **Smart storage** - Each memory gets timestamped and organized  
3. **Always loaded** - VS Code's 2025 behavior means your memories are included in every chat request
4. **Cross-session persistence** - Your memories survive VS Code restarts and new conversations

## Bonus Features

Beyond memory, this tool also manages your VS Code prompt ecosystem:
- **Curated library** - 20+ professional chatmodes and instructions  
- **File management** - Create, edit, and organize `.chatmode.md` and `.instructions.md` files
- **Stay updated** - Update files from source while keeping your customizations

## Get It Running (2 Minutes)

### 1. Install from PyPI
```bash
pip install mode-manager-mcp
```

### 2. Add to VS Code
Add this to your VS Code MCP settings (`mcp.json`):
```json
{
  "servers": {
    "mode-manager": {
      "command": "mode-manager-mcp"
    }
  }
}
```

That's it! Start chatting with Copilot and use: *"Remember that..."*

### Bonus ..

As a convenience, you can run the following prompt in VS Code to get started in the best way:

```
/mcp.mode-manager.onboarding
```

This will guide you through the onboarding process, set up your persistent memory, and ensure Copilot knows your preferences from the start.

## Perfect Timing for 2025

This tool is built specifically for VS Code's new behavior where **custom instructions load with every chat message**. This makes persistent memory incredibly powerful - your memories are always active, no matter what topic you're discussing.

---

**Ready to have Copilot that actually remembers you? [Get started now!](#get-it-running-2-minutes)**

## Contributing

Want to help improve this tool? Check out [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.
