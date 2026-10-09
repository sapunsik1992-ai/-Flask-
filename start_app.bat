@echo off
cd /d "%~dp0"
start "Flask Ads Server" cmd /k python server.py
ping -n 2 127.0.0.1 >nul
start http://127.0.0.1:5000/
