"""Plugin management logic."""

from pathlib import Path
from typing import List, Dict, Any, Optional
from .config import ClaudeConfig


class PluginInfo:
    """Information about a plugin."""

    def __init__(self, name: str, installations: List[Dict[str, Any]]):
        """
        Initialize plugin info.

        Args:
            name: Plugin name (e.g., "kotlin-lsp@claude-plugins-official")
            installations: List of installation records
        """
        self.name = name
        self.installations = installations

    @property
    def full_name(self) -> str:
        """Get full plugin name."""
        return self.name

    @property
    def plugin_name(self) -> str:
        """Get plugin name without marketplace."""
        return self.name.split('@')[0]

    @property
    def marketplace(self) -> str:
        """Get marketplace name."""
        parts = self.name.split('@')
        return parts[1] if len(parts) > 1 else 'unknown'

    @property
    def version(self) -> Optional[str]:
        """Get plugin version (from first installation)."""
        if self.installations:
            return self.installations[0].get('version')
        return None

    @property
    def scope(self) -> Optional[str]:
        """Get plugin scope (from first installation)."""
        if self.installations:
            return self.installations[0].get('scope')
        return None

    @property
    def all_scopes(self) -> List[str]:
        """Get all scopes from all installations."""
        scopes = []
        for installation in self.installations:
            scope = installation.get('scope')
            if scope and scope not in scopes:
                scopes.append(scope)
        return scopes

    @property
    def install_path(self) -> Optional[str]:
        """Get plugin install path (from first installation)."""
        if self.installations:
            return self.installations[0].get('installPath')
        return None

    def __repr__(self) -> str:
        """String representation."""
        return f"PluginInfo(name='{self.name}', version='{self.version}')"


class PluginManager:
    """Manages Claude plugins."""

    def __init__(self):
        """Initialize plugin manager."""
        self.config = ClaudeConfig()

    def list_plugins(self) -> List[PluginInfo]:
        """
        List all installed plugins.

        Returns:
            List of PluginInfo objects
        """
        installed = self.config.get_installed_plugins()
        plugins = []

        for plugin_name, installations in installed.items():
            plugins.append(PluginInfo(plugin_name, installations))

        # Sort by plugin name
        plugins.sort(key=lambda p: p.plugin_name)

        return plugins

    def get_plugin_status(self, project_path: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all plugins for a project.

        Args:
            project_path: Path to project directory (default: current directory)

        Returns:
            Dictionary with plugin info and enabled status
        """
        plugins = self.list_plugins()
        global_settings = self.config.get_global_settings()
        global_enabled = global_settings.get('enabledPlugins', {})
        local_settings = self.config.get_local_settings(project_path)
        local_enabled = local_settings.get('enabledPlugins', {})

        status = {}
        for plugin in plugins:
            # global_status: True/False if defined in global settings, None if undefined
            global_status = global_enabled.get(plugin.full_name)
            # local_status: True/False if defined in local settings, None if undefined
            local_status = local_enabled.get(plugin.full_name)

            status[plugin.full_name] = {
                'name': plugin.plugin_name,
                'marketplace': plugin.marketplace,
                'version': plugin.version,
                'global_status': global_status,  # None if not in global settings
                'local_status': local_status,  # None if not in local settings
                'scope': plugin.scope,
                'all_scopes': plugin.all_scopes,
                'install_path': plugin.install_path,
            }

        return status

    def sync_plugins_to_local(self, project_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Add all installed plugins to local settings.json with enabled=False
        if they're not already defined there.

        Args:
            project_path: Path to project directory (default: current directory)

        Returns:
            Dictionary with 'added' (list of added plugins) and 'skipped' (already defined)
        """
        plugins = self.list_plugins()
        local_settings = self.config.get_local_settings(project_path)

        if 'enabledPlugins' not in local_settings:
            local_settings['enabledPlugins'] = {}

        local_enabled = local_settings['enabledPlugins']

        added = []
        skipped = []

        for plugin in plugins:
            if plugin.full_name not in local_enabled:
                local_enabled[plugin.full_name] = False
                added.append(plugin.full_name)
            else:
                skipped.append(plugin.full_name)

        if added:
            self.config.save_local_settings(local_settings, project_path)

        return {'added': added, 'skipped': skipped}

    def enable_plugin(self, plugin_name: str, project_path: Optional[Path] = None) -> bool:
        """
        Enable a plugin for a project.

        Args:
            plugin_name: Name of the plugin (can be partial name or full name with marketplace)
            project_path: Path to project directory (default: current directory)

        Returns:
            True if successful, False otherwise
        """
        # Find matching plugin
        full_name = self._find_plugin_full_name(plugin_name)
        if not full_name:
            print(f"Plugin '{plugin_name}' not found")
            return False

        return self.config.set_plugin_enabled(full_name, True, project_path)

    def disable_plugin(self, plugin_name: str, project_path: Optional[Path] = None) -> bool:
        """
        Disable a plugin for a project.

        Args:
            plugin_name: Name of the plugin (can be partial name or full name with marketplace)
            project_path: Path to project directory (default: current directory)

        Returns:
            True if successful, False otherwise
        """
        # Find matching plugin
        full_name = self._find_plugin_full_name(plugin_name)
        if not full_name:
            print(f"Plugin '{plugin_name}' not found")
            return False

        return self.config.set_plugin_enabled(full_name, False, project_path)

    def change_plugin_scope(self, plugin_name: str, new_scope: str,
                           installation_index: int = 0,
                           new_project_path: Optional[Path] = None) -> bool:
        """
        Change the scope of a plugin installation.

        Args:
            plugin_name: Name of the plugin (can be partial name or full name with marketplace)
            new_scope: New scope ('project', 'user', 'global', etc.)
            installation_index: Index of the installation to modify (default: 0)
            new_project_path: New project path (required if new_scope is 'project')

        Returns:
            True if successful, False otherwise
        """
        # Find matching plugin
        full_name = self._find_plugin_full_name(plugin_name)
        if not full_name:
            print(f"Plugin '{plugin_name}' not found")
            return False

        return self.config.change_plugin_scope(full_name, new_scope, installation_index, new_project_path)

    def _find_plugin_full_name(self, partial_name: str) -> Optional[str]:
        """
        Find full plugin name from partial name.

        Args:
            partial_name: Partial or full plugin name

        Returns:
            Full plugin name or None if not found
        """
        plugins = self.list_plugins()

        # Exact match
        for plugin in plugins:
            if plugin.full_name == partial_name:
                return plugin.full_name

        # Partial match on plugin name
        matches = [p for p in plugins if p.plugin_name == partial_name or partial_name in p.plugin_name]

        if len(matches) == 1:
            return matches[0].full_name
        elif len(matches) > 1:
            print(f"Multiple plugins match '{partial_name}':")
            for match in matches:
                print(f"  - {match.full_name}")
            print("Please use the full plugin name.")
            return None

        return None
