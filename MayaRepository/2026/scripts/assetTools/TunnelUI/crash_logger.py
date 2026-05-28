import os
import time
from datetime import datetime


class CrashLogger:
    def __init__(self, log_file_path=None):
        if log_file_path is None:
            # Write to a temp location that survives Maya crashes
            self.log_file = r"C:\temp\maya_crash_debug.log"
        else:
            self.log_file = log_file_path

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

        # Initialize log file
        self.log(f"=== CRASH DEBUG SESSION STARTED: {datetime.now()} ===")

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # Include milliseconds
        log_line = f"[{timestamp}] {message}\n"

        # Write immediately and flush to ensure it persists
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_line)
                f.flush()
                os.fsync(f.fileno())  # Force write to disk
        except Exception as e:
            print(f"Failed to write to crash log: {e}")

        # Also print to console if Maya is still alive
        print(f"🔍 {message}")


# Global logger instance
crash_logger = CrashLogger()
