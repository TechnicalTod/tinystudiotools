import subprocess
 
def composite_exr_sequences_to_mov(background_seq_pattern, foreground_seq_pattern, output_mov, framerate=24, chroma_key_color="0x00FF00", tolerance=0.1, blend=0.2):
    """
    Composites two EXR sequences into a .mov file using ffmpeg with a chroma key applied to the foreground.
 
    Args:
    - background_seq_pattern (str): Path pattern to the background EXR sequence (e.g., 'background_%04d.exr').
    - foreground_seq_pattern (str): Path pattern to the foreground EXR sequence (e.g., 'foreground_%04d.exr').
    - output_mov (str): Path to the output .mov file.
    - framerate (int): Frame rate of the sequences. Default is 24.
    - chroma_key_color (str): Color to key out from the foreground (in hex format, e.g., "0x00FF00" for green).
    - tolerance (float): Tolerance for the chroma key (default is 0.1).
    - blend (float): Blend for the chroma key (default is 0.2).
    """
    ffmpeg_command = [
        "ffmpeg",
        "-framerate", str(framerate),
        "-i", background_seq_pattern,
        "-i", foreground_seq_pattern,
        "-filter_complex", 
        f"[1:v]chromakey={chroma_key_color}:{tolerance}:{blend}[fg]; [0:v][fg]overlay=0:0",
        "-c:v", "prores_ks",
        "-pix_fmt", "yuv422p10le",
        output_mov
    ]
    # Run the ffmpeg command
    subprocess.run(ffmpeg_command, check=True)
 
# Example usage
background_seq_pattern = "Y:/CFX_1567_HOA/episodes/101/101_lud/101_lud_0280/publish/unreal_render/unreal_render_main/v003/HOA_101_lud_0280_unreal_render_main_v003.%04d.exr"
foreground_seq_pattern = "Y:/CFX_1567_HOA/episodes/101/101_lud/101_lud_0280/publish/plate_undist/undistorted_plate_bg01/v001/HOA_101_lud_0280_undistorted_plate_bg01_no_bbox_v001.%04d.exr"
output_mov = "C:/Users/sam.tack/Downloads/output.mov"
 
composite_exr_sequences_to_mov(background_seq_pattern, foreground_seq_pattern, output_mov)