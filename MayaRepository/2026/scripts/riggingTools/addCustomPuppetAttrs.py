import pymel.core as pm

#Get first Selection
selectedNode = pm.ls(sl=1)[0]

#Add Attrs
if not selectedNode.hasAttr("assetType"):
    pm.addAttr(selectedNode, longName='assetType', dataType='string', k=True)
selectedNode.assetType.set('CHR')
if not selectedNode.hasAttr("assetName"):
    pm.addAttr(selectedNode, longName='assetName', dataType='string', k=True)
selectedNode.assetName.set('GenericMale_chr')
if not selectedNode.hasAttr("variant"):
    pm.addAttr(selectedNode, longName='variant', dataType='string', k=True)
selectedNode.variant.set('rig_Main')
if not selectedNode.hasAttr("version"):
    pm.addAttr(selectedNode, longName='version', dataType='string', k=True)
selectedNode.version.set('v001')
if not selectedNode.hasAttr("rootJointName"):
    pm.addAttr(selectedNode, longName='rootJointName', dataType='string', k=True)
selectedNode.rootJointName.set('root_joint')
if not selectedNode.hasAttr("visGeoGroupName"):
    pm.addAttr(selectedNode, longName='visGeoGroupName', dataType='string', k=True)
selectedNode.visGeoGroupName.set('visGeo')

#Remove Attrs
customPuppetAttrs = ["assetType",
                    "assetName",
                    "variant",
                    "version",
                    "rootJointName",
                    "visGeoGroupName",
                    "version"]
for attr in customPuppetAttrs:
    if selectedNode.hasAttr(attr):
        pm.deleteAttr(selectedNode.attr(attr))