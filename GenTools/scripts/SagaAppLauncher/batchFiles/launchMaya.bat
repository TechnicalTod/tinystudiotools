@echo off

REM Ensure a show name argument is provided
if "%1"=="" (
    echo No show name provided. Exiting...
    exit /b 1
)

REM Set show name from the provided argument
set SHOW_NAME=%1

REM Set Maya version from the provided argument
set MAYA_VERSION=%2

REM Set Maya application paths
set MAYA_APP_BASE_PATH=C:/Program Files/Autodesk/Maya%MAYA_VERSION%/
set MAYA_APP_PATH=%MAYA_APP_BASE_PATH%bin/maya.exe
set QT_PLUGIN_PATH=C:/Program Files/Autodesk/Maya2023/plugins/platforms

REM Set Show Directory
set SAGA_BASE_SHOW_DIR=S:/
REM Set Lib Directory
set SAGA_LIB_DIR=L:/
REM Set the Sagatools dir
set SCRIPT_DIR=%SAGA_LIB_DIR%SagaTools/
REM Set the Sagatools Maya repo dir, hard coded to 2023 for now until a maya version breaks the repo
set MAYA_REPO=%SCRIPT_DIR%MayaRepository/2023/

set MAYA_SCRIPT_PATH=^
%MAYA_REPO%scripts;^
%MAYA_REPO%shared;^
%MAYA_REPO%scripts/melScripts;^
%MAYA_REPO%tools

set PYTHONPATH=^
%MAYA_REPO%scripts;^
%MAYA_REPO%shared;^
%MAYA_REPO%scripts/melScripts;^
%MAYA_REPO%tools

REM Display the environment paths for verification
echo MAYA_SCRIPT_PATH is set to %MAYA_SCRIPT_PATH%
echo PYTHONPATH is set to %PYTHONPATH%
echo QT_PLUGIN_PATH is set to %QT_PLUGIN_PATH%
echo SHOW_NAME is set to %SHOW_NAME%
echo MAYA_VERSION is set to %MAYA_VERSION%

REM Ensure Maya executable exists
if not exist "%MAYA_APP_PATH%" (
    echo Maya executable not found at %MAYA_APP_PATH%. Exiting...
    exit /b 1
)

REM Launch Maya
start "" "%MAYA_APP_PATH%"
exit
