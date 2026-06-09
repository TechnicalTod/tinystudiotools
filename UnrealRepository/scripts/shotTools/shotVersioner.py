import gc

import unreal

LEVEL_PREFIX = "PL_"
SEQUENCE_PREFIX = "LS_"
_TICKS_BETWEEN_STEPS = 30
_TICKS_BEFORE_LOAD_MAP = 60


def _is_version_token(token):
    return len(token) >= 2 and token[0].lower() == "v" and token[1:].isdigit()


def parse_version_token(token):
    if not _is_version_token(token):
        return None
    return int(token[1:])


def version_prefix_from_token(token):
    if not _is_version_token(token):
        return "V"
    return token[0]


def format_version_token(version_number, prefix="V"):
    return "{}{:03d}".format(prefix, version_number)


def resolve_version_prefix(level_asset):
    parent_folder = level_asset.get_path_name().split("/")[-2]
    if _is_version_token(parent_folder):
        return version_prefix_from_token(parent_folder)

    version_part = level_asset.get_name().split("_")[-1]
    return version_prefix_from_token(version_part)


def update_version_number(name, new_version, prefix="V"):
    try:
        parts = name.split("_")
        parts[-1] = format_version_token(new_version, prefix)
        return "_".join(parts)
    except Exception as e:
        unreal.log_error(f"Failed to update version number for {name}: {e}")
        return name


def is_level(asset):
    return asset is not None and asset.get_name().startswith(LEVEL_PREFIX)


def is_level_sequence(asset):
    return asset is not None and asset.get_name().startswith(SEQUENCE_PREFIX)


def version_folder_exists(base_folder, version_number):
    sub_paths = unreal.EditorAssetLibrary.list_assets(
        base_folder, recursive=False, include_folder=True
    )
    for asset_path in sub_paths:
        folder_name = asset_path.rstrip("/").split("/")[-1]
        if parse_version_token(folder_name) == version_number:
            return True
    return False


def get_all_versions(base_folder):
    try:
        sub_paths = unreal.EditorAssetLibrary.list_assets(
            base_folder, recursive=False, include_folder=True
        )
        version_numbers = []

        for asset_path in sub_paths:
            folder_name = asset_path.rstrip("/").split("/")[-1]
            version_number = parse_version_token(folder_name)
            if version_number is not None:
                version_numbers.append(version_number)

        version_numbers_sorted = sorted(set(version_numbers))
        unreal.log_warning(f"All versions found: {version_numbers_sorted}")
        return version_numbers_sorted

    except Exception as e:
        unreal.log_error(f"Error getting all versions from {base_folder}: {e}")
        return []


def get_next_version_number(version_numbers):
    if not version_numbers:
        return 1

    next_version = max(version_numbers) + 1
    unreal.log_warning(f"Next version to create: {next_version}")
    return next_version


def _prepare_version_plan():
    selected_assets = unreal.EditorUtilityLibrary.get_selected_assets()
    levels = [asset for asset in selected_assets if is_level(asset)]
    sequences = [asset for asset in selected_assets if is_level_sequence(asset)]

    if len(levels) != 1 or len(sequences) != 1:
        unreal.log_error(
            "Please select exactly one level (PL_*) and one level sequence (LS_*)."
        )
        return None

    level_asset = levels[0]
    sequence_asset = sequences[0]
    base_folder = "/".join(level_asset.get_path_name().split("/")[:-2])
    version_prefix = resolve_version_prefix(level_asset)

    version_numbers = get_all_versions(base_folder)
    for asset in (level_asset, sequence_asset):
        parent_folder = asset.get_path_name().split("/")[-2]
        source_version = parse_version_token(parent_folder)
        if source_version is not None and source_version not in version_numbers:
            version_numbers.append(source_version)

    next_version_number = get_next_version_number(version_numbers)
    new_folder = "{}/{}".format(
        base_folder, format_version_token(next_version_number, version_prefix)
    )

    if version_folder_exists(base_folder, next_version_number):
        unreal.log_error(
            "Version folder already exists for version {}: {}".format(
                next_version_number, new_folder
            )
        )
        return None

    return {
        "level_source_path": level_asset.get_path_name(),
        "sequence_source_path": sequence_asset.get_path_name(),
        "level_source_name": level_asset.get_name(),
        "sequence_source_name": sequence_asset.get_name(),
        "new_folder": new_folder,
        "next_version_number": next_version_number,
        "version_prefix": version_prefix,
        "level_dest_path": "{}/{}".format(
            new_folder,
            update_version_number(
                level_asset.get_name(), next_version_number, version_prefix
            ),
        ),
        "sequence_dest_path": "{}/{}".format(
            new_folder,
            update_version_number(
                sequence_asset.get_name(), next_version_number, version_prefix
            ),
        ),
    }


