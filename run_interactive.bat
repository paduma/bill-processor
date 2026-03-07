@echo off
REM 账单处理工具 - 交互式启动脚本
REM 自动设置正确的编码

REM 设置控制台代码页为 UTF-8
chcp 65001 >nul 2>&1

REM 设置环境变量
set PYTHONIOENCODING=utf-8

REM 运行 Python 脚本
python bill_processor_interactive.py

REM 如果出错，暂停以查看错误信息
if errorlevel 1 pause
