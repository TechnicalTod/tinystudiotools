"""
Migration script to extract package information from existing tools directories

This script helps migrate from the old manual package installation approach
to the new UV-managed environments.
"""

import os
import re
from pathlib import Path


def extract_packages_from_tools_dir(tools_dir: Path) -> list:
    """
    Extract package names and versions from a tools directory.

    Args:
        tools_dir: Path to the tools directory containing packages

    Returns:
        List of package specifications (e.g., ["numpy==1.26.4"])
    """
    packages = []

    if not tools_dir.exists():
        print(f"Warning: {tools_dir} does not exist")
        return packages

    # Look for .dist-info directories
    for item in tools_dir.iterdir():
        if item.is_dir() and item.name.endswith(".dist-info"):
            # Extract package name and version from directory name
            # Format is typically: package_name-version.dist-info
            match = re.match(r"^(.+?)-(.+?)\.dist-info$", item.name)
            if match:
                package_name = match.group(1).replace("_", "-")
                version = match.group(2)
                packages.append(f"{package_name}=={version}")
            else:
                print(f"Warning: Could not parse package info from {item.name}")

    # Also look for .whl files as backup
    for item in tools_dir.iterdir():
        if item.is_file() and item.name.endswith(".whl"):
            # Extract from wheel filename
            match = re.match(r"^(.+?)-(.+?)-", item.name)
            if match:
                package_name = match.group(1).replace("_", "-")
                version = match.group(2)
                package_spec = f"{package_name}=={version}"
                if package_spec not in packages:
                    packages.append(package_spec)

    return sorted(packages)


def main():
    """Main migration function"""

    print("=" * 60)
    print("Package Migration Tool")
    print("=" * 60)

    # Define source directories
    maya_repo = Path("L:/SagaTools/MayaRepository")
    unreal_repo = Path("L:/SagaTools/UnrealRepository")

    migrations = [
        (maya_repo / "2023" / "tools", "maya-2023", "Maya 2023"),
        (maya_repo / "2026" / "tools", "maya-2026", "Maya 2026"),
        (unreal_repo / "tools", "unreal", "Unreal Engine"),
    ]

    # Output directory for requirements
    output_dir = Path(__file__).parent / "requirements"
    output_dir.mkdir(exist_ok=True)

    print(f"\nMigrating packages to: {output_dir}")
    print("-" * 60)

    for tools_dir, env_name, display_name in migrations:
        print(f"\n{display_name}:")
        print(f"  Source: {tools_dir}")

        # Extract packages
        packages = extract_packages_from_tools_dir(tools_dir)

        if packages:
            print(f"  Found {len(packages)} packages:")
            for pkg in packages:
                print(f"    - {pkg}")

            # Write requirements file
            req_file = output_dir / f"{env_name}.txt"
            with open(req_file, "w") as f:
                f.write(f"# {display_name} Python Requirements\n")
                f.write(f"# Migrated from {tools_dir}\n\n")
                f.write("\n".join(packages))
                f.write("\n")

            print(f"  ✓ Written to: {req_file}")
        else:
            print("  No packages found")

    print("\n" + "=" * 60)
    print("Migration complete!")
    print("\nNext steps:")
    print("1. Review the generated requirements files")
    print("2. Add any missing packages that weren't detected")
    print("3. Run setup_environments.py to create the environments")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        import traceback

        traceback.print_exc()
