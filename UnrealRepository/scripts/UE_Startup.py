import os
import json

import keyring

import unreal

import perforceAutomation

import CustomPIEExecutor

# Path to the JSON configuration file
config_file_path = 'config.json'

# Ftrack Variables
service_api_key = "OpenPype/ftrack/causeandfx.ftrackapp.com/api_key"
service_api_user = "OpenPype/ftrack/causeandfx.ftrackapp.com/username"

os.environ['Ftrack_API_Key'] = keyring.get_password(service_api_key, "api_key")
os.environ['Ftrack_API_User'] = keyring.get_password(service_api_user, "username")
os.environ['Ftrack_Server'] = "https://causeandfx.ftrackapp.com"


# Json Variables
project_dir = unreal.SystemLibrary.get_project_directory()

# Construct the path to the config.json file
config_file_path = os.path.join(project_dir, 'config.json')

# Check if the config file exists
if not os.path.exists(config_file_path):
    unreal.log_error(f"Config file not found: {config_file_path}")
else:
    with open(config_file_path, 'r') as file:
        config_data = json.load(file)
    for key, value in config_data.items():
        os.environ[key] = value
        print(f'Set {key} = {value}')

    # Verify that the environment variables are set
    print("Environment variables set:")
    for key in config_data.keys():
        print(f'{key} = {os.getenv(key)}')

path = unreal.Paths.get_project_file_path()
path = path.replace('\\', '/')
parts = path.split('/')
depth = int(os.getenv('Uproject_Depth'))
depth += 2
os.environ['Workspace'] = parts[-depth]

perforceAutomation.pull_unreal_changes_to_perforce(os.getenv("workspace"))
perforceAutomation.pull_unreal_changes_to_perforce(os.getenv("Shared_Render_Workspace"))