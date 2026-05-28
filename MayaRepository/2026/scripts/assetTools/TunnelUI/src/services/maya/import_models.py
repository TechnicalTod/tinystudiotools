"""
Data models and exceptions for Maya import operations
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum


# ============================================================================
# Exception Hierarchy
# ============================================================================


class TunnelUIImportError(Exception):
    """Base exception for import operations"""

    pass


class MayaEnvironmentError(TunnelUIImportError):
    """Maya not available or not properly configured"""

    pass


class TextureProcessingError(TunnelUIImportError):
    """Failed to process textures"""

    pass


class CacheError(TunnelUIImportError):
    """Cache operation failed"""

    pass


class AssetExtractionError(TunnelUIImportError):
    """Failed to extract asset from zip"""

    pass


# ============================================================================
# Data Models
# ============================================================================


@dataclass
class ImportResult:
    """Result of a complete import operation"""

    success: bool
    asset_id: str
    imported_objects: List[str] = field(default_factory=list)
    created_materials: List[str] = field(default_factory=list)
    cache_entry: Optional["CacheEntry"] = None
    error_message: Optional[str] = None
    import_duration: float = 0.0
    processing_steps: List[str] = field(default_factory=list)


@dataclass
class CacheEntry:
    """Cache entry for a processed asset"""

    asset_id: str
    asset_name: str
    cache_directory: Path
    processed_files: Dict[str, Path] = field(default_factory=dict)  # texture_type -> file_path
    geometry_files: List[Path] = field(default_factory=list)
    metadata_file: Optional[Path] = None
    creation_time: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    file_size_mb: float = 0.0
    asset_type: str = "Standard"  # "Standard" or "Plant"

    def update_access_time(self):
        """Update last accessed timestamp"""
        self.last_accessed = datetime.now()


@dataclass
class TextureProcessingResult:
    """Result of texture processing operation"""

    success: bool
    processed_textures: Dict[str, Path] = field(
        default_factory=dict
    )  # parameter_name -> processed_file_path
    geometry_files: List[Path] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0
    error_details: Optional[str] = None
    temp_directory: Optional[Path] = None
    asset_type: str = "Standard"


@dataclass
class AssetInfo:
    """Enhanced asset information for import"""

    asset_id: str
    asset_name: str
    asset_type: str = "Standard"  # "Standard" or "Plant"
    category: str = ""
    zip_path: Optional[Path] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    estimated_size_mb: float = 0.0

    @property
    def display_name(self) -> str:
        """Get display-friendly asset name"""
        return self.asset_name.replace("_", " ").title()


@dataclass
class CacheStatistics:
    """Cache usage statistics"""

    cache_location: Path
    entry_count: int = 0
    total_size_mb: float = 0.0
    oldest_entry: Optional[datetime] = None
    newest_entry: Optional[datetime] = None
    hit_rate: float = 0.0  # Cache hit percentage

    @property
    def size_gb(self) -> float:
        """Get size in GB"""
        return self.total_size_mb / 1024.0


@dataclass
class ValidationResult:
    """Result of cache validation operation"""

    valid: bool
    total_entries: int = 0
    valid_entries: int = 0
    corrupted_entries: List[str] = field(default_factory=list)
    missing_files: List[str] = field(default_factory=list)
    repaired_entries: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class ImportPreview:
    """Preview of what will be imported"""

    asset_info: AssetInfo
    will_use_cache: bool
    estimated_import_time: float
    textures_to_process: List[str] = field(default_factory=list)
    geometry_files: List[str] = field(default_factory=list)
    material_name: str = ""
    group_name: str = ""
    warnings: List[str] = field(default_factory=list)


@dataclass
class ImportRecord:
    """Record of an import operation for history tracking"""

    timestamp: datetime
    asset_id: str
    asset_name: str
    success: bool
    import_duration: float
    cache_used: bool
    error_message: Optional[str] = None
    maya_objects_created: int = 0
    materials_created: int = 0


@dataclass
class ImportStatistics:
    """Overall import usage statistics"""

    total_imports: int = 0
    successful_imports: int = 0
    failed_imports: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    average_import_time: float = 0.0
    most_imported_assets: List[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_imports == 0:
            return 0.0
        return (self.successful_imports / self.total_imports) * 100.0

    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate percentage"""
        total_cache_operations = self.cache_hits + self.cache_misses
        if total_cache_operations == 0:
            return 0.0
        return (self.cache_hits / total_cache_operations) * 100.0


# ============================================================================
# Configuration Models
# ============================================================================


@dataclass
class ImportCacheConfig:
    """Import cache management configuration"""

    cache_root: Path
    max_cache_size_gb: float = 10.0
    cleanup_strategy: str = "lru"  # lru, age, manual
    compression_enabled: bool = False
    cache_index_file: str = "import_cache_index.json"
    auto_cleanup_enabled: bool = True
    cleanup_threshold_gb: float = 8.0  # Start cleanup when cache exceeds this

    def __post_init__(self):
        """Ensure cache_root is a Path object"""
        if isinstance(self.cache_root, str):
            self.cache_root = Path(self.cache_root)


# ============================================================================
# Enums
# ============================================================================


class ImportStep(Enum):
    """Enumeration of import process steps"""

    VALIDATION = "validation"
    CACHE_CHECK = "cache_check"
    ZIP_EXTRACTION = "zip_extraction"
    TEXTURE_PROCESSING = "texture_processing"
    CACHE_STORAGE = "cache_storage"
    MAYA_IMPORT = "maya_import"
    MATERIAL_CREATION = "material_creation"
    CLEANUP = "cleanup"


class AssetType(Enum):
    """Asset type enumeration"""

    STANDARD = "Standard"
    PLANT = "Plant"
    UNKNOWN = "Unknown"


class ProcessingStatus(Enum):
    """Processing status enumeration"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
