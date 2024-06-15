import maya.cmds as mc
from importlib import reload

def onStartUp():
    import buildSagaShelf
    buildSagaShelf.makeShelfAndButtons()

    print ("##############################")
    print ("##############################")
    print ("###  |\/\/\/|  ###############")
    print ("###  |      |  #### SAGA #####")
    print ("###  |      |  #### PREVIS ###")
    print ("###  | (o)(o)  #### SHELF ####")
    print ("###  C      _) ###############")
    print ("###   | ,___|  #### V1.0 #####")
    print ("###   |   /    ###############")
    print ("###  /____\    ###############")
    print ("### /      \   ###############")
    print ("##############################")
    print ("##############################")

mc.evalDeferred(onStartUp) 

