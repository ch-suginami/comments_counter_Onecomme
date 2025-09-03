@echo off

if not "%~0"=="%~dp0.\%~nx0" (
     start /min cmd /c,"%~dp0.\%~nx0" %*
     exit
)

cd /d %~dp0
set WD=%~dp0
start python %WD%\comment_counter_ws_server.py
start python %WD%\commnet_counter_ws.py