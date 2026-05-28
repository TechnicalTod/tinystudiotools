import maya.cmds as mc
from importlib import reload
import warnings
import sys
import os

print("TinyStudio userSetup.py loaded successfully")


def onStartUp():
    print("Starting TinyStudio initialization...")

    try:
        import buildTinyStudioShelf

        buildTinyStudioShelf.buildTinyStudioShelf()
        print("TinyStudio shelf built successfully")
    except Exception as e:
        print(f"Error building TinyStudio shelf: {e}")

    print("##############################")
    print("##############################")
    print("###  |\/\/\/|  ###############")
    print("###  |      |  ## TINYSTUDIO #")
    print("###  |      |  #### SHELF ####")
    print("###  | (o)(o)  ##############")
    print("###  C      _) ###############")
    print("###   | ,___|  #### V1.0 #####")
    print("###   |   /    ###############")
    print("###  /____\    ###############")
    print("### /      \   ###############")
    print("##############################")
    print("##############################")


mc.evalDeferred(onStartUp)
