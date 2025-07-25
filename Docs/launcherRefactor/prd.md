# TinyStudioLauncher - Product Requirements Document

## Overview

TinyStudioLauncher is a modern application launcher for Saga Studio that provides isolated Python environments for each application and version combination. Using `uv` for lightning-fast environment management, it ensures no environment variable conflicts between different instances of Maya, Unreal Engine, or other DCC applications.

## Purpose

- **Environment Isolation**: Prevent Python path and environment variable conflicts between applications
- **Dependency Management**: Maintain separate package versions for each application/version
- **Fast Launch Times**: Leverage uv's speed for quick environment activation
- **Centralized Configuration**: Manage all application environments from a single interface
- **Future-Proof Architecture**: Support easy addition of new applications and versions

## User Stories

### Artist Stories

1. As an artist, I want to launch Maya 2023 for Show A and Maya 2026 for Show B simultaneously without conflicts
2. As an artist, I want the launcher to remember my last selected show and version
3. As an artist, I want to see real-time feedback about what's happening during launch
4. As an artist, I want to quickly switch between different shows without restarting the launcher

### Technical Artist Stories

1. As a technical artist, I want to ensure each application has the correct Python packages installed
2. As a technical artist, I want to add new tools/packages to specific environments without affecting others
3. As a technical artist, I want to see which environment is being used for each launch
4. As a technical artist, I want to troubleshoot launch issues through detailed console output

### Developer Stories

1. As a developer, I want to easily add support for new applications
2. As a developer, I want to manage Python dependencies through standard requirements.txt files
3. As a developer, I want to test different package versions without affecting production
4. As a developer, I want to configure environment variables per application/show combination

## Functional Requirements

### Core Functionality

- Launch multiple instances of DCC applications with isolated environments
- Manage Python virtual environments using `uv`
- Configure environment variables per application/version/show combination
- Display real-time console output during launch
- Persist user preferences (last selected show, version, etc.)

### Application Support

Initially support:

- Maya 2023 (Python 3.9)
- Maya 2026 (Python 3.10)
- Unreal Engine (Python 3.10)
- After Effects (Future)

### Environment Management

- Create and maintain separate virtual environments per application/version
- Install packages from PyPI or local wheels
- Support both online and offline package installation
- Synchronize environments from requirements.txt files

### Configuration System

- JSON-based configuration for each application/version
- Support for:
  - Python paths
  - Environment variables
  - Application executable paths
  - Show-specific overrides

### User Interface

- Similar layout to current SagaAppLauncher
- Show selection dropdown
- Version selection per application
- Large, visual application launch buttons
- Real-time console output window
- Status indicators for environment health

## Technical Requirements

### Technology Stack

- **Language**: Python 3.10+
- **GUI Framework**: PySide2/PySide6
- **Environment Manager**: uv
- **Configuration**: JSON
- **Packaging**: PyInstaller

### Directory Structure

```
TinyStudioLauncher/
├── src/
│   ├── launcher.py          # Main application
│   ├── environment_manager.py
│   ├── launch_controller.py
│   └── ui/
│       ├── main_window.py
│       └── widgets/
├── configs/
│   ├── maya_2023.json
│   ├── maya_2026.json
│   └── unreal.json
├── environments/           # UV-managed environments
│   ├── maya-2023/
│   ├── maya-2026/
│   └── unreal/
├── requirements/
│   ├── maya_2023.txt
│   ├── maya_2026.txt
│   └── unreal.txt
└── resources/
    ├── icons/
    └── styles/
```

### Performance Requirements

- Environment activation: < 100ms (leveraging uv's speed)
- Application launch: < 5 seconds total
- UI responsiveness: Immediate feedback on all actions
- Memory usage: < 100MB for launcher process

## Out of Scope (Initial Release)

- Package version conflict resolution UI
- Environment cloning/templating
- Remote environment synchronization
- Plugin management for DCC applications
- License server configuration UI

## Future Considerations

- Support for Houdini, Nuke, and other DCC applications
- Environment templates for different project types
- Integration with studio asset management system
- Automated testing of environments
- Web-based launcher interface
- Container-based isolation (Docker/Podman)

## Success Metrics

- Zero environment conflicts between simultaneous application launches
- 90% reduction in environment-related support tickets
- < 2 second total launch time (launcher + environment + application)
- Successful adoption by 100% of artists within 2 weeks

## Migration Strategy

- Parallel operation with existing SagaAppLauncher
- Automated migration of existing package installations
- Gradual rollout by department/show
- Comprehensive documentation and training materials
