import os

import unreal
from genTools.genUnrealUtils import warningPopup

_INTERCHANGE_FBX_CVAR = "Interchange.FeatureFlags.Import.FBX"


def _normalize_disk_path(path: str) -> str:
    try:
        from genTools.studio_python_path import ensure_gen_tools_shared

        ensure_gen_tools_shared()
        from studioShowPaths import normalize_disk_path

        return normalize_disk_path(path)
    except Exception:
        path = (path or "").replace("\\", "/")
        if (
            len(path) >= 2
            and path[1] == ":"
            and (len(path) == 2 or path[2] not in "/\\")
        ):
            path = path[:2] + "/" + path[2:]
        return path


def _task_uses_legacy_fbx_options(task) -> bool:
    options = task.get_editor_property("options")
    return isinstance(options, unreal.FbxImportUI)


def _task_is_fbx_file(task) -> bool:
    filename = task.get_editor_property("filename") or ""
    return filename.replace("\\", "/").lower().endswith(".fbx")


def _read_interchange_fbx_enabled():
    """Best-effort read; returns None when this UE build exposes no Python cvar API."""
    try:
        console_manager = getattr(unreal, "IConsoleManager", None)
        if console_manager is not None:
            cvar = console_manager.get().find_console_variable(_INTERCHANGE_FBX_CVAR)
            if cvar is not None:
                return cvar.get_bool()
    except Exception:
        pass

    get_bool = getattr(unreal.SystemLibrary, "get_console_variable_bool_value", None)
    if get_bool is not None:
        try:
            return get_bool(_INTERCHANGE_FBX_CVAR)
        except Exception:
            pass

    return None


def _set_interchange_fbx_enabled(enabled: bool) -> None:
    editor_subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = editor_subsystem.get_editor_world()
    value = "true" if enabled else "false"
    unreal.SystemLibrary.execute_console_command(
        world,
        "{} {}".format(_INTERCHANGE_FBX_CVAR, value),
    )


#Function to set generic asset import options using unreal.AssetImportTask()
#The additional import options are then fed into this using the options property
def buildImportTask(filename='', destination_path='', options=None):
    task = unreal.AssetImportTask()
    task.set_editor_property('automated', True)
    filename = _normalize_disk_path(filename)
    destination_name = ''
    if filename:
        destination_name = os.path.splitext(os.path.basename(filename.replace("\\", "/")))[0]
    task.set_editor_property('destination_name', destination_name)
    task.set_editor_property('destination_path', destination_path)
    task.set_editor_property('filename', filename)
    task.set_editor_property('replace_existing', True)
    task.set_editor_property('replace_existing_settings', True)
    task.set_editor_property('save', True)
    task.set_editor_property('options', options)
    if isinstance(options, unreal.FbxImportUI) and hasattr(unreal, "FbxFactory"):
        task.set_editor_property('factory', unreal.FbxFactory())
    return task

#Function to execute built task
def executeImportTasks(tasks=[]):
    use_legacy_fbx = any(
        _task_is_fbx_file(task) and _task_uses_legacy_fbx_options(task) for task in tasks
    )
    previous_interchange_fbx = _read_interchange_fbx_enabled() if use_legacy_fbx else None
    if use_legacy_fbx:
        _set_interchange_fbx_enabled(False)

    try:
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    finally:
        if use_legacy_fbx and previous_interchange_fbx is not None:
            _set_interchange_fbx_enabled(previous_interchange_fbx)

    imported_asset_paths = []
    for task in tasks:
        imported_asset_paths.extend(_collect_import_task_paths(task))
    return imported_asset_paths


def _collect_import_task_paths(task) -> list[str]:
    paths: list[str] = []
    get_objects = getattr(task, "get_objects", None)
    if get_objects is not None:
        try:
            for obj in get_objects() or []:
                if obj is None:
                    continue
                path_name = obj.get_path_name()
                if path_name and path_name not in paths:
                    paths.append(path_name)
        except Exception:
            pass

    for path in task.get_editor_property("imported_object_paths") or []:
        if path and path not in paths:
            paths.append(path)
    return paths


