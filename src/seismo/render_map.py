from __future__ import annotations

import os
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd


def render_frames(events, out_dir: str, duration_s: float, fps: int = 30) -> None:
    """
    Render seismic events on a dark-mode world map with coastline outlines.

    Improvements:
    - World map outline (Natural Earth)
    - Dark background with bright events
    - Display Month + Year instead of abstract t
    """

    os.makedirs(out_dir, exist_ok=True)

    # ---- Time handling (tz-safe, pandas-native) ----
    t0 = events["time"].min()
    t1 = events["time"].max()
    span = (t1 - t0).total_seconds()
    if span <= 0:
        raise ValueError("Need events spanning time.")

    nframes = int(duration_s * fps)

    # ---- Preconvert arrays ----
    lats = events["lat"].to_numpy()
    lons = events["lon"].to_numpy()
    mags = events["mag"].to_numpy()

    event_vid_times = (
        (events["time"] - t0).dt.total_seconds() / span * duration_s
    ).to_numpy()

    # ---- Load world map outline (once) ----
    world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))

    # ---- Styling ----
    bg_color = "black"
    map_color = "#444444"     # muted gray
    event_color = "#00BFFF"   # deep sky blue

    for i in range(nframes):
        now = i / fps

        # Sliding time window (seconds)
        window = 6.0
        mask = (event_vid_times >= now - window) & (event_vid_times <= now)
        idx = np.where(mask)[0]

        # ---- Interpolated real-world time for label ----
        frac = np.clip(now / duration_s, 0.0, 1.0)
        current_time = t0 + (t1 - t0) * frac
        time_label = current_time.strftime("%B %Y")

        # ---- Figure ----
        fig = plt.figure(figsize=(12, 6), dpi=150)
        ax = fig.add_subplot(111)
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)

        # World outline
        world.boundary.plot(
            ax=ax,
            linewidth=0.6,
            color=map_color,
            zorder=1
        )

        ax.set_xlim(-180, 180)
        ax.set_ylim(-90, 90)
        ax.set_xticks([])
        ax.set_yticks([])

        ax.set_title(
            f"Global Seismic Events — {time_label}",
            color="white",
            fontsize=12,
            pad=10
        )

        # ---- Plot events ----
        if idx.size:
            age = now - event_vid_times[idx]
            alpha = np.clip(1.0 - age / window, 0.05, 1.0)

            size = 12 + (mags[idx] ** 2)
            ax.scatter(
                lons[idx],
                lats[idx],
                s=size,
                c=event_color,
                alpha=alpha,
                edgecolors="none",
                zorder=2
            )

        frame_path = os.path.join(out_dir, f"frame_{i:06d}.png")
        fig.savefig(frame_path, facecolor=fig.get_facecolor())
        plt.close(fig)