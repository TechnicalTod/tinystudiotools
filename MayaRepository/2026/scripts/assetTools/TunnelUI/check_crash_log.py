# Utility to check Maya crash log
import os

crash_log_file = r"C:\temp\maya_crash_debug.log"

print("=== MAYA CRASH LOG ANALYSIS ===")

if not os.path.exists(crash_log_file):
    print("❌ No crash log found at:", crash_log_file)
    print("Make sure you ran the crash logging test first.")
else:
    print(f"📁 Reading crash log: {crash_log_file}")
    print("=" * 50)

    try:
        with open(crash_log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if not lines:
            print("📄 Crash log is empty - Maya may have crashed before any checkpoints")
        else:
            # Show all lines
            for line in lines:
                print(line.rstrip())

            print("=" * 50)
            print(f"📊 Total log entries: {len(lines)}")

            # Find the last checkpoint
            checkpoint_lines = [
                line
                for line in lines
                if any(x in line for x in ["CHECKPOINT", "GEO-", "MAT-", "FBX-"])
            ]

            if checkpoint_lines:
                last_checkpoint = checkpoint_lines[-1].strip()
                print(f"🔍 LAST CHECKPOINT: {last_checkpoint}")

                # Analyze what the crash tells us
                if "GEO-5" in last_checkpoint and "GEO-6" not in str(lines):
                    print("💥 CRASH LOCATION: During maya_bridge.import_geometry() call")
                    print("   The FBX import itself is crashing")
                elif "MAT-3" in last_checkpoint and "MAT-4" not in str(lines):
                    print("💥 CRASH LOCATION: During create_usd_preview_material() call")
                    print("   Material creation is crashing")
                elif "Step 2: Calling mc.file()" in last_checkpoint:
                    print("💥 CRASH LOCATION: During FBX mc.file() import command")
                    print("   The low-level FBX import is crashing")
                else:
                    print("💥 CRASH LOCATION: Unknown - check the last few log entries")
            else:
                print("⚠️  No checkpoints found - crash happened very early")

    except Exception as e:
        print(f"❌ Error reading crash log: {e}")

print("=" * 50)
