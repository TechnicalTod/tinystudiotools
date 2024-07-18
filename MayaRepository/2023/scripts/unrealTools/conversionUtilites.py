from matrixComposition import *
from changeOfBasis import *
import pxr.Usd, pxr.UsdGeom
from transforms3d.euler import euler2mat
import os

import unreal

np.set_printoptions(precision=3)
np.set_printoptions(suppress=True)

# Convert Maya / Houdini Transform to Unreal Transforms and vice versa
def from_to_rotation_conversion(translation, rotation, scale, units):
    YUP_TO_ZUP = np.array([
        [1, 0, 0, 0],
        [0, 0, 1, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1]
    ], dtype=int)

    matrixA = compose_matrix(translation, rotation, scale, order='sxyz')
    matrixB = change_xform(matrixA, YUP_TO_ZUP)
    t, r, s = decompose_matrix(matrixB, order='sxyz')

    scaled_t = (t[0] * units, t[1] * units, t[2] * units)

    t = scaled_t

    return t, r, s

def euler_from_quaternion(x, y, z, w):
        """
        Convert a quaternion into euler angles (roll, pitch, yaw)
        roll is rotation around x in radians (counterclockwise)
        pitch is rotation around y in radians (counterclockwise)
        yaw is rotation around z in radians (counterclockwise)
        """
        t0 = +2.0 * (w * x + y * z)
        t1 = +1.0 - 2.0 * (x * x + y * y)
        roll_x = math.atan2(t0, t1)
     
        t2 = +2.0 * (w * y - z * x)
        t2 = +1.0 if t2 > +1.0 else t2
        t2 = -1.0 if t2 < -1.0 else t2
        pitch_y = math.asin(t2)
     
        t3 = +2.0 * (w * z + x * y)
        t4 = +1.0 - 2.0 * (y * y + z * z)
        yaw_z = math.atan2(t3, t4)

        roll_x = math.degrees(roll_x)
        pitch_y = math.degrees(pitch_y)
        yaw_z = math.degrees(yaw_z)
        return roll_x, pitch_y, yaw_z # in Degrees

def complete_path(file_path, variant, version, asset_name, ext):
    path_ext = None
    if ext == 'maya':
        path_ext = '.ma'
    elif ext == 'usd':
        path_ext = '.usda'
    else:
        path_ext = '.' + ext
    if ext == 'ue':
        file_path = transform_path(file_path,'SETDEC', '/Game/01_Assets/')
        file_path = file_path.replace("\\", "/")
        final_path = file_path + asset_name + '/' + variant + '/' + version + '/' + asset_name + '_' + version
    else:
        file_path = file_path.replace("\\", "/")
        final_path = file_path + asset_name + '/' + variant + '/' + version + '/'  + ext + '/' + asset_name + '_' + version + path_ext
    

    return final_path.strip()

def transform_path(original_path, pivot, new_base):
    # Find the index of the pivot in the original path
    pivot_index = original_path.find(pivot)
    
    # Check if the pivot substring was found
    if pivot_index == -1:
        # Pivot not found, return original path or handle error as needed
        return original_path
    
    # Extract everything from the pivot substring onwards
    pivot_onwards = original_path[pivot_index:]
    
    # Prepend the new base path to the extracted portion
    transformed_path = new_base + pivot_onwards
    
    return transformed_path