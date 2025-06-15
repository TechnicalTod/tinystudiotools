import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ShowConfig:
    """Configuration for a specific show"""

    show_name: str
    asset_tasks: List[str]
    shot_tasks: List[str]
    validation_rules: Dict[str, bool]
    naming_convention: Dict[str, str]
    network_path: str = "S:/"

    @classmethod
    def from_json(cls, json_path: Path) -> "ShowConfig":
        """Load configuration from JSON file"""
        with open(json_path, "r") as f:
            data = json.load(f)

        return cls(
            show_name=data.get("show_name", ""),
            asset_tasks=data.get("asset_tasks", []),
            shot_tasks=data.get("shot_tasks", []),
            validation_rules=data.get("validation_rules", {}),
            naming_convention=data.get("naming_convention", {}),
            network_path=data.get("network_path", "S:/"),
        )

    def to_json(self, json_path: Path):
        """Save configuration to JSON file"""
        data = {
            "show_name": self.show_name,
            "asset_tasks": self.asset_tasks,
            "shot_tasks": self.shot_tasks,
            "validation_rules": self.validation_rules,
            "naming_convention": self.naming_convention,
            "network_path": self.network_path,
        }

        json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)


class ConfigurationManager:
    """Manages show configurations"""

    def __init__(self, config_dir: str):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def get_show_config(self, show_name: str) -> Optional[ShowConfig]:
        """Load configuration for a specific show"""
        config_file = self.config_dir / f"{show_name}.json"

        if config_file.exists():
            return ShowConfig.from_json(config_file)
        else:
            # Create default configuration
            return self.create_default_config(show_name)

    def create_default_config(self, show_name: str) -> ShowConfig:
        """Create default configuration for a new show"""
        config = ShowConfig(
            show_name=show_name,
            asset_tasks=["model", "texture", "shading", "rig"],
            shot_tasks=["previs", "layout", "anim", "lighting"],
            validation_rules={
                "naming_convention": True,
                "scene_cleanup": True,
                "file_paths": True,
                "geometry": False,
                "required_comments": False,
            },
            naming_convention={
                "asset_prefix": "AST_",
                "shot_prefix": "SHT_",
                "version_format": "v{version:03d}",
                "separator": "_",
            },
        )

        # Save default configuration
        config_file = self.config_dir / f"{show_name}.json"
        config.to_json(config_file)

        return config

    def save_show_config(self, config: ShowConfig):
        """Save show configuration"""
        config_file = self.config_dir / f"{config.show_name}.json"
        config.to_json(config_file)

    def list_shows(self) -> List[str]:
        """List all configured shows"""
        config_files = self.config_dir.glob("*.json")
        return [f.stem for f in config_files]

    def delete_show_config(self, show_name: str) -> bool:
        """Delete show configuration"""
        config_file = self.config_dir / f"{show_name}.json"
        if config_file.exists():
            config_file.unlink()
            return True
        return False

    def get_global_config_path(self) -> Path:
        """Get path to global configuration file"""
        return self.config_dir / "global_config.json"

    def get_global_config(self) -> Dict:
        """Get global configuration settings"""
        global_config_path = self.get_global_config_path()

        if global_config_path.exists():
            with open(global_config_path, "r") as f:
                return json.load(f)
        else:
            # Return default global config
            default_config = {
                "database_path": str(self.config_dir.parent / "database" / "publishes.db"),
                "default_network_path": "S:/",
                "ui_settings": {"theme": "dark", "window_size": [800, 600]},
                "logging": {
                    "level": "INFO",
                    "file_path": str(self.config_dir.parent / "logs" / "publisher.log"),
                },
            }

            # Save default config
            self.save_global_config(default_config)
            return default_config

    def save_global_config(self, config: Dict):
        """Save global configuration settings"""
        global_config_path = self.get_global_config_path()
        global_config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(global_config_path, "w") as f:
            json.dump(config, f, indent=2)
