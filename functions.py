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
    return gdf[(gdf[year_col] >= 2016) & (gdf[year_col] <= 2025)]


def calc_business_dynamics(open_close_gdf: gpd.GeoDataFrame, biz_gdf: gpd.GeoDataFrame, poly_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Calculates business dynamics metrics for each tract and year.
    
    Parameters:
        open_close_gdf: GeoDataFrame with openings and closings per tract per year
        biz_gdf: GeoDataFrame with individual business records
        poly_gdf: GeoDataFrame with tract/block group geometries and GEOID
    
    Returns:
        GeoDataFrame with net_change, growth_pct_over_2016, biz_stock, net_entry_rate, gross_exit_rate
    """
    gdf = open_close_gdf.copy()
    biz = biz_gdf.copy()

    ## net change (openings-closings)
    gdf['net_change'] = gdf['opened'] - gdf['closed']

    # get 2016 baseline of net change for each geometry
    baseline = gdf[gdf['year'] == 2016][['GEOID', 'net_change']].rename(columns={'net_change': 'baseline_2016'})

    # merge baseline into gdf of openings closings and tracts
    gdf = gdf.merge(baseline, on='GEOID')

    # calculating percent chg in growth from baseline of 2016
    gdf['growth_pct_over_2016'] = (gdf['net_change'] / gdf['baseline_2016']) * 100

    ## getting total number of businesses active in each year

    # first filling year_closed with 2025 in order to include active businesses in the range
    biz['year_closed'] = biz['year_closed'].fillna(2025).astype(int)
    biz['year_open'] = biz['year_open'].astype(int)

    # creating an active_years list for each business, which includes an integer of each year it was active at all
    biz['active_years'] = biz.apply(
        lambda row: list(range(row['year_open'], row['year_closed'] + 1)), axis=1
    )

    # explode takes a column of lists and creates a row for each item in the column, but still indexed by the same other info/columns
    # so here, it's creating a row for each active year of the business
    biz_exploded = biz.explode('active_years').rename(columns={'active_years': 'year'})

    # joining this exploded gdf with tract/grp GEOID of its location
    biz_exploded = gpd.sjoin(biz_exploded, poly_gdf[['GEOID', 'geometry']], how='left', predicate='within')

    # grouping by geoid and year and counting the number of businesses in each year
    biz_stock = biz_exploded.groupby(['GEOID', 'year']).size().reset_index(name='biz_stock')

    # joining that grouped df into gdf, which is already grouped by geoid and year
    # joining on the left, which means biz_stock rows for years not included in open_close will not be carried over
    gdf = gdf.merge(biz_stock, on=['GEOID', 'year'], how='left')

    # calculating net entry rate for each tract/grp and year
    gdf['net_entry_rate'] = (gdf['net_change'] / gdf['biz_stock']) * 100

    # gross exit rate, to help show how much turnover there was in relation to the net entry
    gdf['gross_exit_rate'] = (gdf['opened'] / gdf['biz_stock']) * 100


    return gdf