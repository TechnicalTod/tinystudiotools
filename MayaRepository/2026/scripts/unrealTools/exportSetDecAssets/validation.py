import pymel.core as pm


def transform_short_name(transform_dag_path):
    node = pm.PyNode(transform_dag_path)
    return node.nodeName().split("|")[-1]


def has_usd_preview_material(shape_node):
    shading_engines = shape_node.shadingGroups()
    if not shading_engines:
        return False

    for shading_engine in shading_engines:
        materials = shading_engine.surfaceShader.inputs()
        for material in materials:
            if material.type() == "usdPreviewSurface":
                return True
            else:
                return False
    return False


def duplicate_short_names(transform_dag_paths):
    short_names = []
    for dag_path in transform_dag_paths:
        short_names.append(transform_short_name(dag_path))
    return {name for name in short_names if short_names.count(name) > 1}


def published_short_names(transform_dag_paths):
    published = []
    for dag_path in transform_dag_paths:
        obj = pm.PyNode(dag_path)
        try:
            if obj.published.get():
                published.append(transform_short_name(dag_path))
        except Exception:
            pass
    return published


def invalid_shader_short_names(transform_dag_paths):
    bad = []
    for dag_path in transform_dag_paths:
        obj = pm.PyNode(dag_path)
        shape = obj.getShape()
        if not has_usd_preview_material(shape):
            bad.append(transform_short_name(dag_path))
    return bad
