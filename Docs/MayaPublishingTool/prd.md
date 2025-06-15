# Maya Asset Publishing Tool - PRD

## Overview

The Maya Asset Publishing Tool is a shelf-integrated Maya plugin that provides artists with a centralized publishing system for assets, rigs, and shots. The tool features a tree-view browser for navigating published content, automatic environment variable detection for context awareness, and local database tracking for version management and metadata.

## Purpose

- **Context-Aware Publishing**: Automatically detect current work context through environment variables
- **Centralized Asset Management**: Browse and publish all show assets through a unified interface
- **Version Control**: Track all published versions with metadata and comments
- **Quality Assurance**: Enforce show-specific standards through configurable pre-publish validation
- **Flexible Task Management**: Support show-specific task types through JSON configuration
- **Network Integration**: Organize published files on network drives with consistent structure

## User Stories

### Artist Stories

1. As an artist, I want to open a scene and have the publish tool automatically know what I'm working on
2. As an artist, I want to browse existing published assets and shots in a tree view to see what's available
3. As an artist, I want to see version history and publish notes for each asset/shot in a detail panel
4. As an artist, I want to publish my work with comments and have it automatically versioned
5. As an artist, I want optional validation feedback available in a separate tab to help improve my work
6. As an artist, I want to work on different task types (model, texture, anim, etc.) for the same asset

### Technical Director Stories

1. As a TD, I want to configure task types per show through JSON files
2. As a TD, I want to enforce naming conventions and scene standards through validation rules
3. As a TD, I want to see who published what and when for tracking purposes
4. As a TD, I want consistent file organization on network drives across all shows

### Pipeline Stories

1. As a pipeline developer, I want environment variable detection to work seamlessly with Maya
2. As a pipeline developer, I want the system to scale to future asset management integrations
3. As a pipeline developer, I want local database tracking for fast UI performance

## Functional Requirements

### Core Functionality

- **Environment Detection**: Automatically detect SHOW_NAME and relevant context variables
- **Smart Context Setting**: Set environment variables when Maya scenes are opened
- **Tree View Browser**: Hierarchical display of assets/shots with expandable versions
- **Detail Panel**: Show publish metadata, comments, file info, and publish controls
- **Version Management**: Automatic version incrementing with manual override option
- **File Publishing**: Copy/save Maya scenes to network drives with proper naming

### UI Requirements

#### Main Interface Layout

- **Left Panel**: Tree view showing:
  - Show name at root level
  - Assets and Shots as top-level categories
  - Individual assets/shots as expandable nodes
  - Task types under each asset/shot
  - Version numbers under each task
- **Right Panel**: Tabbed interface with:
  - **Details Tab**: Selected item information, publish history, comments, file info
  - **Publish Tab**: Publish controls, comments field, version settings
  - **Validation Tab**: Pre-publish checks and validation results (optional)

#### Publish Workflow

- **Auto-Detection**: Pre-populate asset/shot and task based on environment
- **Manual Override**: Allow users to select different asset/shot/task if needed
- **Comment System**: Require or encourage publish comments
- **Optional Validation**: Validation checks available in separate tab (non-blocking)

### Technical Requirements

#### Database Structure

- **Local SQLite Database**: Fast querying for UI responsiveness
- **Publish Tracking**: Store all publish metadata locally
- **User Information**: Track who published what and when
- **File Metadata**: Store file paths, sizes, dependencies

#### File Organization

```
/S:/[SHOW_NAME]/
├── assets/
│   └── [ASSET_ID]/
│       └── [TASK]/
│           └── v[VERSION]/
│               └── [ASSET_ID]_[TASK]_v[VERSION].ma
└── shots/
    └── [SHOT_ID]/
        └── [TASK]/
            └── v[VERSION]/
                └── [SHOT_ID]_[TASK]_v[VERSION].ma
```

#### Configuration System

- **JSON-based Task Configuration**: Per-show task type definitions
- **Validation Rules**: Configurable pre-publish checks
- **Environment Settings**: Show-specific path and naming configurations

### Validation Framework

#### Pre-Publish Checks

- **Naming Conventions**: Ensure consistent asset/shot naming
- **Scene Cleanliness**: Check for unused nodes, empty groups
- **File Dependencies**: Validate texture paths and references
- **Technical Standards**: Poly counts, UV coverage, etc. (configurable)
- **Required Metadata**: Ensure publish comments and context

#### Validation Behavior

- **Optional Validation**: Pre-publish checks are optional and accessed via the Validation tab
- **Non-Blocking**: Validation results do not prevent publishing in Phase 1
- **Informational**: Show validation status and recommendations to users
- **Future Enhancement**: Blocking/warning behavior to be implemented in future phases

## Out of Scope (Phase 1)

- Asset assignment and checkout systems
- Real-time collaboration features
- Advanced dependency tracking
- Integration with external asset management systems
- Automated backup and archive systems
- Advanced user permission systems

## Future Considerations

- **Asset Management Integration**: ShotGrid, Perforce, or custom systems
- **Collaborative Features**: Asset locking, conflict resolution
- **Advanced Validation**: Render tests, automated quality checks
- **Cloud Storage**: Integration with cloud-based storage systems
- **Mobile Access**: Web-based asset browsing and approval
- **Analytics**: Usage tracking and performance metrics

## Success Metrics

- Artists can successfully publish assets with proper versioning
- Environment detection works seamlessly across different Maya sessions
- UI provides fast browsing of published content
- Optional validation system provides helpful feedback to users
- File organization remains consistent across all shows and users
- Local database provides responsive UI performance

## Configuration Example

### Task Configuration (tasks.json)

```json
{
  "show_name": "PROJECT_ALPHA",
  "asset_tasks": ["model", "texture", "shading", "rig"],
  "shot_tasks": ["previs", "layout", "anim", "lighting"],
  "validation_rules": {
    "naming_convention": true,
    "scene_cleanup": true,
    "required_comments": true
  }
}
```
