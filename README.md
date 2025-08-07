<picture>
  <source media="(prefers-color-scheme: dark)" srcset="logo-dark-theme.svg">
  <source media="(prefers-color-scheme: light)" srcset="logo-light-theme.svg">
  <img alt="GitHub Copilot Memory Tool" src="https://raw.githubusercontent.com/NiclasOlofsson/mode-manager-mcp/refs/heads/main/logo-light-theme.svg" width="800">
</picture>


# Meet #remember -- Real Memory for You, Your Team, and Your AI

[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_Server-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=modemanager&config=%7B%22command%22%3A%22pipx%22%2C%22args%22%3A%5B%22run%22%2C%22mode-manager-mcp%22%5D%7D)
[![Install in VS Code Insiders](https://img.shields.io/badge/VS_Code_Insiders-Install_Server-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=modemanager&config=%7B%22command%22%3A%22pipx%22%2C%22args%22%3A%5B%22run%22%2C%22mode-manager-mcp%22%5D%7D&quality=insiders)
&nbsp;&nbsp;&nbsp;&nbsp;[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

Mode Manager MCP is an AI-powered memory and context system for developers and teams. It lets you and your team “remember” important facts, preferences, and best practices—so your AI assistant always has the right context, and your team’s knowledge is never lost.

With Mode Manager MCP, you can:
- Instantly store and retrieve personal, team, and language-specific knowledge.
- Share onboarding notes, coding conventions, and project wisdom—right where you work.
- Make your AI assistant smarter, more helpful, and always in sync with your workflow.

## Why “Remember”? (Features & Benefits)

- **Personal AI Memory:** Instantly store preferences, facts, and reminders for yourself—your AI assistant will always know your context.
- **Workspace (Team) Memory:** Share best practices, onboarding notes, and team knowledge directly in the repo. New team members ramp up faster, and everyone stays on the same page.
- **Language-Specific Memory:** Save and retrieve language-specific tips and conventions. Your assistant adapts to each language’s best practices automatically.
- **Natural Language Simplicity:** Just say “remember…”—no config files, no YAML, no technical hurdles.
- **Smarter Coding, Fewer Repeated Questions:** Your team’s memory grows over time, reducing repeated questions and ensuring consistent practices.

&nbsp;  
>&nbsp;  
> **Before this tool**  
> *"Hey Copilot, write me a Python function..."*  
> Copilot: *Gives generic Python code*
>
> **After using `remember`**  
> You: *"Remember I'm a senior data architect at Oatly, prefer type hints, and use Black formatting"*  
> Next conversation: *"Write me a Python function..."*  
> Copilot: *Generates perfectly styled code with type hints, following your exact preferences*  
>&nbsp;  

**Ready to have Copilot that actually remembers you? [Get started now!](#get-it-running-2-minutes)**

## Real-World Examples: Just Say It!

You don’t need special syntax—just talk to Copilot naturally. Mode Manager MCP is extremely relaxed about how you phrase things. 
If it sounds like something you want remembered, it will be!

>&nbsp;  
>**Personal memory**  
> You: *I like detailed docstrings and use pytest for testing.
> (Copilot, keep that in mind.)*  
>
> ---  
>**Team memory**  
> You: *We alw&nbsp;ays use the Oatly data pipeline template and follow our naming conventions.
> (Let’s make sure everyone remembers that.)*
>
> ---  
>**Language-specific memory**
> You: *For Python, use type hints and Black formatting.
> In C#, always use nullable reference types.*  
>&nbsp;  

## Get It Running (2 Minutes)

*If you don't even have `python`, you need to install that first. You can get it at [python.org/downloads](https://www.python.org/downloads/)*

### 1. Install pipx from PyPI
```bash
pip install pipx
```
### 2. Click on the badge for your VS Code

[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_Server-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=modemanager&config=%7B%22command%22%3A%22pipx%22%2C%22args%22%3A%5B%22run%22%2C%22mode-manager-mcp%22%5D%7D)
[![Install in VS Code Insiders](https://img.shields.io/badge/VS_Code_Insiders-Install_Server-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=modemanager&config=%7B%22command%22%3A%22pipx%22%2C%22args%22%3A%5B%22run%22%2C%22mode-manager-mcp%22%5D%7D&quality=insiders)

### .. Or manually add it to your VS Code

Add this to your VS Code MCP settings (`mcp.json`):

```json
{
  "servers": {
    "mode-manager": {
      "command": "pipx",
      "args": [
        "run",
        "mode-manager-mcp"
      ]
    }
  }
}
```

That's it! Start chatting with Copilot and use: *"Remember that..."*

### Bonus ..

As a convenience, you can run the following prompt in VS Code to get started in the best way:

>&nbsp;  
>You; */mcp.mode-manager.onboarding*  
>&nbsp;  

This will guide you through the onboarding process, set up your persistent memory, and ensure Copilot knows your preferences from the start.

### For the impatient (and brave) that can't wait for next release ..

If you add this in to your `mcp.json` it will result in `pipx` download and install the latest directly from github, every time. Always bleeding edge .. 

```json
{
  "servers": {
    "mode-manager": {
      "command": "pipx",
      "args": [
        "run",
        "--no-cache",
        "--system-site-packages",
        "--spec",
        "git+https://github.com/NiclasOlofsson/mode-manager-mcp.git",
        "mode-manager-mcp"
      ]
    }
  }
}
```


## Under the Hood: How Memory Magic Happens

Mode Manager MCP is designed to make memory persistent, context-aware, and 
easy to manage—without you having to think about the details. Here’s how 
it works under the hood:

### Memory Scopes

- **Personal Memory:**  
  Stored in a user-specific file (`memory.instructions.md`) in your VS Code prompts directory. This is your private memory—preferences, habits, and facts that follow you across all projects.

- **Workspace (Team) Memory:**  
  Stored in a workspace-level file (also `memory.instructions.md`, but in the workspace’s `.github/instructions` directory). This is shared with everyone working in the same repo, so team conventions and onboarding notes are always available.

- **Language-Specific Memory:**  
  Stored in files like `memory-python.instructions.md`, `memory-csharp.instructions.md`, etc. These are automatically loaded when you’re working in a particular language, so language tips and conventions are always at hand.

### How Memory is Stored

All memory is saved as Markdown files with a YAML frontmatter header, 
making it both human- and machine-readable. Each entry is timestamped and 
neatly organized, so you can always see when and what was remembered. You 
never have to manage these files yourself—Mode Manager MCP automatically 
creates and updates them as you add new memories.

### How Memory is Loaded

Here’s the magic: Mode Manager MCP writes and manages all your memory files, 
but it’s actually the new VS Code Copilot Chat that automatically loads 
them—every single turn. This deep integration means that, every time you send 
a message or ask Copilot for help, your user, workspace, and language memories 
are instantly available to the AI.

Language-specific memory is even smarter: it’s tied to file types using 
the `applyTo` property in the YAML frontmatter (for example, `**/*.py` for Python 
or `**/*.cs` for C#). This means you get the right tips, conventions, and 
reminders only when you’re working in the relevant language or file type—no clutter, 
just the context you need, exactly when you need it.

You never have to worry about context being lost between messages or sessions; your 
memory is always active and available. We’re simply leveraging this new, amazing 
VS Code feature to make your Copilot (and your team) smarter than ever.

### No Special Syntax Needed

There’s no need to remember special commands or keywords—just talk naturally. Mode Manager 
MCP is flexible and understands a wide range of phrasing. You don’t have to say 
“workspace” to store team memory; it recognizes common alternatives like “project,” 
“repo,” or even just describing something as a team convention. Whether you’re 
making a personal note, a team guideline, or a language-specific tip, just say it 
in your own words—Mode Manager MCP figures out what you want to remember and where it belongs.

## Wait, There’s More: Power Prompts & Custom Modes

Context prompting is critical for getting the best results from modern large language models like Copilot. As these models evolve and improve rapidly, so must the prompts and instructions we use with them. That’s why we built this functionality right into Mode Manager MCP—so you can always stay up to date, experiment with new approaches, and make sure your Copilot is as smart and helpful as possible.
>&nbsp;  
>**Want to see what’s available?**  
> You: *Show me the list of available chatmodes from the library.*  
>
>**Ready to try one?**  
> You: *Install the 'Beast Mode' chatmode from the library.*  
>&nbsp;  

Memory is just the beginning—Mode Manager MCP also helps you manage your entire Copilot experience with powerful instructions and chatmodes.

- **Instructions:**  
  Memory is stored as instruction files, but you can create your own instructions for any purpose—personal reminders, team guidelines, or project-specific tips.

- **Chatmodes:**  
  Switch between different “modes” for Copilot, like “Beast Mode” for deep research and coding, or “Architect Mode” for big-picture thinking with attention to critical details. The right system prompt can transform your Copilot from a generic assistant into a true expert for your current task.

- **Prompt Library & File Management:**  
  Access a curated library of professional prompts, and easily create, edit, and organize your own `.chatmode.md` and `.instructions.md` files.


A great Copilot experience isn’t just about memory—it’s about having the right context, the right instructions, and the right mode for every situation.

You have full control over your instructions and chatmodes with easy CLRUD (Create, List, Read, Update, Delete) commands—so you can manage, organize, and evolve your prompts as your needs change. There’s a curated library of high-quality chatmodes and instructions to get you started or inspire your own customizations.

One of the most powerful features is the ability to update your prompts and instructions directly from the online library. This keeps your setup in sync with the latest improvements, best practices, and new ideas—without losing your own custom tweaks. Stay up to date, collaborate with others, and always have the best Copilot experience possible.


## Contributing

Want to help improve this tool? Check out [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.
