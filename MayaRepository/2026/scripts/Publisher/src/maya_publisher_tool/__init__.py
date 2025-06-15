"""
Maya Asset Publishing Tool

A comprehensive tool for publishing Maya assets and shots with version control,
validation, and metadata management.
"""

__version__ = "1.0.0"
__author__ = "SagaTools"

from .core.models import PublishRecord, EnvironmentContext
from .database.publish_database import PublishDatabase
from .file_system.network_publisher import NetworkDrivePublisher
from .validation.validation_manager import ValidationManager
from .maya_integration.scene_handler import MayaSceneHandler

__all__ = [
    "PublishRecord",
    "EnvironmentContext",
    "PublishDatabase",
    "NetworkDrivePublisher",
    "ValidationManager",
    "MayaSceneHandler",
]
