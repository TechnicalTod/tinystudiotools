"""
Texture Processing Service

Handles texture extraction and conversion from Megascans assets.
Based on logic from convertMegascansAssets.py.
"""

import json
import logging
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any

from configuration.config_models import MayaImportSettings
from .import_models import (
    TextureProcessingResult,
    AssetInfo,
    TextureProcessingError,
    AssetExtractionError,
)


class TextureProcessingService:
    """Handles texture extraction and conversion from Megascans assets"""

    def __init__(self, config: MayaImportSettings):
        """
        Initialize texture processing service

        Args:
            config: Maya import configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Find ImageMagick
        self.imagemagick_path = self._find_imagemagick()

        # Parameter mapping from convertMegascansAssets.py
        self.parameter_mapping = {
            "diffuse": {"suffix": "Albedo", "maya_param": "baseColor"},
            "normal": {"suffix": "Normal", "maya_param": "normalCamera"},
            "roughness": {"suffix": "Roughness", "maya_param": "specularRoughness"},
            "metallic": {"suffix": "Metallic", "maya_param": "metalness"},
            "ao": {"suffix": "AO", "maya_param": "baseColor"},  # Special handling
            "displacement": {"suffix": "Displacement", "maya_param": "displacement"},
            "emissive": {"suffix": "Emissive", "maya_param": "emissionColor"},
            "opacity": {"suffix": "Opacity", "maya_param": "opacity"},
        }

    def _find_imagemagick(self) -> Optional[str]:
        """
        Find ImageMagick installation

        Returns:
            Path to ImageMagick executable or None if not found
        """
        if self.config.imagemagick_path != "auto":
            # Use explicit path
            explicit_path = Path(self.config.imagemagick_path)
            if explicit_path.exists():
                return str(explicit_path)
            else:
                self.logger.warning(f"Explicit ImageMagick path not found: {explicit_path}")

        # Auto-detect ImageMagick
        possible_paths = [
            r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe",
            r"C:\Program Files\ImageMagick\magick.exe",
            r"C:\Program Files\Autodesk\Maya2023\bin\magick.exe",
            r"C:\Program Files\Autodesk\Maya2024\bin\magick.exe",
            r"C:\Program Files\Autodesk\Maya2025\bin\magick.exe",
            r"C:\Program Files\Autodesk\Maya2026\bin\magick.exe",
            "magick",  # Try PATH
            "magick.exe",  # Try PATH with extension
        ]

        for path in possible_paths:
            try:
                if path in ["magick", "magick.exe"]:
                    # Test PATH command (hide console window on Windows)
                    kwargs = {"capture_output": True, "timeout": 5}
                    if os.name == "nt":  # Windows
                        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
                    result = subprocess.run([path, "--version"], **kwargs)
                    if result.returncode == 0:
                        self.logger.info(f"Found ImageMagick in PATH: {path}")
                        return path
                else:
                    # Test explicit path
                    if Path(path).exists():
                        self.logger.info(f"Found ImageMagick at: {path}")
                        return path
            except Exception:
                continue

        self.logger.warning("ImageMagick not found. Texture processing will be disabled.")
        return None

    def extract_and_process_textures(
        self,
        zip_path: Path,
        output_directory: Path,
        asset_info: AssetInfo,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> TextureProcessingResult:
        """
        Extract textures from zip and process them

        Args:
            zip_path: Path to source zip file
            output_directory: Directory to store processed textures
            asset_info: Asset information
            progress_callback: Optional progress callback function

        Returns:
            TextureProcessingResult with processed texture paths
        """
        result = TextureProcessingResult(success=False)
        temp_dir = None

        try:
            # Update progress
            if progress_callback:
                progress_callback("Extracting asset archive...", 10)

            # Create temporary extraction directory
            temp_dir = Path(tempfile.mkdtemp(prefix="tunnelui_extract_"))
            result.temp_directory = temp_dir

            # Extract zip file
            self._extract_zip_file(zip_path, temp_dir)

            if progress_callback:
                progress_callback("Analyzing asset structure...", 20)

            # Identify asset type
            asset_type = self._identify_asset_type(temp_dir)
            result.asset_type = asset_type
            asset_info.asset_type = asset_type

            if progress_callback:
                progress_callback("Finding texture files...", 30)

            # Find texture files and metadata
            texture_files = self._find_texture_files(temp_dir, asset_type)
            geometry_files = self._find_geometry_files(temp_dir, asset_type)
            metadata = self._extract_metadata(temp_dir)

            result.geometry_files = geometry_files
            result.metadata = metadata

            if progress_callback:
                progress_callback("Processing textures...", 40)

            # Process textures if enabled
            if self.config.process_textures and self.imagemagick_path:
                processed_textures = self._process_texture_files(
                    texture_files, output_directory, asset_info, progress_callback
                )
                result.processed_textures = processed_textures
            else:
                # Copy original textures if processing disabled
                result.processed_textures = self._copy_texture_files(
                    texture_files, output_directory, asset_info
                )

            if progress_callback:
                progress_callback("Copying geometry files...", 90)

            # Copy geometry files to output directory
            copied_geometry = self._copy_geometry_files(geometry_files, output_directory)
            result.geometry_files = copied_geometry

            result.success = True

            if progress_callback:
                progress_callback("Texture processing complete", 100)

        except Exception as e:
            result.error_details = str(e)
            result.success = False
            self.logger.error(f"Texture processing failed: {e}")

        finally:
            # Cleanup temporary directory
            if temp_dir and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    self.logger.warning(f"Failed to cleanup temp directory: {e}")

        return result

    def _extract_zip_file(self, zip_path: Path, extract_to: Path) -> None:
        """Extract zip file to specified directory"""
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_file:
                zip_file.extractall(extract_to)
            self.logger.debug(f"Extracted {zip_path} to {extract_to}")
        except Exception as e:
            raise AssetExtractionError(f"Failed to extract zip file: {e}")

    def _identify_asset_type(self, extracted_path: Path) -> str:
        """
        Determine if asset is 'Standard' or 'Plant' type
        Based on convertMegascansAssets.py logic

        Args:
            extracted_path: Path to extracted asset files

        Returns:
            "Standard" or "Plant"
        """
        try:
            # Look for plant-specific directory structure
            # Plants typically have deeper nesting: asset/variation/lod/files
            for item in extracted_path.rglob("*"):
                if item.is_dir():
                    # Check for typical plant structure patterns
                    if any(
                        pattern in str(item).lower() for pattern in ["variation", "var_", "lod"]
                    ):
                        return "Plant"

                    # Check for plant-specific naming patterns
                    if any(
                        pattern in item.name.lower()
                        for pattern in ["plant", "tree", "grass", "flower"]
                    ):
                        return "Plant"

            # Default to Standard for most assets
            return "Standard"

        except Exception as e:
            self.logger.warning(f"Failed to identify asset type: {e}")
            return "Standard"

    def _find_texture_files(self, base_path: Path, asset_type: str) -> Dict[str, Path]:
        """
        Find texture files in extracted directory

        Args:
            base_path: Base extraction path
            asset_type: "Standard" or "Plant"

        Returns:
            Dictionary mapping parameter names to texture file paths
        """
        texture_files = {}

        try:
            # Search patterns based on parameter mapping
            for param_name, param_info in self.parameter_mapping.items():
                suffix = param_info["suffix"]

                # Search for files with this suffix
                for texture_file in base_path.rglob("*"):
                    if texture_file.is_file() and texture_file.suffix.lower() in [
                        ".jpg",
                        ".png",
                        ".exr",
                        ".tiff",
                    ]:
                        if suffix.lower() in texture_file.name.lower():
                            texture_files[param_name] = texture_file
                            break

            self.logger.debug(f"Found {len(texture_files)} texture files")
            return texture_files

        except Exception as e:
            self.logger.error(f"Failed to find texture files: {e}")
            return {}

    def _find_geometry_files(self, base_path: Path, asset_type: str) -> List[Path]:
        """Find geometry files in extracted directory (prioritize LOD0 only)"""
        geometry_files = []

        try:
            geometry_extensions = [".fbx", ".obj", ".ma", ".mb", ".abc", ".usd", ".usda", ".usdz"]

            # Find all geometry files first
            all_geometry_files = []
            for geo_file in base_path.rglob("*"):
                if geo_file.is_file() and geo_file.suffix.lower() in geometry_extensions:
                    all_geometry_files.append(geo_file)

            # Prioritize LOD0 files only
            lod0_files = []
            for geo_file in all_geometry_files:
                # Check if this is a LOD0 file (contains "LOD0" in filename)
                if "LOD0" in geo_file.name:
                    lod0_files.append(geo_file)

            if lod0_files:
                # Use LOD0 files if available
                geometry_files = lod0_files
                self.logger.info(f"Using LOD0 files: {[f.name for f in lod0_files]}")
            elif all_geometry_files:
                # Fallback: use first geometry file if no LOD0 found
                geometry_files = [all_geometry_files[0]]
                self.logger.info(
                    f"No LOD0 found, using first geometry file: {all_geometry_files[0].name}"
                )
            else:
                self.logger.warning("No geometry files found")

            self.logger.debug(f"Selected {len(geometry_files)} geometry files for import")
            return geometry_files

        except Exception as e:
            self.logger.error(f"Failed to find geometry files: {e}")
            return []

    def _extract_metadata(self, base_path: Path) -> Dict[str, Any]:
        """Extract metadata from JSON files"""
        metadata = {}

        try:
            for json_file in base_path.rglob("*.json"):
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        file_metadata = json.load(f)
                        metadata[json_file.name] = file_metadata
                except Exception as e:
                    self.logger.warning(f"Failed to read JSON file {json_file}: {e}")

            return metadata

        except Exception as e:
            self.logger.error(f"Failed to extract metadata: {e}")
            return {}

    def _process_texture_files(
        self,
        texture_files: Dict[str, Path],
        output_directory: Path,
        asset_info: AssetInfo,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> Dict[str, Path]:
        """Process texture files with ImageMagick"""
        processed_textures = {}

        if not self.imagemagick_path:
            raise TextureProcessingError("ImageMagick not available for texture processing")

        try:
            output_directory.mkdir(parents=True, exist_ok=True)

            # Filter texture files based on enabled texture types in settings
            filtered_texture_files = {}
            if hasattr(self.config, "enabled_texture_types"):
                enabled_types = self.config.enabled_texture_types
                for param_name, source_path in texture_files.items():
                    if enabled_types.get(param_name, True):  # Default to True if not specified
                        filtered_texture_files[param_name] = source_path
                    else:
                        self.logger.info(f"Skipping {param_name} texture (disabled in settings)")
            else:
                # If no settings available, process all textures
                filtered_texture_files = texture_files

            total_textures = len(filtered_texture_files)
            for i, (param_name, source_path) in enumerate(filtered_texture_files.items()):

                if progress_callback:
                    progress = 40 + (i / total_textures) * 40  # 40-80% of total progress
                    progress_callback(f"Processing {param_name} texture...", progress)

                # Generate standardized output filename
                if self.config.standardize_naming:
                    param_title = param_name.capitalize()
                    if param_name == "ao":
                        param_title = "AO"
                    output_filename = f"T_M_{asset_info.asset_name}_{param_title}.1001.{self.config.texture_format}"
                else:
                    output_filename = f"{source_path.stem}_processed.{self.config.texture_format}"

                output_path = output_directory / output_filename

                # Process with ImageMagick
                success = self._process_texture_file(source_path, output_path, param_name)

                if success:
                    processed_textures[param_name] = output_path
                else:
                    # Fall back to copying original
                    fallback_path = (
                        output_directory / f"{source_path.stem}_original{source_path.suffix}"
                    )
                    shutil.copy2(source_path, fallback_path)
                    processed_textures[param_name] = fallback_path
                    self.logger.warning(f"Used original texture for {param_name}")

            return processed_textures

        except Exception as e:
            raise TextureProcessingError(f"Failed to process textures: {e}")

    def _process_texture_file(
        self, source_path: Path, target_path: Path, texture_type: str
    ) -> bool:
        """
        Process individual texture file with ImageMagick

        Args:
            source_path: Source texture file
            target_path: Target processed file
            texture_type: Type of texture (diffuse, normal, etc.)

        Returns:
            True if successful
        """
        try:
            # Build ImageMagick command
            cmd = [
                self.imagemagick_path,
                str(source_path),
                "-format",
                self.config.texture_format.upper(),
            ]

            # Add resolution scaling if needed
            if self.config.texture_resolution != "original":
                resolution_map = {"1K": "1024x1024", "2K": "2048x2048", "4K": "4096x4096"}
                if self.config.texture_resolution in resolution_map:
                    cmd.extend(["-resize", resolution_map[self.config.texture_resolution]])

            # Add format-specific options
            if self.config.texture_format.lower() == "png":
                cmd.extend(["-quality", "95"])
            elif self.config.texture_format.lower() in ["jpg", "jpeg"]:
                cmd.extend(["-quality", "90"])

            cmd.append(str(target_path))

            # Execute ImageMagick (hide console window on Windows)
            kwargs = {"capture_output": True, "text": True, "timeout": 60}
            if os.name == "nt":  # Windows
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            result = subprocess.run(cmd, **kwargs)

            if result.returncode == 0:
                self.logger.debug(f"Processed texture: {source_path} -> {target_path}")
                return True
            else:
                self.logger.error(f"ImageMagick failed for {source_path}: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error(f"ImageMagick timeout for {source_path}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to process texture {source_path}: {e}")
            return False

    def _copy_texture_files(
        self, texture_files: Dict[str, Path], output_directory: Path, asset_info: AssetInfo
    ) -> Dict[str, Path]:
        """Copy texture files without processing"""
        copied_textures = {}

        try:
            output_directory.mkdir(parents=True, exist_ok=True)

            for param_name, source_path in texture_files.items():
                # Generate output filename
                if self.config.standardize_naming:
                    param_title = param_name.capitalize()
                    if param_name == "ao":
                        param_title = "AO"
                    output_filename = (
                        f"T_M_{asset_info.asset_name}_{param_title}{source_path.suffix}"
                    )
                else:
                    output_filename = source_path.name

                output_path = output_directory / output_filename
                shutil.copy2(source_path, output_path)
                copied_textures[param_name] = output_path

            return copied_textures

        except Exception as e:
            self.logger.error(f"Failed to copy texture files: {e}")
            return {}

    def _copy_geometry_files(
        self, geometry_files: List[Path], output_directory: Path
    ) -> List[Path]:
        """Copy geometry files to output directory"""
        copied_files = []

        try:
            geometry_dir = output_directory / "geometry"
            geometry_dir.mkdir(parents=True, exist_ok=True)

            for source_file in geometry_files:
                target_file = geometry_dir / source_file.name
                shutil.copy2(source_file, target_file)
                copied_files.append(target_file)

            return copied_files

        except Exception as e:
            self.logger.error(f"Failed to copy geometry files: {e}")
            return []
