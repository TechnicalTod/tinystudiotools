import mayaFilePaths

SHOWDRIVE = mayaFilePaths.showDir


def setdec_production_folder(show):
    return "{}/{}/03_Production/Assets/SETDEC".format(SHOWDRIVE, show)


def setdec_group_folder(show, group_name):
    return "{}/{}/03_Production/Assets/SETDEC/{}/".format(SHOWDRIVE, show, group_name)


def version_asset_root(show, group_name, asset_short_name, variant_name, version_name):
    return (
        setdec_group_folder(show, group_name)
        + asset_short_name
        + "/"
        + variant_name
        + "/"
        + version_name
        + "/"
    )
