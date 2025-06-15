'''
Separate all meshes in selected hierarchy based on their shader assignments.
'''

import maya.cmds as mc
import maya.mel as mm
from importlib import reload
import genTools.jsGeneral
import sys

import genTools.genUtils as genUtils


sys.path.append('/weta/prod/previs/scripts/')
#from prePub.previsPrePub import correctShapeName

class SeparateObjectByShadingGroup():
    def __init__(self, object_name):
        self.object_name = object_name
        self.shape_node = genTools.jsGeneral.getShapeNodes(self.object_name)[0]


    def separateObject(self):
        '''Separate object into multiple objects based on the shading groups.
        If there is only one shading group associated with the object, but still with per-face assignment, then just keep the object, but remove
        per-face assignment
        '''
        separated_geos = []
        shading_groups = self.queryShadingGroups()
        
        i = 1
        while len(shading_groups) > 1:
            shading_group_assignments = self.queryShadingGroupAssignments(shading_groups[0])
            separated_geo = self.separate(shading_group_assignments, i)
            separated_geos.append(separated_geo)
            shading_groups = shading_groups[1:]
            i = i + 1
            
        else:
            self.fixPerFaceAssignment(self.object_name, self.shape_node) 
        
        return separated_geos
        

    def queryShadingGroups(self):
        ''' Return all shading groups associated with object. '''
        
        shading_groups = mc.listConnections(self.shape_node, d=True, s=False, p=False, t='shadingEngine')
        shading_groups = list(set(shading_groups))
       
        return shading_groups
    
    
    def queryShadingGroupAssignments(self, shading_group):
        '''
        Input: all shading groups associated with the object
        Return: Dictionary where key is a name of shading group and value is a list of all faces associated with shading group
        '''
        object_assignments = []
        all_assignments = mc.sets(shading_group, q=True)
        for assignment in all_assignments:
            if genTools.jsGeneral.getShortName(self.object_name) in assignment:
                object_assignments.append(assignment)
         
        shading_group_assignments = (shading_group, object_assignments)
                 
        return shading_group_assignments
    
    
    def separate(self, shading_group_assignments, i):
        '''Separate the actual geometry
        '''
        separated_geo = None
        if shading_group_assignments[1]:
            mc.select(shading_group_assignments[1], r=True)
            genUtils.detachComponents()
            separated_geo = mc.ls(sl=True, fl=True, l=True)[0]

            #fix shape name
            #correctShapeName(separated_geo)

            #remove per face assignment from the detached faces
            mc.select(hi=True)
            shape_node = genTools.jsGeneral.getShapeNodes(separated_geo)[0]
            self.fixPerFaceAssignment(separated_geo, shape_node) 
        
        return separated_geo

    
    def fixPerFaceAssignment(self, object_name, shape):
        '''if the object has only one shading group associated with it, but has per-face assignment, that means 'initialShadingGroup' is assigned as well.
        If that is the case, remove the association with 'initialShadingGroup'
        '''
        shaders = mc.listConnections(shape, d=True,s=False, p=False,t='shadingEngine')
        if 'initialShadingGroup' in shaders and len(shaders) > 1:
            shaders.remove('initialShadingGroup')
        mc.sets(object_name, fe = shaders[0])
    


def getAllObjects():
  '''Get names of all objects in the scene. This will be used to see if there are any duplicates of the object we want to separate
  '''
  all_objects_flat = mc.ls()
  all_objects = []
  
  for item in all_objects_flat:
      if "|" in item:
          item_name = item.rsplit("|", 1)[1]
          all_objects.append(item_name)
      else:
          all_objects.append(item)
      
  return all_objects
    
def main():

    separated_geos = []
    selection = mc.ls(sl=True, fl=True, l=True)
    
    flatSelection = genTools.jsGeneral.getFlatSelection(selection)
    for sel in flatSelection:
        if genTools.jsGeneral.isMesh(sel):
            separateSel = SeparateObjectByShadingGroup(sel)
            separated_geo = separateSel.separateObject()
            separated_geos.append(separated_geo)

    if separated_geos: 
        mc.select(cl=True)
        for geo in separated_geos:
            if geo:  
                mc.select(geo, add=True)
    else:
        try:
            mc.select(selection, r=True)
        except:
            pass
    if mc.ls(sl=True):
        mm.eval('print "Job done!"')
    else:
        mc.select(selection, r=True)
        mm.eval('print "Nothing to separate."')

    
    