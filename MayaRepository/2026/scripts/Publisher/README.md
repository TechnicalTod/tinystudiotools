# Maya Asset Publishing Tool

A comprehensive Maya publishing tool for managing asset and shot workflows with version control, validation, and metadata tracking.

## Features

- **Asset & Shot Publishing**: Streamlined publishing workflow for Maya assets and shots
- **Version Control**: Automatic version management and tracking
- **Validation Framework**: Extensible validation system with built-in rules
- **Database Integration**: SQLite database for publish metadata and history
- **Network Drive Support**: Automatic file publishing to network locations
- **Maya Integration**: Deep integration with Maya APIs and scene handling
- **Configuration Management**: Per-show configuration and global settings

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Add the tool to your Maya Python path or run as standalone

## Quick Start

### Basic Usage

```python
from maya_publisher_tool import (
    PublishRecord,
    PublishDatabase,
    NetworkDrivePublisher,
    ValidationManager,
    MayaSceneHandler
)

# Initialize components
db = PublishDatabase("path/to/database.db")
publisher = NetworkDrivePublisher("S:/")
validator = ValidationManager()

# Create a publish record
record = PublishRecord(
    show_name="MyShow",
    asset_type="asset",
    asset_id="character_hero",
    task="model",
    version=1,
    artist="artist_name",
    comments="Initial model publish"
)

# Validate scene
results = validator.run_validation()
passed, errors, warnings = validator.get_overall_status(results)

if passed:
    # Publish to network
    target_path = publisher.generate_publish_path(record)
    success, message = publisher.publish_file("", target_path)

    if success:
        # Save to database
        record.file_path = str(target_path)
        record.file_size = publisher.get_file_size(target_path)
        db.create_publish(record)
        print("Publish successful!")
```
