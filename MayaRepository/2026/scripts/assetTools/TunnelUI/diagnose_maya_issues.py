#!/usr/bin/env python
"""
TunnelUI Maya Diagnostic Script

This script checks for common issues preventing TunnelUI from loading in Maya.
"""

import sys
import os
from pathlib import Path


def diagnose_maya_environment():
    """Diagnose common Maya environment issues"""
    print("🔍 TunnelUI Maya Environment Diagnostic")
    print("=" * 50)

    issues_found = []

    # Check 1: Python version
    print(f"✅ Python version: {sys.version}")

    # Check 2: PySide6 availability
    try:
        import PySide6

        print(f"✅ PySide6 version: {PySide6.__version__}")
    except ImportError as e:
        error = f"❌ PySide6 not available: {e}"
        print(error)
        issues_found.append("PySide6 missing - install with: pip install PySide6")

    # Check 3: Maya detection
    try:
        import maya.cmds as cmds

        maya_version = cmds.about(version=True)
        print(f"✅ Maya version: {maya_version}")
    except ImportError:
        print("❌ Not running in Maya environment")
        issues_found.append("Not running in Maya")

    # Check 4: TunnelUI directory structure
    current_dir = Path(__file__).parent
    src_dir = current_dir / "src"
    config_dir = current_dir / "config"

    print(f"\n📁 Directory structure:")
    print(f"  TunnelUI dir: {current_dir}")
    print(f"  Src exists: {'✅' if src_dir.exists() else '❌'} {src_dir}")
    print(f"  Config exists: {'✅' if config_dir.exists() else '❌'} {config_dir}")

    if not src_dir.exists():
        issues_found.append(f"Missing src directory: {src_dir}")

    # Check 5: Configuration file
    config_file = config_dir / "tunnel_config.json"
    print(f"  Config file: {'✅' if config_file.exists() else '❌'} {config_file}")

    if not config_file.exists():
        issues_found.append(f"Missing config file: {config_file}")

    # Check 6: Asset library paths
    metadata_path = Path("L:/megaScansMetadata")
    assets_path = Path("B:/MegascansLib/Zips")

    print(f"\n📦 Asset library:")
    print(f"  Metadata: {'✅' if metadata_path.exists() else '❌'} {metadata_path}")
    print(f"  Assets: {'✅' if assets_path.exists() else '❌'} {assets_path}")

    if not metadata_path.exists():
        issues_found.append(f"Missing metadata directory: {metadata_path}")
    if not assets_path.exists():
        issues_found.append(f"Missing assets directory: {assets_path}")

    # Check 7: Key metadata files
    if metadata_path.exists():
        index_file = metadata_path / "inverted_index_combined.json"
        print(f"  Index file: {'✅' if index_file.exists() else '❌'} {index_file}")

        if not index_file.exists():
            issues_found.append(f"Missing index file: {index_file}")

    # Check 8: Try importing application
    print(f"\n🧪 Testing imports:")
    try:
        sys.path.insert(0, str(src_dir))
        from application import TunnelUIApplication

        print("✅ Application import successful")

        # Try creating application
        try:
            app = TunnelUIApplication()
            print("✅ Application initialization successful")
        except Exception as e:
            error = f"❌ Application initialization failed: {e}"
            print(error)
            issues_found.append(f"App init error: {e}")

    except ImportError as e:
        error = f"❌ Import failed: {e}"
        print(error)
        issues_found.append(f"Import error: {e}")

    # Summary
    print(f"\n📋 Summary:")
    if issues_found:
        print(f"❌ {len(issues_found)} issues found:")
        for i, issue in enumerate(issues_found, 1):
            print(f"  {i}. {issue}")

        print(f"\n🔧 Recommended fixes:")
        if any("PySide6" in issue for issue in issues_found):
            print("  • Install PySide6 in Maya: pip install PySide6")
        if any("Missing" in issue for issue in issues_found):
            print("  • Check file paths and directory structure")
        if any("metadata" in issue.lower() for issue in issues_found):
            print("  • Run asset processing pipeline to generate metadata")

    else:
        print("✅ All checks passed! TunnelUI should work correctly.")

    return len(issues_found) == 0


if __name__ == "__main__":
    success = diagnose_maya_environment()
    sys.exit(0 if success else 1)
