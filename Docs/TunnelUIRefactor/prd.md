# TunnelUI Asset Browser - Refactoring PRD

## Overview

The TunnelUI Asset Browser is a Qt-based tool for browsing and importing 3D assets from a megascans-like library within Maya. This refactoring project aims to improve maintainability, add configuration flexibility, enable standalone operation, and enhance the user interface while preserving all existing functionality.

## Purpose

- **Maintainability**: Compartmentalize code for easier updates and modifications
- **Configuration**: Make file paths and settings configurable rather than hardcoded
- **Standalone Operation**: Enable the tool to run independently of Maya
- **UI Enhancement**: Add proper menu structure with file and help options
- **Code Quality**: Improve architecture without changing core functionality

## User Stories

### Current User Stories (Must Preserve)

1. As a Maya artist, I want to browse assets by category (3D, Plants, Surfaces, etc.) so I can find relevant content
2. As a user, I want to search assets by keywords so I can quickly locate specific items
3. As a user, I want to see thumbnail previews of assets so I can visually identify what I need
4. As a user, I want to preview full-size images with navigation so I can examine assets in detail
5. As a user, I want to import selected assets into my project
6. As a user, I want the interface to be responsive with lazy-loaded images for performance

### New User Stories

1. As a user, I want to configure asset library paths so I can point to different repositories
2. As a user, I want to run the tool standalone (outside Maya) for asset browsing
3. As a developer, I want compartmentalized code so I can easily maintain and extend functionality
4. As a user, I want access to file and help menus for additional functionality
5. As an admin, I want configurable settings so I can customize the tool for different environments

## Functional Requirements

### Core Functionality (Must Preserve)

- **Asset Browsing**: Categorized view of assets (3D, Plants, Atlas, Decals, Brushes, Surfaces)
- **Search System**: Keyword-based search with auto-completion
- **Image Loading**: Threaded, lazy-loading of asset thumbnails
- **Preview Dialog**: Full-size image preview with navigation between assets
- **Asset Import**: Integration with zip file importing system
- **Maya Integration**: Seamless operation within Maya environment

### New Requirements

- **Configuration Management**: JSON-based configuration for paths and settings
- **Standalone Mode**: Ability to run without Maya dependencies
- **Menu System**: File and Help dropdown menus
- **Path Configuration**: UI for setting metadata and asset library paths
- **Modular Architecture**: Separated concerns for UI, data access, and business logic

### Configuration Requirements

- **Asset Paths**: Configurable base paths for metadata and zip files
- **UI Settings**: Customizable interface preferences
- **Environment Detection**: Automatic Maya vs standalone mode detection
- **Default Fallbacks**: Sensible defaults when configuration is missing

## Technical Requirements

### Architecture Goals

- **Separation of Concerns**: Distinct layers for UI, business logic, and data access
- **Configuration System**: Centralized settings management
- **Dependency Injection**: Flexible component initialization
- **Error Handling**: Robust error management with user feedback
- **Logging**: Comprehensive logging for debugging and monitoring

### Compatibility Requirements

- **Maya Integration**: Must work seamlessly in Maya 2023+ environments
- **Standalone Operation**: Must run independently with Qt application
- **Python Compatibility**: Support Python 3.7+ (Maya compatibility)
- **Cross-Platform**: Windows primary, with consideration for other platforms

### Performance Requirements

- **Image Loading**: Maintain current lazy-loading performance
- **Search Response**: Sub-second search results for typical queries
- **Memory Management**: Efficient image caching and cleanup
- **Startup Time**: Quick initialization in both Maya and standalone modes

## User Interface Requirements

### Menu Structure

- **File Menu**:

  - Settings/Preferences
  - Configure Paths
  - Refresh Library
  - Exit (standalone mode only)

- **Help Menu**:
  - About
  - Documentation
  - Keyboard Shortcuts
  - Report Issue

### Settings Dialog

- **Paths Configuration**:

  - Metadata folder path
  - Asset zip files path
  - Cache directory
  - Custom stylesheet path

- **Display Options**:
  - Thumbnail size
  - Grid spacing
  - Theme selection

### Preserved UI Elements

- **Stretched Tab Bar**: Maintain current tab behavior
- **Asset Grid View**: Keep existing icon view with thumbnails
- **Search Field**: Preserve auto-completion functionality
- **Preview Dialog**: Maintain current preview and navigation

## Out of Scope

- **New Asset Sources**: Only refactoring existing megascans integration
- **Advanced Search**: Complex filtering beyond current keyword search
- **Asset Management**: No creation, editing, or organization of assets
- **Multiple Libraries**: Single library support only (for this phase)
- **Cloud Integration**: Local file system only

## Implementation Constraints

### Must Preserve

- **Entry Point**: `openWindow()` function signature must remain identical
- **External Dependencies**: Maya shelf integration must continue working
- **User Workflow**: No changes to how users interact with the tool
- **File Formats**: Current JSON metadata structure compatibility

### Technical Constraints

- **PySide6**: Continue using current Qt version for Maya compatibility
- **Thread Safety**: Maintain safe threading for image loading
- **Memory Usage**: No significant increase in memory footprint
- **Startup Impact**: Refactoring should not slow down tool initialization

## Success Metrics

### Functionality Metrics

- **Feature Parity**: 100% of current functionality preserved
- **Performance**: No degradation in search or loading times
- **Compatibility**: Works in all supported Maya versions
- **Standalone**: Successfully runs outside Maya environment

### Code Quality Metrics

- **Modularity**: Clear separation between UI, business logic, and data layers
- **Configuration**: All hardcoded paths moved to configuration system
- **Test Coverage**: Comprehensive test suite covering core functionality
- **Documentation**: Clear code documentation and user guides

### User Experience Metrics

- **Zero Breaking Changes**: Existing users experience no workflow disruption
- **Enhanced Usability**: New menu system provides additional functionality
- **Error Handling**: Improved error messages and recovery options
- **Configuration**: Easy path setup for different environments

## Future Considerations

### Potential Enhancements

- **Multiple Asset Libraries**: Support for multiple simultaneous libraries
- **Advanced Filtering**: Category, date, size, and tag-based filtering
- **Asset Organization**: Collections, favorites, and custom groupings
- **Cloud Integration**: Remote asset library support
- **Plugin Architecture**: Extensible import/export system

### Scalability

- **Large Libraries**: Optimization for libraries with 10,000+ assets
- **Distributed Storage**: Support for network-attached storage
- **Caching Strategy**: Intelligent caching for frequently accessed assets
- **Performance Profiling**: Built-in performance monitoring

## Risk Assessment

### Technical Risks

- **Maya Integration**: Risk of breaking existing Maya workflow
- **Threading Issues**: Potential race conditions in image loading
- **Configuration Complexity**: Over-engineering the settings system
- **Performance Regression**: Abstraction layers impacting speed

### Mitigation Strategies

- **Incremental Refactoring**: Gradual migration with extensive testing
- **Backward Compatibility**: Fallback to current behavior when needed
- **Performance Testing**: Benchmark critical paths during development
- **User Testing**: Validate with actual Maya artists throughout process
