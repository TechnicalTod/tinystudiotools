@echo off

REM Ensure a show name argument is provided
if "%1"=="" (
    echo No show name provided. Exiting...
    exit /b 1
)

REM Set show name from the provided argument
set CURRENT_SHOW=%1

REM Set Show Directory
set SAGA_BASE_SHOW_DIR=S:/
REM Set Lib Directory
set SAGA_LIB_DIR=L:/
REM Set the Sagatools dir
set SCRIPT_DIR=%SAGA_LIB_DIR%SagaTools/
REM Set the Sagatools Unreal repo dir
set UNREAL_REPO=%SCRIPT_DIR%UnrealRepository/

REM Set the Unreal project directory for the specific show
set UNREAL_PROJECT_BASE_DIR=%SAGA_BASE_SHOW_DIR%%CURRENT_SHOW%/05_Unreal/SAGA_%CURRENT_SHOW%/
set UNREAL_PROJECT_DIR=%UNREAL_PROJECT_BASE_DIR%SAGA_%CURRENT_SHOW%.uproject

set UNREAL_SCRIPT_PATH=^
%UNREAL_REPO%scripts;^
%UNREAL_REPO%shared;^
%UNREAL_REPO%tools

set PYTHONPATH=^
%UNREAL_REPO%scripts;^
%UNREAL_REPO%shared;^
%UNREAL_REPO%tools

REM Display environment variables for debugging
echo CURRENT_SHOW is set to %CURRENT_SHOW%
echo UNREAL_PROJECT_DIR is set to %UNREAL_PROJECT_DIR%
echo UNREAL_SCRIPT_PATH is set to %UNREAL_SCRIPT_PATH%
echo PYTHONPATH is set to %PYTHONPATH%

REM Check if Unreal project exists
if not exist "%UNREAL_PROJECT_DIR%" (
    echo Unreal project file not found at %UNREAL_PROJECT_DIR%. Exiting...

    REM PowerShell to show a popup message
    powershell -command "Add-Type -AssemblyName PresentationCore,PresentationFramework;[System.Windows.MessageBox]::Show('Unreal project file not found at %UNREAL_PROJECT_DIR%', 'Error', 'OK', 'Error')"

    exit /b 1
)

REM Launch Unreal project
start "" "%UNREAL_PROJECT_DIR%"
exit
