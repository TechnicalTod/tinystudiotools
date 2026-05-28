"""
Configuration manager for TunnelUI Asset Browser.
Enhanced with multi-DCC application support.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from configuration.config_models import AssetLibraryConfig, AppEnvironment, DCCApplication


class ConfigurationManager:
    """Manages loading, saving, and validation of TunnelUI configuration with multi-DCC support."""

    def __init__(self, config_path: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)

        # Determine config path
        if config_path is None:
            # Default to config/tunnel_config.json relative to this script
            config_path = Path(__file__).parent.parent.parent / "config" / "tunnel_config.json"

        self.config_path = Path(config_path)
        self._config: Optional[AssetLibraryConfig] = None

    def load_config(self) -> AssetLibraryConfig:
        """
        Load configuration from JSON file.

        Returns:
            AssetLibraryConfig: Loaded configuration object
        """
        if self._config is not None:
            return self._config

        try:
            # Load the raw configuration
            config_dict = self._load_config_dict()

            # Migrate legacy configuration format if needed
            config_dict = self._migrate_config_format(config_dict)

            # Convert nested dicts to dataclasses
            config_dict = self._convert_nested_dataclasses(config_dict)

            # Create configuration object from the dictionary
            self._config = AssetLibraryConfig(**config_dict)

            self.logger.info(f"Configuration loaded from {self.config_path}")
            return self._config

        except FileNotFoundError:
            self.logger.info("Configuration file not found, using defaults")
            self._config = AssetLibraryConfig()
            return self._config
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            self._config = AssetLibraryConfig()
            return self._config

    def _load_config_dict(self) -> Dict[str, Any]:
        """
        Load configuration from JSON file and return as a dictionary.
        """
        with open(self.config_path, "r", encoding="utf-8") as f:
            config_dict = json.load(f)
        return config_dict

    def _migrate_config_format(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrate older configuration formats to new multi-DCC format.

        Args:
            config_dict: Raw configuration dictionary from JSON

        Returns:
            Dict with migrated configuration format
        """
        # Handle application-specific settings migration
        if "maya_settings" in config_dict and isinstance(config_dict["maya_settings"], dict):
            # Maya settings are properly nested, keep as-is
            pass
        elif any(key.startswith("maya_") for key in config_dict.keys()):
            # Migrate old flat maya settings to nested structure
            maya_settings = {}
            keys_to_remove = []

            for key, value in config_dict.items():
                if key.startswith("maya_import_"):
                    new_key = key.replace("maya_import_", "")
                    maya_settings[new_key] = value
                    keys_to_remove.append(key)

            if maya_settings:
                config_dict["maya_settings"] = maya_settings
                for key in keys_to_remove:
                    del config_dict[key]

                self.logger.info("Migrated legacy Maya settings to new format")

        # Handle application override migration
        if "application_override" not in config_dict and "target_application" in config_dict:
            target_app = config_dict.get("target_application", "auto")
            if target_app != "auto":
                config_dict["application_override"] = target_app

        return config_dict

    def _convert_nested_dataclasses(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Convert nested dictionaries to dataclasses"""
        from configuration.config_models import (
            MayaImportSettings,
            UnrealImportSettings,
            StandaloneSettings,
        )

        # Convert maya_settings dict to MayaImportSettings dataclass
        if "maya_settings" in config_dict and isinstance(config_dict["maya_settings"], dict):
            try:
                maya_settings_dict = config_dict["maya_settings"]
                config_dict["maya_settings"] = MayaImportSettings(**maya_settings_dict)
                self.logger.debug("Converted maya_settings dict to MayaImportSettings dataclass")
            except Exception as e:
                self.logger.warning(f"Failed to convert maya_settings: {e}, using defaults")
                config_dict["maya_settings"] = MayaImportSettings()

        # Convert unreal_settings dict to UnrealImportSettings dataclass
        if "unreal_settings" in config_dict and isinstance(config_dict["unreal_settings"], dict):
            try:
                unreal_settings_dict = config_dict["unreal_settings"]
                config_dict["unreal_settings"] = UnrealImportSettings(**unreal_settings_dict)
                self.logger.debug(
                    "Converted unreal_settings dict to UnrealImportSettings dataclass"
                )
            except Exception as e:
                self.logger.warning(f"Failed to convert unreal_settings: {e}, using defaults")
                config_dict["unreal_settings"] = UnrealImportSettings()

        # Convert standalone_settings dict to StandaloneSettings dataclass
        if "standalone_settings" in config_dict and isinstance(
            config_dict["standalone_settings"], dict
        ):
            try:
                standalone_settings_dict = config_dict["standalone_settings"]
                config_dict["standalone_settings"] = StandaloneSettings(**standalone_settings_dict)
                self.logger.debug(
                    "Converted standalone_settings dict to StandaloneSettings dataclass"
                )
            except Exception as e:
                self.logger.warning(f"Failed to convert standalone_settings: {e}, using defaults")
                config_dict["standalone_settings"] = StandaloneSettings()

        return config_dict

    def save_config(self, config: Optional[AssetLibraryConfig] = None) -> bool:
        """
        Save configuration to JSON file.

        Args:
            config: Configuration to save (uses current if None)

        Returns:
            bool: True if saved successfully
        """
        if config is not None:
            self._config = config

        if self._config is None:
            self.logger.error("No configuration to save")
            return False

        try:
            # Ensure config directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert to dict and save
            config_dict = self._serialize_config(self._config)

            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Configuration saved to {self.config_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False

    def _serialize_config(self, config: AssetLibraryConfig) -> Dict[str, Any]:
        """
        Serialize configuration to JSON-compatible dictionary.

        Args:
            config: Configuration object to serialize

        Returns:
            Dict suitable for JSON serialization
        """
        config_dict = {}

        # Handle basic fields
        for field_name, field_value in config.__dict__.items():
            if isinstance(field_value, Path):
                config_dict[field_name] = str(field_value)
            elif hasattr(field_value, "__dict__"):
                # Handle nested dataclass objects (like maya_settings)
                config_dict[field_name] = field_value.__dict__.copy()
            else:
                config_dict[field_name] = field_value

        return config_dict

    def validate_config(self) -> Dict[str, bool]:
        """
        Validate current configuration.

        Returns:
            Dict[str, bool]: Validation results
        """
        if self._config is None:
            self.load_config()

        results = {}

        # Validate paths
        metadata_path = Path(self._config.metadata_path)
        assets_path = Path(self._config.assets_path)

        results["metadata_path_exists"] = metadata_path.exists()
        results["assets_path_exists"] = assets_path.exists()

        # Validate required files
        if results["metadata_path_exists"]:
            index_file = metadata_path / "inverted_index_combined.json"
            results["index_file_exists"] = index_file.exists()
        else:
            results["index_file_exists"] = False

        # Validate stylesheet if specified
        if self._config.stylesheet_path:
            stylesheet_path = Path(self._config.stylesheet_path)
            results["stylesheet_exists"] = stylesheet_path.exists()
        else:
            results["stylesheet_exists"] = True  # Not required

        # Validate application settings
        results["application_settings_valid"] = self._validate_application_settings()

        return results

    def _validate_application_settings(self) -> bool:
        """Validate application-specific settings"""
        try:
            # Validate target application setting
            if self._config.target_application not in [
                "auto",
                "maya",
                "unreal",
                "blender",
                "standalone",
            ]:
                return False

            # Validate application override if set
            if self._config.application_override:
                if self._config.application_override not in [
                    "maya",
                    "unreal",
                    "blender",
                    "standalone",
                ]:
                    return False

            return True
        except Exception as e:
            self.logger.error(f"Application settings validation failed: {e}")
            return False

    def apply_environment_settings(self, environment: AppEnvironment):
        """
        Apply environment-specific settings to configuration.

        Args:
            environment: Environment information with multi-DCC detection
        """
        if self._config is None:
            self.load_config()

        # Detect all available applications
        available_apps = environment.detect_all_applications()

        # Apply settings based on detected application
        active_app = environment.get_active_application()

        if active_app == DCCApplication.MAYA:
            self._config.maya_mode = True
            maya_stylesheet = environment.get_maya_stylesheet_path()
            if maya_stylesheet:
                self._config.stylesheet_path = maya_stylesheet
                self.logger.info(f"Applied Maya stylesheet: {maya_stylesheet}")
            self.logger.info(f"Applied Maya mode settings (version: {environment.maya_version})")

        elif active_app == DCCApplication.UNREAL:
            self._config.maya_mode = False
            # Add Unreal-specific settings here when available
            self.logger.info("Applied Unreal Engine mode settings")

        elif active_app == DCCApplication.BLENDER:
            self._config.maya_mode = False
            # Add Blender-specific settings here when available
            self.logger.info("Applied Blender mode settings")

        else:  # Standalone mode
            self._config.maya_mode = False
            # Use shared dark stylesheet for standalone mode
            fallback_stylesheet = Path(__file__).resolve().parents[5] / "shared" / "pyQtStyleSheets" / "dark.qss"
            if fallback_stylesheet.exists():
                self._config.stylesheet_path = str(fallback_stylesheet)
                self.logger.info(
                    f"Applied standalone mode settings with dark theme: {fallback_stylesheet}"
                )
            else:
                self.logger.warning("No dark stylesheet found for standalone mode")
            self.logger.info("Applied standalone mode settings")

        # Handle user override if set
        if self._config.application_override:
            try:
                override_app = DCCApplication(self._config.application_override)
                if environment.set_user_override(override_app):
                    self.logger.info(f"Applied user application override: {override_app.value}")
                else:
                    self.logger.warning(
                        f"Cannot apply override to unavailable application: {override_app.value}"
                    )
                    self._config.application_override = None
            except ValueError:
                self.logger.error(
                    f"Invalid application override: {self._config.application_override}"
                )
                self._config.application_override = None

    def get_config(self) -> AssetLibraryConfig:
        """
        Get current configuration.

        Returns:
            AssetLibraryConfig: Current configuration
        """
        if self._config is None:
            return self.load_config()
        return self._config

    def set_application_override(self, application: Optional[DCCApplication]) -> bool:
        """
        Set application override in configuration.

        Args:
            application: Application to override to, or None to clear override

        Returns:
            bool: True if successfully set
        """
        try:
            if self._config is None:
                self.load_config()

            if application is None:
                self._config.application_override = None
                self.logger.info("Cleared application override")
            else:
                self._config.application_override = application.value
                self.logger.info(f"Set application override to: {application.value}")

            return self.save_config()

        except Exception as e:
            self.logger.error(f"Failed to set application override: {e}")
            return False

    def get_application_settings(self, application: DCCApplication) -> Dict[str, Any]:
        """
        Get settings for a specific application.

        Args:
            application: Application to get settings for

        Returns:
            Dict with application-specific settings
        """
        if self._config is None:
            self.load_config()

        if application == DCCApplication.MAYA:
            return self._config.maya_settings.__dict__.copy()
        elif application == DCCApplication.UNREAL:
            return self._config.unreal_settings.__dict__.copy()
        elif application == DCCApplication.STANDALONE:
            return self._config.standalone_settings.__dict__.copy()
        else:
            return {}

    def update_application_settings(
        self, application: DCCApplication, settings: Dict[str, Any]
    ) -> bool:
        """
        Update settings for a specific application.

        Args:
            application: Application to update settings for
            settings: Dictionary of setting updates

        Returns:
            bool: True if successfully updated
        """
        try:
            if self._config is None:
                self.load_config()

            if application == DCCApplication.MAYA:
                for key, value in settings.items():
                    if hasattr(self._config.maya_settings, key):
                        setattr(self._config.maya_settings, key, value)

            elif application == DCCApplication.UNREAL:
                for key, value in settings.items():
                    if hasattr(self._config.unreal_settings, key):
                        setattr(self._config.unreal_settings, key, value)

            elif application == DCCApplication.STANDALONE:
                for key, value in settings.items():
                    if hasattr(self._config.standalone_settings, key):
                        setattr(self._config.standalone_settings, key, value)

            self.logger.info(f"Updated {application.value} settings: {settings}")
            return self.save_config()

        except Exception as e:
            self.logger.error(f"Failed to update {application.value} settings: {e}")
            return False

    def reset_to_defaults(self) -> AssetLibraryConfig:
        """
        Reset configuration to defaults.

        Returns:
            AssetLibraryConfig: Default configuration
        """
        self.logger.info("Resetting configuration to defaults")
        self._config = AssetLibraryConfig()
        return self._config
