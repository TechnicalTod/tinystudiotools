import subprocess
import os

UNREAL_EXE = "C:/Program Files/Epic Games/UE_5.3/Engine/Binaries/Win64/UnrealEditor-cmd.exe"
UNREAL_PROJECT = "D:/Projects/Perforce/Boedi_sandbox/CFX_Sandbox/CFX_Sandbox.uproject"

def render():
    command = [
        UNREAL_EXE,
        UNREAL_PROJECT,
        "-execcmds=py {}".format("D:/Dev/UnrealRepository/scripts/CustomRenderBootstrap.py"),
        "-MoviePipelineConfig={}".format("/Game/DeadlineQueues/DeadlineQueueAsset")
    ]
    '''
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    '''
    #return proc.communicate()
    return command


command = render()
print(command)

"C:/Program Files/Epic Games/UE_5.3/Engine/Binaries/Win64/UnrealEditor-cmd.exe" "D:/Projects/Perforce/Boedi_sandbox/CFX_Sandbox/CFX_Sandbox.uproject" -execcmds="py D:/Dev/UnrealRepository/scripts/CustomRenderBootstrap.py" -MoviePipelineConfig="/Game/DeadlineQueues/DeadlineQueueAsset"

import subprocess
import os

u_level_file ='/Game/02_Episodes/101/101_AAA/101_AAA_0010/v015/PL_101_101_AAA_101_AAA_0010_v015'
u_level_seq_file = '/Game/02_Episodes/101/101_AAA/101_AAA_0010/v015/LS_101_101_AAA_101_AAA_0010_v015'
u_preset_file = '/Game/Utilities/RenderPresets/RenderTest'

UNREAL_EXE = "C:/Program Files/Epic Games/UE_5.3/Engine/Binaries/Win64/UnrealEditor-cmd.exe"
UNREAL_PROJECT = "D:/Projects/Perforce/Boedi_sandbox/CFX_Sandbox/CFX_Sandbox.uproject"

def movie_queue_render(u_level_file, u_level_seq_file, u_preset_file):
    command = [
        UNREAL_EXE,
        UNREAL_PROJECT,
        u_level_file,
 
        # required
        "-LevelSequence=%s" % u_level_seq_file,  # The sequence to render
        "-MoviePipelineConfig=\"%s\"" % u_preset_file,
        "-game",
 
        # options
        "-NoLoadingScreen",
        "-log",
 
        # window size not resolution
        "-Windowed",
        "-ResX=800",
        "-ResY=600",
    ]
    #proc = subprocess.Popen(command)
    #return proc.communicate()
    return command

command = movie_queue_render(u_level_file, u_level_seq_file, u_preset_file)
print(command)

"C:/Program Files/Epic Games/UE_5.3/Engine/Binaries/Win64/UnrealEditor-cmd.exe" "D:/Projects/Perforce/Boedi_sandbox/CFX_Sandbox/CFX_Sandbox.uproject" "/Game/02_Episodes/101/101_AAA/101_AAA_0010/v015/PL_101_101_AAA_101_AAA_0010_v015" -LevelSequence="/Game/02_Episodes/101/101_AAA/101_AAA_0010/v015/LS_101_101_AAA_101_AAA_0010_v015" -MoviePipelineConfig="/Game/Utilities/RenderPresets/RenderTest" -game -NoLoadingScreen -log -Windowed -ResX=800 -ResY=600
