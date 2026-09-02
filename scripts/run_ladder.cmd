@echo off
REM Launch the self-dual sweep ladder detached from any editor or terminal.
REM
REM Started via WMI (Win32_Process.Create) the resulting process is owned by
REM the WMI service rather than by the shell that asked for it, so closing
REM VS Code or the terminal cannot take the sweep down with it.  These runs
REM last days; being tied to an editor window is not acceptable.
REM
REM   powershell -NoProfile -Command "Invoke-CimMethod -ClassName Win32_Process ^
REM     -MethodName Create -Arguments @{CommandLine='C:\Users\Nehal Ahmed\Code\three-stacks\scripts\run_ladder.cmd 19 20'}"
REM
REM Arguments are the lengths to sweep, in order.
cd /d "%~dp0.."
"C:\Program Files\Git\bin\bash.exe" scripts/dual_ladder.sh %* > logs\ladder.log 2>&1
