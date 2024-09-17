import requests
import json
import socket


'''
# Define the Deadline REST API URL and Job ID
job_id = "66c6750261be711908ace9a5"
url = f"http://gracie:8081/api/jobs/{job_id}"

# Set the headers to specify JSON data
headers = {
    "Content-Type": "application/json"
}

# Step 1: Retrieve the job details and check the status
print(f"Fetching job details for Job ID: {job_id}")
response = requests.get(url, headers=headers)

if response.status_code == 200:
    job = response.json()
    job_status = job['Props']['Status']
    print(f"Job Status: {job_status}")

    # Step 2: Attempt to update job progress regardless of status
    # (You can add conditions later if needed)
    data = {
        "Props": {
            "Progress": 40.0  # Set progress to 40%
        }
    }
    print(f"Attempting to update job progress to 40%...")
    update_response = requests.put(url, headers=headers, data=json.dumps(data))

    if update_response.status_code == 200:
        print("Job progress updated to 40% successfully!")
    else:
        print(f"Failed to update job progress: {update_response.status_code} - {update_response.text}")

else:
    print(f"Failed to retrieve job details: {response.status_code} - {response.text}")

'''
def get_current_machine_name():
        # Get the current machine's hostname
        return socket.gethostname()

print(get_current_machine_name())
