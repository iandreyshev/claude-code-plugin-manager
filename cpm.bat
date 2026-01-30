@echo off
chcp 65001 >nul
python -m claude_plugins_manager.cli %*
