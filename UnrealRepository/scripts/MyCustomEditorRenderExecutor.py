import unreal
import os
from datetime import datetime
import perforceAutomation
import time
import sys

import json
import requests
import getpass

import subprocess

import keyring

import socket

import re

import threading

import shutil

from PySide2.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton

from importlib import reload
import unrealFilePaths
reload(unrealFilePaths)

pieExecutor = None

# Publish Comment Window
class UserInputDialog(QDialog):
    def __init__(self):
        super().__init__()
        # window prefs
        with open("{}/dark.qss".format(unrealFilePaths.UNREAL_styleSheetFilepath), "r") as fh:
            self.setStyleSheet(fh.read())
        self.setWindowTitle("Publish Comment")
        self.resize(300, 50)
        self.setFocus()
        self.show()

        # Set up the layout
        layout = QVBoxLayout()

        # Add a label
        self.label = QLabel("Comment:")
        layout.addWidget(self.label)

        # Add a text box
        self.textBox = QLineEdit()
        layout.addWidget(self.textBox)

        # Add a submit button
        self.submitButton = QPushButton("Submit")
        layout.addWidget(self.submitButton)

        # Set the dialog layout
        self.setLayout(layout)

        # Connect the button click signal to the slot
        self.submitButton.clicked.connect(self.on_submit)

        self.user_input = None

    def on_submit(self):
        self.user_input = self.textBox.text()
        self.accept()

