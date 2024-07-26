import unreal
import os
from datetime import datetime
import perforceAutomation
import time

import json
import requests

import threading

pieExecutor = None
 
@unreal.uclass()
class MoviePipelineMyCustomEditorRenderExecutor (unreal.MoviePipelinePythonHostExecutor):
    pieExecutor = unreal.uproperty(unreal.MoviePipelinePIEExecutor)
    loadedQueue = unreal.uproperty(unreal.MoviePipelineQueue)
    currentQueue = unreal.uproperty(unreal.MoviePipelineQueue)
    jobIndex = unreal.uproperty(int)
    
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
            project_name = unreal.SystemLibrary.get_game_name()
            jobs = memory_queue.get_jobs()
            for job in jobs:
                jobnum += 1
                config = job.get_configuration()
                settings = config.get_all_settings()
                deadlinepath = ''
                sequence_soft_ref = unreal.SystemLibrary.conv_soft_obj_path_to_soft_obj_ref(job.sequence)
                frame_start = unreal.MovieSceneSequenceExtensions.get_playback_start(sequence_soft_ref)
                frame_end = unreal.MovieSceneSequenceExtensions.get_playback_end(sequence_soft_ref)
                chunksize = frame_end - frame_start + 1
                frame_range = f"{frame_start}-{frame_end}"
                sequeance_name = sequence_soft_ref.get_name()
                for setting in settings:
                    if 'MoviePipelineOutputSetting' in setting.get_class().get_path_name():
                        output_setting = unreal.MoviePipelineOutputSetting.cast(setting)
                        check_path = output_setting.output_directory.path
                        if not check_path.startswith('CUSTOM'):
                            seq_path = sequence_soft_ref.get_path_name()
                            # Set the path based on the show if it doesn't match our standard naming
                            #prefix = '/Game/02_Episodes/'
                            #if seq_path.startswith(prefix):
                            #    seq_path = seq_path[len(prefix):]
                            seq_path = seq_path.split('/', 3)[-1]
                            last_slash_index = seq_path.rfind('/')
                            if last_slash_index != -1:
                                seq_path = seq_path[:last_slash_index]
                            seq_path += '/'
                            print('/=================================/')
                            print(seq_path)
                            seq_path = f'Y:/CFX_1567_HOA/episodes/' + seq_path

                            # Split the path into parts and remove the last part
                            seq_path_parts = seq_path.rstrip('/').split('/')
                            last_part = seq_path_parts.pop()
                            seq_path = '/'.join(seq_path_parts)

                            # Construct the new path with the inserted directories
                            new_seq_path = f'{seq_path}/work/unreal/renders/{last_part}'

                            print('=================================')
                            print(new_seq_path)

                            output_setting.output_directory = unreal.DirectoryPath(path=new_seq_path)
                            deadlinepath = new_seq_path
                        else:
                            check_path = check_path[6:]
                            output_setting.output_directory = unreal.DirectoryPath(path=check_path)
                            deadlinepath = check_path

                        unreal.log(output_setting.output_directory)

                job.set_configuration(config)

                deadlineQueue, assetpath = self.create_queue_from_transient(job, jobnum)
                
                path = unreal.Paths.get_project_file_path()
                # Normalize path to use forward slashes
                path = path.replace('\\', '/')
                
                # Split the path by slashes
                parts = path.split('/')
                
                # Check if there are at least two directories in the path
                if len(parts) >= 3:
                    # Get the third directory from the end
                    result = parts[-4]
                
                print(result)

                #perforceAutomation.push_all_pending_changes(result)
                perforceAutomation.push_specific_changes(result, assetpath)
                perforceAutomation.pull_unreal_changes_to_perforce('CFX_1567_HOA_Shared') # Pull onto X:drive - This is the shared on x for remote machines - This needs to exist, or renders will not boot on remote machines
                user = perforceAutomation.get_Username(result)

                unrealversion = unreal.SystemLibrary.get_engine_version()
                unrealversion = unrealversion[:3]

                # Define the executable path
                exe = f'C:/Program Files/Epic Games/UE_{unrealversion}/Engine/Binaries/Win64/UnrealEditor-cmd.exe'

                # Define the arguments
                args = (
                    f'"X:/PerforceWorkspaces/CFX_1567_HOA_Shared/client/{project_name}/{project_name}.uproject" '
                    f'-execcmds="py X:/UnrealRepository/scripts/CustomRenderBootstrap.py" '
                    f'-MoviePipelineConfig="/Game/DeadlineQueues/{deadlineQueue}"'
                )
                
                # Log for debugging
                unreal.log(f"Executable: {exe}")
                unreal.log(f"Arguments: {args}")

                job_info = {
                "JobInfo": {
                    "Plugin": "CommandLine",
                    "Name": f"{project_name}_{deadlineQueue}",
                    "BatchName": f"{project_name} - {sequeance_name}",
                    "UserName": user,
                    "Pool": "unreal",
                    "Group": "none",
                    "Priority": 100,
                    "TaskTimeoutMinutes": "0",
                    "EnableAutoTimeout": "False",
                    "ConcurrentTasks": "1",
                    "LimitConcurrentTasksToNumberOfCpus": "True",
                    "MachineLimit": "0",
                    "Frames": frame_range,
                    "OutputDirectory0": deadlinepath,
                    "Whitelist": "",
                    "OnJobComplete": "Nothing",
                    "ChunkSize": str(chunksize)
                },
                "PluginInfo": {
                    "Executable": exe,
                    "Arguments": args,
                    "WorkingDirectory": deadlinepath,
                },
                "AuxFiles": []
                }

                job_info_json = json.dumps(job_info)

                url = "http://gracie:8081/api/jobs"
                headers = {"Content-Type": "application/json"}

                response = requests.post(url, headers=headers, data=job_info_json)

                if response.status_code == 200:
                    print("Job submitted successfully")
                    try:
                        # Try to print the entire response JSON to see what it actually contains
                        response_json = response.json()
                        print("Response JSON:", response_json)

                        # Adjust according to the actual response structure
                        job_id = response_json.get('response') or response_json.get('_id') or response_json.get('JobID')
                        print("Job ID:", job_id)

                    except KeyError as e:
                        print(f"KeyError: {e} - the key is not in the response. Check the JSON structure.")
                    except json.JSONDecodeError:
                        print("Failed to decode JSON. Here is the raw response:")
                        print(response.text)
                else:
                    print("Failed to submit job")
                    print("Status Code:", response.status_code)
                    print("Response:", response.text)

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
        
        self.currentjob = job

        # Now create the executor and listen to it finish one job
        self.pieExecutor = unreal.MoviePipelinePIEExecutor()
        self.pieExecutor.on_executor_finished_delegate.add_function_unique(self, "on_individual_job_finished")
        self.pieExecutor.execute(self.currentQueue)

        '''
        uncomment this to enable percentage tracking on another thread
        Currently writes logs to Unreal, inorder for this to be 
        given to deadline will require a custom plugin

        # Start the progress update thread
        self.rendering = True
        self.start_time = unreal.MathLibrary.utc_now()
        progress_thread = threading.Thread(target=self.update_progress_periodically)
        progress_thread.start()
        '''
        
    @unreal.ufunction(ret=None, params=[unreal.MoviePipelineExecutorBase, bool])
    def on_individual_job_finished(self, executor, fatal_error):
        unreal.log("Job finished! Job Index: " + str(self.jobIndex))
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
    
    def update_progress_periodically(self):
        while self.rendering:
            # Here you should fetch the actual progress from the rendering job
            # Since we don't have actual rendering logic, we simulate progress
            progress = self.currentjob.get_status_progress() #Between 0-1
            progress = progress * 100 # Convert to actual percentage
            progress = round(progress)
            unreal.log(f"progress: {progress}%")
            time.sleep(2)