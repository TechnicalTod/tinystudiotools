# TunnelUI Asset Browser - Implementation Plan

## Phase 1: Project Setup and Configuration System

### 1.1 Create Project Structure

Create organized directory structure for the refactored TunnelUI:

```
MayaRepository/2026/scripts/TunnelUI/
├── config/
│   └── tunnel_config.json.example
├── src/
│   ├── __init__.py
│   ├── configuration/
│   │   ├── __init__.py
│   │   ├── config_models.py
│   │   └── config_manager.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── base_repository.py
│   │   │   ├── metadata_repository.py
│   │   │   └── import_repository.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── asset_search_service.py
│   │   ├── asset_management_service.py
│   │   └── image_loading_service.py
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   ├── settings_dialog.py
│   │   ├── widgets/
│   │   │   ├── __init__.py
│   │   │   ├── asset_list_widget.py
│   │   │   ├── image_preview_dialog.py
│   │   │   └── custom_widgets.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── exceptions.py
│   │   ├── error_handler.py
│   │   └── maya_integration.py
│   └── application.py
├── tests/
│   ├── __init__.py
│   ├── test_configuration.py
│   ├── test_repositories.py
│   ├── test_services.py
│   └── test_ui.py
├── TunnelUi_refactored.py  # New main entry point
└── TunnelUi_legacy.py     # Backup of original
```

### 1.2 Implement Configuration System

1. **Create Configuration Models** (`src/configuration/config_models.py`):

   - `AssetLibraryConfig` dataclass with all settings
   - `AppEnvironment` dataclass for runtime detection
   - Default values matching current hardcoded paths

2. **Create Configuration Manager** (`src/configuration/config_manager.py`):

   - Load/save configuration from JSON
   - Environment detection (Maya vs standalone)
   - Fallback to defaults when configuration missing
   - Validation of paths and settings

3. **Create Default Configuration File** (`config/tunnel_config.json.example`):
   ```json
   {
     "metadata_path": "L:/megaScansMetadata",
     "assets_path": "M:/Zips",
     "thumbnail_size": 150,
     "grid_spacing": 10,
     "window_width": 900,
     "window_height": 800,
     "max_concurrent_loads": 10,
     "cache_size": 100,
     "debug_mode": false,
     "log_level": "INFO"
   }
   ```

### 1.3 Testing Setup

1. **Create Test Framework** (`tests/test_configuration.py`):
   - Test configuration loading/saving
   - Test environment detection
   - Test fallback behavior
   - Mock Maya environment for testing

**Estimated Time**: 2 days

## Phase 2: Data Access Layer Implementation

### 2.1 Create Repository Abstractions

1. **Base Repository** (`src/data/repositories/base_repository.py`):

   - Abstract base class for all repositories
   - Common error handling patterns
   - Logging integration

2. **Metadata Repository** (`src/data/repositories/metadata_repository.py`):

   - Abstract interface for metadata access
   - File system implementation
   - Caching mechanisms
   - JSON file loading with error handling

3. **Import Repository** (`src/data/repositories/import_repository.py`):
   - Asset zip file validation
   - Import path resolution
   - Asset existence checking

### 2.2 Migrate Existing Data Access

1. **Extract Current JSON Loading Logic**:

   - Move inverted index loading from main class
   - Move asset groupings loading
   - Move zip index loading
   - Add proper error handling and logging

2. **Implement Caching Strategy**:

   - In-memory caching of loaded JSON data
   - Cache invalidation methods
   - Performance optimization for large libraries

3. **Add Path Flexibility**:
   - Use configuration for all file paths
   - Proper path resolution across platforms
   - Graceful handling of missing files/directories

### 2.3 Testing Data Layer

Create comprehensive tests for all repository classes:

- Mock file system operations
- Test error conditions (missing files, corrupted JSON)
- Verify caching behavior
- Performance testing with large datasets

**Estimated Time**: 3 days

## Phase 3: Service Layer Implementation

### 3.1 Asset Search Service

1. **Extract Search Logic** (`src/services/asset_search_service.py`):

   - Move search functionality from UI
   - Implement caching for search results
   - Support for advanced search patterns
   - Category filtering logic

2. **Optimize Search Performance**:
   - Implement search result caching
   - Optimize string matching algorithms
   - Add search analytics/logging

### 3.2 Asset Management Service

1. **High-Level Asset Operations** (`src/services/asset_management_service.py`):

   - Combine metadata and import repositories
   - Provide unified interface for UI
   - Handle category management
   - Asset validation and preparation

2. **Image Loading Service** (`src/services/image_loading_service.py`):
   - Extract threaded image loading
   - Implement proper Qt signal/slot communication
   - Add image caching and memory management
   - Error handling for missing images

### 3.3 Service Integration Testing

- Test service interactions
- Mock repository dependencies
- Verify thread safety for image loading
- Performance testing under load

**Estimated Time**: 3 days

## Phase 4: UI Layer Refactoring

### 4.1 Create Main Window Architecture

1. **Main Window** (`src/ui/main_window.py`):

   - Extract UI setup from current monolithic class
   - Implement dependency injection for services
   - Add menu bar with File and Help menus
   - Proper window management for Maya vs standalone

