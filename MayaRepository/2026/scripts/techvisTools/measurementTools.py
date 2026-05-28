import maya.cmds as cmds
import maya.OpenMayaUI as omui
import maya.OpenMaya as om
import maya.mel as mm
import pymel.core as pm
import math
import time

import maya.app.type.typeToolSetup

measurements = {}
current_measurement = 1
jobDict = {}
cylinderDict = {}

def createTypeTool(font=None, style=None, text=None, legacy=False):
    typeTool = cmds.createNode('type', n='type#', skipSelect=True)
    maya.app.type.typeToolSetup.createTypeToolWithNode(typeTool, font, style, text, legacy)
    return typeTool

def string_to_hex(s):
    return ' '.join(format(ord(c), '02X') for c in s)

def get_connected_transform(typeShape):
    connections = cmds.listConnections(typeShape, type='transform')
    return connections[0] if connections else None

def set_pivot_to_center(typeToolTransform):
    # World pivots only; BakeCustomPivot() rewrites type mesh history and spams warnings.
    bbox = typeToolTransform.getBoundingBox(space='world')
    center = [(bbox.min().x + bbox.max().x) / 2,
              (bbox.min().y + bbox.max().y) / 2,
              (bbox.min().z + bbox.max().z) / 2]
    typeToolTransform.setRotatePivot(center, worldSpace=True)
    typeToolTransform.setScalePivot(center, worldSpace=True)

def add_camera_list_attribute(object_name):
    if not object_name or not cmds.objExists(object_name):
        return
    # Get all cameras in the scene
    cameras = cmds.listCameras(perspective=True) + cmds.listCameras(orthographic=True)
    # Create an enum attribute with all cameras
    camera_enum = ":".join(cameras)
    if not cmds.attributeQuery('cameraLink', node=object_name, exists=True):
        cmds.addAttr(object_name, longName='cameraLink', attributeType='enum', enumName=camera_enum, keyable=True)

def update_camera_list_attribute(object_name):
    if not object_name or not cmds.objExists(object_name):
        return
    # Get all cameras in the scene
    cameras = cmds.listCameras(perspective=True) + cmds.listCameras(orthographic=True)
    # Create an enum string from the camera list
    camera_enum = ":".join(cameras)
    
    if cmds.attributeQuery('cameraLink', node=object_name, exists=True):
        # Try to update the attribute without deleting it
        cmds.addAttr(f'{object_name}.cameraLink', edit=True, enumName=camera_enum)
    else:
        # If the attribute does not exist, create it
        cmds.addAttr(object_name, longName='cameraLink', attributeType='enum', enumName=camera_enum, keyable=True)

def update_aim_constraint(group_name, target_group,attribute_name='cameraLink'):
    if not group_name or not cmds.objExists(group_name):
        return
    if not target_group or not cmds.objExists(target_group):
        return
    if not cmds.attributeQuery(attribute_name, node=group_name, exists=True):
        return
    # Safely handle the aim constraint update
    index = cmds.getAttr(f'{group_name}.{attribute_name}')
    cameras = cmds.listCameras(perspective=True) + cmds.listCameras(orthographic=True)
    target_camera = cameras[index]
    
    # Delete existing aim constraints carefully
    existing_constraints = cmds.listRelatives(target_group, type='aimConstraint')
    if existing_constraints:
        cmds.delete(existing_constraints)
    
    # Recreate the aim constraint
    cmds.aimConstraint(target_camera, target_group, aimVector=(0, 0, 1), upVector=(0, 1, 0), worldUpType="vector", worldUpVector=(0, 1, 0))
    
# Create a script job that calls this function whenever the cameraLink attribute changes
def create_camera_change_script_job(group_name, target_group):
    attr = f'{group_name}.cameraLink'
    job_id = cmds.scriptJob(attributeChange=[attr, lambda: update_aim_constraint(group_name, target_group)])
    return job_id

