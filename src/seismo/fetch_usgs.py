from __future__ import annotations
import requests
import pandas as pd

USGS_EVENT_API = "https://earthquake.usgs.gov/fdsnws/event/1/query"

def fetch_events_geojson(
    starttime: str,
    endtime: str,
    minmagnitude: float = 5.5,
    limit: int | None = None,
) -> pd.DataFrame:
    """
    Fetch earthquakes from USGS ComCat/FDSN event service in GeoJSON format.
    Docs: https://earthquake.usgs.gov/fdsnws/event/1/  (format=geojson)
    """
    params = {
        "format": "geojson",
        "starttime": starttime,
        "endtime": endtime,
        "minmagnitude": minmagnitude,
        "orderby": "time-asc",
    }
    if limit is not None:
        params["limit"] = limit

    r = requests.get(USGS_EVENT_API, params=params, timeout=60)
    r.raise_for_status()
    gj = r.json()

    rows = []
    for f in gj.get("features", []):
        props = f["properties"]
        lon, lat, depth_km = f["geometry"]["coordinates"]
        rows.append({
            "time_ms": props["time"],
            "mag": props.get("mag"),
            "place": props.get("place"),
            "lat": lat,
            "lon": lon,
            "depth_km": depth_km,
            "id": f.get("id"),
        })

    df = pd.DataFrame(rows).dropna(subset=["mag", "lat", "lon"])
    df["time"] = pd.to_datetime(df["time_ms"], unit="ms", utc=True)
    return df