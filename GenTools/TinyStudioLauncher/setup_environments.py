"""
Setup script for TinyStudioLauncher environments

This script creates and configures all necessary virtual environments.
Run this after initial installation or to reset environments.
"""

import sys
from pathlib import Path

# Project root on path so `src` is a package (needed for relative imports inside src/)
_root = Path(__file__).resolve().parent
sys.path.insert(0, str(_root))

from src.environment_manager import EnvironmentManager


def main():
    """Set up all environments for TinyStudioLauncher"""

    print("=" * 60)
    print("TinyStudioLauncher Environment Setup")
    print("=" * 60)

    # Initialize environment manager
    base_path = Path(__file__).parent
    manager = EnvironmentManager(base_path)

    # Define environments to create
    environments = [
        ("maya-2026", "3.10", "Maya 2026"),
        ("unreal-5.6", "3.10", "Unreal Engine 5.6"),
        ("ae-2024", "3.10", "After Effects 2024"),
    ]

    print(f"\nSetting up environments in: {manager.environments_dir}")
    print("-" * 60)

    # Create each environment
    for env_name, python_version, display_name in environments:
        print(f"\n{display_name}:")
        print(f"  Environment: {env_name}")
        print(f"  Python: {python_version}")

        # Check if environment already exists
        env_info = manager.get_environment_info(env_name)
        if env_info["exists"]:
            response = input(f"  Environment already exists. Recreate? (y/N): ")
            if response.lower() != "y":
                print("  Skipping...")
                continue

            # Remove existing environment
            manager.remove_environment(env_name)

        # Create environment
        print(f"  Creating environment...")
        if manager.create_environment(env_name, python_version):
            print(f"  ✓ Environment created")

            # Sync packages from requirements
            print(f"  Syncing packages...")
            if manager.sync_environment(env_name):
                print(f"  ✓ Packages synced")
            else:
                print(f"  ⚠ Package sync failed (check requirements/{env_name}.txt)")

            # Check health
            healthy, msg = manager.check_environment_health(env_name)
            if healthy:
                print(f"  ✓ Health check passed")
            else:
                print(f"  ✗ Health check failed: {msg}")
        else:
            print(f"  ✗ Failed to create environment")

    # Summary
    print("\n" + "=" * 60)
    print("Setup Summary:")
    print("-" * 60)

    envs = manager.list_environments()
    if envs:
        print(f"Successfully created {len(envs)} environments:")
        for env in envs:
            print(f"  - {env['name']} (Python {env.get('python_version', 'unknown')})")
    else:
        print("No environments were created.")

    print("\n✓ Setup complete!")
    print("\nNext steps:")
    print("1. Install any additional packages needed for your pipeline")
    print("2. Run the launcher with: python launcher.py")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Setup failed with error: {e}")
        sys.exit(1)
