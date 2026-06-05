from P4 import P4, P4Exception
import unreal
import os

def pull_unreal_changes_to_perforce(workspace):
    # Configuration: Set your Perforce server connection details
    p4 = P4()
    p4.port = "ssl:akl01vhelix01.ad.causefx.co.nz:1666"  # Replace with your Perforce server address
    p4.client = workspace  # Replace with your Perforce workspace (client)
    
    # Default user and password (only set if user does not exist)
    default_user = "Sam.tack"  # Replace with your default Perforce username
    default_password = "Genuser123!"  # Replace with your default Perforce password
    
    try:
        p4.connect()
        
        # Check if the current user exists
        user_exists = True
        try:
            user_info = p4.run("user", "-o", p4.user)
        except P4Exception as e:
            if "doesn't exist" in str(e):
                user_exists = False
        
        if not user_exists:
            # Set the default user and password if the user does not exist
            p4.user = default_user
            p4.password = default_password
            # Reconnect with the new user credentials
            p4.disconnect()
            p4.connect()

        # Perform sync
        p4.run("sync")
        
    except P4Exception as e:
        unreal.log_error("P4Exception: {}".format(e))
        for error in p4.errors:
            unreal.log_error(error)
    finally:
        unreal.log("Completed Sync")
        p4.disconnect()

def push_all_pending_changes(workspace):
    # Configuration: Set your Perforce server connection details
    p4 = P4()
    p4.port = "ssl:akl01vhelix01.ad.causefx.co.nz:1666"  # Replace with your Perforce server address
    p4.client = workspace  # Replace with your Perforce workspace (client)
    
    # Default user and password (only set if user does not exist)
    default_user = "sam.tack"  # Replace with your default Perforce username
    default_password = "Genuser123!"  # Replace with your default Perforce password

    try:
        # Connect to Perforce server
        p4.connect()
        
        # Check if the current user exists
        user_exists = True
        try:
            user_info = p4.run("user", "-o", p4.user)
        except P4Exception as e:
            if "doesn't exist" in str(e):
                user_exists = False
        
        if not user_exists:
            # Set the default user and password if the user does not exist
            p4.user = default_user
            p4.password = default_password
            # Reconnect with the new user credentials
            p4.disconnect()
            p4.connect()

        # Prepare changelist description
        changelist_description = """
        Submitting all pending changes from Unreal Engine.
        """

        # Create a new changelist
        change = p4.fetch_change()
        change["Description"] = changelist_description.strip()

        # Save the changelist to get a changelist number
        result = p4.save_change(change)
        changelist_number = result[0].split()[1]

        # Reopen all open files in the new changelist
        opened_files = p4.run_opened()
        if opened_files:
            file_paths = [file['depotFile'] for file in opened_files]
            p4.run_reopen(["-c", changelist_number] + file_paths)

        # Submit the changelist
        p4.run_submit("-c", changelist_number)

        unreal.log("All pending changes pushed successfully to Perforce.")
    
    except P4Exception as e:
        unreal.log_error("P4Exception: {}".format(e))
        for error in p4.errors:
            unreal.log_error(error)
    finally:
        p4.disconnect()
        unreal.log("Completed Full Push")
'''
def push_specific_changes(workspace, file_path):
    # Configuration: Set your Perforce server connection details
    p4 = P4()
    p4.port = "ssl:akl01vhelix01.ad.causefx.co.nz:1666"  # Replace with your Perforce server address
    p4.client = workspace  # Replace with your Perforce workspace (client)
    
    # Default user and password (only set if user does not exist)
    default_user = "sam.tack"  # Replace with your default Perforce username
    default_password = "Genuser123!"  # Replace with your default Perforce password

    try:
        # Connect to Perforce server
        p4.connect()
        
        # Check if the current user exists
        user_exists = True
        try:
            user_info = p4.run("user", "-o", p4.user)
        except P4Exception as e:
            if "doesn't exist" in str(e):
                user_exists = False
        
        if not user_exists:
            # Set the default user and password if the user does not exist
            p4.user = default_user
            p4.password = default_password
            # Reconnect with the new user credentials
            p4.disconnect()
            p4.connect()

        # Prepare changelist description
        changelist_description = "Pushing specific file to Perforce."

        # Create a new changelist
        change = p4.fetch_change()
        change["Description"] = changelist_description

        # Save the new changelist to get a changelist number
        result = p4.save_change(change)
        changelist_number = result[0].split()[1]

        # Revert the file from the current changelist, if it is already in one
        p4.run_revert(file_path)

        # Ensure the file is opened for add/edit in the new changelist
        file_status = p4.run_fstat(file_path)
        if 'headAction' not in file_status[0]:
            # If the file is not under version control, add it to the changelist
            p4.run_add("-c", changelist_number, file_path)
        else:
            # If the file is under version control, open it for edit in the changelist
            p4.run_edit("-c", changelist_number, file_path)

        # Submit the changelist
        p4.run_submit("-c", changelist_number)

        unreal.log("Specific file pushed successfully to Perforce.")
    
    except P4Exception as e:
        unreal.log_error("P4Exception: {}".format(e))
        for error in p4.errors:
            unreal.log_error(error)
    finally:
        p4.disconnect()
        unreal.log("Completed Sync")

'''
def push_specific_changes(workspace, file_path):
    # Configuration: Set your Perforce server connection details
    p4 = P4()
    p4.port = "ssl:akl01vhelix01.ad.causefx.co.nz:1666"  # Replace with your Perforce server address
    p4.client = workspace  # Replace with your Perforce workspace (client)
    
    # Default user and password (only set if user does not exist)
    default_user = "sam.tack"  # Replace with your default Perforce username
    default_password = "Genuser123!"  # Replace with your default Perforce password

    try:
        # Connect to Perforce server
        p4.connect()
        
        # Check if the current user exists
        user_exists = True
        try:
            user_info = p4.run("user", "-o", p4.user)
        except P4Exception as e:
            if "doesn't exist" in str(e):
                user_exists = False
        
        if not user_exists:
            # Set the default user and password if the user does not exist
            p4.user = default_user
            p4.password = default_password
            # Reconnect with the new user credentials
            p4.disconnect()
            p4.connect()

        # Prepare changelist description
        changelist_description = "Pushing specific file to Perforce."

        # Create a new blank changelist
        new_change = p4.fetch_change()
        new_change["Description"] = changelist_description
        new_change["Files"] = []

        # Save the new changelist to get a changelist number
        result = p4.save_change(new_change)
        new_changelist_number = result[0].split()[1]

        # Revert any existing changes to the file
        p4.run_revert(file_path)
        
        # Add the file to the new changelist
        p4.run_add("-c", new_changelist_number, file_path)

        # Submit the new changelist
        p4.run_submit("-c", new_changelist_number)

        unreal.log("Specific file pushed successfully to Perforce.")
    
    except P4Exception as e:
        unreal.log_error(f"P4Exception: {e}")
        for error in p4.errors:
            unreal.log_error(error)
    finally:
        p4.disconnect()
        unreal.log("Completed Sync")