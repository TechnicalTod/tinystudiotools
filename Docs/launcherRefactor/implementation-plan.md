# TinyStudioLauncher - Implementation Plan

## Overview

This document outlines the step-by-step implementation plan for refactoring the SagaAppLauncher into TinyStudioLauncher with UV-based environment management.

## Phase 1: Foundation (Week 1)

### 1.1 Project Setup

- [ ] Create project directory structure
- [ ] Install UV globally on development machines
- [ ] Set up Git repository with .gitignore
- [ ] Create initial requirements.txt for launcher dependencies

```bash
# Directory creation
mkdir -p L:/SagaTools/GenTools/scripts/TinyStudioLauncher/{src,configs,environments,requirements,resources/{icons,styles}}

# Install UV
pip install uv
# or
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 1.2 Environment Manager Development

- [ ] Implement EnvironmentManager class
- [ ] Create unit tests for environment operations
- [ ] Test UV environment creation for each Python version
- [ ] Document environment setup process

```python
# Test environment creation
from pathlib import Path
from src.environment_manager import EnvironmentManager

manager = EnvironmentManager(Path("L:/SagaTools/GenTools/scripts/TinyStudioLauncher"))
assert manager.create_environment("maya-2023", "3.9")
assert manager.create_environment("maya-2026", "3.10")
assert manager.create_environment("unreal", "3.10")
```

### 1.3 Configuration System

- [ ] Create JSON schema for application configs
- [ ] Implement config loader with validation
- [ ] Create initial config files for Maya 2023, Maya 2026, and Unreal
- [ ] Test config loading and variable substitution

## Phase 2: Core Functionality (Week 2)

### 2.1 Launch Controller

- [ ] Implement LaunchController class
- [ ] Create launch configuration builder
- [ ] Implement process tracking system
- [ ] Add comprehensive logging

### 2.2 Environment Isolation Testing

- [ ] Test simultaneous Maya 2023 and Maya 2026 launches
- [ ] Verify no environment variable conflicts
- [ ] Test Python package isolation
- [ ] Document any edge cases

### 2.3 Migration Tools

- [ ] Create script to migrate existing package installations
- [ ] Build requirements.txt from current tools folders
- [ ] Test package installation in new environments
- [ ] Create rollback procedure

```python
# Migration script example
import os
import subprocess
from pathlib import Path

def migrate_packages(old_tools_dir: Path, requirements_file: Path):
    """Extract installed packages from old tools directory"""
    packages = []

    # Find all .dist-info directories
    for item in old_tools_dir.iterdir():
        if item.is_dir() and item.name.endswith('.dist-info'):
            # Extract package name and version
            parts = item.name.split('-')
            if len(parts) >= 2:
                package_name = parts[0]
                version = parts[1]
                packages.append(f"{package_name}=={version}")

    # Write requirements file
    with open(requirements_file, 'w') as f:
        f.write('\n'.join(sorted(packages)))
