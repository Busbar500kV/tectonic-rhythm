from __future__ import annotations

import os
import urllib.request
import zipfile
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd


# Prefer CDN mirror first (reliable for automated downloads).
NE_URLS = [
    "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip",
    # Fallback: original site (sometimes returns 406 without good headers)
    "https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/110m/cultural/ne_110m_admin_0_countries.zip",
]


def _download_with_headers(url: str, dst_path: str) -> None:
    req = urllib.request.Request(
        url,
        headers={
            # Make it look like a real browser
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
            "Accept": "*/*",
        },
        method="GET",
    )
    with urllib.request.urlopen(req) as resp, open(dst_path, "wb") as f:
        f.write(resp.read())


def _load_world_outline() -> gpd.GeoDataFrame:
    """
    Download and cache Natural Earth world boundaries if needed.
    Works with GeoPandas >= 1.0 (no geopandas.datasets dependency).
    """
    data_dir = os.path.join("data", "natural_earth")
    shp_path = os.path.join(data_dir, "ne_110m_admin_0_countries.shp")

    if not os.path.exists(shp_path):
        os.makedirs(data_dir, exist_ok=True)
        zip_path = os.path.join(data_dir, "ne_110m_admin_0_countries.zip")

        last_err = None
        for url in NE_URLS:
            try:
                print(f"Downloading Natural Earth boundaries from: {url}")
                _download_with_headers(url, zip_path)
                last_err = None
                break
            except Exception as e:
                last_err = e
                print(f"Download failed from {url}: {e}")

        if last_err is not None:
            raise RuntimeError(
                "Could not download Natural Earth dataset from any source. "
                "Check network access or switch to a different mirror."
            ) from last_err

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(data_dir)

    return gpd.read_file(shp_path)


def render_frames(events, out_dir: str, duration_s: float, fps: int = 30) -> None:
    """
    Render seismic events on a dark-mode world map outline with Month–Year labels.
    """
    os.makedirs(out_dir, exist_ok=True)

    # ---- Time handling (tz-safe, pandas-native) ----
    t0 = events["time"].min()
    t1 = events["time"].max()
    span = (t1 - t0).total_seconds()
    if span <= 0:
        raise ValueError("Need events spanning time.")

    nframes = int(duration_s * fps)

    lats = events["lat"].to_numpy()
    lons = events["lon"].to_numpy()
    mags = events["mag"].to_numpy()

    # tz-safe, pandas-native timing -> seconds in compressed video space
    event_vid_times = (
        (events["time"] - t0).dt.total_seconds() / span * duration_s
    ).to_numpy()

    # ---- Load world outline (cached locally after first download) ----
    world = _load_world_outline()

    # ---- Styling (dark mode) ----
    bg_color = "black"
    map_color = "#444444"     # muted outline
    event_color = "#00BFFF"   # bright cyan

    for i in range(nframes):
        now = i / fps

        window = 6.0
        mask = (event_vid_times >= now - window) & (event_vid_times <= now)
        idx = np.where(mask)[0]

        # Label Month + Year (interpolated narrative time)
        frac = np.clip(now / duration_s, 0.0, 1.0)
        current_time = t0 + (t1 - t0) * frac
        time_label = current_time.strftime("%B %Y")

        fig = plt.figure(figsize=(12, 6), dpi=150)
        ax = fig.add_subplot(111)
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)

        # Map outline
        world.boundary.plot(ax=ax, linewidth=0.6, color=map_color, zorder=1)

        ax.set_xlim(-180, 180)
        ax.set_ylim(-90, 90)
        ax.set_xticks([])
        ax.set_yticks([])

        ax.set_title(
            f"Global Seismic Events — {time_label}",
            color="white",
            fontsize=12,
            pad=10,
        )

        # Events
        if idx.size:
            age = now - event_vid_times[idx]
            alpha = np.clip(1.0 - age / window, 0.05, 1.0)
            size = 12 + (mags[idx] ** 2)

            ax.scatter(
                lons[idx], lats[idx],
                s=size,
                c=event_color,
                alpha=alpha,
                edgecolors="none",
                zorder=2,
            )

        frame_path = os.path.join(out_dir, f"frame_{i:06d}.png")
        fig.savefig(frame_path, facecolor=fig.get_facecolor())
        plt.close(fig)