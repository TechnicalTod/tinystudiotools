#!/usr/bin/env python
"""
Basic Maya Publishing Example

This example demonstrates how to use the Maya Asset Publishing Tool
to publish assets from Maya.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from maya_publisher_tool import (
    PublishRecord,
    EnvironmentContext,
    PublishDatabase,
    NetworkDrivePublisher,
    ValidationManager,
    MayaSceneHandler,
)
from maya_publisher_tool.configuration import ConfigurationManager


def main():
    """Main publish workflow example"""

    print("=== Maya Asset Publishing Tool - Basic Example ===")

    # Setup paths
    project_root = Path(__file__).parent.parent
    config_dir = project_root / "config"
    db_path = project_root / "database" / "publishes.db"

    # Initialize managers
    config_manager = ConfigurationManager(str(config_dir))
    db = PublishDatabase(str(db_path))
    validator = ValidationManager()

    # Get current Maya environment context
    print("\n1. Getting Maya environment context...")
    context = EnvironmentContext.from_maya_environment()

    print(f"   Current scene: {context.current_scene}")
    print(f"   Show: {context.show_name}")
    print(f"   Detected asset: {context.detected_asset_id}")
    print(f"   Asset type: {context.detected_asset_type}")
    print(f"   Task: {context.detected_task}")
    print(f"   User: {context.user_name}")
    print(f"   Maya version: {context.maya_version}")

    # Get or create show configuration
    print("\n2. Loading show configuration...")
    show_name = context.show_name or "DefaultShow"
    show_config = config_manager.get_show_config(show_name)
    print(f"   Show: {show_config.show_name}")
    print(f"   Asset tasks: {show_config.asset_tasks}")
    print(f"   Shot tasks: {show_config.shot_tasks}")

    # Initialize network publisher
    publisher = NetworkDrivePublisher(show_config.network_path)

    # Validate network access
    print("\n3. Validating network access...")
    network_ok, network_msg = publisher.validate_network_access()
    print(f"   Network status: {network_msg}")

    if not network_ok:
        print("   WARNING: Network not accessible, using local publish")

    # Run scene validation
    print("\n4. Running scene validation...")
    validation_results = validator.run_validation()
    passed, total_errors, total_warnings = validator.get_overall_status(validation_results)

    print(f"   Validation passed: {passed}")
    print(f"   Total errors: {total_errors}")
    print(f"   Total warnings: {total_warnings}")

    # Show detailed validation results
    for rule_name, (rule_passed, errors, warnings) in validation_results.items():
        print(f"   {rule_name}: {'PASS' if rule_passed else 'FAIL'}")
        for error in errors:
            print(f"     ERROR: {error}")
        for warning in warnings:
            print(f"     WARNING: {warning}")

    if not passed:
        print("\n   Scene validation failed. Please fix errors before publishing.")
        return False

    # Create publish record
    print("\n5. Creating publish record...")

    # Use detected values or prompt for missing info
    asset_id = context.detected_asset_id or input("Enter asset ID: ")
    asset_type = context.detected_asset_type or "asset"
    task = context.detected_task or input("Enter task: ")
    comments = input("Enter publish comments (optional): ")

    # Get next version number
    next_version = db.get_next_version(show_name, asset_type, asset_id, task)

    record = PublishRecord(
        show_name=show_name,
        asset_type=asset_type,
        asset_id=asset_id,
        task=task,
        version=next_version,
        artist=context.user_name,
        maya_version=context.maya_version,
        comments=comments,
    )

    print(f"   Asset: {record.asset_id}")
    print(f"   Type: {record.asset_type}")
    print(f"   Task: {record.task}")
    print(f"   Version: {record.version}")
    print(f"   Artist: {record.artist}")

    # Generate publish path
    target_path = publisher.generate_publish_path(record)
    print(f"   Target path: {target_path}")

    # Publish file
    print("\n6. Publishing file...")
    success, message = publisher.publish_file(context.current_scene, target_path)

    if success:
        print(f"   {message}")

        # Update record with file info
        record.file_path = str(target_path)
        record.file_size = publisher.get_file_size(target_path)

        # Save to database
        print("\n7. Saving to database...")
        saved_record = db.create_publish(record)
        print(f"   Publish ID: {saved_record.id}")
        print(f"   File size: {saved_record.file_size} bytes")

        print("\n✅ Publish completed successfully!")
        return True

    else:
        print(f"   Publish failed: {message}")
        return False


def show_recent_publishes():
    """Show recent publishes from database"""
    print("\n=== Recent Publishes ===")

    project_root = Path(__file__).parent.parent
    db_path = project_root / "database" / "publishes.db"
    db = PublishDatabase(str(db_path))

    recent = db.get_recent_publishes(limit=10)

    if not recent:
        print("No publishes found in database.")
        return

    for record in recent:
        print(f"{record.show_name}/{record.asset_type}/{record.asset_id}")
        print(f"  Task: {record.task}")
        print(f"  Version: v{record.version:03d}")
        print(f"  Artist: {record.artist}")
        print(f"  Published: {record.published_at}")
        print(f"  Path: {record.file_path}")
        print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Maya Asset Publishing Tool Example")
    parser.add_argument("--recent", action="store_true", help="Show recent publishes")

    args = parser.parse_args()

    if args.recent:
        show_recent_publishes()
    else:
        main()
