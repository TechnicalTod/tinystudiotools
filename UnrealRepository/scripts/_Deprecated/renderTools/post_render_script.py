import os
import json
import subprocess
import sys

class PostRender:
    def __init__(self, render_dir, project_name, layer_name):
        self.render_dir = render_dir
        self.project_name = project_name
        self.layer_name = layer_name

        self.publish_json_file = os.path.join(self.render_dir, "publish_metadata", f"{self.project_name}_{self.layer_name}_metadata.json")

    def publish_to_ftrack(self):
        openpype_publish_command = ["openpype", "publish", self.publish_json_file]
        result = subprocess.run(openpype_publish_command, capture_output=True, text=True)
        if result.returncode == 0:
            print("Successfully published to ftrack.")
        else:
            print(f"Failed to publish to ftrack: {result.stderr}")

# Main entry point
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python post_render_script.py <render_dir> <project_name> <layer_name>")
        sys.exit(1)

    render_dir = sys.argv[1]
    project_name = sys.argv[2]
    layer_name = sys.argv[3]

    post_render = PostRender(render_dir, project_name, layer_name)
    post_render.publish_to_ftrack()