def setup_camera_monitor_job(object_name):
    # Monitor and update the camera list only when necessary
    previous_cameras = set(cmds.listCameras(perspective=True) + cmds.listCameras(orthographic=True))
    job_holder = {'id': None}

    def camera_monitor():
        nonlocal previous_cameras
        if not object_name or not cmds.objExists(object_name):
            jid = job_holder.get('id')
            if jid is not None:
                try:
                    cmds.scriptJob(kill=jid, force=True)
                except RuntimeError:
                    pass
            return
        current_cameras = set(cmds.listCameras(perspective=True) + cmds.listCameras(orthographic=True))
        if current_cameras != previous_cameras:
            update_camera_list_attribute(object_name)
            previous_cameras = current_cameras

    job_id = cmds.scriptJob(event=["DagObjectCreated", camera_monitor], protected=True)
    job_holder['id'] = job_id
    return job_id

def assign_surface_shader_to_mesh_shapes(transform, shader_name, shading_group):
    """Wire the shader to the SG and add only mesh shapes. hyperShade on the transform also targets
    sibling aimConstraints under that transform, which shadingEngines reject."""
    mesh_shapes = cmds.listRelatives(transform, shapes=True, path=True, type='mesh', noIntermediate=True) or []
    if not mesh_shapes:
        return
    cmds.connectAttr(shader_name + '.outColor', shading_group + '.surfaceShader', force=True)
    for shp in mesh_shapes:
        cmds.sets(shp, edit=True, forceElement=shading_group)

def cm_to_inches(cm):
    inches = cm / 2.54
    return inches

def cm_to_ft(cm):
    return cm / 30.48

def cm_to_m(cm):
    return cm / 100

