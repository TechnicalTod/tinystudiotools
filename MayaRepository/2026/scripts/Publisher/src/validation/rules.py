import os
from typing import List, Tuple
from .validation_manager import ValidationRule


class NamingConventionRule(ValidationRule):
    """Validate scene naming conventions"""

    def __init__(self):
        super().__init__("Naming Convention", "Check asset/shot naming standards")

    def validate(self) -> Tuple[bool, List[str], List[str]]:
        errors = []
        warnings = []

        try:
            import maya.cmds as cmds

            # Check current scene name
            scene_name = cmds.file(query=True, sceneName=True, shortName=True)
            if not scene_name:
                errors.append("Scene must be saved with a proper name")
                return False, errors, warnings

            # Check naming pattern (customize based on studio standards)
            if not self._check_naming_pattern(scene_name):
                warnings.append(f"Scene name may not follow naming convention: {scene_name}")

        except ImportError:
            warnings.append("Maya not available for naming validation")

        return len(errors) == 0, errors, warnings

    def _check_naming_pattern(self, name: str) -> bool:
        """Check if name follows expected pattern"""
        # Simple example - customize for your studio
        return "_" in name and not name.startswith("untitled")


class SceneCleanupRule(ValidationRule):
    """Validate scene cleanliness"""

    def __init__(self):
        super().__init__("Scene Cleanup", "Check for unused nodes and cleanup issues")

    def validate(self) -> Tuple[bool, List[str], List[str]]:
        errors = []
        warnings = []

        try:
            import maya.cmds as cmds

            # Check for unknown nodes
            unknown_nodes = cmds.ls(type="unknown")
            if unknown_nodes:
                warnings.append(f"Unknown nodes found: {len(unknown_nodes)}")

            # Check for empty groups
            empty_groups = [
                node
                for node in cmds.ls(type="transform")
                if not cmds.listRelatives(node, children=True)
            ]
            if empty_groups:
                warnings.append(f"Empty groups found: {len(empty_groups)}")

            # Check for unused materials
            all_materials = cmds.ls(materials=True)
            used_materials = set()
            for shape in cmds.ls(type="mesh"):
                shading_engines = cmds.listConnections(shape, type="shadingEngine")
                if shading_engines:
                    for sg in shading_engines:
                        materials = cmds.listConnections(f"{sg}.surfaceShader")
                        if materials:
                            used_materials.update(materials)

            unused_materials = [
                mat
                for mat in all_materials
                if mat not in used_materials and not mat.startswith("lambert1")
            ]
            if unused_materials:
                warnings.append(f"Unused materials found: {len(unused_materials)}")

        except ImportError:
            warnings.append("Maya not available for cleanup validation")
        except Exception as e:
            warnings.append(f"Error during cleanup validation: {str(e)}")

        return True, errors, warnings


class FilePathRule(ValidationRule):
    """Validate file paths and references"""

    def __init__(self):
        super().__init__("File Paths", "Check for missing files and broken references")

    def validate(self) -> Tuple[bool, List[str], List[str]]:
        errors = []
        warnings = []

        try:
            import maya.cmds as cmds

            # Check for missing texture files
            file_nodes = cmds.ls(type="file")
            missing_textures = []
            for node in file_nodes:
                try:
                    texture_path = cmds.getAttr(f"{node}.fileTextureName")
                    if texture_path and not os.path.exists(texture_path):
                        missing_textures.append(texture_path)
                except:
                    pass

            if missing_textures:
                errors.append(f"Missing texture files: {len(missing_textures)}")

            # Check references
            references = cmds.file(query=True, reference=True) or []
            broken_refs = []
            for ref in references:
                if not os.path.exists(ref):
                    broken_refs.append(ref)

            if broken_refs:
                errors.append(f"Broken references: {len(broken_refs)}")

        except ImportError:
            warnings.append("Maya not available for file path validation")
        except Exception as e:
            warnings.append(f"Error during file path validation: {str(e)}")

        return len(errors) == 0, errors, warnings


class GeometryRule(ValidationRule):
    """Validate geometry in the scene"""

    def __init__(self):
        super().__init__("Geometry", "Check geometry for common issues")

    def validate(self) -> Tuple[bool, List[str], List[str]]:
        errors = []
        warnings = []

        try:
            import maya.cmds as cmds

            # Check for non-manifold geometry
            meshes = cmds.ls(type="mesh")
            non_manifold_count = 0

            for mesh in meshes:
                try:
                    # Basic check - could be enhanced with more detailed validation
                    if cmds.polyInfo(mesh, nonManifoldVertices=True):
                        non_manifold_count += 1
                except:
                    pass

            if non_manifold_count > 0:
                warnings.append(f"Non-manifold geometry found in {non_manifold_count} meshes")

            # Check polygon count
            total_polys = 0
            for mesh in meshes:
                try:
                    poly_count = cmds.polyEvaluate(mesh, face=True)
                    total_polys += poly_count
                except:
                    pass

            if total_polys > 100000:  # Configurable threshold
                warnings.append(f"High polygon count: {total_polys}")

            # Check for duplicate names
            all_transforms = cmds.ls(type="transform")
            unique_names = set(all_transforms)
            if len(all_transforms) != len(unique_names):
                warnings.append("Duplicate object names found")

        except ImportError:
            warnings.append("Maya not available for geometry validation")
        except Exception as e:
            warnings.append(f"Error during geometry validation: {str(e)}")

        return len(errors) == 0, errors, warnings
