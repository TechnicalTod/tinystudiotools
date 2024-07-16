@echo off

REM Set Maya version and script directory
set MAYAVERSION=2023
REM Set the folder that this Bat file is being run from
set SCRIPT_DIR=%~dp0

REM Set Maya application paths
set MAYA_APP_BASE_PATH=C:\Program Files\Autodesk\Maya%MAYAVERSION%
set MAYA_APP_PATH=%MAYA_APP_BASE_PATH%\bin\maya.exe

REM Set Show Directory
set SAGA_SHOW_DIR=S:\

REM Set custom script paths
set SAGA_MAYA_SCRIPT_PATH=%SCRIPT_DIR%

set MAYA_SCRIPT_PATH=^
%SCRIPT_DIR%scripts;^
%SCRIPT_DIR%shared;^
%SCRIPT_DIR%scripts\melScripts;^
%SCRIPT_DIR%tools

set PYTHONPATH=^
%SCRIPT_DIR%scripts;^
%SCRIPT_DIR%shared;^
%SCRIPT_DIR%scripts\melScripts;^
%SCRIPT_DIR%tools

REM Display the environment paths for verification
echo MAYA_SCRIPT_PATH is set to %MAYA_SCRIPT_PATH%
echo PYTHONPATH is set to %PYTHONPATH%

REM Launch Maya
start "" "%MAYA_APP_PATH%"
exit