def resolve_static_mesh_object_path(task, destination_path: str) -> str:
    """Return a loadable object path for the StaticMesh created by one import task."""
    destination_path = (destination_path or "").rstrip("/")
    imported_paths = _collect_import_task_paths(task)

    for path in imported_paths:
        object_path = path.rsplit(".", 1)[0] if "." in path else path
        for candidate in (path, object_path):
            if not candidate:
                continue
            asset = unreal.EditorAssetLibrary.load_asset(candidate)
            if isinstance(asset, unreal.StaticMesh):
                return candidate

    destination_name = task.get_editor_property("destination_name") or ""
    if destination_name:
        expected = "{}/{}".format(destination_path, destination_name)
        if unreal.EditorAssetLibrary.does_asset_exist(expected):
            asset = unreal.EditorAssetLibrary.load_asset(expected)
            if isinstance(asset, unreal.StaticMesh):
                return expected

    if destination_path:
        for asset_path in unreal.EditorAssetLibrary.list_assets(
            destination_path,
            recursive=True,
        ):
            asset = unreal.EditorAssetLibrary.load_asset(asset_path)
            if isinstance(asset, unreal.StaticMesh):
                return asset_path

    imported_summary = []
    for path in imported_paths:
        object_path = path.rsplit(".", 1)[0] if "." in path else path
        asset = unreal.EditorAssetLibrary.load_asset(object_path)
        asset_type = type(asset).__name__ if asset is not None else "None"
        imported_summary.append("{} ({})".format(path, asset_type))

    filename = task.get_editor_property("filename") or destination_path
    raise RuntimeError(
        "Could not find imported static mesh asset for {}. Imported: {}".format(
            filename,
            ", ".join(imported_summary) if imported_summary else "none",
        )
    )


#Function to build Static mesh import options
def buildStaticMeshImportOptions():
    options = unreal.FbxImportUI()

    options.set_editor_property('import_mesh', True)
    options.set_editor_property('import_animations', False)
    options.set_editor_property('import_textures', False)
    options.set_editor_property('import_materials', False)
    options.set_editor_property('import_as_skeletal', False)  # Static Mesh

    fbx_import_type = getattr(unreal, "FBXImportType", None)
    if fbx_import_type is not None:
        static_mesh_type = getattr(fbx_import_type, "FBXIT_STATIC_MESH", None)
        if static_mesh_type is not None:
            options.set_editor_property('automated_import_should_detect_type', False)
            options.set_editor_property('mesh_type_to_import', static_mesh_type)

    options.static_mesh_import_data.set_editor_property('import_translation', unreal.Vector(0.0, 0.0, 0.0))
    options.static_mesh_import_data.set_editor_property('import_rotation', unreal.Rotator(0.0, 0.0, 0.0))
    options.static_mesh_import_data.set_editor_property('import_uniform_scale', 1.0)
    options.static_mesh_import_data.set_editor_property('combine_meshes', True)
    options.static_mesh_import_data.set_editor_property('generate_lightmap_u_vs', True)
    options.static_mesh_import_data.set_editor_property('auto_generate_collision', True)
    return options

#Function to build Skeletal mesh import options
def buildSkeletalMeshImportOptions():
    options = unreal.FbxImportUI()

    options.set_editor_property('import_mesh', True)
    options.set_editor_property('import_textures', False)
    options.set_editor_property('import_materials', False)
    options.set_editor_property('import_as_skeletal', True)  # Skeletal Mesh

    options.skeletal_mesh_import_data.set_editor_property('import_translation', unreal.Vector(0.0, 0.0, 0.0))
    options.skeletal_mesh_import_data.set_editor_property('import_rotation', unreal.Rotator(0.0, 0.0, 0.0))
    options.skeletal_mesh_import_data.set_editor_property('import_uniform_scale', 1.0)
    options.skeletal_mesh_import_data.set_editor_property('import_morph_targets', True)
    options.skeletal_mesh_import_data.set_editor_property('update_skeleton_reference_pose', False)
    return options

#Function to build animation import options
def buildAnimationImportOptions(skeleton_path=''):
    options = unreal.FbxImportUI()
    # unreal.FbxImportUI
    options.set_editor_property('import_animations', True)
    options.skeleton = unreal.load_asset(skeleton_path)
    # unreal.FbxMeshImportData
    options.anim_sequence_import_data.set_editor_property('import_translation', unreal.Vector(0.0, 0.0, 0.0))
    options.anim_sequence_import_data.set_editor_property('import_rotation', unreal.Rotator(0.0, 0.0, 0.0))
    options.anim_sequence_import_data.set_editor_property('import_uniform_scale', 1.0)
    # unreal.FbxAnimSequenceImportData
    options.anim_sequence_import_data.set_editor_property('animation_length', unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME)
    options.anim_sequence_import_data.set_editor_property('remove_redundant_keys', False)
    return options

#Function to build USD import options
def buildUSDImportOptions():
    options = unreal.UsdStageImportOptions()
    
    options.set_editor_property('import_geometry', True)
    options.set_editor_property('import_skeletal_animations', False)
    options.set_editor_property('import_level_sequences', False)
    options.set_editor_property('import_materials', True)
    return options


def buildGeometryCacheImportOptions():
    options = unreal.AbcImportSettings()
    options.set_editor_property(
        "import_type",
        unreal.AlembicImportType.GEOMETRY_CACHE,
    )
    sampling = options.get_editor_property("sampling_settings")
    if sampling is not None:
        sampling.set_editor_property("frame_start", 0)
    return options


def buildAbcImportTask(filename='', destination_path='', options=None):
    return buildImportTask(filename=filename, destination_path=destination_path, options=options)