def group_and_position_type_tool(typeToolShape, locator1_name, locator2_name, group_name, camera_name='persp'):
    locator1 = pm.PyNode(locator1_name)
    locator2 = pm.PyNode(locator2_name)
    midpoint = (locator1.getTranslation(space='object') + locator2.getTranslation(space='object')) / 2
    distance = (locator2.getTranslation(space='world') - locator1.getTranslation(space='world')).length()
    distance = round(distance, 2)

    units_mapping = {'cm': 0, 'm': 1, 'in': 2, 'ft': 3}
    units_index = cmds.getAttr(f"{group_name}.Units")
    units = next((unit for unit, index in units_mapping.items() if index == units_index), None)

    # Convert units to appropriate distance string
    if units == "cm":
        distancestr = "{:.2f}".format(distance) + 'cm'
    elif units == "in":
        distance = cm_to_inches(distance)
        distancestr = "{:.2f}".format(distance) + 'in'
    elif units == "ft":
        distance = cm_to_ft(distance)
        distancestr = "{:.2f}".format(distance) + 'ft'
    elif units == "m":
        distance = cm_to_m(distance)
        distancestr = "{:.2f}".format(distance) + 'm'

    # Convert distancestr to hexadecimal
    hex_distance = string_to_hex(distancestr)
    typeToolShapeNode = pm.PyNode(typeToolShape)
    typeToolShapeNode.textInput.set(hex_distance)
    typeToolShapeNode.fontSize.set(1)
    typeToolShapeNode.curveResolution.set(10)
    
    typeToolTransformName = get_connected_transform(typeToolShape)
    typeToolTransform = pm.PyNode(typeToolTransformName)
    typeToolTransform.setScale([1, 1, 1])  # Scale the text down
    
    #Disable Extrusion
    connections = cmds.listConnections(typeToolShape)
    type_extrude_nodes = [node for node in connections if node.startswith('typeExtrude')]
    cmds.setAttr(type_extrude_nodes[0] + ".enableExtrusion", 0)
    
    groupNode = pm.group(em=True, name='{}_{}_Text'.format(locator1_name, locator2_name))
    groupNode2 = pm.group(em=True, name='Null_{}_{}'.format(locator1_name, locator2_name))

    locator1_parent = locator1.getParent()
    
    # If locator1 has a parent, then reparent groupNode to that parent
    if locator1_parent:
        pm.parent(groupNode, locator1_parent)

    groupNode.setTranslation(midpoint, space='world')

    set_pivot_to_center(typeToolTransform)

    pm.xform(typeToolTransform, worldSpace=True, translation=pm.xform(groupNode, query=True, worldSpace=True, translation=True))
    
    pm.parent(groupNode2, groupNode, absolute=True)
    groupNode2.setTranslation([0, 0, 0], space='object')
    
    pm.parent(typeToolTransform, groupNode2, absolute=True)
    typeToolTransform.setTranslation([0, 0, 0], space='object')
    # Convert groupNode to cmds group
    groupNode_name = groupNode.name() 
    
    add_camera_list_attribute(group_name)
    job_id = create_camera_change_script_job(group_name, groupNode_name)
    job_id = setup_camera_monitor_job(group_name)
    
    cmds.setAttr(f'{group_name}.cameraLink', 0)
    
    cmds.connectAttr(f'{group_name}.FontSize', f'{typeToolTransform}.scaleX', force=True)
    cmds.connectAttr(f'{group_name}.FontSize', f'{typeToolTransform}.scaleY', force=True)
    
    # Create a new surface shader
    shader_name = cmds.shadingNode('surfaceShader', asShader=True, name=typeToolTransformName + "_shader")
    shading_group = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=shader_name + "SG")

    # Set the shader color to black
    cmds.setAttr(shader_name + '.outColor', 0, 0, 0, type='double3')

    assign_surface_shader_to_mesh_shapes(typeToolTransformName, shader_name, shading_group)
    
    # Create script job to update text when locators move
    def update_text(dummy=None):
        selection = cmds.ls(selection=True)
        if not cmds.objExists(typeToolShape):
            # If the text object has been deleted, return without doing anything
            return

        typeToolShapeNode.curveResolution.set(9)

        midpoint = (locator1.getTranslation(space='object') + locator2.getTranslation(space='object')) / 2
        groupNode.setTranslation(midpoint, space='object')
        
        distance = (locator2.getTranslation(space='world') - locator1.getTranslation(space='world')).length()
        distance = round(distance, 2)

        units_mapping = {'cm': 0, 'm': 1, 'in': 2, 'ft': 3}
        units_index = cmds.getAttr(f"{group_name}.Units")
        units = next((unit for unit, index in units_mapping.items() if index == units_index), None)

        # Convert units to appropriate distance string
        if units == "cm":
            distancestr = "{:.2f}".format(distance) + 'cm'
        elif units == "in":
            distance = cm_to_inches(distance)
            distancestr = "{:.2f}".format(distance) + 'in'
        elif units == "ft":
            distance = cm_to_ft(distance)
            distancestr = "{:.2f}".format(distance) + 'ft'
        elif units == "m":
            distance = cm_to_m(distance)
            distancestr = "{:.2f}".format(distance) + 'm'

        # Convert distancestr to hexadecimal
        hex_distance = string_to_hex(distancestr)
        typeToolShapeNode.textInput.set(hex_distance)  

        set_pivot_to_center(typeToolTransform)
        
        #pm.xform(typeToolTransform, worldSpace=True, translation=pm.xform(groupNode, query=True, worldSpace=True, translation=True))
        typeToolTransform.setTranslation([0, 0, 0], space='object')

        typeToolShapeNode.textInput.set(hex_distance)
        typeToolShapeNode.curveResolution.set(3)

        cmds.select(selection[0])
    
    # Create script job to update text when locators move
    job_ids = []
    locators = [locator1, locator2]  # Replace with your actual locator names
    
    for locator in locators:
        job_id = pm.scriptJob(attributeChange=[locator + '.translate', update_text], compressUndo=True)
        if job_id:
            job_ids.append(job_id)
            
    # Script job to monitor the 'freedomUnits' attribute
    freedom_units_job_id = pm.scriptJob(attributeChange=[f'{group_name}.Units', update_text], compressUndo=True)
    if freedom_units_job_id:
        job_ids.append(freedom_units_job_id)

    return groupNode

