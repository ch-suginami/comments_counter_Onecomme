@echo off

if not "%~0"=="%~dp0.\%~nx0" (
     start /min cmd /c,"%~dp0.\%~nx0" %*
     exit
)

set EXE_ONE_COMME=%LOCALAPPDATA%\Programs\OneComme\OneComme.exe
echo %EXE_ONE_COMME%
start %EXE_ONE_COMME%

cd /d %~dp0
set WD=%~dp0
start python %WD%\comment_counter_ws_server.py
start python %WD%\comment_counter_ws.py