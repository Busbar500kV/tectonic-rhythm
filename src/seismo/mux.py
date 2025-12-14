from __future__ import annotations
import subprocess

def frames_to_video(frames_dir: str, fps: int, video_path: str):
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", f"{frames_dir}/frame_%06d.png",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        video_path
    ]
    subprocess.check_call(cmd)

def mux_audio(video_path: str, audio_path: str, out_path: str):
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        out_path
    ]
    subprocess.check_call(cmd)