def get_unique_group_name(base_name):
    current_measurement = 0
    while True:
        group_name = f"{base_name}_{current_measurement}"
        if not cmds.objExists(group_name):
            break
        current_measurement += 1
    return group_name

def place_locator_ray(init_gapsize, init_fontsize, init_cyl, init_coneL, init_coneW):
    global current_measurement
    if cmds.draggerContext('locatorPlacerContext', exists=True):
        cmds.deleteUI('locatorPlacerContext')

    def on_press():
        global current_measurement
        locators = measurements.get(current_measurement, [])

        if len(locators) >= 2:
            current_measurement += 1
            locators = []

        view = omui.M3dView.active3dView()
        pressPosition = cmds.draggerContext('locatorPlacerContext', query=True, anchorPoint=True)
        x, y = int(pressPosition[0]), int(pressPosition[1])

        worldPoint, worldVector = om.MPoint(), om.MVector()
        view.viewToWorld(x, y, worldPoint, worldVector)

        raySource = om.MFloatPoint(worldPoint.x, worldPoint.y, worldPoint.z)
        rayDirection = om.MFloatVector(worldVector.x, worldVector.y, worldVector.z)

        meshes = cmds.ls(type='mesh')
        if not meshes:
            print("No meshes found in the scene for intersection.")
            return

        for mesh in meshes:
            selectionList = om.MSelectionList()
            selectionList.add(mesh)
            dagPath = om.MDagPath()
            selectionList.getDagPath(0, dagPath)
            fnMesh = om.MFnMesh(dagPath)

            hitPoint = om.MFloatPoint()
            if fnMesh.closestIntersection(raySource, rayDirection, None, None, False, om.MSpace.kWorld, 10000.0, False, None, hitPoint, None, None, None, None, None):
                locator_name = cmds.spaceLocator()[0]
                cmds.xform(locator_name, worldSpace=True, translation=(hitPoint.x, hitPoint.y, hitPoint.z))
                locators.append(locator_name)
                measurements[current_measurement] = locators
                print(f"Locator placed at: ({hitPoint.x}, {hitPoint.y}, {hitPoint.z}), Name: {locator_name}")

                if len(locators) == 2:
                    group_name = get_unique_group_name('MeasurementGroup')
                    cmds.group(locators, name=group_name)

                    cmds.addAttr(group_name, longName='GapSize', attributeType='float', defaultValue=init_gapsize, minValue=0.0, maxValue=0.5)
                    cmds.setAttr(f'{group_name}.GapSize', e=True, keyable=True)
                    
                    cmds.addAttr(group_name, longName='FontSize', attributeType='float', defaultValue=init_fontsize, minValue=0.1, maxValue=100.0)
                    cmds.setAttr(f'{group_name}.FontSize', e=True, keyable=True)
                    
                    cmds.addAttr(group_name, longName='CylinderWidth', attributeType='float', defaultValue=init_cyl, minValue=0, maxValue=100)
                    cmds.setAttr(f'{group_name}.CylinderWidth', e=True, keyable=True)
                    
                    cmds.addAttr(group_name, longName='coneLength', attributeType='float', defaultValue=init_coneL, minValue=0.01, maxValue=0.5)
                    cmds.setAttr(f'{group_name}.coneLength', e=True, keyable=True)
                    
                    cmds.addAttr(group_name, longName='coneWidth', attributeType='float', defaultValue=init_coneW, minValue=0, maxValue=100)
                    cmds.setAttr(f'{group_name}.coneWidth', e=True, keyable=True)
                    
                    units = ['cm', 'm', 'in', 'ft']
                    units_enum = ":".join(units)

                    # Now, you can use this string to create an enum attribute in Maya
                    cmds.addAttr(group_name, longName='Units', attributeType='enum', enumName=units_enum, keyable=True)
                    cmds.setAttr(f'{group_name}.Units', e=True, keyable=True)
                    
                    measurement_geo = []
                    
                    measurement_geo.append(create_or_update_cone(locators[0], locators[1], f"{current_measurement}_1", group_name))
                    measurement_geo.append(create_or_update_cone(locators[1], locators[0], f"{current_measurement}_2", group_name))
                    
                    measurement_geo.append(create_or_update_cylinder(locators[0], locators[1], 'alignedCylinder', group_name))
                    measurement_geo.append(create_or_update_cylinder(locators[1], locators[0], 'alignedCylinder', group_name))
                    
                    #createToonOutlineOnDimensions(measurement_geo)
                    
                    typeToolShape = createTypeTool(text="StruggleStreet")
                    group_and_position_type_tool(typeToolShape, locators[0], locators[1], group_name)
                return

        print("No intersection found with any mesh.")

    cmds.draggerContext('locatorPlacerContext', pressCommand=on_press, cursor='crossHair')
    cmds.setToolTo('locatorPlacerContext')

