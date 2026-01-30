"""Configuration file management for Claude plugins."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any


class ClaudeConfig:
    """Manages Claude configuration files."""

    def __init__(self):
        """Initialize configuration paths."""
        self.home_dir = Path.home()
        self.claude_dir = self.home_dir / ".claude"
        self.plugins_dir = self.claude_dir / "plugins"
        self.global_settings_file = self.claude_dir / "settings.json"
        self.installed_plugins_file = self.plugins_dir / "installed_plugins.json"

    def get_installed_plugins(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all installed plugins from global configuration.

        Returns:
            Dictionary with plugin names as keys and installation info as values
        """
        if not self.installed_plugins_file.exists():
            return {}

        try:
            with open(self.installed_plugins_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('plugins', {})
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading installed plugins: {e}")
            return {}

    def get_global_settings(self) -> Dict[str, Any]:
        """
        Get global Claude settings.

        Returns:
            Dictionary with global settings
        """
        if not self.global_settings_file.exists():
            return {}

        try:
            with open(self.global_settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading global settings: {e}")
            return {}

    def get_local_settings(self, project_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Get local project settings.

        Args:
            project_path: Path to project directory (default: current directory)

        Returns:
            Dictionary with local settings
        """
        if project_path is None:
            project_path = Path.cwd()

        local_settings_file = project_path / ".claude" / "settings.json"

        if not local_settings_file.exists():
            return {}

        try:
            with open(local_settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading local settings: {e}")
            return {}

    def save_local_settings(self, settings: Dict[str, Any], project_path: Optional[Path] = None) -> bool:
        """
        Save local project settings.

        Args:
            settings: Settings dictionary to save
            project_path: Path to project directory (default: current directory)

        Returns:
            True if successful, False otherwise
        """
        if project_path is None:
            project_path = Path.cwd()

        claude_dir = project_path / ".claude"
        local_settings_file = claude_dir / "settings.json"

        try:
            # Create .claude directory if it doesn't exist
            claude_dir.mkdir(parents=True, exist_ok=True)

            with open(local_settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)

            return True
        except (IOError, OSError) as e:
            print(f"Error saving local settings: {e}")
            return False

    def get_enabled_plugins(self, project_path: Optional[Path] = None) -> Dict[str, bool]:
        """
        Get enabled/disabled status of plugins for a project.

        Combines global and local settings, with local taking precedence.

        Args:
            project_path: Path to project directory (default: current directory)

        Returns:
            Dictionary with plugin names as keys and enabled status as values
        """
        global_settings = self.get_global_settings()
        local_settings = self.get_local_settings(project_path)

        # Start with global enabled plugins
        enabled = global_settings.get('enabledPlugins', {}).copy()

        # Override with local settings
        local_enabled = local_settings.get('enabledPlugins', {})
        enabled.update(local_enabled)

        return enabled

    def set_plugin_enabled(self, plugin_name: str, enabled: bool,
                          project_path: Optional[Path] = None,
                          scope: str = 'local') -> bool:
        """
        Enable or disable a plugin.

        Args:
            plugin_name: Name of the plugin (e.g., "kotlin-lsp@claude-plugins-official")
            enabled: True to enable, False to disable
            project_path: Path to project directory (default: current directory)
            scope: 'local' or 'global' - where to save the setting

        Returns:
            True if successful, False otherwise
        """
        if scope == 'local':
            settings = self.get_local_settings(project_path)

            if 'enabledPlugins' not in settings:
                settings['enabledPlugins'] = {}

            settings['enabledPlugins'][plugin_name] = enabled

            return self.save_local_settings(settings, project_path)

        else:  # global
            # For global settings, we would need to modify the global settings file
            # This is more risky, so we'll implement it carefully
            print("Global scope modification not implemented yet. Use 'local' scope.")
            return False

    def save_installed_plugins(self, plugins: Dict[str, List[Dict[str, Any]]]) -> bool:
        """
        Save installed plugins to global configuration.

        Args:
            plugins: Dictionary with plugin names as keys and installation info as values

        Returns:
            True if successful, False otherwise
        """
        if not self.plugins_dir.exists():
            try:
                self.plugins_dir.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                print(f"Error creating plugins directory: {e}")
                return False

        try:
            with open(self.installed_plugins_file, 'w', encoding='utf-8') as f:
                json.dump({'plugins': plugins}, f, indent=2, ensure_ascii=False)
            return True
        except (IOError, OSError) as e:
            print(f"Error saving installed plugins: {e}")
            return False

    def change_plugin_scope(self, plugin_name: str, new_scope: str,
                           installation_index: int = 0,
                           new_project_path: Optional[Path] = None) -> bool:
        """
        Change the scope of a plugin installation.

        Args:
            plugin_name: Name of the plugin (e.g., "kotlin-lsp@claude-plugins-official")
            new_scope: New scope ('project', 'user', 'global', etc.)
            installation_index: Index of the installation to modify (default: 0)
            new_project_path: New project path (required if new_scope is 'project')

        Returns:
            True if successful, False otherwise
        """
        plugins = self.get_installed_plugins()

        if plugin_name not in plugins:
            print(f"Plugin '{plugin_name}' not found")
            return False

        installations = plugins[plugin_name]

        if installation_index >= len(installations):
            print(f"Installation index {installation_index} out of range")
            return False

        # Update the scope
        installations[installation_index]['scope'] = new_scope

        # If changing to project scope, update projectPath
        if new_scope == 'project':
            if new_project_path is None:
                new_project_path = Path.cwd()
            installations[installation_index]['projectPath'] = str(new_project_path.resolve())
        elif 'projectPath' in installations[installation_index]:
            # Remove projectPath if not project scope
            del installations[installation_index]['projectPath']

        # Update lastUpdated timestamp
        from datetime import datetime
        installations[installation_index]['lastUpdated'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        # Save changes
        return self.save_installed_plugins(plugins)
