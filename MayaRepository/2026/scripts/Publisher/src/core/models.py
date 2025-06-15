import sqlite3
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass
import os


@dataclass
class PublishRecord:
    """Model for storing publish metadata"""

    id: Optional[int] = None
    show_name: str = ""
    asset_type: str = ""  # "asset" or "shot"
    asset_id: str = ""
    task: str = ""
    version: int = 1
    file_path: str = ""
    file_size: int = 0
    artist: str = ""
    comments: str = ""
    published_at: Optional[datetime] = None
    maya_version: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage"""
        return {
            "id": self.id,
            "show_name": self.show_name,
            "asset_type": self.asset_type,
            "asset_id": self.asset_id,
            "task": self.task,
            "version": self.version,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "artist": self.artist,
            "comments": self.comments,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "maya_version": self.maya_version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PublishRecord":
        """Create instance from database dictionary"""
        published_at = None
        if data.get("published_at"):
            published_at = datetime.fromisoformat(data["published_at"])

        return cls(
            id=data.get("id"),
            show_name=data.get("show_name", ""),
            asset_type=data.get("asset_type", ""),
            asset_id=data.get("asset_id", ""),
            task=data.get("task", ""),
            version=data.get("version", 1),
            file_path=data.get("file_path", ""),
            file_size=data.get("file_size", 0),
            artist=data.get("artist", ""),
            comments=data.get("comments", ""),
            published_at=published_at,
            maya_version=data.get("maya_version", ""),
        )


@dataclass
class EnvironmentContext:
    """Model for Maya environment context"""

    show_name: str = ""
    current_scene: str = ""
    detected_asset_id: str = ""
    detected_asset_type: str = ""  # "asset" or "shot"
    detected_task: str = ""
    user_name: str = ""
    maya_version: str = ""
    scene_modified: bool = False

    @classmethod
    def from_maya_environment(cls) -> "EnvironmentContext":
        """Extract context from current Maya environment"""
        try:
            import maya.cmds as cmds
        except ImportError:
            # Return basic context if Maya is not available
            return cls(
                user_name=os.environ.get("USER", os.environ.get("USERNAME", "")),
                show_name=os.environ.get("SHOW_NAME", ""),
            )

        context = cls()
        context.show_name = os.environ.get("SHOW_NAME", "")
        context.current_scene = cmds.file(query=True, sceneName=True)
        context.user_name = os.environ.get("USER", os.environ.get("USERNAME", ""))
        context.maya_version = cmds.about(version=True)
        context.scene_modified = cmds.file(query=True, modified=True)

        # Auto-detect asset/shot from scene name or path
        if context.current_scene:
            context._parse_scene_context()

        return context

    def _parse_scene_context(self):
        """Parse asset/shot context from scene path"""
        import os

        scene_name = os.path.basename(self.current_scene)
        scene_dir = os.path.dirname(self.current_scene)

        # Simple parsing logic - can be enhanced
        if "/assets/" in scene_dir or "\\assets\\" in scene_dir:
            self.detected_asset_type = "asset"
        elif "/shots/" in scene_dir or "\\shots\\" in scene_dir:
            self.detected_asset_type = "shot"

        # Extract asset/shot ID from path or filename
        # This would need to be customized based on naming conventions
        path_parts = scene_dir.replace("\\", "/").split("/")

        # Try to find asset/shot ID in path
        for i, part in enumerate(path_parts):
            if part in ["assets", "shots"] and i + 1 < len(path_parts):
                self.detected_asset_id = path_parts[i + 1]
                break

        # Try to extract task from parent directory
        if self.detected_asset_id:
            for i, part in enumerate(path_parts):
                if part == self.detected_asset_id and i + 1 < len(path_parts):
                    self.detected_task = path_parts[i + 1]
                    break