def _force_garbage_collection():
    editor_subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = editor_subsystem.get_editor_world()
    if world is not None:
        unreal.SystemLibrary.execute_console_command(world, "obj gc", None)
    gc.collect()


def _duplicate_asset(source_path, dest_path):
    duplicated_asset = unreal.EditorAssetLibrary.duplicate_asset(source_path, dest_path)
    if duplicated_asset is None:
        return False

    del duplicated_asset
    return True


def _duplicate_level(source_path, dest_path):
    duplicated_level = unreal.EditorAssetLibrary.duplicate_asset(source_path, dest_path)
    if duplicated_level is None:
        return False

    if not unreal.EditorLoadingAndSavingUtils.save_map(duplicated_level, dest_path):
        unreal.log_error("Shot Versioner: failed to save duplicated level {}".format(dest_path))
        del duplicated_level
        return False

    del duplicated_level
    return True


def _save_and_unload_assets(asset_paths, folder_path):
    if not unreal.EditorAssetLibrary.save_directory(
        folder_path, only_if_is_dirty=False, recursive=False
    ):
        unreal.log_error(
            "Shot Versioner: failed to save duplicated assets in {}".format(folder_path)
        )
        return False

    packages = []
    for asset_path in asset_paths:
        package = unreal.load_package(asset_path)
        if package is not None:
            packages.append(package)
            continue

        asset = unreal.EditorAssetLibrary.load_asset(asset_path)
        if asset is None:
            unreal.log_warning(
                "Shot Versioner: could not resolve package for {}".format(asset_path)
            )
            continue

        package = unreal.EditorAssetLibrary.get_package_for_object(asset)
        del asset
        if package is not None:
            packages.append(package)

    if not packages:
        unreal.log_warning(
            "Shot Versioner: no loaded packages to unload for {}".format(asset_paths)
        )
        return False

    unloaded, error_message = unreal.EditorLoadingAndSavingUtils.unload_packages(packages)
    for package in packages:
        del package

    if error_message:
        unreal.log_error("Shot Versioner: unload packages: {}".format(error_message))
    if not unloaded:
        unreal.log_error("Shot Versioner: failed to unload duplicated asset packages.")
    return unloaded


def _ticks_for_step(step):
    if step == 6:
        return _TICKS_BEFORE_LOAD_MAP
    return _TICKS_BETWEEN_STEPS


def _stop_deferred(state, error_message=None):
    if error_message:
        unreal.log_error(error_message)

    handle = state.get("handle")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        state["handle"] = None


