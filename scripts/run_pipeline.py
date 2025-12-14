from __future__ import annotations

import os
import sys

# Make src/ importable when running "python scripts/run_pipeline.py"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

import os as _os
from seismo.fetch_usgs import fetch_events_geojson
from seismo.sonify import SonifyConfig, render_soundtrack, write_wav
from seismo.render_map import render_frames
from seismo.mux import frames_to_video, mux_audio


def main() -> None:
    # 1) Fetch events (tune these as you like)
    df = fetch_events_geojson(
        starttime="1970-01-01",
        endtime="2025-12-31",
        minmagnitude=6.0,
    )

    # MVP plate/region mapping (quick + reliable)
    def crude_plate(lat: float, lon: float) -> str:
        if -170 < lon < -30:
            return "Americas"
        if -30 <= lon <= 60:
            return "Africa-Europe"
        if 60 < lon <= 180:
            return "Asia-Pacific"
        return "Other"

    df["plate"] = [crude_plate(lat, lon) for lat, lon in zip(df["lat"], df["lon"])]

    # Plate -> waveform mapping (no MIDI required)
    plate_to_wave = {
        "Americas": "saw",
        "Africa-Europe": "tri",
        "Asia-Pacific": "square",
        "Other": "sine",
        "Unknown": "sine",
    }

    # 2) Sonify
    cfg = SonifyConfig(duration_s=120.0)  # start small to keep mp4 size manageable
    audio = render_soundtrack(df, cfg, plate_to_wave)

    _os.makedirs("out", exist_ok=True)
    write_wav("out/audio.wav", audio, cfg.sr)

    # 3) Render frames -> video
    fps = 20  # keep moderate for size + speed
    render_frames(df, out_dir="out/frames", duration_s=cfg.duration_s, fps=fps)
    frames_to_video("out/frames", fps, "out/video.mp4")

    # 4) Mux audio + video
    mux_audio("out/video.mp4", "out/audio.wav", "out/final.mp4")

    print("Done: out/final.mp4")


if __name__ == "__main__":
    main()