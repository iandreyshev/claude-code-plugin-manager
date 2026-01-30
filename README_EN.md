# Claude Plugins Manager (CPM)

🇷🇺 [Русская версия](README.md)

A command-line utility for managing Claude Code plugins on Windows.

![Version](https://img.shields.io/badge/version-0.3.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)

## Features

- 📋 View all installed plugins in `plugin@marketplace` format
- ✅ Enable/disable plugins per project
- 🔄 Change plugin installation scope
- 📊 Display Global Status and Local Status separately
- 🔍 Tab-completion for plugin names in interactive mode
- 🎨 Beautiful output with Rich library
- 🪟 Proper UTF-8 support in Windows console

## Quick Start

```bash
# 1. Clone repository
git clone https://github.com/iandreyshev/claude-code-plugin-manager.git
cd claude-code-plugin-manager

# 2. Install
python -m pip install -e .

# 3. Run in interactive mode
cpm.bat
```

## Usage

### Interactive Mode (recommended)

```bash
cpm.bat
```

```
Claude Plugins Manager v0.3.0
Interactive mode

┌─────────────────────────────────┬────────────────────────────────────────┐
│ Command                         │ Description                            │
├─────────────────────────────────┼────────────────────────────────────────┤
│ list                            │ Show all installed plugins             │
│ enable <plugin>                 │ Enable plugin for current project      │
│ disable <plugin>                │ Disable plugin for current project     │
│ change-scope <plugin> <scope>   │ Change plugin installation scope       │
│ sync                            │ Sync plugins to local settings         │
│ info                            │ Show configuration paths               │
│ exit                            │ Exit interactive mode                  │
└─────────────────────────────────┴────────────────────────────────────────┘

Use Tab for autocompletion, ↑/↓ for command history

> list
```

### List Output

```
                        Installed Claude Plugins
┌───────────────────────────┬─────────┬───────┬───────────────┬──────────────┐
│ Plugin                    │ Version │ Scope │ Global Status │ Local Status │
├───────────────────────────┼─────────┼───────┼───────────────┼──────────────┤
│ kotlin-lsp@claude-plugins │ 1.0.0   │ user  │ Disabled      │ Enabled      │
│ superpowers@claude-plugin │ 4.1.1   │ user  │ Undefined     │ Enabled      │
│ superpowers@superpowers   │ 4.1.1   │ user  │ Enabled       │ Undefined    │
└───────────────────────────┴─────────┴───────┴───────────────┴──────────────┘
```

- **Plugin** — full name in `plugin@marketplace` format
- **Global Status** — status from `~/.claude/settings.json` (read-only)
- **Local Status** — status from project's `.claude/settings.json`

### Command Mode

```bash
cpm.bat list                                    # Show all plugins
cpm.bat enable kotlin-lsp@claude-plugins        # Enable plugin
cpm.bat disable superpowers@superpowers         # Disable plugin
cpm.bat change-scope kotlin-lsp@claude user     # Change scope
cpm.bat sync                                    # Add all plugins to local
cpm.bat info                                    # Show config paths
```

### Multiple Plugins with Same Name

If you have plugins with the same name from different marketplaces, use the full name:

```bash
# Two superpowers plugins:
cpm.bat enable superpowers@claude-plugins-official
cpm.bat enable superpowers@superpowers
```

Tab-completion suggests full plugin names.

## Installation

### Requirements

- Python 3.8+
- Windows
- Claude Code installed

### Install from Source

```bash
git clone https://github.com/iandreyshev/claude-code-plugin-manager.git
cd claude-code-plugin-manager
python -m pip install -e .
```

### Dependencies

Installed automatically:
- `click>=8.0.0` — CLI framework
- `rich>=13.0.0` — formatted output
- `prompt-toolkit>=3.0.36` — interactive mode

## How It Works

### Claude Code Configuration

| File | Description |
|------|-------------|
| `~/.claude/plugins/installed_plugins.json` | All installed plugins |
| `~/.claude/settings.json` | Global settings (Global Status) |
| `.claude/settings.json` | Project settings (Local Status) |

### Settings Priority

Local Status overrides Global Status:

| Global | Local | Result |
|--------|-------|--------|
| Enabled | Undefined | Enabled |
| Enabled | Disabled | **Disabled** |
| Disabled | Enabled | **Enabled** |
| Disabled | Undefined | Disabled |

### settings.json Format

```json
{
  "enabledPlugins": {
    "kotlin-lsp@claude-plugins-official": true,
    "superpowers@superpowers": false
  }
}
```

## Project Structure

```
claude-code-plugin-manager/
├── claude_plugins_manager/
│   ├── __init__.py
│   ├── cli.py          # CLI and interactive mode
│   ├── manager.py      # Plugin management logic
│   └── config.py       # Configuration handling
├── cpm.bat             # Windows entry point
├── pyproject.toml      # Project configuration
└── README.md
```

## License

MIT

## Author

[@iandreyshev](https://github.com/iandreyshev)