@unreal.uclass()
class MoviePipelineMyCustomEditorRenderExecutor (unreal.MoviePipelinePythonHostExecutor):
    pieExecutor = unreal.uproperty(unreal.MoviePipelinePIEExecutor)
    loadedQueue = unreal.uproperty(unreal.MoviePipelineQueue)
    currentQueue = unreal.uproperty(unreal.MoviePipelineQueue)
    jobIndex = unreal.uproperty(int)

    jobdir = ''

    def generate_publish_json(self, shotname, start_frame, end_frame, comment, workdir, source_file, xres, yres):
        FTRACK_API_KEY = os.getenv('Ftrack_API_Key')
        FTRACK_API_USER = os.getenv('Ftrack_API_User')
        FTRACK_SERVER = os.getenv('Ftrack_Server')
        
        pattern = r'LS_|_v00\d'
        cleaned_name = re.sub(pattern, '', shotname)

        AVALON_PROJECT = os.getenv('Project_Name')
        AVALON_ASSET = cleaned_name
        AVALON_TASK = os.getenv('Render_Task_Name')
        AVALON_APP_NAME = "unreal/5-0"
        AVALON_WORKDIR = workdir

        user = getpass.getuser()

        frame_range = range(int(start_frame), int(end_frame) + 1)
        list_of_files = [f"{shotname}.{frame}.exr" for frame in frame_range]

        publish_json = {
            "asset": AVALON_ASSET,
            "comment": comment,
            "fps": 24.0,
            "frameEnd": float(end_frame),
            "frameStart": float(start_frame),
            "source": source_file,
            "user": user,
            "version": None,
            "hostName": AVALON_APP_NAME,
            "ftrack": {
                "FTRACK_API_KEY": FTRACK_API_KEY,
                "FTRACK_API_USER": FTRACK_API_USER,
                "FTRACK_SERVER": FTRACK_SERVER
            },
            "intent": {
                "label": "Dailies",
                "value": "dailies"
            },
            "instances": [
                {
                    "asset": AVALON_ASSET,
                    "fps": 24.0,
                    "frameEnd": float(end_frame),
                    "frameStart": float(start_frame),
                    "handleStart": 0,
                    "handleEnd": 0,
                    "resolutionHeight": int(yres),
                    "resolutionWidth": int(xres),
                    "source": source_file,
                    "subset": "unreal_render_main",
                    "family": "unreal_render",
                    "families": [
                        "unreal_render",
                        "ftrack"
                    ],
                    "version": None,
                    "representations": [
                        {
                            "ext": "exr",
                            "files": list_of_files,
                            "stagingDir": workdir,
                            "name": "exr",
                            "is_sequence": True
                        }
                    ]
                }
            ],
            "job": {
                "_id": ""
            },
            "session": {
                "AVALON_ASSET": AVALON_ASSET,
                "AVALON_PROJECT": AVALON_PROJECT,
                "AVALON_WORKDIR": AVALON_WORKDIR,
                "AVALON_APP": AVALON_APP_NAME,
                "AVALON_DB": "avalon",
                "AVALON_DEADLINE": "http://gracie:8081",
                "AVALON_LABEL": "OpenPype",
                "AVALON_PROJECTS": "",
                "AVALON_SCENEDIR": "",
                "AVALON_TASK": AVALON_TASK,
                "AVALON_TIMEOUT": "1000",
                "schema": "openpype:session-3.0",
                "OPENPYPE_PUBLISH_JOB": "1",
                "OPENPYPE_RENDER_JOB": "0"
            }
        }

        publish_json_file = os.path.join(workdir, "publish_metadata", f"{shotname}_metadata.json")
        os.makedirs(os.path.dirname(publish_json_file), exist_ok=True)

        with open(publish_json_file, "w") as json_file:
            json.dump(publish_json, json_file, indent=4)

        return publish_json_file

    def submit_publish_job(self, layer_name, dl_comment, publish_json_file, batch_name, job_dependency, output_dir):
        FTRACK_API_KEY = os.getenv('Ftrack_API_Key')
        FTRACK_API_USER = os.getenv('Ftrack_API_User')
        FTRACK_SERVER = os.getenv('Ftrack_Server')
        
        pattern = r'LS_|_v00\d'
        cleaned_name = re.sub(pattern, '', layer_name)

        AVALON_PROJECT = os.getenv('Project_Name')
        AVALON_ASSET = cleaned_name
        AVALON_TASK = os.getenv('Render_Task_Name')
        AVALON_APP_NAME = "unreal/5-0"

        OPENPYPE_USERNAME = getpass.getuser()
        MACHINE_NAME = os.getenv("COMPUTERNAME")

        publish_cmds = f"--headless publish {publish_json_file} --targets deadline --targets farm"
        dl_job_name = f"UE | Publish - {layer_name}"

        publish_job_dl_json = {
            "JobInfo": {
                "BatchName": batch_name,
                "Name": dl_job_name,
                "Comment": dl_comment,
                "Priority": 50,
                "Frames": 0,
                "OutputDirectory0": output_dir,
                "MachineName": MACHINE_NAME,
                "Plugin": "OpenPype",
                "Pool": "publish",
                "UserName": OPENPYPE_USERNAME,
                "InitialStatus": "Suspended",
                "JobDependencies": [job_dependency],
                "OverrideJobFailureDetection": True,
                "FailureDetectionJobErrors": 1,
                "EnvironmentKeyValue0": f"FTRACK_API_KEY={FTRACK_API_KEY}",
                "EnvironmentKeyValue1": f"FTRACK_API_USER={FTRACK_API_USER}",
                "EnvironmentKeyValue2": f"FTRACK_SERVER={FTRACK_SERVER}",
                "EnvironmentKeyValue3": f"AVALON_PROJECT={AVALON_PROJECT}",
                "EnvironmentKeyValue4": f"AVALON_ASSET={AVALON_ASSET}",
                "EnvironmentKeyValue5": f"AVALON_TASK={AVALON_TASK}",
                "EnvironmentKeyValue6": f"AVALON_APP_NAME={AVALON_APP_NAME}",
                "EnvironmentKeyValue7": f"OPENPYPE_USERNAME={OPENPYPE_USERNAME}",
                "EnvironmentKeyValue8": "OPENPYPE_PUBLISH_JOB=1",
                "EnvironmentKeyValue9": "OPENPYPE_RENDER_JOB=0"
            },
            "PluginInfo": {
                "Arguments": publish_cmds,
                "SingleFrameOnly": True,
                "Version": "3.0"
            },
            "AuxFiles": [],
            "IdOnly": True
        }

        url = "http://gracie:8081/api/jobs"
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, headers=headers, data=json.dumps(publish_job_dl_json))

        if response.status_code == 200:
            print("Publish job submitted successfully")
            response_json = response.json()
            return response_json.get('JobID')
        else:
            print("Failed to submit publish job")
            print("Status Code:", response.status_code)
            print("Response:", response.text)
            return None

    def submit_to_deadline(self, project_name, sequence_name, deadlineQueue, frame_range, deadlinepath, exe, args, chunksize, source_file, xres, yres, comment, publish):
        #post_render_script = "X:/UnrealRepository/scripts/post_render_script.py"

        start_frame, end_frame = frame_range.split('-')

        if(publish):
            publish_json_file = self.generate_publish_json(sequence_name, start_frame, end_frame, comment, deadlinepath, source_file, xres, yres)

        user = getpass.getuser()

        # Render job information
        render_job_info = {
            "JobInfo": {
                "Plugin": "CommandLine",
                "Name": f"{project_name}_{deadlineQueue}_render",
                "Comment": comment,
                "BatchName": f"{project_name} - {sequence_name}",
                "UserName": user,
                "Pool": "unreal",
                "Group": "none",
                "Priority": 80,
                "TaskTimeoutMinutes": "0",
                "EnableAutoTimeout": "False",
                "ConcurrentTasks": "1",
                "LimitConcurrentTasksToNumberOfCpus": "True",
                "MachineLimit": "0",
                "Frames": frame_range,
                "OutputDirectory0": deadlinepath,
                "Whitelist": "",
                "MachineName": os.getenv("COMPUTERNAME"),
                "ChunkSize": str(chunksize),
                "EnvironmentKeyValue": [
                    f"RENDER_DIR={deadlinepath}",
                    f"SOURCE_BASE_NAME={os.path.splitext(os.path.basename(source_file))[0]}",
                    f"LAYER_NAME={sequence_name}"
                ]
            },
            "PluginInfo": {
                "Executable": exe,
                "Arguments": args,
                "WorkingDirectory": deadlinepath,
            },
            "AuxFiles": []
        }

        render_job_info_json = json.dumps(render_job_info)

        url = "http://gracie:8081/api/jobs"
        headers = {"Content-Type": "application/json"}

        # Submit the render job
        render_response = requests.post(url, headers=headers, data=render_job_info_json)
        if render_response.status_code == 200:
            print("Render job submitted successfully")
            try:
                render_response_json = render_response.json()
                render_job_id = render_response_json.get('response') or render_response_json.get('_id') or render_response_json.get('JobID')
                print("Render Job ID:", render_job_id)

                if(publish):
                    # Submit the publish job
                    publish_job_id = self.submit_publish_job(
                        layer_name=sequence_name,
                        dl_comment=comment,
                        publish_json_file=publish_json_file,
                        batch_name=f"{project_name} - {sequence_name}",
                        job_dependency=render_job_id,
                        output_dir=deadlinepath
                    )
                    print("Publish Job ID:", publish_job_id)

            except KeyError as e:
                print(f"KeyError: {e} - the key is not in the response. Check the JSON structure.")
            except json.JSONDecodeError:
                print("Failed to decode JSON. Here is the raw response:")
                print(render_response.text)
        else:
            print("Failed to submit render job")
            print("Status Code:", render_response.status_code)
            print("Response:", render_response.text)
            return

    # Function to create a movie pipeline queue asset
    def create_queue_from_transient(self, job, jobnum):
        temp_asset = unreal.MoviePipelineQueue()
        
        new_job = temp_asset.allocate_new_job(unreal.MoviePipelineExecutorJob)
        new_job.job_name = 'test'
        new_job.map = job.map
        new_job.sequence = job.sequence
        new_job.set_configuration(job.get_configuration())

        asset_path = "/Game/DeadlineQueues"
        asset_name = "DeadlineQueueAsset" #Will need to uniquely append to names for each queue
        timestamp = datetime.now().strftime("%m%d%H%M%S")
        asset_name = asset_name + timestamp + '_job' + str(jobnum)
        # AssetTools is used to manipulate assets
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

        # Specify the class type for the movie pipeline queue
        movie_pipeline_queue_class = unreal.MoviePipelineQueue
        
        # Create a new asset using the specified class
        queue_asset = asset_tools.create_asset(asset_name, asset_path, movie_pipeline_queue_class, None)
        
        # Get the package path for the asset
        package_path = queue_asset.get_outermost().get_name()

        # Unreal package paths use "/" as separators and start with "/Game" for assets in the content directory
        # Convert the package path to a file system path
        content_dir = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir())
        asset_relative_path = package_path.replace("/Game", "").replace("/", os.sep) + ".uasset"
        asset_full_path = os.path.join(content_dir, asset_relative_path.lstrip(os.sep))
        asset_full_path = asset_full_path.replace("\\", "/")

        queue_asset.copy_from(temp_asset)

        unreal.EditorAssetLibrary.save_loaded_asset(queue_asset)

        return asset_name, asset_full_path

    # Constructor that gets called when created either via C++ or Python
    def _post_init(self):
        self.loadedQueue = None
        self.currentQueue = None
        self.pieExecutor = None
        self.jobIndex = -1

        self.progress_update_interval = 2
        self.currentjob = None
        self.rendering = False

    @unreal.ufunction(override=True)
    def execute_delayed(self, memory_queue):
        
        # Check to see if this is an actual queue to save to disk and send to Deadline. 
        # It's a little bit of a hacky work around. If the memory_queue is 0 it means 
        # it's coming from a command line and can be processed as if it's being run on 
        # a remote machine. Otherwise we can save the memory_queue and send it to deadline.
        # Also doing processing for automatically saving to show drives - This is hard coded 
        # for the most part which I dislike - So Hopefully I fix it at some point
        jobnum = 0
        num_jobs = len(memory_queue.get_jobs())
        if num_jobs > 0:
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)

            # Create and show the dialog
            dialog = UserInputDialog()
            result = dialog.exec_()  # This line blocks execution until the dialog is closed

            comment = ''
            if result == QDialog.Accepted:
                comment = dialog.user_input

            project_name = unreal.SystemLibrary.get_game_name()
            jobs = memory_queue.get_jobs()
            for job in jobs:
                if not job.is_enabled():  # Assuming this is the correct method to check if a job is enabled
                    unreal.log_warning(f"Skipping job {job.get_name()} as it is not enabled.")
                    continue
                jobnum += 1
                config = job.get_configuration()
                settings = config.get_all_settings()
                deadlinepath = ''
                sequence_soft_ref = unreal.SystemLibrary.conv_soft_obj_path_to_soft_obj_ref(job.sequence)
                frame_start = unreal.MovieSceneSequenceExtensions.get_playback_start(sequence_soft_ref)
                frame_end = unreal.MovieSceneSequenceExtensions.get_playback_end(sequence_soft_ref)
                frame_end = frame_end - 1
                chunksize = frame_end - frame_start + 1
                frame_range = f"{frame_start}-{frame_end}"
                sequence_name = sequence_soft_ref.get_name()
                xres = 1920  # Default values in case we don't find the settings
                yres = 1080

                publish = False

                for setting in settings:
                    if 'MoviePipelineOutputSetting' in setting.get_class().get_path_name():
                        output_setting = unreal.MoviePipelineOutputSetting.cast(setting)
                        xres = output_setting.output_resolution.x
                        yres = output_setting.output_resolution.y
                        check_path = output_setting.output_directory.path
                        if not check_path.startswith('CUSTOM'):
                            seq_path = sequence_soft_ref.get_path_name()
                            seq_path = seq_path.split('/', 3)[-1]
                            last_slash_index = seq_path.rfind('/')
                            if last_slash_index != -1:
                                seq_path = seq_path[:last_slash_index]
                            seq_path += '/'
                            basedir = os.getenv('Show_Dir')
                            seq_path = f'{basedir}/episodes/' + seq_path

                            # Split the path into parts and remove the last part
                            seq_path_parts = seq_path.rstrip('/').split('/')
                            last_part = seq_path_parts.pop()
                            seq_path = '/'.join(seq_path_parts)

                            # Construct the new path with the inserted directories
                            new_seq_path = f'{seq_path}/work/unreal/renders/{last_part}'

                            output_setting.output_directory = unreal.DirectoryPath(path=new_seq_path)
                            deadlinepath = new_seq_path

                            publish = True
                        else:
                            check_path = check_path[6:]
                            output_setting.output_directory = unreal.DirectoryPath(path=check_path)
                            deadlinepath = check_path

                        unreal.log(output_setting.output_directory)

                job.set_configuration(config)

                deadlineQueue, assetpath = self.create_queue_from_transient(job, jobnum)
                
                perforceAutomation.push_specific_changes(os.getenv('Workspace'), assetpath)
                perforceAutomation.pull_unreal_changes_to_perforce(os.getenv('Shared_Render_Workspace')) # Pull onto X:drive - This is the shared on x for remote machines

                # Define the executable path
                exe = f'C:/Program Files/Epic Games/UE_{os.getenv("UE_version")}/Engine/Binaries/Win64/UnrealEditor-cmd.exe'

                # Define the arguments
                args = (
                    f'"{os.getenv("Shared_Workspace_Dir")}" '
                    f'-execcmds="py X:/UnrealRepository/scripts/CustomRenderBootstrap.py" '
                    f'-MoviePipelineConfig="/Game/DeadlineQueues/{deadlineQueue}" '
                    '-stdout -log'
                )
                
                # Log for debugging
                unreal.log(f"Executable: {exe}")
                unreal.log(f"Arguments: {args}")

                path = unreal.Paths.get_project_file_path()
                path = path.replace('\\', '/')

                self.submit_to_deadline(project_name, sequence_name, deadlineQueue, frame_range, deadlinepath, exe, args, chunksize, path, xres, yres, comment, publish)
            return
        
        unreal.log('No Memory Queue, Running Remote')
        cmd_tokens, cmd_switches, cmd_parameters = unreal.SystemLibrary.parse_command_line(
            unreal.SystemLibrary.get_command_line()
        )
        
        try:
            queue_asset_path = cmd_parameters['MoviePipelineConfig']
        except Exception:
            unreal.log_error("Missing '-MoviePipelineConfig' argument")
            self.on_executor_errored_impl_impl()
            return
        
        unreal.log(f"Loading Queue file from path: {queue_asset_path}")
        self.loadedQueue = unreal.EditorAssetLibrary.load_asset(queue_asset_path)

        if self.loadedQueue is None:
            unreal.log_error("Failed to load queue from path, is asset missing?")
            self.on_executor_errored_impl()
            return
            
        if len(self.loadedQueue.get_jobs()) == 0:
            unreal.log_error("No jobs in queue to process.")
            self.on_executor_errored_impl()
            return
            
        # Here's a good time to edit the self.loadedQueue if you wanted to, as its
        # now a copy (ie: changes won't affect the asset on disk) such as resolving
        # output directories or checking things out in Shotgrid, etc.
        
        # Start the rendering process
        self.start_job_by_index(0)
    
    @unreal.ufunction(ret=None, params=[int])
    def start_job_by_index(self, inIndex):
        if(inIndex >= len(self.loadedQueue.get_jobs())):
            unreal.log_error("Out of Bounds Job Index!")
            self.on_executor_errored_impl()
        
        self.jobIndex = inIndex
        
        # Load the map in the editor
        map_package_path = unreal.MoviePipelineLibrary.get_map_package_name(
                self.loadedQueue.get_jobs()[self.jobIndex])
                
        map_load_start_time = unreal.MathLibrary.utc_now()
        unreal.EditorLoadingAndSavingUtils.load_map(map_package_path)
        curr_time = unreal.MathLibrary.utc_now()
        total_seconds = unreal.MathLibrary.get_total_seconds(
            unreal.MathLibrary.subtract_date_time_date_time(
                curr_time,
                map_load_start_time
            )
        )
        unreal.log(f"Map load took: {total_seconds} seconds.")
        
        # This is a little bit of a change in behavior compared to the in-editor behavior,
        # we first duplicate the job into its own Queue and then use the PIE Executor to
        # render that new queue (which only has one job). This allows us to do two things:
        # 1) Fully load the map in the editor before rendering a job (in case different jobs have different maps)
        # 2) Iterate through the queue ourself which gives us better control over updating extenral systems, etc.
        self.currentQueue = unreal.MoviePipelineQueue()
        job = self.currentQueue.duplicate_job(self.loadedQueue.get_jobs()[self.jobIndex])
        
        # Set Output dir
        config = job.get_configuration()
        output_settings = config.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
        if output_settings:
            self.jobdir = output_settings.output_directory.path

        self.currentjob = job

        # create the executor and listen to it finish one job
        self.pieExecutor = unreal.MoviePipelinePIEExecutor()
        self.pieExecutor.on_executor_finished_delegate.add_function_unique(self, "on_individual_job_finished")
        self.pieExecutor.execute(self.currentQueue)

        #self.start_progress_update()
        
        # Start the progress update thread
        self.rendering = True
        self.start_time = unreal.MathLibrary.utc_now()
        progress_thread = threading.Thread(target=self.update_progress_periodically) # Function Running on seperate thread to check progress and output to logs
        progress_thread.start()
        
    def process_exr_to_mov(self, exr_directory):
        oiiotool_path = r"C:\Program Files (x86)\OpenPype\3.14.0\vendor\bin\oiio\windows\oiiotool.exe"  # Path to oiiotool
        ffmpeg_path = r"X:\FFMPEG\bin\ffmpeg.exe"  # Path to ffmpeg
        ocio_config_path = r"X:\CG_Repository\OCIO\aces_1.2\config.ocio"  # Path to your OCIO config file
        
        # Set the OCIO environment variable
        env = os.environ.copy()
        env["OCIO"] = ocio_config_path
        
        # Print OCIO environment variable for debugging
        print("OCIO environment variable set to:", env["OCIO"])
        
        # List all files in the directory
        exr_files = [f for f in os.listdir(exr_directory) if f.endswith('.exr')]
        
        # Check if there are any EXR files in the directory
        if not exr_files:
            print("No EXR files found.")
            return
        
        # Sort the files
        exr_files.sort()
        
        # Create a "converted" folder inside the EXR directory if it doesn't exist
        converted_dir = os.path.join(exr_directory, "converted")
        os.makedirs(converted_dir, exist_ok=True)
        
        # Get the first EXR file to determine the starting frame
        first_exr = exr_files[0]
        match = re.search(r'(\d+)\.exr$', first_exr)
        starting_frame = match.group(1) if match else "0"
        
        # Convert each EXR file to a corresponding PNG in the "converted" folder
        for exr_file in exr_files:
            exr_path = os.path.join(exr_directory, exr_file)
            png_file = exr_file.replace(".exr", ".png")
            png_path = os.path.join(converted_dir, png_file)
            
            oiiotool_cmd = [
                oiiotool_path,
                "-i", exr_path,
                "--colorconvert", "ACES - ACEScg", "Output - sRGB",  # Convert color space from ACEScg to sRGB
                "-o", png_path
            ]
            
            try:
                print(f"Converting {exr_file} to {png_file}...")
                subprocess.run(oiiotool_cmd, check=True, env=env)
            except subprocess.CalledProcessError as e:
                print(f"Failed to convert {exr_file} to PNG: {e}")
                return
        
        print("Conversion complete!")
        
        # Determine the correct pattern for the PNG sequence in the converted directory
        first_png = os.listdir(converted_dir)[0]  # Get the first PNG file in the converted directory
        base_name = re.sub(r'\d+\.png$', '', first_png)  # Extract the base name before the frame number
        
        # Construct the PNG sequence pattern for FFMPEG
        png_sequence = os.path.join(converted_dir, f"{base_name}%04d.png")
        
        # Encode the PNG sequence to MOV using ffmpeg
        output_file = os.path.join(exr_directory, f"{base_name}mov")
        
        ffmpeg_cmd = [
            ffmpeg_path,  # Path to your ffmpeg executable
            '-y',  # Overwrite output files without asking
            '-start_number', starting_frame,  # Set the starting frame number
            '-framerate', '24',  # Frame rate
            '-i', png_sequence,  # Input PNG sequence
            '-vcodec', 'libx264',  # Video codec
            '-preset', 'slow',  # Encoding preset
            '-crf', '18',  # Quality setting (lower is better)
            '-r', '24',  # Frame rate
            output_file  # Output MOV file
        ]
        
        try:
            print("Encoding PNG sequence to MOV...")
            subprocess.run(ffmpeg_cmd, check=True)
            print("Encoding complete!")

            # Cleanup: Delete all PNG files and remove the converted folder
            print("Cleaning up...")
            shutil.rmtree(converted_dir)
            print("Cleanup complete!")

        except subprocess.CalledProcessError as e:
            print(f"Failed to process video for directory {exr_directory}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred while processing {exr_directory}: {e}")

    @unreal.ufunction(ret=None, params=[unreal.MoviePipelineExecutorBase, bool])
    def on_individual_job_finished(self, executor, fatal_error):
        unreal.log("Job finished! Job Index: " + str(self.jobIndex))

        print('ffmpeg output')
        self.process_exr_to_mov(self.jobdir)

        self.currentQueue = None
        self.rendering = False
        # Render the next job in the queue (if any)
        if (self.jobIndex < len(self.loadedQueue.get_jobs()) - 1):
            self.start_job_by_index(self.jobIndex + 1)
        else:
            # Notify whoever created us that we're done
            self.on_executor_finished_impl()
    
    @unreal.ufunction(override=True)
    def is_rendering(self):
        # This will block anyone from trying to use the UI to launch other
        # jobs and cause confusion
        return self.pieExecutor is not None


    '''
    def get_job_id_from_slave(self):
        # Get the current machine's hostname
        machine_name = socket.gethostname()
        
        # Query the Deadline API for this specific slave's info and settings
        url = f"http://gracie:8081/api/slaves?Name={machine_name}&Data=infosettings"
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                slave_info = response.json()
                unreal.log(f"Full slave data returned from API: {slave_info}")

                if slave_info and isinstance(slave_info, list):
                    # Assuming the first item in the list corresponds to this machine
                    slave_data = slave_info[0].get("Info", {})
                    job_id = slave_data.get("JobId")  # Extract the Job ID
                    
                    if job_id:
                        unreal.log(f"Found Job ID: {job_id} for slave: {machine_name}")
                        return job_id
                    else:
                        unreal.log("No Job ID found in the slave info.")
                else:
                    unreal.log("No slave data found.")
            else:
                unreal.log_error(f"Failed to retrieve slave data: {response.status_code} - {response.text}")
        except Exception as e:
            unreal.log_error(f"Error retrieving slave data from Deadline API: {e}")

        return None


    def start_progress_update(self):
        # Retrieve the Deadline Job ID from the environment
        unreal.log("STARTING PRGORESS THREAD")

        job_id = self.get_job_id_from_slave()
        if job_id:
            unreal.log(f"Job ID: {job_id}")
            self.rendering = True
            self.start_time = unreal.MathLibrary.utc_now()
            
            # Start the progress update thread, passing the job ID
            progress_thread = threading.Thread(target=self.update_progress_periodically, args=(job_id,))
            progress_thread.start()
        else:
            unreal.log("JOB ID Is not valid")
    '''
    def update_progress_periodically(self):
        while self.rendering:
            # Calculate progress (this is your logic for tracking progress)
            progress = self.currentjob.get_status_progress()  # Between 0-1
            progress = progress * 100  # Convert to percentage
            progress = round(progress)
            
            # Convert progress to string format with a percentage sign
            progress_str = f"{progress}%"
            
            # Log the calculated progress
            unreal.log_warning(f"progress: {progress_str}")
            
            time.sleep(2)  # Adjust the interval as needed