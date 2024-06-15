import os
import maya.mel as mel
import maya.cmds as mc
from functools import partial

def ignoreParameters(cmd, *args, **kwargs):
    cmd()

class ShelfTool(object):

    def __init__(self, shelfName=None, iconDirectory=None, organisation_id=None, configPath=None):

        self.topLevelShelf = mel.eval('string $m = $gShelfTopLevel')
        self.shelfName = shelfName or 'newShelf'
        self.iconDirectory = iconDirectory
        self.shelfTab = None
        #self.sanctionedTools = loadConfig(organisation_id, configPath=configPath)

    def __parent__(self, item):

        if mc.objectTypeUI(item) == 'menu':

            parent = item

        if mc.objectTypeUI(item) == 'shelfButton':

            popups = mc.shelfButton(item, q=True, pma=True)
            if not popups:
                parent = mc.popupMenu(parent=item)
            else:
                parent = popups[0]

        return parent

    def fixShelfIndexes(self):

        shelves = mc.shelfTabLayout(self.topLevelShelf, query=True, tabLabelIndex=True)
        for index, shelf in enumerate(shelves):
            print (index, shelf)
            mc.optionVar(stringValue=('shelfName%d' % (index+1), str(shelf)))

    def createShelf(self):

        mel.eval('if (`shelfLayout -exists {0}`) deleteUI {0};'.format(self.shelfName))

        shelfTab = mel.eval('global string $gShelfTopLevel;'.format(self.shelfName))
        mel.eval('global string ${0};'.format(self.shelfName))
        shelfTab = mel.eval('${0} = `shelfLayout -cellWidth 33 -cellHeight 33 -p $gShelfTopLevel {0}`;'.format(self.shelfName))
        #self.fixShelfIndexes()
        self.shelfTab = shelfTab

        return shelfTab

    def cleanButton(self, button):

        popups = mc.shelfButton(button, q=True, pma=True)
        for menu in popups:
            mc.deleteUI(menu)

    def shelfButton(self, command, iconImage=None, annotation='', label='', imageOverlayLabel='', width=None, height=None):

        '''
        if self.sanctionedTools:
            if annotation and annotation not in self.sanctionedTools:
                return
        '''

        if iconImage:
            if not os.sep in iconImage:
                iconImage = os.path.join(self.iconDirectory, iconImage)

        buttonSize = 32

        mc.setParent(self.shelfTab)

        buttonArgs = dict(
                enableCommandRepeat=True,
                enable=True,
                width=width or buttonSize,
                height=height or buttonSize,
                manage=True,
                visible=True,
                annotation=annotation,
                label=label,
                imageOverlayLabel=imageOverlayLabel,
                image1=iconImage,
                style="iconOnly",
                )

        if command:
            buttonArgs['command'] = command

        button = mc.shelfButton(**buttonArgs)
        self.cleanButton(button)
        return button

    def addShelfSpacer(self, iconImage=None):

        if iconImage:
            if not os.sep in iconImage:
                iconImage = os.path.join(self.iconDirectory, iconImage)

        buttonArgs = dict(
                enableCommandRepeat=True,
                enable=True,
                width=10,
                height=32,
                manage=True,
                visible=True,
                style="iconOnly",
                )

        if iconImage:
            buttonArgs['image1'] = iconImage

        button = mc.shelfButton(**buttonArgs)
        self.cleanButton(button)
        return button

    def addMenu(self, button=None, label='Menu Item', cmd=None):

        if not button:
            return

        '''
        if self.sanctionedTools:
            if label not in self.sanctionedTools and not label == '':
                return
        '''
        
        parent = self.__parent__(button)

        #subCmd = command(cmd)

        if cmd:
            menuItem = mc.menuItem(l=label, c=partial(ignoreParameters, cmd), parent=parent)
        else:
            menuItem = mc.menuItem(l=label, parent=parent)
        return menuItem

    def addSubMenu(self, button=None, label='SubMenu'):

        if not button:
            return

        parent = self.__parent__(button)
        menuItem = mc.menuItem(l=label, parent=parent, subMenu=True)
        return menuItem

    def addMenuSpacer(self, button=None, label=None):

        if not button:
            return

        parent = self.__parent__(button)

        if label:
            menuItem = mc.menuItem(d=True, l=label, parent=parent)
        else:
            menuItem = mc.menuItem(d=True, parent=parent)

        return menuItem

    def showTab(self):

        mc.tabLayout(self.topLevelShelf, edit=True, selectTab=self.shelfName)