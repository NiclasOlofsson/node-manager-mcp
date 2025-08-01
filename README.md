# Mode Manager MCP

🧠 **Personal AI Memory + VS Code Prompt Management**

Streamlined MCP server that gives AI assistants a **persistent memory** of your preferences and manages VS Code `.chatmode.md` and `.instructions.md` files.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## 🎯 Primary Feature: AI Memory

**One tool to rule them all**: `remember()`

- 🧠 **Personal AI Memory** - Store preferences, facts, and context that AI should remember about you
- 🔄 **Auto-setup** - Creates memory file automatically in your VS Code prompts directory  
- 💾 **Persistent** - Memories are saved as a VS Code instruction file that AI assistants can access
- ⚡ **Simple** - Just one tool instead of managing multiple complex operations

## 🧠 Primary Usage: Personal AI Memory

### Store Information About Yourself
Ask Copilot: *"Remember that I prefer Python over JavaScript for backend development"*

### Add Personal Context  
Ask Copilot: *"Remember that I work at Oatly and focus on sustainability projects"*

### Save Preferences
Ask Copilot: *"Remember that I like detailed code comments and use Black for Python formatting"*

### How It Works
1. **First use** - Automatically creates `memory.instructions.md` in your VS Code prompts directory
2. **Each memory** - Adds timestamped entries to your personal memory file
3. **AI access** - Any AI assistant can read your memories when the instruction is active
4. **Persistent** - Memories survive across VS Code sessions and conversations

## 📚 The Mode Manager MCP Library

The official library contains **20 curated entries** with proper license attribution:

### Popular Chatmodes
- **Beast Mode 3.1** - Advanced autonomous coding agent
- **AI Architect** - System design and architecture specialist  
- **Code Reviewer** - Comprehensive code review assistant
- **Tech Lead** - Technical leadership and project management
- **Security Expert** - Cybersecurity and secure coding practices

### Professional Instructions
- **Python Developer** - Modern Python patterns and best practices
- **React Developer** - Frontend development with React
- **API Design Guidelines** - RESTful API design principles
- **Git Workflow Standards** - Professional version control practices
- **Testing Strategy** - Comprehensive testing patterns

All entries include:
- 📄 **License information** (MIT, Apache 2.0, Open Source)
- 👤 **Author attribution** 
- 🏷️ **Categories and tags**
- 🔗 **Source links** to original content

## ✨ Additional Features

- 📂 **Manage VS Code prompt files** - Create, edit, and organize chatmodes and instructions
- 📚 **Browse the curated library** - Install popular chatmodes and instructions from the community with license attribution
- 🔄 **Keep files updated** - Update chatmodes from source while preserving your custom tool settings
- 🛡️ **Safe operations** - Automatic backups before any deletions
- ⚙️ **Configurable library** - Use the official library or point to your own custom collection

## 🚀 Quick Setup

### 1. Install

```bash
git clone https://github.com/NiclasOlofsson/node-manager-mcp.git
cd node-manager-mcp
pipenv install
```

### 2. Test it works

```bash
pipenv run python test_basic.py
```

### 3. Add to VS Code

Copy the example configuration:

```bash
cp mcp-config-example.json .vscode/mcp.json
```

Or manually add to your VS Code MCP settings:

```json
{
  "mcpServers": {
    "mode-manager": {
      "command": "pipenv",
      "args": ["run", "python", "-m", "src.mode_manager_mcp"],
      "cwd": "."
    }
  }
}
```

## ⚙️ Library Configuration

The server uses the **official Mode Manager MCP Library** by default, but you can configure it to use custom libraries for development or organizational needs.

### Default Library
```
https://raw.githubusercontent.com/NiclasOlofsson/node-manager-mcp/refs/heads/main/library/memory-mode-library.json
```

### Configuration Options

#### Command Line Parameter
```bash
pipenv run python -m src.mode_manager_mcp --library-url "https://your-custom-library.json"
```

#### Environment Variable
```bash
export MCP_LIBRARY_URL="https://your-custom-library.json"
pipenv run python -m src.mode_manager_mcp
```

#### VS Code Configuration
```json
{
  "mcpServers": {
    "mode-manager": {
      "command": "pipenv",
      "args": ["run", "python", "-m", "src.mode_manager_mcp", "--library-url", "https://your-custom-library.json"],
      "cwd": "."
    }
  }
}
```

### Common Use Cases

**Development/Testing:**
```bash
# Use a local development library
python -m http.server 8000 --directory ./library
export MCP_LIBRARY_URL="http://localhost:8000/memory-mode-library.json"
```

**Custom Organization Library:**
```bash
# Point to your organization's curated library
export MCP_LIBRARY_URL="https://raw.githubusercontent.com/yourorg/custom-prompts/main/library.json"
```

## 💡 Usage Examples

### Browse the Library
Ask Copilot: *"What chatmodes are available in the library?"*

### Install a Popular Chatmode  
Ask Copilot: *"Install Beast Mode 3.1 from the library"*

### Create Your Own
Ask Copilot: *"Create a new chatmode for API testing"*

### Manage Files
Ask Copilot: *"List my current chatmodes"* or *"Update my chatmode from its source"*

## 📁 Where Files Are Stored

Your prompt files live in VS Code's prompts directory:
- **Windows:** `%APPDATA%\Code\User\prompts`
- **macOS:** `~/Library/Application Support/Code/User/prompts`  
- **Linux:** `~/.config/Code/User/prompts`

## 🤝 Contributing

Want to help improve Mode Manager MCP? Check out [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, coding guidelines, and how to submit changes.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
