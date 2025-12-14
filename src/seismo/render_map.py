from __future__ import annotations
import os
import numpy as np
import matplotlib.pyplot as plt

def render_frames(events, out_dir: str, duration_s: float, fps: int = 30):
    os.makedirs(out_dir, exist_ok=True)
    t0 = events["time"].min()
    t1 = events["time"].max()
    span = (t1 - t0).total_seconds()

    nframes = int(duration_s * fps)

    # Preconvert to arrays for speed
    lats = events["lat"].to_numpy()
    lons = events["lon"].to_numpy()
    mags = events["mag"].to_numpy()
    times = events["time"].to_numpy()

    # map time->audio time
    def time_to_vid_s(t):
        # t is numpy datetime64[ns]
        dt = (t - np.datetime64(t0)).astype("timedelta64[s]").astype(float)
        return dt / span * duration_s

    event_vid_times = np.array([time_to_vid_s(t) for t in times])

    for i in range(nframes):
        now = i / fps
        # show last X seconds of events as fading trail
        window = 6.0
        mask = (event_vid_times >= now - window) & (event_vid_times <= now)
        idx = np.where(mask)[0]

        fig = plt.figure(figsize=(12, 6), dpi=150)
        ax = fig.add_subplot(111)
        ax.set_xlim(-180, 180)
        ax.set_ylim(-90, 90)
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_title(f"Global Seismic Events (t={now:0.1f}s)")
        ax.grid(True, linewidth=0.3)

        if idx.size:
            age = now - event_vid_times[idx]
            alpha = np.clip(1.0 - age / window, 0.05, 1.0)
            size = 10 + (mags[idx] ** 2)  # simple scale
            ax.scatter(lons[idx], lats[idx], s=size, alpha=alpha)

        frame_path = os.path.join(out_dir, f"frame_{i:06d}.png")
        fig.tight_layout()
        fig.savefig(frame_path)
        plt.close(fig)