def place_locator(init_gapsize, init_fontsize, init_cyl, init_coneL, init_coneW):
    global current_measurement

    locators = measurements.get(current_measurement, [])

    if len(locators) >= 2:
        current_measurement += 1
        locators = []

    selected = cmds.ls(selection=True)
    print(selected)
    
    for object in selected:
        selected_translation = cmds.getAttr(f"{object}.translate")[0]

        locator_name = cmds.spaceLocator()[0]
        cmds.xform(locator_name, worldSpace=True, translation=(selected_translation))
        locators.append(locator_name)
        measurements[current_measurement] = locators

        if len(locators) == 2:
            group_name = get_unique_group_name('MeasurementGroup')
            cmds.group(locators, name=group_name)

            cmds.addAttr(group_name, longName='GapSize', attributeType='float', defaultValue=init_gapsize, minValue=0.0, maxValue=0.5)
            cmds.setAttr(f'{group_name}.GapSize', e=True, keyable=True)
            
            cmds.addAttr(group_name, longName='FontSize', attributeType='float', defaultValue=init_fontsize, minValue=0.1, maxValue=100.0)
            cmds.setAttr(f'{group_name}.FontSize', e=True, keyable=True)
            
            cmds.addAttr(group_name, longName='CylinderWidth', attributeType='float', defaultValue=init_cyl, minValue=0, maxValue=100)
            cmds.setAttr(f'{group_name}.CylinderWidth', e=True, keyable=True)
            
            cmds.addAttr(group_name, longName='coneLength', attributeType='float', defaultValue=init_coneL, minValue=0.01, maxValue=0.5)
            cmds.setAttr(f'{group_name}.coneLength', e=True, keyable=True)
            
            cmds.addAttr(group_name, longName='coneWidth', attributeType='float', defaultValue=init_coneW, minValue=0, maxValue=100)
            cmds.setAttr(f'{group_name}.coneWidth', e=True, keyable=True)
            
            units = ['cm', 'm', 'in', 'ft']
            units_enum = ":".join(units)

            cmds.addAttr(group_name, longName='Units', attributeType='enum', enumName=units_enum, keyable=True)
            cmds.setAttr(f'{group_name}.Units', e=True, keyable=True)
            
            measurement_geo = []
            
            measurement_geo.append(create_or_update_cone(locators[0], locators[1], f"{current_measurement}_1", group_name))
            measurement_geo.append(create_or_update_cone(locators[1], locators[0], f"{current_measurement}_2", group_name))
            
            measurement_geo.append(create_or_update_cylinder(locators[0], locators[1], 'alignedCylinder', group_name))
            measurement_geo.append(create_or_update_cylinder(locators[1], locators[0], 'alignedCylinder', group_name))
            
            #createToonOutlineOnDimensions(measurement_geo)
            
            typeToolShape = createTypeTool(text="StruggleStreet")
            group_and_position_type_tool(typeToolShape, locators[0], locators[1], group_name)
            return

        #print("No intersection found with any mesh.")

