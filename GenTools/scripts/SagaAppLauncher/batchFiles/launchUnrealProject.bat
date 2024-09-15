@echo off

REM Set Show Directory
set SAGA_SHOW_DIR=S:/
REM Set Lib Directory
set SAGA_LIB_DIR=L:/
REM Set the Sagatools dir
set SCRIPT_DIR=%SAGA_LIB_DIR%SagaTools/
REM Set the Sagatools unreal repo dir
set UNREAL_REPO=%SCRIPT_DIR%UnrealRepository/

REM Set the Unreal project directory
set UNREAL_PROJECT_DIR=%SAGA_SHOW_DIR%002_PRISMSHOW\05_Unreal\SagaSandbox\SagaSandbox.uproject

set MAYA_SCRIPT_PATH=^
%UNREAL_REPO%scripts;^
%UNREAL_REPO%shared;^
%MAYA_REPO%tools

set PYTHONPATH=^
%UNREAL_REPO%scripts;^
%UNREAL_REPO%shared;^
%UNREAL_REPO%tools

REM Launch Maya
start "" "%UNREAL_PROJECT_DIR%"
exit