```

## Phase 3: User Interface (Week 3)

### 3.1 UI Development

- [ ] Port existing UI design to new architecture
- [ ] Implement ConsoleOutput widget with formatting
- [ ] Create ApplicationButton with status indicators
- [ ] Add environment health monitoring display

### 3.2 UI Integration

- [ ] Connect UI to LaunchController
- [ ] Implement real-time console output
- [ ] Add progress indicators for environment operations
- [ ] Test UI responsiveness during launches

### 3.3 Styling and Polish

- [ ] Port dark theme from existing launcher
- [ ] Add animations for launch feedback
- [ ] Implement keyboard shortcuts
- [ ] Create help/about dialog

## Phase 4: Testing and Optimization (Week 4)

### 4.1 Integration Testing

- [ ] Test all application launch scenarios
- [ ] Verify show-specific configurations work
- [ ] Test error handling and recovery
- [ ] Performance testing with multiple launches

### 4.2 Performance Optimization

- [ ] Implement parallel environment checking
- [ ] Add caching for environment info
- [ ] Optimize startup time
- [ ] Profile memory usage

### 4.3 User Acceptance Testing

- [ ] Deploy to test group of artists
- [ ] Gather feedback on UI/UX
- [ ] Test with real production scenarios
- [ ] Document any issues found

## Phase 5: Deployment (Week 5)

### 5.1 Packaging

- [ ] Create PyInstaller spec file
- [ ] Test executable on clean systems
- [ ] Create installer with environment setup
- [ ] Build auto-update mechanism

```python
# Build command
pyinstaller --clean --noconfirm TinyStudioLauncher.spec
```

### 5.2 Documentation

- [ ] Create user guide with screenshots
- [ ] Write troubleshooting guide
- [ ] Document environment management for TAs
- [ ] Create video tutorials

### 5.3 Rollout Strategy

- [ ] Phase 1: Technical artists and developers
- [ ] Phase 2: Single show pilot (1 week)
- [ ] Phase 3: Department-wide rollout
- [ ] Phase 4: Studio-wide deployment

## Phase 6: Post-Launch (Ongoing)

### 6.1 Monitoring

- [ ] Set up error reporting system
- [ ] Monitor launch success rates
- [ ] Track performance metrics
- [ ] Gather user feedback

### 6.2 Maintenance

- [ ] Weekly environment health checks
- [ ] Package update procedures
- [ ] Bug fix deployment process
- [ ] Feature request tracking

## Risk Mitigation

### Technical Risks

1. **UV Installation Issues**

   - Solution: Provide offline installer package
   - Fallback: Traditional virtualenv support

2. **Network Dependencies**

   - Solution: Local PyPI mirror
   - Fallback: Offline wheel repository

3. **Permission Issues**
   - Solution: Run from user-writable location
   - Fallback: Request IT assistance for setup

### Operational Risks

1. **User Resistance**

   - Solution: Keep UI familiar
   - Training: Comprehensive documentation

2. **Production Disruption**
   - Solution: Parallel operation period
   - Rollback: Keep old launcher available

## Success Criteria

### Technical Metrics

- Zero environment conflicts in production
- < 2 second launch time (excluding app startup)
- 99.9% launch success rate
- < 100MB memory footprint

### User Metrics

- 95% user adoption within 4 weeks
- 50% reduction in environment-related tickets
- Positive feedback from 80% of users
- Zero critical production issues

## Timeline Summary

| Phase              | Duration | Key Deliverables             |
| ------------------ | -------- | ---------------------------- |
| Foundation         | Week 1   | Environment manager, configs |
| Core Functionality | Week 2   | Launch controller, isolation |
| User Interface     | Week 3   | Complete UI, integration     |
| Testing            | Week 4   | UAT complete, optimizations  |
| Deployment         | Week 5   | Released to production       |
| Post-Launch        | Ongoing  | Monitoring, maintenance      |

## Next Steps

1. Review and approve implementation plan
2. Allocate development resources
3. Set up development environment
4. Begin Phase 1 implementation

## Appendix: Technical Details

### Python Version Compatibility

| Application   | Python Version | Notes             |
| ------------- | -------------- | ----------------- |
| Maya 2023     | 3.9.7          | Embedded Python   |
| Maya 2026     | 3.10.11        | Embedded Python   |
| Unreal Engine | 3.10.x         | Project dependent |
| After Effects | TBD            | Future support    |

### Required Python Packages

```txt
# Launcher requirements (requirements.txt)
PySide2>=5.15.2
uv>=0.4.0
psutil>=5.9.0
watchdog>=3.0.0

# Maya 2023 requirements (requirements/maya_2023.txt)
numpy==1.26.4
pymel==1.4.0
# Add other Maya-specific packages

# Maya 2026 requirements (requirements/maya_2026.txt)
numpy==1.26.4
pymel==1.5.0
# Add other Maya-specific packages

# Unreal requirements (requirements/unreal.txt)
numpy==2.1.1
PySide2==5.15.2.1
transforms3d==0.4.2
# Add other Unreal-specific packages
```

### Environment Variables Template

```json
{
  "base_vars": {
    "SAGA_BASE_SHOW_DIR": "S:/",
    "SAGA_LIB_DIR": "L:/",
    "SCRIPT_DIR": "L:/SagaTools/"
  },
  "maya_vars": {
    "MAYA_SCRIPT_PATH": "{PYTHONPATH}",
    "MAYA_MODULE_PATH": "{MAYA_REPO}/modules",
    "MAYA_SHELF_PATH": "{MAYA_REPO}/shelves",
    "MAYA_PLUG_IN_PATH": "{MAYA_REPO}/plug-ins"
  },
  "unreal_vars": {
    "UE_PYTHONPATH": "{PYTHONPATH}",
    "UE_SITE_PACKAGES": "{ENV_PATH}/Lib/site-packages"
  }
}
```
