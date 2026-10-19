@echo off
rem Startup of every Obsidian Terminal tab (profile runs: cmd /k claude-tab.cmd).
rem The tab is plain cmd. Typing `claude` goes through claude-run.cmd, which remembers
rem this tab's folder and session; if Claude was still running when Obsidian closed,
rem the reopened tab resumes it there. OBSIDIAN_TAB_ID comes from the
rem claude-tab-sessions plugin and is saved with the tab.
doskey claude="%~dp0claude-run.cmd" $*
if "%OBSIDIAN_TAB_ID%"=="" goto :eof
setlocal
set "STATE=%LOCALAPPDATA%\claude-tabs\%OBSIDIAN_TAB_ID%.txt"
if not exist "%STATE%" goto :eof
for /f "usebackq tokens=1,* delims=|" %%a in ("%STATE%") do (
  set "SID=%%a"
  set "DIR=%%b"
)
cd /d "%DIR%"
call "%~dp0claude-run.cmd" --resume-tab %SID%