2. **Settings Dialog** (`src/ui/settings_dialog.py`):
   - Configuration UI with tabs
   - Path browsing functionality
   - Validation and error handling
   - Apply/Reset functionality

### 4.2 Widget Refactoring

1. **Asset List Widget** (`src/ui/widgets/asset_list_widget.py`):

   - Extract asset list functionality
   - Maintain current delegate and model behavior
   - Add configuration-driven sizing
   - Improved error handling

2. **Image Preview Dialog** (`src/ui/widgets/image_preview_dialog.py`):

   - Extract preview dialog functionality
   - Maintain current navigation behavior
   - Add configuration for image sizing
   - Better error handling for missing images

3. **Custom Widgets** (`src/ui/widgets/custom_widgets.py`):
   - Extract StretchedTabBar
   - Extract any other custom Qt widgets
   - Make widgets configurable

### 4.3 Maya Integration

1. **Maya Compatibility Layer** (`src/utils/maya_integration.py`):
   - Abstract Maya-specific functionality
   - Graceful degradation for standalone mode
   - Stylesheet handling
   - Parent window detection

**Estimated Time**: 4 days

## Phase 5: Application Architecture and Entry Points

### 5.1 Application Factory

1. **Main Application Class** (`src/application.py`):

   - Coordinate all services and dependencies
   - Handle initialization sequence
   - Provide factory methods for different run modes
   - Centralized error handling

2. **Entry Point Refactoring** (`TunnelUi_refactored.py`):
   - Create new main entry point
   - Maintain backward compatibility with `openWindow()`
   - Add standalone execution capability
   - Proper application lifecycle management

### 5.2 Legacy Compatibility

1. **Preserve Original File** (`TunnelUi_legacy.py`):

   - Backup current implementation
   - Ensure rollback capability
   - Document differences

2. **Gradual Migration**:
   - Create feature flags for new vs old behavior
   - Allow gradual testing and validation
   - Minimize risk of breaking changes

**Estimated Time**: 2 days

## Phase 6: Testing and Quality Assurance

### 6.1 Comprehensive Testing Suite

1. **Unit Tests**:

   - Test all configuration functionality
   - Test all repository operations
   - Test all service logic
   - Mock external dependencies

2. **Integration Tests**:

   - Test UI with real services
   - Test Maya integration
   - Test standalone mode
   - Test with real asset library data

3. **Performance Tests**:
   - Compare performance with original
   - Test with large asset libraries
   - Memory usage validation
   - Thread safety verification

### 6.2 User Acceptance Testing

1. **Maya Artist Testing**:

   - Test in real Maya workflows
   - Validate all existing functionality
   - Test new configuration features
   - Gather feedback on UI improvements

2. **Standalone Testing**:
   - Test without Maya
   - Validate all features work independently
   - Test on different environments

**Estimated Time**: 3 days

## Phase 7: Documentation and Deployment

### 7.1 Code Documentation

1. **API Documentation**:

   - Document all public interfaces
   - Create usage examples
   - Document configuration options
   - Create troubleshooting guide

2. **Developer Documentation**:
   - Architecture overview
   - Extension guidelines
   - Testing procedures
   - Deployment instructions

### 7.2 User Documentation

1. **Configuration Guide**:

   - How to set up paths
   - Settings explanation
   - Troubleshooting common issues

2. **Migration Guide**:
   - What's changed for end users
   - New features overview
   - How to report issues

### 7.3 Deployment Strategy

1. **Gradual Rollout**:

   - Deploy to test environment first
   - Beta testing with select users
   - Gradual production rollout
   - Monitoring and feedback collection

2. **Rollback Plan**:
   - Keep original version available
   - Document rollback procedure
   - Monitor for issues post-deployment

**Estimated Time**: 2 days

## Implementation Timeline

| Phase | Description                   | Estimated Time | Dependencies | Status     |
| ----- | ----------------------------- | -------------- | ------------ | ---------- |
| 1     | Project Setup & Configuration | 2 days         | None         | ⏳ Pending |
| 2     | Data Access Layer             | 3 days         | Phase 1      | ⏳ Pending |
| 3     | Service Layer                 | 3 days         | Phase 2      | ⏳ Pending |
| 4     | UI Layer Refactoring          | 4 days         | Phase 3      | ⏳ Pending |
| 5     | Application Architecture      | 2 days         | Phase 4      | ⏳ Pending |
| 6     | Testing & QA                  | 3 days         | Phase 5      | ⏳ Pending |
| 7     | Documentation & Deployment    | 2 days         | Phase 6      | ⏳ Pending |

**Total Estimated Time**: 19 working days (~4 weeks)

## Detailed Implementation Steps

### Step 1: Configuration System Implementation

1. **Create Directory Structure**:

   ```bash
   mkdir -p MayaRepository/2026/scripts/TunnelUI/{config,src/{configuration,data/repositories,services,ui/widgets,utils},tests}
   ```