def _run_deferred_versioning(plan):
    state = {
        "plan": plan,
        "step": 0,
        "frames": 0,
        "handle": None,
        "level_dest_path": None,
        "sequence_dest_path": None,
    }

    def _advance_step(next_step, message):
        unreal.log(message)
        state["step"] = next_step
        state["frames"] = 0

    def _tick(_delta_time):
        state["frames"] += 1
        if state["frames"] < _ticks_for_step(state["step"]):
            return

        state["frames"] = 0
        current_plan = state["plan"]

        try:
            if state["step"] == 0:
                _advance_step(1, "Shot Versioner: saving dirty packages")
                unreal.EditorLoadingAndSavingUtils.save_dirty_packages(False, True)
                return

            if state["step"] == 1:
                if not unreal.EditorAssetLibrary.make_directory(current_plan["new_folder"]):
                    _stop_deferred(
                        state,
                        "Failed to create directory: {}".format(current_plan["new_folder"]),
                    )
                    return
                _advance_step(2, "Shot Versioner: duplicating level sequence")
                return

            if state["step"] == 2:
                if not _duplicate_asset(
                    current_plan["sequence_source_path"],
                    current_plan["sequence_dest_path"],
                ):
                    _stop_deferred(
                        state,
                        "Failed to duplicate sequence: {}".format(
                            current_plan["sequence_source_name"]
                        ),
                    )
                    return

                state["sequence_dest_path"] = current_plan["sequence_dest_path"]
                unreal.log(
                    "Duplicated {} to {}".format(
                        current_plan["sequence_source_name"],
                        current_plan["sequence_dest_path"],
                    )
                )
                _advance_step(3, "Shot Versioner: duplicating level")
                return

            if state["step"] == 3:
                if not _duplicate_level(
                    current_plan["level_source_path"],
                    current_plan["level_dest_path"],
                ):
                    _stop_deferred(
                        state,
                        "Failed to duplicate level: {}".format(
                            current_plan["level_source_name"]
                        ),
                    )
                    return

                state["level_dest_path"] = current_plan["level_dest_path"]
                unreal.log(
                    "Duplicated {} to {}".format(
                        current_plan["level_source_name"],
                        current_plan["level_dest_path"],
                    )
                )
                _advance_step(
                    4, "Shot Versioner: saving duplicated assets before unload"
                )
                return

            if state["step"] == 4:
                asset_paths = [
                    current_plan["level_dest_path"],
                    current_plan["sequence_dest_path"],
                ]
                if not _save_and_unload_assets(asset_paths, current_plan["new_folder"]):
                    _stop_deferred(
                        state,
                        "Shot Versioner: could not save and unload duplicated assets.",
                    )
                    return

                _force_garbage_collection()
                _advance_step(5, "Shot Versioner: preparing to load versioned level")
                return

            if state["step"] == 5:
                _force_garbage_collection()
                _advance_step(6, "Shot Versioner: loading versioned level")
                return

            if state["step"] == 6:
                unreal.EditorLoadingAndSavingUtils.load_map(state["level_dest_path"])
                _advance_step(7, "Shot Versioner: opening versioned level sequence")
                return

            if state["step"] == 7:
                sequence = unreal.load_asset(state["sequence_dest_path"])
                if sequence is None:
                    _stop_deferred(
                        state,
                        "Failed to load level sequence: {}".format(
                            state["sequence_dest_path"]
                        ),
                    )
                    return

                unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(sequence)
                unreal.LevelSequenceEditorBlueprintLibrary.refresh_current_level_sequence()
                _advance_step(8, "Shot Versioner: fixing actor references")
                return

            if state["step"] == 8:
                level_sequence_subsystem = unreal.get_editor_subsystem(
                    unreal.LevelSequenceEditorSubsystem
                )
                if level_sequence_subsystem is None:
                    _stop_deferred(
                        state, "Failed to get LevelSequenceEditorSubsystem."
                    )
                    return

                level_sequence_subsystem.fix_actor_references()
                unreal.log("Fixed actor references successfully.")
                _advance_step(9, "Shot Versioner: saving versioned assets")
                return

            if state["step"] == 9:
                if unreal.EditorAssetLibrary.save_directory(current_plan["new_folder"]):
                    unreal.log(
                        "Successfully saved all assets in {}.".format(
                            current_plan["new_folder"]
                        )
                    )
                else:
                    unreal.log_error(
                        "Failed to save assets in {}.".format(current_plan["new_folder"])
                    )

                unreal.log("Shot versioning complete.")
                _stop_deferred(state)

        except Exception as e:
            _stop_deferred(
                state,
                "Shot Versioner failed at step {}: {}".format(state["step"], e),
            )

    state["handle"] = unreal.register_slate_post_tick_callback(_tick)


def version_and_fix_redirectors():
    try:
        plan = _prepare_version_plan()
        if plan is None:
            return

        unreal.log("Shot Versioner: scheduling deferred versioning workflow")
        _run_deferred_versioning(plan)
    except Exception as e:
        unreal.log_error(f"Error in version_and_fix_redirectors: {e}")


def schedule_version_and_fix_redirectors():
    tick_handle = None

    def _start(_delta_time):
        nonlocal tick_handle
        if tick_handle is not None:
            unreal.unregister_slate_post_tick_callback(tick_handle)
            tick_handle = None
        version_and_fix_redirectors()

    tick_handle = unreal.register_slate_post_tick_callback(_start)
