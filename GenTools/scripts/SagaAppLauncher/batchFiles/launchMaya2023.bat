@echo off

REM Ensure a show name argument is provided
if "%1"=="" (
    echo No show name provided. Exiting...
    exit /b 1
)

REM Set show name from the provided argument
set CURRENT_SHOW=%1

REM Set Maya version and script directory
set MAYAVERSION=2023

REM Set Maya application paths
set MAYA_APP_BASE_PATH="C:/Program Files/Autodesk/Maya%MAYAVERSION%/"
set MAYA_APP_PATH="%MAYA_APP_BASE_PATH%bin/maya.exe"
set QT_PLUGIN_PATH="C:/Program Files/Autodesk/Maya2023/plugins/platforms"

REM Set Show Directory
set SAGA_BASE_SHOW_DIR=S:/
REM Set Lib Directory
set SAGA_LIB_DIR=L:/
REM Set the Sagatools dir
set SCRIPT_DIR=%SAGA_LIB_DIR%SagaTools/
REM Set the Sagatools Maya repo dir
set MAYA_REPO=%SCRIPT_DIR%MayaRepository/%MAYAVERSION%/

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
echo CURRENT_SHOW is set to %CURRENT_SHOW%

REM Ensure Maya executable exists
if not exist "%MAYA_APP_PATH%" (
    echo Maya executable not found at %MAYA_APP_PATH%. Exiting...
    exit /b 1
)

REM Launch Maya
start "" "%MAYA_APP_PATH%"
exit
