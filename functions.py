import pandas as pd
import numpy as np
import geopandas as gpd


def group_points_by_tract_year (points: gpd.GeoDataFrame, tracts: gpd.GeoDataFrame):
    """
    Groups all the business location points by tract, year and status (open or closed)
    
    Parameters:
        points: geodataframe with point data
        tracts: geodataframe with tract geometries
    
    Returns:
        GeoDataFrame
    """
    tract_year = (
        points
        .groupby(["GEOID", "year", "status"])
        .size()
        .reset_index(name="count")
        .pivot(index=["GEOID", "year"], columns="status", values="count")
        .fillna(0)
        .reset_index()
        .sort_values('year')
    )

    tracts_plot = tracts[["GEOID", "geometry"]].merge(
        tract_year,
        on="GEOID",
        how="left"
    ).fillna(0)

    return tracts_plot


def group_points_by_tract (points: gpd.GeoDataFrame, tracts: gpd.GeoDataFrame):
    """
    Groups all the business location points by tract and status (open or closed)
    
    Parameters:
        points: geodataframe with point data
        tracts: geodataframe with tract geometries
    
    Returns:
        GeoDataFrame
    """
    tract_grouped = (
        points
        .groupby(["GEOID", 'status'])
        .size()
        .reset_index(name="count")
        .pivot(index=["GEOID"], columns="status", values="count")
        .fillna(0)
        .reset_index()
    )

    tracts_plot = tracts[["GEOID", "geometry"]].merge(
        tract_grouped,
        on="GEOID",
        how="left"
    ).fillna(0)

    return tracts_plot



