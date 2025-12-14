from __future__ import annotations
import geopandas as gpd
from shapely.geometry import Point

def load_plate_polygons(plates_path: str) -> gpd.GeoDataFrame:
    """
    Expect a polygon dataset of tectonic plates (PB2002-derived).
    If you only have boundaries (lines), grab a plate polygon layer instead.
    """
    gdf = gpd.read_file(plates_path)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    else:
        gdf = gdf.to_crs("EPSG:4326")
    return gdf

def tag_plate(events_df, plates_gdf: gpd.GeoDataFrame, plate_name_col: str = "PlateName"):
    """
    Point-in-polygon join: assigns each event to a plate polygon.
    """
    egdf = gpd.GeoDataFrame(
        events_df.copy(),
        geometry=[Point(xy) for xy in zip(events_df["lon"], events_df["lat"])],
        crs="EPSG:4326",
    )
    joined = gpd.sjoin(egdf, plates_gdf[[plate_name_col, "geometry"]], how="left", predicate="within")
    joined = joined.drop(columns=["index_right"], errors="ignore")
    joined.rename(columns={plate_name_col: "plate"}, inplace=True)
    joined["plate"] = joined["plate"].fillna("Unknown")
    return joined.drop(columns=["geometry"])