def create_or_update_cylinder(start_locator, end_locator, cylinder_base_name="alignedCylinder", group_name=''):
    # Create a unique name for the cylinder using the base name and current timestamp
    unique_suffix = str(int(time.time() * 1000))  # Millisecond timestamp for uniqueness
    cylinder_name = cylinder_base_name + '_' + unique_suffix
    
    # Get the world space positions of the start and end locators
    start_pos = cmds.xform(start_locator, query=True, worldSpace=True, translation=True)
    end_pos = cmds.xform(end_locator, query=True, worldSpace=True, translation=True) 
    
    # Create the cylinder
    cylinder = cmds.polyCylinder(name=cylinder_name, radius=0.1, height=1, subdivisionsX=10, subdivisionsY=1, subdivisionsZ=1, axis=[0, 1, 0])[0]
    cmds.xform(cylinder, pivots=[0, -0.55, 0], worldSpace=True)
    cmds.parent(cylinder, start_locator)
    cmds.xform(cylinder, translation=[0, 0.55, 0], objectSpace=True)  # Compensate for initial pivot setting
    
    # Align the cylinder by aiming it towards the end locator
    temp_locator = cmds.spaceLocator()[0]
    cmds.move(end_pos[0], end_pos[1], end_pos[2], temp_locator)
    cmds.aimConstraint(temp_locator, cylinder, aimVector=(0, 1, 0), upVector=(0, 0, 1), worldUpType="scene")
    cmds.delete(cmds.aimConstraint(cylinder, q=True), temp_locator)  # Clean up after alignment
    
    # Create a distanceDimension node to calculate distance between the two locators
    distance_node = cmds.createNode('distanceBetween', name=cylinder_name + '_distance')
    cmds.connectAttr(start_locator + '.worldMatrix[0]', distance_node + '.inMatrix1')
    cmds.connectAttr(end_locator + '.worldMatrix[0]', distance_node + '.inMatrix2')
    
    # Create a multiplyDivide node to adjust the distance by the GapSize scaling factor
    md_node = cmds.createNode('multiplyDivide', name=cylinder_name + '_scaleAdjust')
    cmds.setAttr(md_node + '.operation', 1)  # Set to divide to scale down by GapSize
    cmds.connectAttr(distance_node + '.distance', md_node + '.input1X')
    cmds.connectAttr(f'{group_name}.GapSize', md_node + '.input2X')  # Connect GapSize as the scaling factor
    
    # Connect the adjusted distance output to scaleY of the cylinder for dynamic scaling
    cmds.connectAttr(md_node + '.outputX', cylinder + '.scaleY')
    
    cmds.connectAttr(f'{group_name}.CylinderWidth', cylinder + '.scaleZ')
    cmds.connectAttr(f'{group_name}.CylinderWidth', cylinder + '.scaleX')
    
    # Apply a permanent aim constraint to keep the cylinder aiming at the end locator
    cmds.aimConstraint(end_locator, cylinder, aimVector=(0, 1, 0), upVector=(0, 0, 1), worldUpType="scene")
    
    # Create a new surface shader
    shader_name = cmds.shadingNode('surfaceShader', asShader=True, name=cylinder_base_name + "_shader")
    shading_group = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=shader_name + "SG")

    # Set the shader color to black
    cmds.setAttr(shader_name + '.outColor', 0, 0, 0, type='double3')

    assign_surface_shader_to_mesh_shapes(cylinder, shader_name, shading_group)
    
    return cylinder

