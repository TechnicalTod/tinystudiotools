# Script to read and output crash log contents
import os

crash_log_file = r"C:\temp\maya_crash_debug.log"

print("=== CRASH LOG CONTENTS ===")

if os.path.exists(crash_log_file):
    try:
        with open(crash_log_file, "r", encoding="utf-8") as f:
            content = f.read()

        print(content)
        print("\n" + "=" * 50)

        # Find the last few checkpoints
        lines = content.split("\n")
        checkpoint_lines = [
            line
            for line in lines
            if any(x in line for x in ["Step 2", "GEO-", "MAT-", "CHECKPOINT"])
        ]

        if checkpoint_lines:
            print("LAST 5 CHECKPOINTS:")
            for line in checkpoint_lines[-5:]:
                print(f"  {line}")
        else:
            print("No checkpoints found")

    except Exception as e:
        print(f"Error reading crash log: {e}")
else:
    print("Crash log file not found at:", crash_log_file)
