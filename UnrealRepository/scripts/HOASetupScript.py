import unreal

# Constructing the directory and asset paths in Unreal's format
PathList = ("/Game/01_Assets/CHR",
            "/Game/01_Assets/CRE",
            "/Game/01_Assets/ENV",
            "/Game/01_Assets/FX",
            "/Game/01_Assets/PROP",
            "/Game/01_Assets/SETDEC",
            "/Game/01_Assets/VEH",
            "/Game/02_Episodes")

# Create the directory if it doesn't exist
for path in PathList:
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)