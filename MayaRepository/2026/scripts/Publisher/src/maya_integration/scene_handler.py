import os
from typing import Dict, List, Tuple


class MayaSceneHandler:
    """Handles Maya-specific operations"""

    @staticmethod
    def get_scene_info() -> Dict[str, any]:
        """Get current Maya scene information"""
        try:
            import maya.cmds as cmds

            return {
                "scene_name": cmds.file(query=True, sceneName=True),
                "scene_modified": cmds.file(query=True, modified=True),
                "maya_version": cmds.about(version=True),
                "current_unit": cmds.currentUnit(query=True, linear=True),
                "frame_range": [
                    cmds.playbackOptions(query=True, minTime=True),
                    cmds.playbackOptions(query=True, maxTime=True),
                ],
            }
        except ImportError:
            return {
                "scene_name": "",
                "scene_modified": False,
                "maya_version": "Unknown",
                "current_unit": "cm",
                "frame_range": [1, 24],
            }

    @staticmethod
    def prepare_scene_for_publish() -> List[str]:
        """Prepare scene for publishing and return any warnings"""
        warnings = []

        try:
            import maya.cmds as cmds
            import maya.mel as mel

            # Save current selection
            selection = cmds.ls(selection=True)

            try:
                # Clear selection
                cmds.select(clear=True)

                # Basic scene cleanup
                if cmds.ls(type="unknown"):
                    warnings.append("Unknown nodes found in scene")

                # Check for empty groups
                empty_groups = [
                    node
                    for node in cmds.ls(type="transform")
                    if not cmds.listRelatives(node, children=True)
                ]
                if empty_groups:
                    warnings.append(f"Empty groups found: {len(empty_groups)}")

                # Check for unused shading nodes
                try:
                    unused_shaders = mel.eval("MLdeleteUnused;")
                    if unused_shaders:
                        warnings.append("Unused shading nodes removed")
                except:
                    warnings.append("Could not clean unused shading nodes")

            finally:
                # Restore selection
                if selection:
                    cmds.select(selection)

        except ImportError:
            warnings.append("Maya not available - cannot prepare scene")

        return warnings

    @staticmethod
    def validate_scene() -> Tuple[bool, List[str], List[str]]:
        """Validate current scene and return errors/warnings"""
        errors = []
        warnings = []

        try:
            import maya.cmds as cmds

            # Check if scene is saved
            if not cmds.file(query=True, sceneName=True):
                errors.append("Scene must be saved before publishing")

            # Check for references
            references = cmds.file(query=True, reference=True) or []
            if references:
                warnings.append(f"Scene contains {len(references)} references")

            # Check for missing textures
            file_nodes = cmds.ls(type="file")
            missing_textures = []
            for node in file_nodes:
                try:
                    texture_path = cmds.getAttr(f"{node}.fileTextureName")
                    if texture_path and not os.path.exists(texture_path):
                        missing_textures.append(texture_path)
                except:
                    pass  # Skip if attribute doesn't exist

            if missing_textures:
                warnings.append(f"Missing textures: {len(missing_textures)}")

            # Check polygon count (configurable threshold)
            poly_count = len(cmds.ls(type="mesh"))
            if poly_count > 10000:  # Example threshold
                warnings.append(f"High polygon count: {poly_count}")

        except ImportError:
            errors.append("Maya not available for validation")

        return len(errors) == 0, errors, warnings

    @staticmethod
    def get_scene_statistics() -> Dict[str, int]:
        """Get scene statistics for reporting"""
        try:
            import maya.cmds as cmds

            return {
                "poly_count": len(cmds.ls(type="mesh")),
                "transform_count": len(cmds.ls(type="transform")),
                "material_count": len(cmds.ls(materials=True)),
                "texture_count": len(cmds.ls(type="file")),
                "reference_count": len(cmds.file(query=True, reference=True) or []),
                "camera_count": len(cmds.ls(type="camera")),
                "light_count": len(cmds.ls(type="light")),
            }
        except ImportError:
            return {
                "poly_count": 0,
                "transform_count": 0,
                "material_count": 0,
                "texture_count": 0,
                "reference_count": 0,
                "camera_count": 0,
                "light_count": 0,
            }

    @staticmethod
    def save_scene_as(file_path: str) -> Tuple[bool, str]:
        """Save current scene to specified path"""
        try:
            import maya.cmds as cmds

            # Ensure directory exists
            from pathlib import Path

            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            # Save the scene
            cmds.file(rename=file_path)
            cmds.file(save=True, type="mayaAscii")

            return True, f"Scene saved to: {file_path}"

        except ImportError:
            return False, "Maya not available"
        except Exception as e:
            return False, f"Failed to save scene: {str(e)}"
