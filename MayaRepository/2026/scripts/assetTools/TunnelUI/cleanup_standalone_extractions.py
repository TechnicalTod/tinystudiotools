#!/usr/bin/env python
"""
Cleanup script for TunnelUI standalone mode extractions.

This script removes any extracted assets that might have been created
during standalone testing. It preserves imports for Maya/Unreal modes.
"""

import shutil
import os
from pathlib import Path


def cleanup_standalone_extractions():
    """Remove any standalone-mode extracted assets"""
    print("TunnelUI Standalone Cleanup")
    print("=" * 40)

    current_dir = Path(__file__).parent
    cleanup_dirs = ["extracted_assets", "temp_import", "extracted", "standalone_extracts"]

    removed_count = 0

    for dir_name in cleanup_dirs:
        dir_path = current_dir / dir_name
        if dir_path.exists() and dir_path.is_dir():
            print(f"Removing: {dir_path}")
            try:
                shutil.rmtree(dir_path)
                removed_count += 1
                print(f"  ✅ Removed successfully")
            except Exception as e:
                print(f"  ❌ Failed to remove: {e}")
        else:
            print(f"Not found: {dir_name} (already clean)")

    # Also check for any .zip files that might have been extracted here
    zip_files = list(current_dir.glob("*.zip"))
    if zip_files:
        print(f"\nFound {len(zip_files)} zip files in working directory:")
        for zip_file in zip_files:
            print(f"  - {zip_file.name}")
        print("These are likely temporary and can be removed if needed.")

    print(f"\nCleanup complete!")
    print(f"Removed {removed_count} directories")
    print("\n✅ Standalone mode will now only OPEN zip files (no extraction)")
    print("✅ Maya/Unreal imports remain unaffected")


if __name__ == "__main__":
    cleanup_standalone_extractions()
