import json
import os
import unreal
import sys
import subprocess
from PySide2 import QtGui, QtWidgets, QtCore

from importlib import reload
import unrealFilePaths
reload(unrealFilePaths)
import genTools.genUnrealImportUtils as genUnrealImportUtils
reload(genUnrealImportUtils)

class MainWindow(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.initUI()

    def initUI(self):
        # window prefs
        with open("{}/dark.qss".format(unrealFilePaths.UNREAL_styleSheetFilepath), "r") as fh:
            self.setStyleSheet(fh.read())
        self.resize(600, 50)
        self.setWindowTitle('Import published Shot')
        self.setFocus()
        self.center()
        self.show()

        # text field widget
        self.jsonFilePath = QtWidgets.QLineEdit(self)
        self.jsonFilePath.setPlaceholderText("File path")

        # button widget
        self.importJsonButton = QtWidgets.QPushButton('Import Shot from Scene Description', self)
        self.importJsonButton.clicked.connect(self.importShot)

        openFolderIconFilepath = unrealFilePaths.UNREAL_openFolderIconFilepath
        self.browseButton = QtWidgets.QPushButton()
        self.browseButton.setIcon(QtGui.QIcon(openFolderIconFilepath))
        self.browseButton.clicked.connect(self.showFileDialog)

        self.importMediaPlateCheckbox = QtWidgets.QCheckBox("Import Media Plate", self)

        # layout
        self.grid = QtWidgets.QGridLayout()
        self.grid.setSpacing(10)

        # add widgets to layout
        self.grid.addWidget(self.jsonFilePath, 0, 0, 1, 3)
        self.grid.addWidget(self.browseButton, 0, 3, 1, 1)
        self.grid.addWidget(self.importJsonButton, 1, 0, 1, 4)
        self.grid.addWidget(self.importMediaPlateCheckbox, 2, 0, 1, 4)
        self.setLayout(self.grid)

    def showFileDialog(self):
        initialDir = unrealFilePaths.UNREAL_downloadsFolder
        options = QtWidgets.QFileDialog.Options()
        fileFilter = "Json Files (*.json);;All Files (*)"
        filePath, _ = QtWidgets.QFileDialog.getOpenFileName(self,
                                                "Open Json File",
                                                initialDir,
                                                fileFilter,
                                                options=options)
        if filePath:
            # Set the selected file path in the QLineEdit
            self.jsonFilePath.setText(filePath)

    # definition that sets UI to be created in center (used in window prefs)
    def center(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def importShot(self):
        jsonPath = self.jsonFilePath.text()
        with open(jsonPath, 'r') as file:
            shotSceneDescription = json.load(file)

        shotInfoDict = shotSceneDescription[2]["Shot Info"]
        dirPath, levelAssetPath, sequenceAssetPath, startFrame, endFrame = self.createShotFolders(shotInfoDict)

        try:
            cameraDict = shotSceneDescription[0]["Cameras"]
            self.importCameras(dirPath, cameraDict, sequenceAssetPath, startFrame, endFrame)
        except:
            print ("No cameras found in published json")
            pass

        try:
            puppetDict = shotSceneDescription[1]["Puppets"]
            self.importPuppets(dirPath, puppetDict, sequenceAssetPath, startFrame, endFrame)
        except:
            print ("No puppets found in published json")
            pass

        self.saveAssets([levelAssetPath, sequenceAssetPath])

    def createShotFolders(self, shotInfoDict):
        #Unpack Shot Data
        for shotInfo in shotInfoDict:
            for info, attrs in shotInfo.items():
                if "Shot Number" in info:
                    episode = attrs[0].split("_")[0]
                    seq = "{}_{}".format(attrs[0].split("_")[0], attrs[0].split("_")[1])
                    shot = attrs[0]
                if "Version" in info:
                    versionNumber = attrs[0]
                if "Timeline" in info:
                    startFrame = attrs[0].get('Start Frame')
                    endFrame = attrs[0].get('End Frame') + 1
                if "FPS" in info:
                    fpsVal = attrs[0]

        # Constructing the directory and asset paths in Unreal's format
        basePath = "/Game/02_Episodes"
        dirPath = "{}/{}/{}/{}/{}".format(basePath, episode, seq, shot, versionNumber)

        # Create the directory if it doesn't exist
        if not unreal.EditorAssetLibrary.does_directory_exist(dirPath):
            unreal.EditorAssetLibrary.make_directory(dirPath)

        # Create the "Animation" folder within the same directory
        animationFolderPath = "{}/Animation".format(dirPath)
        if not unreal.EditorAssetLibrary.does_directory_exist(animationFolderPath):
            unreal.EditorAssetLibrary.make_directory(animationFolderPath)
        
        # Create the "Animation" folder within the same directory
        mediaFolderPath = "{}/Media".format(dirPath)
        if not unreal.EditorAssetLibrary.does_directory_exist(mediaFolderPath):
            unreal.EditorAssetLibrary.make_directory(mediaFolderPath)

        # Construct asset names
        baseAssetName = "{}_{}".format(shot, versionNumber)
        levelName = "PL_{}".format(baseAssetName)
        sequenceName = "LS_{}".format(baseAssetName)

        # Create a new level
        levelAssetPath = "{}/{}".format(dirPath, levelName)
        if not unreal.EditorAssetLibrary.does_asset_exist(levelAssetPath + ".umap"):
            levelLibrary = unreal.EditorLevelLibrary()
            success = levelLibrary.new_level(levelAssetPath)
            if success:
                print(f"New level created: {levelAssetPath}.umap")
            else:
                print("Failed to create new level.")

        # Creating a level sequence and folders inside the LS
        sequenceAssetPath = "{}/{}".format(dirPath, sequenceName)
        if not unreal.EditorAssetLibrary.does_asset_exist(sequenceAssetPath + ".uasset"):
            assetTools = unreal.AssetToolsHelpers.get_asset_tools()
            factory = unreal.LevelSequenceFactoryNew()
            sequenceAsset = assetTools.create_asset(sequenceName, dirPath, None, factory)
            if sequenceAsset:
                print("Level Sequence created: {}.uasset".format(sequenceAssetPath))
            else:
                print("Failed to create Level Sequence.")

        #update level sequence data
        #load and open sequence
        loadedLevelSequence = unreal.load_asset(sequenceAssetPath)
        unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(loadedLevelSequence)

        newFrameRate = unreal.FrameRate()
        fpsVal = round(fpsVal, 3)

        # Set the numerator and denominator
        newFrameRate.numerator = int(fpsVal * 1000)
        newFrameRate.denominator = 1000
        if fpsVal == 23.976:
            newFrameRate.numerator = int(24.0 * 1000)
            newFrameRate.denominator = 1001


        loadedLevelSequence.set_display_rate(newFrameRate)
        #set current frame
        unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(float(startFrame))
        #set playback start/end
        loadedLevelSequence.set_playback_start(float(startFrame))
        loadedLevelSequence.set_playback_end(float(endFrame))
        loadedLevelSequence.set_view_range_start(float(startFrame - 0) / float(fpsVal))
        loadedLevelSequence.set_view_range_end(float(endFrame + 9) / float(fpsVal))
        loadedLevelSequence.set_work_range_start(float(startFrame - 10) / float(fpsVal))
        loadedLevelSequence.set_work_range_end(float(endFrame + 9) / float(fpsVal))

        print("Folder structure and assets created under: {}".format(dirPath))

        return dirPath, levelAssetPath, sequenceAssetPath, startFrame, endFrame

    def importCameras(self, dirPath,  cameraDict, sequenceAssetPath, startFrame, endFrame):
        # Specify the path to the Level Sequence asset
        sequence_asset_path = sequenceAssetPath
        # Load the Level Sequence asset
        loaded_level_sequence = unreal.load_asset(sequenceAssetPath)
        # Open the Level Sequence in the editor
        unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(loaded_level_sequence)
        #create Cam Folder
        camFolderName = "CAM"
        camFolder = unreal.MovieSceneSequenceExtensions.add_root_folder_to_sequence(loaded_level_sequence, camFolderName)

        #Unpack Camera Data
        for cameraInfo in cameraDict:
            for camera, attrs in cameraInfo.items():
                cameraFbxPath = attrs[0].get('Export Path')
                SensorWidth = attrs[0].get('horizontalFilmAperture')
                SensorHeight = attrs[0].get('verticalFilmAperture')
                ImagePlate = attrs[0].get('ImagePlate')

                # Spawn a Cine Camera Actor in the level
                cine_camera = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.CineCameraActor, unreal.Vector(0,0,0))
                cine_camera.set_folder_path("CAM")
                # Set a label for the camera actor
                cine_camera.set_actor_label(camera + '_UECam')

                # Add the camera as a possessable to the Level Sequence
                possessableActor = loaded_level_sequence.add_possessable(cine_camera)
                # Create a binding ID for the camera using the GUID directly from the binding
                binding_id = unreal.MovieSceneObjectBindingID()
                binding_id.set_editor_property('guid', possessableActor.get_id())  # Using get_id() method to retrieve the GUID
                # Add a Camera Cut Track to the Level Sequence
                track = loaded_level_sequence.add_track(unreal.MovieSceneCameraCutTrack)
                # Add a new section to the Camera Cut Track
                section = track.add_section()
                # Set the range for the camera section
                section.set_range(startFrame, endFrame)

                importSetting = unreal.MovieSceneUserImportFBXSettings()
                importSetting.set_editor_property('match_by_name_only', False)
                importSetting.set_editor_property('force_front_x_axis', False)
                importSetting.set_editor_property('create_cameras', False)
                importSetting.set_editor_property('reduce_keys', False)
                importSetting.set_editor_property('reduce_keys_tolerance', 0.001)
                world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
                cam = unreal.SequencerTools.import_level_sequence_fbx(world, loaded_level_sequence, [possessableActor], importSetting, cameraFbxPath)

                #get camera Component and adjust settings
                filmback_settings = unreal.CameraFilmbackSettings(sensor_width=SensorWidth, sensor_height=SensorHeight)
                camera_component = cine_camera.get_cine_camera_component()
                camera_component.set_editor_property('filmback', filmback_settings)

                #add cameras to the CAM folder
                camFolder.add_child_object_binding(possessableActor)
                if self.importMediaPlateCheckbox.isChecked():
                    self.importImagePlate(dirPath, ImagePlate, camera_component)
                    print ("Camera imported into sequencer: {}".format(camera))
                print ("From import path: {}".format(cameraFbxPath))

        # Assign the last imported camera to the track section via the binding ID
        section.set_camera_binding_id(binding_id)

    def create_img_source(self, asset_name, asset_path, sequence_path):
        # Get the Asset Tools to handle asset creation
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

        # Specify the class for the asset (Img Media Source)
        img_media_source_class = unreal.ImgMediaSource

        # Create the new asset in the specified location
        img_media_source_asset = asset_tools.create_asset(
            asset_name,
            asset_path,
            img_media_source_class,
            None  # No factory needed for this specific asset type
        )
        
        if img_media_source_asset:
            # Create a DirectoryPath struct and set the sequence path
            directory_path = unreal.DirectoryPath(path=sequence_path)
            img_media_source_asset.set_editor_property("sequence_path", directory_path)
            
            # Save the asset
            full_asset_path = f"{asset_path}/{asset_name}"
            unreal.EditorAssetLibrary.save_asset(full_asset_path)
            
            print(f"Successfully created Img Media Source asset: {asset_name} at path: {full_asset_path}")
            return img_media_source_asset
        else:
            print(f"Failed to create Img Media Source asset: {asset_name} at path: {asset_path}")
            return None

    def create_in_memory_media_playlist(self, img_media_source):
        try:
            # Create a new MediaPlaylist instance in memory
            new_media_playlist = unreal.MediaPlaylist()

            # Add the media source to the new playlist
            if new_media_playlist:
                new_media_playlist.add(img_media_source)
                print("Successfully created in-memory MediaPlaylist.")
                return new_media_playlist
            else:
                print("Failed to create the in-memory MediaPlaylist instance.")
                return None
        except Exception as e:
            print(f"Failed to create in-memory MediaPlaylist: {e}")
            return None

    def add_media_plate_plus_to_level(self, img_media_source_path, media_plate_blueprint_path, camera_actor):
        # Load the MediaPlatePlus Blueprint Generated Class (BPGC)
        media_plate_gc = unreal.EditorAssetLibrary.load_blueprint_class(media_plate_blueprint_path)
        if not media_plate_gc:
            print(f"Failed to load Generated Class from MediaPlatePlus Blueprint at: {media_plate_blueprint_path}")
            return
        
        # Load the CineCameraActor
        #camera_actor = unreal.load_object(None, camera_actor_path)
        if not camera_actor:
            print(f"Failed to load camera actor")
            return

        # Get the currently open level's world using the subsystem approach
        editor_subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        world = editor_subsystem.get_editor_world()

        # Create a location vector for where to place the actor
        spawn_location = unreal.Vector(0.0, 0.0, 0.0)

        # Spawn the MediaPlatePlus actor in the level
        media_plate_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(media_plate_gc, spawn_location)

        if not media_plate_actor:
            print("Failed to spawn MediaPlatePlus actor.")
            return

        # Set the CameraLink property directly on the actor instance
        try:
            media_plate_actor.set_editor_property("CameraLink", camera_actor)
            print("Successfully set CameraLink on MediaPlatePlus actor instance.")
        except Exception as e:
            print(f"Failed to set CameraLink on MediaPlatePlus actor instance: {e}")

        # Access the Media Plate Component
        media_plate_component = media_plate_actor.media_plate_component
        if media_plate_component:
            # Load the existing ImgMediaSource asset
            img_media_source = unreal.EditorAssetLibrary.load_asset(img_media_source_path)
            if img_media_source:
                # Create an in-memory MediaPlaylist for this instance
                new_media_playlist = self.create_in_memory_media_playlist(img_media_source)
                if new_media_playlist:
                    # Set the new in-memory media playlist on the MediaPlateComponent
                    media_plate_component.set_editor_property("media_playlist", new_media_playlist)
                    print("Successfully set new in-memory media playlist on MediaPlateComponent.")
            else:
                print(f"Failed to load ImgMediaSource asset at: {img_media_source_path}")
        else:
            print("MediaPlatePlus actor does not have a media_plate_component.")
        
        self.add_media_source_to_sequence(media_plate_actor, img_media_source)

    def add_media_source_to_sequence(self, media_plate_actor, img_media_source):
        try:
            # Get the currently open level sequence
            level_sequence = unreal.LevelSequenceEditorBlueprintLibrary.get_current_level_sequence()
            if not level_sequence:
                print("No level sequence currently open.")
                return

            # Add a possessable for the MediaPlatePlus actor
            possessable = level_sequence.add_possessable(media_plate_actor)

            # Create a MediaTrack in the possessable
            media_track = possessable.add_track(unreal.MovieSceneMediaTrack)

            if media_track:
                # Add a MediaSection to the MediaTrack
                media_section = media_track.add_section()

                # Set the media source on the media section
                media_section.set_editor_property("media_source", img_media_source)

                # Set the range of the media section to the sequence's start and end frames
                start_frame = level_sequence.get_playback_start()
                end_frame = level_sequence.get_playback_end()
                media_section.set_range(start_frame, end_frame)

                print(f"Successfully set media section range from frame {start_frame} to {end_frame}.")
                print("Successfully added MediaPlatePlus to the level sequence with the correct media source.")
            else:
                print("Failed to create media source track on the possessable.")
        except Exception as e:
            print(f"Failed to add MediaPlatePlus to the level sequence: {e}")

    def importImagePlate(self, dirPath, image_plate, camera_component):
        print (image_plate)
        print (camera_component)
        
        mediaFolderPath = "{}/Media".format(dirPath)

        pathsplit = dirPath.split('/')
        partnames = pathsplit[-2:]
        name = '_'.join(partnames)

        camera_actor = camera_component.get_owner()

        platedir = image_plate.split('/')
        EXRDir = '/'.join(platedir[:-1])

        self.create_img_source(name, mediaFolderPath, EXRDir)
        self.add_media_plate_plus_to_level(f'{mediaFolderPath}/{name}', "/Game/Blueprints/Utilities/MediaPlatePlus", camera_actor)

    def importPuppets(self, dirPath, puppetDict, sequenceAssetPath, startFrame, endFrame):
        animationFolderPath = "{}/Animation".format(dirPath)
        # Specify the path to the Level Sequence asset
        sequence_asset_path = sequenceAssetPath
        # Load the Level Sequence asset
        loaded_level_sequence = unreal.load_asset(sequenceAssetPath)
        # Open the Level Sequence in the editor
        unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(loaded_level_sequence)
        #create Cam Folder
        puppetFolderName = "ANIM"
        puppetFolder = unreal.MovieSceneSequenceExtensions.add_root_folder_to_sequence(loaded_level_sequence, puppetFolderName)
        #Unpack Puppet Data
        for puppetInfo in puppetDict:
            for puppet, attrs in puppetInfo.items():
                puppetAssetType = attrs[0].get('assetType')
                puppetAssetName = attrs[0].get('assetName')
                puppetVariantName = attrs[0].get('variant')
                puppetVersion = attrs[0].get('version')
                puppetFbxPath = attrs[0].get('Export Path')

                skeletalMeshBasePath = "/Game/01_Assets/{}/{}/{}/{}/".format(puppetAssetType, puppetAssetName, puppetVariantName, puppetVersion)

                # List all assets in the specified folder
                all_assets = unreal.EditorAssetLibrary.list_assets(skeletalMeshBasePath)

                # Initialize a list to hold only skeletal meshes
                skeletal_meshes = []

                # Loop through the assets and filter for skeletal meshes
                for asset_path in all_assets:
                    asset = unreal.EditorAssetLibrary.load_asset(asset_path)
                    if isinstance(asset, unreal.SkeletalMesh):
                        skeletalMeshPath = asset_path
                    if isinstance(asset, unreal.Skeleton):
                        skeletonPath = asset_path

                importedAnimation = self.importAnimationFBX(puppetFbxPath, animationFolderPath, skeletonPath)
                loadedSkeletalMesh = unreal.load_asset(skeletalMeshPath)
                # Spawn the skeletal mesh actor
                skeletal_mesh_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0,0,0))
                skeletal_mesh_actor.set_actor_label(puppet)
                skeletal_mesh_actor.set_folder_path("ANIM")
                # Set the skeletal mesh of the actor
                skeletal_mesh_component = skeletal_mesh_actor.get_component_by_class(unreal.SkeletalMeshComponent)
                skeletal_mesh_component.set_skeletal_mesh(loadedSkeletalMesh)
                
                possessableActor = loaded_level_sequence.add_possessable(skeletal_mesh_actor)
                self.addSkeletalAnimationTrackOnPossessable(importedAnimation[0], possessableActor, startFrame, endFrame)

                puppetFolder.add_child_object_binding(possessableActor)

    def importAnimationFBX(self, puppetFbxPath, animationFolderPath, skeletonPath):
        #build import task and run it
        importMeshTask = genUnrealImportUtils.buildImportTask(puppetFbxPath,
                                                            animationFolderPath,
                                                            genUnrealImportUtils.buildAnimationImportOptions(skeletonPath)
        )
        importedMesh = genUnrealImportUtils.executeImportTasks([importMeshTask])
        return importedMesh

    def addSkeletalAnimationTrackOnPossessable(self, animation_path, possessableActor, startFrame, endFrame):
        # Get Animation
        animation_asset = unreal.AnimSequence.cast(unreal.load_asset(animation_path))
        params = unreal.MovieSceneSkeletalAnimationParams()
        params.set_editor_property('Animation', animation_asset)
        # Add track
        animation_track = possessableActor.add_track(track_type=unreal.MovieSceneSkeletalAnimationTrack)
        # Add section
        animation_section = animation_track.add_section()
        animation_section.set_editor_property('Params', params)
        animation_section.set_range(startFrame, endFrame)

    def saveAssets(self, assetList):
        for asset in assetList:
            assetNameClean = str(asset).split('.')[0]
            unreal.EditorAssetLibrary.save_asset(assetNameClean)

#open UI
def openWindow():
    if QtWidgets.QApplication.instance():
        #Id any current instances of tool and destroy
        for win in (QtWidgets.QApplication.allWindows()):
            print (win.objectName())
            if 'Import Unreal Assets' in win.objectName():
                win.destroy()
    else:
        QtWidgets.QApplication(sys.argv)
    # load UI into QApp instance
    MainWindow.window = MainWindow()
    MainWindow.window.show()
    unreal.parent_external_window_to_slate(MainWindow.window.winId())