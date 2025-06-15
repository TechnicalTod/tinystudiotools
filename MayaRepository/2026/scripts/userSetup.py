import maya.cmds as mc
from importlib import reload
import warnings
import sys
import os

print("SagaTools userSetup.py loaded successfully")


def onStartUp():
    print("Starting SagaTools initialization...")

    try:
        # Import and build the shelf
        import buildSagaShelf

        buildSagaShelf.buildSagaShelf()
        print("Saga Shelf built successfully")
    except Exception as e:
        print(f"Error building Saga Shelf: {e}")

    print("##############################")
    print("##############################")
    print("###  |\/\/\/|  ###############")
    print("###  |      |  #### SAGA #####")
    print("###  |      |  #### PREVIS ###")
    print("###  | (o)(o)  #### SHELF ####")
    print("###  C      _) ###############")
    print("###   | ,___|  #### V1.0 #####")
    print("###   |   /    ###############")
    print("###  /____\    ###############")
    print("### /      \   ###############")
    print("##############################")
    print("##############################")


mc.evalDeferred(onStartUp)
