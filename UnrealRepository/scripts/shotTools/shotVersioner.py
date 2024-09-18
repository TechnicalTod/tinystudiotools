import unreal

# Function to get the version number from the asset name
def get_version_number(name):
    try:
        version_str = name.split('_')[-1]
        return int(version_str[1:])
    except (IndexError, ValueError) as e:
        unreal.log_error(f"Failed to extract version number from {name}: {e}")
        return None

# Function to update the version number in the asset name
def update_version_number(name, new_version):
    try:
        parts = name.split('_')
        parts[-1] = 'v{:03d}'.format(new_version)
        return '_'.join(parts)
    except Exception as e:
        unreal.log_error(f"Failed to update version number for {name}: {e}")
        return name

# Function to determine if an asset is a level
def is_level(asset):
    if asset is None:
        return False
    try:
        return asset.get_class().get_name() == 'World'
    except Exception as e:
        unreal.log_error(f"Error checking if asset is a level: {e}")
        return False

# Function to determine if an asset is a level sequence
def is_level_sequence(asset):
    if asset is None:
        return False
    try:
        return asset.get_class().get_name() == 'LevelSequence'
    except Exception as e:
        unreal.log_error(f"Error checking if asset is a level sequence: {e}")
        return False

def open_level_sequence(sequence_path):
    try:
        sequence = unreal.EditorAssetLibrary.load_asset(sequence_path)
        if sequence is not None:
            unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(sequence)
            unreal.log(f"Opened level sequence: {sequence_path}")
        else:
            unreal.log_error(f"Failed to load level sequence: {sequence_path}")
    except Exception as e:
        unreal.log_error(f"Failed to open level sequence {sequence_path}: {e}")

# Function: Get All Versions in the Base Folder
def get_all_versions(base_folder):
    try:
        all_assets = unreal.EditorAssetLibrary.list_assets(base_folder, recursive=True, include_folder=True)
        version_numbers = []

        for asset_path in all_assets:
            folder_name = asset_path.split('/')[-2]  # Get the parent folder name
            if folder_name.startswith('v') and folder_name[1:].isdigit():
                version_number = int(folder_name[1:])
                version_numbers.append(version_number)

        version_numbers_sorted = sorted(set(version_numbers))  # Ensure unique and sorted
        unreal.log_warning(f"All versions found: {version_numbers_sorted}")  # Debugging: Print all version numbers
        return version_numbers_sorted

    except Exception as e:
        unreal.log_error(f"Error getting all versions from {base_folder}: {e}")
        return []

# Function: Find the Next Version Number
def get_next_version_number(version_numbers):
    if not version_numbers:
        return 1  # Start at 1 if no versions exist

    highest_version = max(version_numbers)
    next_version = highest_version + 1
    unreal.log_warning(f"Next version to create: {next_version}")  # Debugging: Print next version
    return next_version

def version_and_fix_redirectors():
    def duplicate_and_move_assets():
        try:
            selected_assets = unreal.EditorUtilityLibrary.get_selected_assets()
            if len(selected_assets) != 2:
                unreal.log_error("Please select exactly one level and one level sequence.")
                return None, None

            first_asset_path = selected_assets[0].get_path_name()
            base_folder = '/'.join(first_asset_path.split('/')[:-2])

            # Get all existing versions
            version_numbers = get_all_versions(base_folder)

            # Find the next version number to create
            next_version_number = get_next_version_number(version_numbers)
            new_version_str = 'v{:03d}'.format(next_version_number)
            new_folder = f"{base_folder}/{new_version_str}"

            if not unreal.EditorAssetLibrary.make_directory(new_folder):
                unreal.log_error(f"Failed to create directory: {new_folder}")
                return None, None

            duplicated_level_path = None
            duplicated_sequence_path = None

            for asset in selected_assets:
                old_name = asset.get_name()
                new_name = update_version_number(old_name, next_version_number)
                new_asset_path = f"{new_folder}/{new_name}"
                new_asset = unreal.EditorAssetLibrary.duplicate_asset(asset.get_path_name(), new_asset_path)

                if new_asset is not None:
                    unreal.log(f"Duplicated {old_name} to {new_asset_path}")
                    if is_level(new_asset):
                        duplicated_level_path = new_asset_path
                    elif is_level_sequence(new_asset):
                        duplicated_sequence_path = new_asset_path
                else:
                    unreal.log_error(f"Failed to duplicate asset: {old_name}")

            unreal.log("Duplication and versioning complete.")
            return duplicated_level_path, duplicated_sequence_path, new_folder

        except Exception as e:
            unreal.log_error(f"Error during duplication and move: {e}")
            return None, None

    try:
        level, sequence, folder = duplicate_and_move_assets()
        if level and sequence:
            unreal.EditorLoadingAndSavingUtils.load_map(level)
            open_level_sequence(sequence)
            level_sequence_subsystem = unreal.get_editor_subsystem(unreal.LevelSequenceEditorSubsystem)
            if level_sequence_subsystem:
                level_sequence_subsystem.fix_actor_references()
                unreal.log("Fixed actor references successfully.")
            else:
                unreal.log_error("Failed to get LevelSequenceEditorSubsystem.")
            
            # Save the newly duplicated assets
            if unreal.EditorAssetLibrary.save_directory('/'.join(level.split('/')[:-1])):
                unreal.log(f"Successfully saved all assets in {folder}.")
            else:
                unreal.log_error(f"Failed to save assets in {folder}.")
        else:
            unreal.log_error("Level or sequence duplication failed. Process aborted.")
    except Exception as e:
        unreal.log_error(f"Error in version_and_fix_redirectors: {e}")
