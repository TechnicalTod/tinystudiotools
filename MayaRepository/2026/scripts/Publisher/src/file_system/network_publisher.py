import os
import shutil
from pathlib import Path
from typing import Tuple
from ..core.models import PublishRecord


class NetworkDrivePublisher:
    """Handles file operations for network drive publishing"""

    def __init__(self, base_path: str = "S:/"):
        self.base_path = Path(base_path)

    def generate_publish_path(self, record: PublishRecord) -> Path:
        """Generate the full network path for a publish"""
        path = self.base_path / record.show_name

        if record.asset_type == "asset":
            path = path / "assets"
        elif record.asset_type == "shot":
            path = path / "shots"

        path = path / record.asset_id / record.task / f"v{record.version:03d}"

        # Generate filename
        filename = f"{record.asset_id}_{record.task}_v{record.version:03d}.ma"
        return path / filename

    def ensure_directory(self, file_path: Path) -> bool:
        """Ensure the directory structure exists"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"Failed to create directory {file_path.parent}: {e}")
            return False

    def publish_file(self, source_path: str, target_path: Path) -> Tuple[bool, str]:
        """Copy/save Maya file to network location"""
        try:
            # Ensure target directory exists
            if not self.ensure_directory(target_path):
                return False, f"Failed to create directory: {target_path.parent}"

            # Try to import Maya commands
            try:
                import maya.cmds as cmds

                # Save Maya file to target location
                cmds.file(rename=str(target_path))
                cmds.file(save=True, type="mayaAscii")

                # Verify file was created
                if target_path.exists():
                    return True, f"Successfully published to: {target_path}"
                else:
                    return False, "File was not created at target location"

            except ImportError:
                # Maya not available, try copying the file if source exists
                if source_path and Path(source_path).exists():
                    shutil.copy2(source_path, target_path)
                    return True, f"Successfully copied to: {target_path}"
                else:
                    return False, "Maya not available and no source file provided"

        except Exception as e:
            return False, f"Publish failed: {str(e)}"

    def get_file_size(self, file_path: Path) -> int:
        """Get file size in bytes"""
        try:
            return file_path.stat().st_size
        except:
            return 0

    def validate_network_access(self) -> Tuple[bool, str]:
        """Check if network drive is accessible"""
        try:
            if not self.base_path.exists():
                return False, f"Network path not accessible: {self.base_path}"

            # Try to create a test file
            test_file = self.base_path / ".maya_publish_test"
            test_file.touch()
            test_file.unlink()

            return True, "Network access verified"
        except Exception as e:
            return False, f"Network access failed: {str(e)}"

    def list_published_files(self, record: PublishRecord) -> list:
        """List all published files for an asset/task"""
        try:
            base_path = self.base_path / record.show_name

            if record.asset_type == "asset":
                base_path = base_path / "assets"
            elif record.asset_type == "shot":
                base_path = base_path / "shots"

            asset_path = base_path / record.asset_id / record.task

            if not asset_path.exists():
                return []

            # Find all version directories
            version_dirs = [
                d for d in asset_path.iterdir() if d.is_dir() and d.name.startswith("v")
            ]
            version_dirs.sort()

            files = []
            for version_dir in version_dirs:
                for file_path in version_dir.glob("*.ma"):
                    files.append(
                        {
                            "path": str(file_path),
                            "version": version_dir.name,
                            "size": self.get_file_size(file_path),
                            "modified": file_path.stat().st_mtime,
                        }
                    )

            return files

        except Exception as e:
            print(f"Error listing published files: {e}")
            return []
