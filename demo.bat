@echo off
chcp 65001 >nul
echo ========================================
echo Claude Plugins Manager - Демонстрация
echo ========================================
echo.

echo 1. Показать все установленные плагины:
echo ----------------------------------------
cpm.bat list
echo.
echo.

echo 2. Показать статус плагинов:
echo ----------------------------------------
cpm.bat status
echo.
echo.

echo 3. Показать информацию о конфигурации:
echo ----------------------------------------
cpm.bat info
echo.
echo.

echo ========================================
echo Демонстрация завершена!
echo ========================================
echo.
echo Попробуйте команды:
echo   cpm.bat list                           - список плагинов
echo   cpm.bat disable kotlin-lsp             - отключить плагин
echo   cpm.bat enable kotlin-lsp              - включить плагин
echo   cpm.bat status                         - статус плагинов
echo   cpm.bat change-scope kotlin-lsp user   - изменить scope плагина
echo.
pause
