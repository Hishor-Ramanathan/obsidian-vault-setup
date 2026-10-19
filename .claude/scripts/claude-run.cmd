@echo off
rem `claude` inside an Obsidian Terminal tab (doskey macro from claude-tab.cmd).
rem Records "<session>|<folder>" for this tab while Claude runs; a clean exit (/exit)
rem forgets it, so only sessions left running when Obsidian closed come back.
setlocal
if "%OBSIDIAN_TAB_ID%"=="" (
  call claude %*
  goto :eof
)
set "STATE=%LOCALAPPDATA%\claude-tabs\%OBSIDIAN_TAB_ID%.txt"
if "%~1"=="--resume-tab" (
  set "SID=%~2"
) else if "%~1"=="" (
  for /f %%g in ('powershell -NoProfile -Command "[guid]::NewGuid().ToString()"') do set "SID=new-%%g"
) else (
  rem own arguments (e.g. --resume): can't know the id, restore with --continue
  set "SID=continue"
)

if "%~1"=="--resume-tab" (
  if "%SID%"=="continue" (set "ARGS=--continue") else (set "ARGS=--resume %SID%")
) else if "%SID:~0,4%"=="new-" (
  set "SID=%SID:~4%"
  set "ARGS=--session-id %SID:~4%"
) else (
  set "ARGS=%*"
)

if not exist "%LOCALAPPDATA%\claude-tabs" mkdir "%LOCALAPPDATA%\claude-tabs"
rem The Terminal plugin leaves claude running when a tab closes: end this session's
rem orphan from the last Obsidian run before resuming it
if not "%SID%"=="continue" powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='claude.exe'\" | Where-Object { $_.CommandLine -like '*%SID%*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
>"%STATE%" echo %SID%^|%CD%
rem start Claude on a clean screen (also drops a resumed tab's replayed history)
cls
call claude %ARGS%
rem killed by Obsidian closing = nonzero exit: keep the state so the tab resumes
if not errorlevel 1 del "%STATE%"
