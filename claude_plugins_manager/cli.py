"""Command-line interface for Claude Plugins Manager."""

import click
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich import box
from .manager import PluginManager


# Настройка кодировки для Windows
if sys.platform == 'win32':
    # Попытка настроить stdout на UTF-8
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

console = Console(force_terminal=True)


def run_repl(group_ctx):
    """Run interactive REPL mode."""
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import NestedCompleter, WordCompleter
    from prompt_toolkit.history import InMemoryHistory

    # Получаем список плагинов для автодополнения (полное имя plugin@marketplace)
    manager = PluginManager()
    try:
        plugin_status = manager.get_plugin_status(None)
        plugin_names = [f"{info['name']}@{info['marketplace']}" for info in plugin_status.values()] if plugin_status else []
    except Exception:
        plugin_names = []

    # Создаём словарь для NestedCompleter
    scopes = {'project': None, 'user': None, 'global': None}
    plugin_completer = WordCompleter(plugin_names, ignore_case=True) if plugin_names else None

    completer = NestedCompleter.from_nested_dict({
        'list': None,
        'enable': plugin_completer,
        'disable': plugin_completer,
        'change-scope': plugin_completer,
        'sync': None,
        'info': None,
        'shell': None,
        'help': None,
        'exit': None,
        'quit': None,
    })

    # Создаем сессию с историей и автодополнением
    session = PromptSession(
        completer=completer,
        history=InMemoryHistory()
    )

    while True:
        try:
            # Получаем ввод пользователя
            text = session.prompt('> ')

            # Обработка специальных команд
            if text.strip() in ('exit', 'quit', ''):
                if text.strip() in ('exit', 'quit'):
                    break
                continue

            # Выполняем команду через click
            try:
                # Разбиваем ввод на аргументы, сохраняя кавычки
                import shlex
                try:
                    args = shlex.split(text)
                except ValueError:
                    args = text.split()

                if not args:
                    continue

                cmd_name = args[0]
                # Убираем префикс / если он есть (для удобства)
                if cmd_name.startswith('/'):
                    cmd_name = cmd_name[1:]

                cmd_args = args[1:]

                # Получаем команду из группы
                valid_commands = ['list', 'enable', 'disable', 'change-scope', 'sync', 'info', 'shell']

                if cmd_name == 'help':
                    # Показываем справку
                    console.print(group_ctx.get_help())
                elif cmd_name in valid_commands:
                    # Получаем команду напрямую из main.commands
                    # Используем globals() чтобы получить функцию main
                    main_func = globals()['main']
                    if cmd_name in main_func.commands:
                        cmd = main_func.commands[cmd_name]
                        # Вызываем команду через invoke, передав аргументы как в командной строке
                        try:
                            # Создаем контекст и вызываем команду
                            cmd.main(cmd_args, standalone_mode=False)
                        except click.exceptions.Exit:
                            pass  # Игнорируем нормальный выход
                    else:
                        console.print(f"[red]Команда '{cmd_name}' не найдена[/red]")
                else:
                    console.print(f"[red]Неизвестная команда: {cmd_name}[/red]")
                    console.print("[yellow]Введите 'help' для списка команд[/yellow]")

            except click.ClickException as e:
                e.show()
            except click.UsageError as e:
                console.print(f"[red]{e}[/red]")
            except SystemExit:
                # Игнорируем SystemExit от --help
                pass
            except Exception as e:
                console.print(f"[red]Ошибка: {e}[/red]")

        except KeyboardInterrupt:
            # Ctrl+C - продолжаем работу
            console.print()
            continue
        except EOFError:
            # Ctrl+D - выход
            break


def print_welcome():
    """Print welcome message for interactive mode."""
    console.print("\n[bold cyan]Claude Plugins Manager v0.3.0[/bold cyan]")
    console.print("Интерактивный режим\n")

    # Создаем таблицу с командами
    table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE)
    table.add_column("Команда", style="cyan", no_wrap=True)
    table.add_column("Описание", style="white")

    table.add_row("list", "Показать все установленные плагины и конфигурацию")
    table.add_row("enable <плагин>", "Включить плагин для текущего проекта")
    table.add_row("disable <плагин>", "Отключить плагин для текущего проекта")
    table.add_row("change-scope <плагин> <scope>", "Изменить область установки плагина")
    table.add_row("sync", "Добавить все плагины в локальный settings.json (disabled)")
    table.add_row("info", "Показать информацию о конфигурации")
    table.add_row("help", "Показать справку по всем командам")
    table.add_row("exit", "Выход из интерактивного режима")

    console.print(table)
    console.print("\n[dim]Команды можно вводить с '/' или без: [cyan]list[/cyan] или [cyan]/list[/cyan][/dim]")
    console.print("[dim]Используйте Tab для автодополнения, ↑/↓ для истории команд[/dim]\n")


@click.group(invoke_without_command=True)
@click.version_option(version="0.3.0")
@click.pass_context
def main(ctx):
    """Claude Plugins Manager - Manage your Claude Code plugins."""
    # Если запущено без команды, войти в интерактивный режим
    if ctx.invoked_subcommand is None:
        print_welcome()
        run_repl(ctx)


@main.command()
@click.pass_context
def shell(ctx):
    """Enter interactive shell mode."""
    print_welcome()
    run_repl(ctx.parent)