def create_or_update_cone(locator1, locator2, unique_id, group_name):
    cone_name = f"{locator1}_cone"
    if cone_name in cylinderDict:
        print(f"Updating {cone_name}...")
    else:
        cone = cmds.polyCone(name=cone_name, radius=0.3, height=1, subdivisionsX=10, subdivisionsY=2, subdivisionsZ=1, axis=[0, 1, 0])[0]
        # Immediately rotate the cone 180 degrees around the Z-axis to flip the base and tip
        cmds.rotate(0, 0, 180, cone, relative=True)

        # Set the pivot at the intended tip, which should now be the narrower end after rotation
        cmds.xform(cone, pivots=[0, -0.5, 0], worldSpace=True)
        cmds.parent(cone, locator1)
        cmds.xform(cone, translation=[0, -0.5, 0], objectSpace=True)

        # Aim the cone towards locator2 with base aiming away from locator1
        cmds.aimConstraint(locator2, cone, aimVector=(0, -1, 0), upVector=(0, 0, 1), worldUpType="scene")

        distance_node = cmds.createNode('distanceBetween', name=f"{cone_name}_distance")
        cmds.connectAttr(locator1 + '.worldMatrix[0]', distance_node + '.inMatrix1')
        cmds.connectAttr(locator2 + '.worldMatrix[0]', distance_node + '.inMatrix2')
        
        # Create a multiplyDivide node to adjust the distance by the GapSize scaling factor
        md_node = cmds.createNode('multiplyDivide', name=f"{cone_name}_scaleAdjust")
        cmds.setAttr(md_node + '.operation', 1)  # Set to divide to scale down by GapSize
        cmds.connectAttr(distance_node + '.distance', md_node + '.input1X')
        cmds.connectAttr(f'{group_name}.coneLength', md_node + '.input2X')  # Connect GapSize as the scaling factor
        
        # Connect the adjusted distance output to scaleY of the cylinder for dynamic scaling
        cmds.connectAttr(md_node + '.outputX', cone + '.scaleY')
        
        cmds.connectAttr(f'{group_name}.coneWidth', cone + '.scaleZ')
        cmds.connectAttr(f'{group_name}.coneWidth', cone + '.scaleX')
        
        cylinderDict[cone_name] = cone
        
        # Create a new surface shader
        shader_name = cmds.shadingNode('surfaceShader', asShader=True, name=cone_name + "_shader")
        shading_group = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=shader_name + "SG")
    
        # Set the shader color to black
        cmds.setAttr(shader_name + '.outColor', 0, 0, 0, type='double3')
    
        assign_surface_shader_to_mesh_shapes(cone, shader_name, shading_group)
        
        return cone
        
def createToonOutlineOnDimensions(listGeo):
    RColor = 1
    GColor = 1
    BColor = 1
    VisibleShapes = []
    for shape_name in listGeo:
        # Assuming shape_name is the transform node that contains the geometry
        shape_node = pm.PyNode(shape_name)
        if shape_node.nodeType() == 'transform':
            meshes = [child for child in shape_node.getChildren() if child.nodeType() == 'mesh']
            if not meshes:
                continue
            mesh = meshes[0]
            if mesh.getAttr('visibility'):
                parent_transform = mesh.getParent()
                if parent_transform and parent_transform.getAttr('visibility'):
                    VisibleShapes.append(shape_name)

    if VisibleShapes:
        cmds.select(VisibleShapes)
        mm.eval('AssignNewPfxToon;')
        # Set attributes on the newly created toon outlines
        for shape in VisibleShapes:
            connections = cmds.listConnections(shape, type='pfxToon')
            if connections:
                toonShapeParent = cmds.listRelatives(connections[0], parent=True)[0]
                cmds.setAttr(toonShapeParent + '.lineWidth', 0.05)
                cmds.setAttr(toonShapeParent + '.profileColorR', RColor)
                cmds.setAttr(toonShapeParent + '.profileColorG', GColor)
                cmds.setAttr(toonShapeParent + '.profileColorB', BColor)
                # Set other colors as needed...
    else:
        print("No visible shapes found to apply Toon Outline.")
        
# Run this function to activate the tool:
#place_locator_ray(0.38, 15, 15, 0.04, 15)