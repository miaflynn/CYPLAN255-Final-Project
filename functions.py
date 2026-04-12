import pandas as pd
import numpy as np
import geopandas as gpd


def group_points_by_poly_year (points: gpd.GeoDataFrame, polygons: gpd.GeoDataFrame):
    """
    Groups all the business location points by tract, year and status (open or closed)
    
    Parameters:
        points: geodataframe with point data
        polygons: geodataframe with tract geometries
    
    Returns:
        GeoDataFrame
    """

    points = gpd.sjoin(points, polygons, how="left", predicate="within")

    year_col = 'year_open' if 'year_open' in points.columns else 'year'

    tract_year = (
        points
        .groupby(["GEOID", year_col, "status"])
        .size()
        .reset_index(name="count")
        .pivot(index=["GEOID", year_col], columns="status", values="count")
        .fillna(0)
        .reset_index()
        .sort_values(year_col)
    )

    tracts_plot = polygons[["GEOID", "geometry"]].merge(
        tract_year,
        on="GEOID",
        how="left"
    ).fillna(0)

    return tracts_plot


def group_points_by_poly (points: gpd.GeoDataFrame, polygons: gpd.GeoDataFrame):
    """
    Groups all the business location points by tract and status (open or closed)
    
    Parameters:
        points: geodataframe with point data
        polygons: geodataframe with tract geometries
    
    Returns:
        GeoDataFrame
    """
    points = gpd.sjoin(points, polygons, how="left", predicate="within")

    tract_grouped = (
        points
        .groupby(["GEOID", 'status'])
        .size()
        .reset_index(name="count")
        .pivot(index=["GEOID"], columns="status", values="count")
        .fillna(0)
        .reset_index()
    )

    tracts_plot = polygons[["GEOID", "geometry"]].merge(
        tract_grouped,
        on="GEOID",
        how="left"
    ).fillna(0)

    return tracts_plot


def clip_to_2016(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    year_col = 'year_open' if 'year_open' in gdf.columns else 'year'
    return gdf[gdf[year_col] >= 2016]
