from __future__ import annotations
import os
from seismo.fetch_usgs import fetch_events_geojson
from seismo.sonify import SonifyConfig, render_soundtrack, write_wav
from seismo.render_map import render_frames
from seismo.mux import frames_to_video, mux_audio

def main():
    # 1) Fetch events (pick a range you like)
    df = fetch_events_geojson(
        starttime="1970-01-01",
        endtime="2025-12-31",
        minmagnitude=6.0,
    )

    # For MVP, just map plates coarsely by hemisphere or region
    # Later we’ll replace this with real PB2002 polygons + point-in-poly join.
    def crude_plate(lat, lon):
        if lon < -30 and lon > -170:
            return "Americas"
        if lon >= -30 and lon <= 60:
            return "Africa-Europe"
        if lon > 60 and lon <= 180:
            return "Asia-Pacific"
        return "Other"

    df["plate"] = [crude_plate(lat, lon) for lat, lon in zip(df["lat"], df["lon"])]

    plate_to_wave = {
        "Americas": "saw",
        "Africa-Europe": "tri",
        "Asia-Pacific": "square",
        "Other": "sine",
        "Unknown": "sine",
    }

    # 2) Sonify
    cfg = SonifyConfig(duration_s=240.0)  # 4 minutes
    audio = render_soundtrack(df, cfg, plate_to_wave)
    os.makedirs("out", exist_ok=True)
    write_wav("out/audio.wav", audio, cfg.sr)

    # 3) Video frames + video
    fps = 30
    render_frames(df, out_dir="out/frames", duration_s=cfg.duration_s, fps=fps)
    frames_to_video("out/frames", fps, "out/video.mp4")

    # 4) Mux
    mux_audio("out/video.mp4", "out/audio.wav", "out/final.mp4")
    print("Done: out/final.mp4")

if __name__ == "__main__":
    main()