2. **Implement Configuration Models**:

   ```python
   # src/configuration/config_models.py
   @dataclass
   class AssetLibraryConfig:
       metadata_path: str = r"L:\megaScansMetadata"
       assets_path: str = r"M:\Zips"
       # ... other fields
   ```

3. **Create Configuration Manager**:

   ```python
   # src/configuration/config_manager.py
   class ConfigurationManager:
       def load_config(self) -> AssetLibraryConfig:
           # Implementation

       def save_config(self) -> bool:
           # Implementation
   ```

4. **Test Configuration System**:
   ```python
   # tests/test_configuration.py
   class TestConfigurationManager(unittest.TestCase):
       def test_load_default_config(self):
           # Test implementation
   ```

### Step 2: Repository Implementation

1. **Create Base Repository**:

   ```python
   # src/data/repositories/base_repository.py
   from abc import ABC, abstractmethod

   class BaseRepository(ABC):
       def __init__(self, config: AssetLibraryConfig):
           self.config = config
   ```

2. **Implement Metadata Repository**:

   ```python
   # src/data/repositories/metadata_repository.py
   class FileSystemMetadataRepository(BaseRepository):
       def load_inverted_index(self) -> Dict:
           # Move logic from current TunnelUi.py
   ```

3. **Test Repositories**:
   ```python
   # tests/test_repositories.py
   class TestMetadataRepository(unittest.TestCase):
       def test_load_inverted_index(self):
           # Test with mock files
   ```

### Step 3: Service Layer Implementation

1. **Asset Search Service**:

   ```python
   # src/services/asset_search_service.py
   class AssetSearchService:
       def search_assets(self, query: str, category: str = None) -> List[str]:
           # Move search logic from UI
   ```

2. **Image Loading Service**:
   ```python
   # src/services/image_loading_service.py
   class ImageLoadingService(QObject):
       image_loaded = pyqtSignal(str, QPixmap)

       def load_image(self, asset_id: str, image_path: Path):
           # Move threaded loading logic
   ```

### Step 4: UI Refactoring

1. **Main Window Refactor**:

   ```python
   # src/ui/main_window.py
   class TunnelMainWindow(QMainWindow):
       def __init__(self, asset_service, image_service, config_manager):
           # Dependency injection instead of creating services internally
   ```

2. **Settings Dialog**:
   ```python
   # src/ui/settings_dialog.py
   class SettingsDialog(QDialog):
       def __init__(self, config_manager: ConfigurationManager):
           # Configuration UI implementation
   ```

### Step 5: Application Factory

1. **Application Coordinator**:

   ```python
   # src/application.py
   class TunnelUIApplication:
       def create_main_window(self) -> TunnelMainWindow:
           # Factory method for creating configured window
   ```

2. **Entry Point Preservation**:
   ```python
   # TunnelUi_refactored.py
   def openWindow():
       """Preserve existing entry point signature"""
       app = TunnelUIApplication()
       return app.run_maya_mode() if app.environment.is_maya else app.run_standalone()
   ```

## Risk Mitigation Strategies

### Technical Risks

1. **Performance Regression**:

   - Benchmark critical paths during development
   - Profile memory usage before/after
   - Load testing with large asset libraries

2. **Maya Integration Issues**:

   - Test in multiple Maya versions
   - Maintain fallback to original behavior
   - Extensive testing of Qt parenting

3. **Threading Problems**:
   - Careful review of all Qt signal/slot connections
   - Test image loading under stress
   - Verify thread safety of all shared data

### Process Risks

1. **Scope Creep**:

   - Strict adherence to "preserve functionality" requirement
   - Feature freeze during refactoring
   - Regular validation against original behavior

2. **Timeline Overrun**:
   - Incremental delivery and testing
   - Parallel development where possible
   - Regular progress reviews

## Success Criteria

### Functional Requirements

- [ ] All existing functionality preserved exactly
- [ ] openWindow() function signature unchanged
- [ ] Performance equal or better than original
- [ ] Works in Maya 2023+ environments
- [ ] Successfully runs standalone
- [ ] Configuration system functional

### Quality Requirements

- [ ] 90%+ unit test coverage
- [ ] No memory leaks in image loading
- [ ] Clean separation of concerns
- [ ] Comprehensive error handling
- [ ] Full documentation coverage

### User Experience Requirements

- [ ] Zero workflow disruption for existing users
- [ ] New settings dialog functional
- [ ] Improved error messages
- [ ] Successful path configuration
- [ ] Responsive UI maintained

## Post-Implementation

### Monitoring

1. **Performance Monitoring**:

   - Track startup times
   - Monitor memory usage
   - Search response times

2. **Error Tracking**:
   - Log configuration issues
   - Track UI errors
   - Monitor asset loading failures

### Future Enhancements

1. **Phase 2 Features** (post-refactoring):

   - Multiple asset library support
   - Advanced search filters
   - Asset favorites and collections
   - Cloud asset library integration

2. **Technical Improvements**:
   - Async/await patterns for file operations
   - More sophisticated caching strategies
   - Plugin architecture for extensibility

This implementation plan provides a structured, low-risk approach to refactoring TunnelUI while maintaining full backward compatibility and adding the desired improvements.