def display_plugin_table(manager: PluginManager, project_path: Path = None):
    """Display plugin table with status and configuration info."""
    status = manager.get_plugin_status(project_path)

    if not status:
        console.print("[yellow]No plugins installed[/yellow]")
        return

    # Create table
    table = Table(title="Installed Claude Plugins", box=box.ROUNDED)
    table.add_column("Plugin", style="cyan", no_wrap=False)
    table.add_column("Version", style="blue")
    table.add_column("Scope", style="yellow")
    table.add_column("Global Status", style="bold")
    table.add_column("Local Status", style="bold")

    for full_name, info in sorted(status.items()):
        # Global status from ~/.claude/settings.json (read-only)
        global_status = info.get('global_status')
        if global_status is None:
            global_status_text = "[yellow]Undefined[/yellow]"
        elif global_status:
            global_status_text = "[green]Enabled[/green]"
        else:
            global_status_text = "[red]Disabled[/red]"

        # Local status from local settings.json
        local_status = info.get('local_status')
        if local_status is None:
            local_status_text = "[yellow]Undefined[/yellow]"
        elif local_status:
            local_status_text = "[green]Enabled[/green]"
        else:
            local_status_text = "[red]Disabled[/red]"

        # Format scopes - join multiple scopes with comma
        scopes = info.get('all_scopes', [info.get('scope')])
        scope_text = ', '.join(s for s in scopes if s) or 'unknown'

        # Plugin name in plugin@marketplace format
        plugin_full_name = f"{info['name']}@{info['marketplace']}"

        table.add_row(
            plugin_full_name,
            info['version'] or 'unknown',
            scope_text,
            global_status_text,
            local_status_text
        )

    console.print(table)

    # Show configuration info
    config = manager.config
    display_path = project_path or Path.cwd()
    local_settings = display_path / ".claude" / "settings.json"

    console.print(f"\n[bold]Project:[/bold] {display_path}")
    if local_settings.exists():
        console.print(f"[bold]Local settings:[/bold] [green]{local_settings}[/green]")
    else:
        console.print(f"[bold]Local settings:[/bold] [yellow]Not found[/yellow]")
    console.print(f"[bold]Global settings:[/bold] {config.global_settings_file}")


@main.command()
@click.option('--path', '-p', type=click.Path(exists=True), help='Project path (default: current directory)')
def list(path):
    """List all installed plugins and their status."""
    project_path = Path(path) if path else None
    manager = PluginManager()

    try:
        display_plugin_table(manager, project_path)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@main.command()
@click.argument('plugin_name')
@click.option('--path', '-p', type=click.Path(exists=True), help='Project path (default: current directory)')
def enable(plugin_name, path):
    """Enable a plugin for the current project."""
    project_path = Path(path) if path else None
    manager = PluginManager()

    try:
        if manager.enable_plugin(plugin_name, project_path):
            console.print(f"[green][OK][/green] Plugin '{plugin_name}' enabled")
        else:
            console.print(f"[red][FAIL][/red] Failed to enable plugin '{plugin_name}'")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@main.command()
@click.argument('plugin_name')
@click.option('--path', '-p', type=click.Path(exists=True), help='Project path (default: current directory)')
def disable(plugin_name, path):
    """Disable a plugin for the current project."""
    project_path = Path(path) if path else None
    manager = PluginManager()

    try:
        if manager.disable_plugin(plugin_name, project_path):
            console.print(f"[green][OK][/green] Plugin '{plugin_name}' disabled")
        else:
            console.print(f"[red][FAIL][/red] Failed to disable plugin '{plugin_name}'")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@main.command()
@click.argument('plugin_name')
@click.argument('new_scope', type=click.Choice(['project', 'user', 'global']))
@click.option('--path', '-p', type=click.Path(exists=True), help='Project path (for project scope)')
@click.option('--index', '-i', type=int, default=0, help='Installation index (default: 0)')
def change_scope(plugin_name, new_scope, path, index):
    """Change the scope of a plugin installation."""
    manager = PluginManager()
    new_project_path = Path(path) if path else None

    try:
        if manager.change_plugin_scope(plugin_name, new_scope, index, new_project_path):
            console.print(f"[green][OK][/green] Changed scope of '{plugin_name}' to '{new_scope}'")
        else:
            console.print(f"[red][FAIL][/red] Failed to change scope of '{plugin_name}'")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@main.command()
@click.option('--path', '-p', type=click.Path(exists=True), help='Project path (default: current directory)')
def sync(path):
    """Add all installed plugins to local settings.json with enabled=False."""
    project_path = Path(path) if path else None
    manager = PluginManager()

    try:
        result = manager.sync_plugins_to_local(project_path)

        added = result['added']
        skipped = result['skipped']

        if added:
            console.print(f"[green][OK][/green] Added {len(added)} plugin(s) to local settings")
        else:
            console.print("[yellow]No new plugins to add[/yellow]")

        if skipped:
            console.print(f"[dim]Skipped {len(skipped)} plugin(s) (already defined)[/dim]")

        console.print()
        display_plugin_table(manager, project_path)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@main.command()
def info():
    """Show information about Claude configuration."""
    manager = PluginManager()
    config = manager.config

    console.print("\n[bold]Claude Configuration:[/bold]")
    console.print(f"Claude directory: {config.claude_dir}")
    console.print(f"Plugins directory: {config.plugins_dir}")
    console.print(f"Global settings: {config.global_settings_file}")

    console.print(f"\n[bold]Current project:[/bold]")
    current_path = Path.cwd()
    console.print(f"Path: {current_path}")

    local_settings = current_path / ".claude" / "settings.json"
    if local_settings.exists():
        console.print(f"Local settings: [green]Found[/green] ({local_settings})")
    else:
        console.print(f"Local settings: [yellow]Not found[/yellow]")


if __name__ == '__main__':
    main()
