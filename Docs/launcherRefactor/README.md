# TinyStudioLauncher Documentation

## Overview

This directory contains the complete documentation for the TinyStudioLauncher project - a modern refactor of the SagaAppLauncher that solves environment isolation issues using UV (Astral's fast Python package manager).

## Problem Statement

The current SagaAppLauncher has a critical limitation: when launching multiple applications (e.g., Maya 2023 for Show A and Maya 2026 for Show B), environment variables can conflict, leading to:

- Wrong Python packages being loaded
- Incorrect tool paths
- Cross-contamination between shows
- Difficulty managing per-version dependencies

## Solution

TinyStudioLauncher leverages UV's lightning-fast virtual environment management to provide:

- **Complete environment isolation** per application/version
- **No conflicts** between simultaneous application launches
- **Fast environment activation** (< 100ms with UV)
- **Standard Python packaging** workflows

## Documentation Structure

### 1. [Product Requirements Document (prd.md)](prd.md)

Defines the business requirements, user stories, and success criteria for the new launcher.

**Key Points:**

- User stories from artists, TAs, and developers
- Functional requirements and UI specifications
- Performance targets and success metrics

### 2. [Backend Blueprint (backend-blueprint.md)](backend-blueprint.md)

Technical architecture and implementation details for all components.

**Key Components:**

- `EnvironmentManager`: UV virtual environment management
- `LaunchController`: Process isolation and launch configuration
- `UI Components`: Modern Qt-based interface
- Configuration system with JSON-based app configs

### 3. [Implementation Plan (implementation-plan.md)](implementation-plan.md)

Step-by-step roadmap for building and deploying the new launcher.

**Timeline:**

- Week 1: Foundation (Environment management, configs)
- Week 2: Core functionality (Launch controller, isolation)
- Week 3: User interface (UI development and integration)
- Week 4: Testing and optimization
- Week 5: Deployment
- Ongoing: Monitoring and maintenance

## Key Architecture Decisions

### Why UV?

- **Speed**: 10-100x faster than pip/virtualenv
- **Reliability**: Built in Rust, handles complex dependency resolution
- **Compatibility**: Works with standard Python packaging
- **Modern**: Actively developed with studio-scale use cases in mind

### Environment Structure

```
TinyStudioLauncher/
├── environments/
│   ├── maya-2023/      # Python 3.9 environment
│   ├── maya-2026/      # Python 3.10 environment
│   └── unreal/         # Python 3.10 environment
├── requirements/
│   ├── maya_2023.txt   # Package list for Maya 2023
│   ├── maya_2026.txt   # Package list for Maya 2026
│   └── unreal.txt      # Package list for Unreal
└── configs/
    ├── maya_2023.json  # Launch configuration
    ├── maya_2026.json  # Launch configuration
    └── unreal.json     # Launch configuration
```

## Quick Start for Developers

1. **Install UV**:

   ```bash
   pip install uv
   # or
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Clone and setup**:

   ```bash
   cd L:/SagaTools/GenTools/scripts
   git clone [repo] TinyStudioLauncher
   cd TinyStudioLauncher
   uv venv
   uv pip install -r requirements.txt
   ```

3. **Create environments**:
   ```python
   from src.environment_manager import EnvironmentManager
   manager = EnvironmentManager(Path.cwd())
   manager.create_environment("maya-2023", "3.9")
   manager.sync_environment("maya-2023")
   ```

## Migration from SagaAppLauncher

The new launcher will:

1. Run in parallel with the existing launcher during transition
2. Automatically migrate existing package installations
3. Preserve the familiar UI layout
4. Maintain all current functionality while adding isolation

## Improvements Over Current Launcher

### Current Issues Solved:

- ✅ Environment variable conflicts between instances
- ✅ Python package version conflicts
- ✅ Slow package management
- ✅ Difficult dependency tracking

### New Features:

- 🚀 Launch multiple Maya versions simultaneously
- 🔒 Complete environment isolation
- 📦 Standard Python packaging workflows
- 🎯 Per-show Python package overrides
- 📊 Real-time environment health monitoring
- ⚡ Sub-second environment activation

## Future Enhancements

Based on the architecture, we can easily add:

- Support for Houdini, Nuke, and other DCCs
- Web-based launcher interface
- Container-based isolation (Docker/Podman)
- Automated environment testing
- Package conflict resolution UI

## Contact

For questions or suggestions about the TinyStudioLauncher project, please contact the Pipeline Development team.
