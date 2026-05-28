"""
Maya Bridge Service

Direct interaction with Maya's API for TunnelUI operations.
Handles geometry import, material creation, and scene organization.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import maya.cmds as mc
import pymel.core as pm  # Add PyMel import like the working script
from dataclasses import dataclass

# Add crash logger import
import sys

try:
    sys.path.append(
        str(Path(__file__).parent.parent.parent.parent.parent)
    )  # Go up 5 levels to TunnelUI root
    from crash_logger import crash_logger
except ImportError:
    # Fallback logger if crash_logger import fails
    class FallbackLogger:
        def log(self, message):
            print(f"🔍 {message}")

    crash_logger = FallbackLogger()

from .import_models import AssetInfo
from configuration.config_models import MayaImportSettings


class MayaBridgeService:
    """Direct Maya integration and scene manipulation"""

    def __init__(self):
        """Initialize Maya bridge service"""
        self.logger = logging.getLogger(__name__)
        self.maya_available = self._check_maya_availability()

        # Import Maya modules if available
        if self.maya_available:
            try:
                import pymel.core as pm
                import maya.cmds as mc

                self.pm = pm
                self.mc = mc
                self.logger.info("Maya bridge service initialized successfully")
            except ImportError as e:
                self.maya_available = False
                self.logger.error(f"Failed to import Maya modules: {e}")
                raise MayaEnvironmentError(f"Maya modules not available: {e}")
        else:
            self.pm = None
            self.mc = None

    def _check_maya_availability(self) -> bool:
        """
        Check if Maya commands are available

        Returns:
            True if Maya is available
        """
        try:
            import maya.cmds
            import pymel.core

            return True
        except ImportError:
            return False

    def validate_maya_environment(self) -> bool:
        """
        Validate Maya environment for import operations

        Returns:
            True if Maya is ready for import
        """
        if not self.maya_available:
            return False

        try:
            # Check if Maya is in a valid state
            self.mc.file(query=True, exists=True)  # Check if a scene exists
            return True
        except Exception as e:
            self.logger.error(f"Maya environment validation failed: {e}")
            return False

    def import_geometry(
        self, file_path: Path, asset_name: str, import_settings: MayaImportSettings
    ) -> List[str]:
        """
        Import FBX files into Maya scene - SIMPLE VERSION
        Just imports the FBX file, returns the mesh objects. Nothing else.

        Args:
            file_path: Path to FBX file
            asset_name: Name for the imported asset (for namespace only)
            import_settings: Import configuration (minimal usage)

        Returns:
            List of imported mesh object names
        """
        if not self.maya_available:
            raise MayaEnvironmentError("Maya not available for geometry import")

        try:
            # Only import FBX files
            if file_path.suffix.lower() != ".fbx":
                raise ValueError(f"Only FBX files supported, got: {file_path.suffix}")

            imported_objects = self._import_fbx(file_path, asset_name, import_settings)
            self.logger.info(f"Imported geometry: {len(imported_objects)} objects from {file_path}")
            return imported_objects

        except Exception as e:
            self.logger.error(f"Failed to import geometry {file_path}: {e}")
            raise

    def _import_fbx(
        self, file_path: Path, asset_name: str, settings: MayaImportSettings
    ) -> List[str]:
        """FBX import using main thread execution to avoid UI conflicts"""
        try:
            import maya.utils as utils

            def safe_import():
                """Import function to run in Maya's main thread"""
                # Capture existing transforms before import
                before_import = set(self.mc.ls(type="transform"))

                # Use the basic mc.file() method that works in isolation
                self.mc.file(str(file_path), i=True, type="FBX")

                # Find new transforms
                after_import = set(self.mc.ls(type="transform"))
                new_transforms = list(after_import - before_import)

                return new_transforms

            self.logger.info(f"Importing FBX in main thread: {file_path}")

            # Execute the import in Maya's main thread to avoid UI conflicts
            new_transforms = utils.executeInMainThreadWithResult(safe_import)

            # Check if we actually imported anything
            if not new_transforms:
                self.logger.warning(f"No geometry imported from FBX: {file_path}")
                self.logger.info("Creating fallback sphere for material preview")

                # Create a simple sphere as fallback
                sphere_result = self.mc.polySphere(name=f"{asset_name}_preview_sphere", radius=1.0)
                fallback_sphere = sphere_result[0]  # Get the transform node

                self.logger.info(f"Created fallback sphere: {fallback_sphere}")
                return [fallback_sphere]

            self.logger.info(f"Main thread import completed: {len(new_transforms)} objects")
            return new_transforms

        except Exception as e:
            self.logger.error(f"Main thread FBX import failed: {e}")

            # Create fallback sphere on any import failure
            self.logger.info("Creating fallback sphere due to import failure")
            try:
                sphere_result = self.mc.polySphere(name=f"{asset_name}_fallback_sphere", radius=1.0)
                fallback_sphere = sphere_result[0]
                self.logger.info(f"Created fallback sphere: {fallback_sphere}")
                return [fallback_sphere]
            except Exception as sphere_error:
                self.logger.error(f"Failed to create fallback sphere: {sphere_error}")
                return []

    def _create_usd_preview_surface(
        self,
        material_name: str,
        textures: Dict[str, Path],
        settings: "MayaImportSettings",
    ) -> str:
        """Create USD Preview Surface material exactly like the working convertMegascansAssets.py script"""
        crash_logger.log(f"MAT-CREATE-1: Creating USD Preview Surface material: {material_name}")

        try:
            # Copy the exact parameter mapping from the working script
            crash_logger.log("MAT-CREATE-1.1: Setting up parameter mapping...")
            parameter_mapping = {
                "diffuse": {"mayaParameter": "diffuseColor", "fileNodeParameter": "outColor"},
                "emissive": {"mayaParameter": "emissiveColor", "fileNodeParameter": "outColor"},
                "ao": {"mayaParameter": "occlusion", "fileNodeParameter": "outAlpha"},
                "opacity": {"mayaParameter": "opacity", "fileNodeParameter": "outAlpha"},
                "metallic": {"mayaParameter": "metallic", "fileNodeParameter": "outAlpha"},
                "roughness": {"mayaParameter": "roughness", "fileNodeParameter": "outAlpha"},
                "normal": {"mayaParameter": "normal", "fileNodeParameter": "outColor"},
                "displacement": {"mayaParameter": "displacement", "fileNodeParameter": "outAlpha"},
            }
            crash_logger.log("MAT-CREATE-1.2: Parameter mapping completed")

            crash_logger.log("MAT-CREATE-2: Checking if material already exists...")

            # Check if material already exists (like working script)
            if pm.objExists(material_name):
                crash_logger.log(f"MAT-CREATE-3: Material {material_name} already exists, skipping")
                return material_name

            crash_logger.log("MAT-CREATE-4: Creating new USD Preview Surface shader...")

            # Create USD Preview Surface shader exactly like working script
            crash_logger.log(
                "MAT-CREATE-4.1: About to call pm.shadingNode for usdPreviewSurface..."
            )
            material_shader = pm.shadingNode("usdPreviewSurface", asShader=True, name=material_name)
            crash_logger.log(f"MAT-CREATE-5: Created USD Preview Surface shader: {material_shader}")

            # Create shading group exactly like working script
            crash_logger.log("MAT-CREATE-6.1: About to create shading group...")
            material_sg = pm.sets(
                renderable=True, noSurfaceShader=True, empty=True, name=f"{material_name}_SG"
            )
            crash_logger.log(f"MAT-CREATE-6: Created shading group: {material_sg}")

            # Connect shader to shading group exactly like working script
            crash_logger.log("MAT-CREATE-7.1: About to connect shader to shading group...")
            pm.connectAttr(
                f"{material_shader}.outColor", f"{material_sg}.surfaceShader", force=True
            )
            crash_logger.log("MAT-CREATE-7: Connected shader to shading group")

            # Process textures exactly like working script
            crash_logger.log(f"MAT-CREATE-8: Processing {len(textures)} textures...")

            # Debug: Log current texture settings
            if hasattr(settings, "enabled_texture_types"):
                crash_logger.log(
                    f"MAT-CREATE-8.0: Texture settings: {settings.enabled_texture_types}"
                )
            else:
                crash_logger.log(
                    "MAT-CREATE-8.0: No texture settings found, processing all textures"
                )

            texture_count = 0
            for param_name, texture_path in textures.items():
                texture_count += 1
                crash_logger.log(
                    f"MAT-CREATE-8.{texture_count}: Processing texture {texture_count}/{len(textures)}: {param_name}"
                )

                if param_name not in parameter_mapping:
                    crash_logger.log(
                        f"MAT-CREATE-8.{texture_count}.1: Skipping unknown parameter: {param_name}"
                    )
                    continue

                # Check if this texture type is enabled in settings
                if hasattr(settings, "enabled_texture_types"):
                    texture_enabled = settings.enabled_texture_types.get(param_name, True)
                    crash_logger.log(
                        f"MAT-CREATE-8.{texture_count}.1: Checking {param_name} enabled: {texture_enabled}"
                    )
                    if not texture_enabled:
                        crash_logger.log(
                            f"MAT-CREATE-8.{texture_count}.1: Skipping {param_name} texture (disabled in settings)"
                        )
                        continue

                crash_logger.log(
                    f"MAT-CREATE-8.{texture_count}.2: Processing texture: {param_name} -> {texture_path}"
                )

                # Get connection parameters from mapping
                maya_param = parameter_mapping[param_name]["mayaParameter"]
                file_output = parameter_mapping[param_name]["fileNodeParameter"]
                crash_logger.log(
                    f"MAT-CREATE-8.{texture_count}.3: Mapping - maya_param: {maya_param}, file_output: {file_output}"
                )

                # Create file node exactly like working script
                file_node_name = f"{material_name}_{param_name}_file"
                crash_logger.log(
                    f"MAT-CREATE-8.{texture_count}.4: About to create file node: {file_node_name}"
                )
                file_node = pm.shadingNode("file", asTexture=True, name=file_node_name)
                crash_logger.log(f"MAT-CREATE-8.{texture_count}.5: Created file node: {file_node}")

                # Set texture path exactly like working script
                crash_logger.log(f"MAT-CREATE-8.{texture_count}.6: About to set texture path...")
                pm.setAttr(f"{file_node}.fileTextureName", str(texture_path), type="string")
                crash_logger.log(
                    f"MAT-CREATE-8.{texture_count}.7: Set texture path: {texture_path}"
                )

                # Handle normal maps with bump2d exactly like working script
                if param_name == "normal":
                    crash_logger.log(
                        f"MAT-CREATE-8.{texture_count}.8: Creating bump2d node for normal map..."
                    )
                    bump2d_node = pm.shadingNode(
                        "bump2d", asUtility=True, name=f"{material_name}_normal_bump2d"
                    )
                    crash_logger.log(
                        f"MAT-CREATE-8.{texture_count}.9: Created bump2d node: {bump2d_node}"
                    )

                    crash_logger.log(
                        f"MAT-CREATE-8.{texture_count}.10: Setting bump2d attributes..."
                    )
                    pm.setAttr(f"{bump2d_node}.bumpInterp", 0)
                    pm.setAttr(f"{bump2d_node}.bumpDepth", 0.1)
                    crash_logger.log(f"MAT-CREATE-8.{texture_count}.11: Set bump2d attributes")

                    crash_logger.log(
                        f"MAT-CREATE-8.{texture_count}.12: Connecting file to bump2d..."
                    )
                    pm.connectAttr(f"{file_node}.outAlpha", f"{bump2d_node}.bumpValue", force=True)
                    crash_logger.log(f"MAT-CREATE-8.{texture_count}.13: Connected file to bump2d")

                    crash_logger.log(
                        f"MAT-CREATE-8.{texture_count}.14: Connecting bump2d to material..."
                    )
                    pm.connectAttr(
                        f"{bump2d_node}.outNormal", f"{material_shader}.{maya_param}", force=True
                    )
                    crash_logger.log(
                        f"MAT-CREATE-8.{texture_count}.15: Connected normal map through bump2d"
                    )
                else:
                    # Connect directly like working script
                    crash_logger.log(
                        f"MAT-CREATE-8.{texture_count}.8: Connecting texture directly..."
                    )
                    pm.connectAttr(
                        f"{file_node}.{file_output}", f"{material_shader}.{maya_param}", force=True
                    )
                    crash_logger.log(
                        f"MAT-CREATE-8.{texture_count}.9: Connected {param_name} texture directly"
                    )

            crash_logger.log(f"MAT-CREATE-9: Material creation completed: {material_name}")
            return material_name

        except Exception as e:
            crash_logger.log(f"MAT-CREATE-ERROR: Failed to create material {material_name}: {e}")
            self.logger.error(f"Failed to create USD Preview Surface material {material_name}: {e}")
            raise

    def create_usd_preview_material(
        self, material_name: str, texture_paths: Dict[str, Path], asset_info: AssetInfo
    ) -> str:
        """Create USD Preview Surface material using the working script's approach"""
        crash_logger.log(f"🔍 MAT-1: Starting material creation...")

        try:
            # Use the new PyMel-based method that copies the working script exactly
            from configuration.config_models import MayaImportSettings

            settings = MayaImportSettings()  # Default settings

            crash_logger.log(f"🔍 MAT-2: Calling PyMel-based material creation...")
            material_name = self._create_usd_preview_surface(
                material_name=material_name, textures=texture_paths, settings=settings
            )

            crash_logger.log(f"🔍 MAT-3: Material creation completed: {material_name}")
            return material_name

        except Exception as e:
            crash_logger.log(f"MAT-ERROR: Exception in material creation: {e}")
            self.logger.error(f"Failed to create material: {e}")
            raise

    def _connect_texture_to_material(
        self, material_shader, param_name: str, texture_path: Path, material_name: str
    ) -> None:
        """Connect texture file to material parameter"""
        try:
            # Parameter mapping from working convertMegascansAssets.py (USD Preview Surface)
            parameter_mapping = {
                "diffuse": {"maya_param": "diffuseColor", "file_output": "outColor"},
                "normal": {"maya_param": "normal", "file_output": "outColor"},
                "roughness": {"maya_param": "roughness", "file_output": "outAlpha"},
                "metallic": {"maya_param": "metallic", "file_output": "outAlpha"},
                "ao": {"maya_param": "occlusion", "file_output": "outAlpha"},
                "displacement": {"maya_param": "displacement", "file_output": "outAlpha"},
                "emissive": {"maya_param": "emissiveColor", "file_output": "outColor"},
                "opacity": {"maya_param": "opacity", "file_output": "outAlpha"},
            }

            if param_name not in parameter_mapping:
                self.logger.warning(f"Unknown texture parameter: {param_name}")
                return

            param_info = parameter_mapping[param_name]
            maya_param = param_info["maya_param"]
            file_output = param_info["file_output"]

            # Debug: Check what attributes are actually available on the material
            try:
                material_attrs = self.mc.listAttr(material_shader, connectable=True)
                crash_logger.log(f"Available attributes on {material_shader}: {material_attrs}")

                # Check if the expected attribute exists
                expected_attr = f"{material_shader}.{maya_param}"
                if self.mc.objExists(expected_attr):
                    crash_logger.log(f"Attribute {expected_attr} exists")
                else:
                    crash_logger.log(f"Attribute {expected_attr} does NOT exist")

                    # Try to find similar attributes
                    similar_attrs = [
                        attr for attr in material_attrs if maya_param.lower() in attr.lower()
                    ]
                    crash_logger.log(f"Similar attributes found: {similar_attrs}")

            except Exception as debug_error:
                crash_logger.log(f"Error checking attributes: {debug_error}")

            # Create file node
            file_node_name = f"{material_name}_{param_name}_file"
            file_node = self.pm.shadingNode("file", asTexture=True, name=file_node_name)

            # Set texture path
            self.pm.setAttr(f"{file_node}.fileTextureName", str(texture_path), type="string")

            # Special handling for normal maps
            if param_name == "normal":
                # Create bump2d node
                bump_node_name = f"{material_name}_normal_bump2d"
                bump_node = self.pm.shadingNode("bump2d", asUtility=True, name=bump_node_name)

                # Set bump2d properties
                self.pm.setAttr(f"{bump_node}.bumpInterp", 0)  # Tangent Space Normal
                self.pm.setAttr(f"{bump_node}.bumpDepth", 0.1)

                # Connect file to bump2d
                self.pm.connectAttr(f"{file_node}.outAlpha", f"{bump_node}.bumpValue", force=True)

                # Connect bump2d to material (with error handling)
                try:
                    self.pm.connectAttr(
                        f"{bump_node}.outNormal", f"{material_shader}.{maya_param}", force=True
                    )
                    crash_logger.log(f"Successfully connected normal texture")
                except Exception as normal_error:
                    crash_logger.log(f"Failed to connect normal texture: {normal_error}")
            else:
                # Direct connection for other textures (with error handling)
                try:
                    self.pm.connectAttr(
                        f"{file_node}.{file_output}", f"{material_shader}.{maya_param}", force=True
                    )
                    crash_logger.log(f"Successfully connected {param_name} texture")
                except Exception as connect_error:
                    crash_logger.log(f"Failed to connect {param_name} texture: {connect_error}")

                    # Try alternative attribute names for USD Preview Surface
                    alternative_attrs = {
                        "baseColor": ["diffuseColor", "baseColor", "color"],
                        "roughness": ["roughness", "specularRoughness"],
                        "metallic": ["metalness", "metallic"],
                        "emissiveColor": ["emissionColor", "emissiveColor"],
                        "opacity": ["opacity", "transmission"],
                    }

                    if maya_param in alternative_attrs:
                        for alt_attr in alternative_attrs[maya_param]:
                            try:
                                alt_full_attr = f"{material_shader}.{alt_attr}"
                                if self.mc.objExists(alt_full_attr):
                                    self.pm.connectAttr(
                                        f"{file_node}.{file_output}", alt_full_attr, force=True
                                    )
                                    crash_logger.log(
                                        f"Successfully connected using alternative attribute: {alt_attr}"
                                    )
                                    break
                            except Exception as alt_error:
                                crash_logger.log(
                                    f"Alternative attribute {alt_attr} also failed: {alt_error}"
                                )

            self.logger.debug(f"Connected {param_name} texture to material {material_name}")

        except Exception as e:
            self.logger.error(f"Failed to connect texture {param_name}: {e}")

    def assign_material_to_objects(self, material_name: str, object_names: List[str]) -> None:
        """Assign material to objects using PyMel like the working script"""
        crash_logger.log(
            f"MAT-ASSIGN-1: Assigning material {material_name} to {len(object_names)} objects"
        )

        try:
            # Get the shading group name (exactly like working script)
            material_sg_name = f"{material_name}_SG"
            crash_logger.log(f"MAT-ASSIGN-1.1: Looking for shading group: {material_sg_name}")

            if not pm.objExists(material_sg_name):
                crash_logger.log(
                    f"MAT-ASSIGN-ERROR: Shading group {material_sg_name} does not exist"
                )
                self.logger.error(f"Shading group {material_sg_name} not found")
                return

            crash_logger.log(f"MAT-ASSIGN-2: Found shading group: {material_sg_name}")

            # Get the shading group as PyMel object
            crash_logger.log("MAT-ASSIGN-2.1: About to get shading group as PyMel object...")
            material_sg = pm.PyNode(material_sg_name)
            crash_logger.log(f"MAT-ASSIGN-2.2: Got shading group PyMel object: {material_sg}")

            # Assign material to each object exactly like working script: pm.sets(material_sg, edit=True, forceElement=shapeObject)
            object_count = 0
            for obj_name in object_names:
                object_count += 1
                crash_logger.log(
                    f"MAT-ASSIGN-3.{object_count}: Processing object {object_count}/{len(object_names)}: {obj_name}"
                )

                if pm.objExists(obj_name):
                    crash_logger.log(
                        f"MAT-ASSIGN-3.{object_count}.1: Object exists, getting PyMel object..."
                    )
                    shape_object = pm.PyNode(obj_name)
                    crash_logger.log(
                        f"MAT-ASSIGN-3.{object_count}.2: Got PyMel object: {shape_object}"
                    )

                    crash_logger.log(
                        f"MAT-ASSIGN-3.{object_count}.3: About to assign material with pm.sets()..."
                    )
                    pm.sets(material_sg, edit=True, forceElement=shape_object)
                    crash_logger.log(
                        f"MAT-ASSIGN-3.{object_count}.4: Successfully assigned material to: {obj_name}"
                    )
                else:
                    crash_logger.log(
                        f"MAT-ASSIGN-WARN-{object_count}: Object {obj_name} does not exist"
                    )
                    self.logger.warning(f"Object {obj_name} does not exist for material assignment")

            crash_logger.log(f"MAT-ASSIGN-5: Material assignment completed for {material_name}")

        except Exception as e:
            crash_logger.log(f"MAT-ASSIGN-ERROR: Failed to assign material {material_name}: {e}")
            self.logger.error(f"Failed to assign material {material_name} to objects: {e}")
            raise
