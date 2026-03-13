import re

import geopandas as gpd
import numpy as np
import pandas as pd
import partisan_dislocation as pdn
import us
import yaml

# Load states we want.
# This imports the yaml file in the code folder.
# We use the list of states and their fips codes a lot, so
# just saving in one place.
# This loads

with open("../config.yaml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)
states = cfg["states"]
samples = cfg["samples"]


state_abbrevs = {fips: us.states.lookup(fips).abbr for fips in states.keys()}

###########
#
# Plot states
#
###########

short_level = {"upper": "u", "lower": "l"}


def plot_points_NM_nw(
    state_fips, level, census_year, sample_pct, map_year, color="PiYG", legend=True
):

    # Projection
    if state_fips != "02":
        projection = "EPSG:32612"
    else:
        projection = "ESRI:102010"

    # Get points
    points = gpd.read_file(
        f"../../20_intermediate_data/30_dislocation/"
        f"dislocation_map{map_year}_{state_fips}_census{census_year}_{level}_{sample_pct * 100:.0f}pct.geojson"
    )
    points = points.to_crs(projection)
    extrem = np.abs(points.partisan_dislocation).max()

    # Get districts
    districts = gpd.read_file(
        f"../../00_source_data/state_legislative_districts/{map_year}/"
        f"{states[state_fips]}/{level}/"
        f"tl_{map_year}_{state_fips}_sld{short_level[level]}.shp"
    )

    districts = districts.to_crs(projection)

    ai = points[points.ai == 1].copy()
    non_ai = points[points.ai == 0].copy()

    ax = non_ai.plot(color="grey", markersize=1, alpha=0.2, figsize=(12, 12))

    ai.plot(
        "partisan_dislocation",
        ax=ax,
        cmap=color,
        legend=legend,
        legend_kwds={"shrink": 0.8, "aspect": 20, "pad": 0.05},
        figsize=(9, 9),
        vmin=-extrem,
        vmax=extrem,
        markersize=3,
        alpha=0.9,
    )
    ax.set_title(
        states[state_fips] + "\n" + level.capitalize() + " Legislative"
        "\n " + f"{census_year} Census Data, Districts from {map_year}"
    )

    # Add rotated text alongside the colorbar

    # text
    SPACES = 70
    ax.text(
        1.16,
        0.5,
        f'Native Racial Dislocation\nConcentrated{" "*SPACES}Diluted      \n("Packed"){" "*SPACES}("Cracked") ',
        transform=ax.transAxes,
        rotation=270,
        va="center",
        ha="center",
        fontsize=14,
    )

    dist_scores = points.groupby("NAMELSAD", as_index=False)[
        ["partisan_dislocation", "knn_shr_ai", "district_ai_share"]
    ].mean()

    dist = pd.merge(
        districts,
        dist_scores,
        on="NAMELSAD",
        how="outer",
        validate="1:1",
        indicator=True,
    )
    dist._merge.value_counts()

    dist.boundary.plot(ax=ax, edgecolor="black", linewidth=0.5)

    hand_adjustments = {
        1: (0, -3_000),
        2: (10_000, -40_000),
        3: (0, 0),
        4: (0, 10_000),
        7: (7_000, -5_000),
        8: (5_000, -15_000),
        9: (0, -15_000),
        22: (-5_000, -20_000),
        41: (-25_000, -20_000),
        43: (-10_000, 0),
        49: (0, 5_000),
        5: (0, 0),
        6: (0, 0),
        65: (-13_000, 0),
        69: (0, 25_000),
        9: (-10_000, 0),
    }

    def add_district_label(x):

        coords = x.geometry.centroid.coords[0]

        bbox_props = None
        if x["dist_num"] == 2:
            bbox_props = dict(
                boxstyle="round", facecolor="white", alpha=0.8, edgecolor="black"
            )

        if x["dist_num"] in hand_adjustments.keys():
            coords = (
                coords[0] + hand_adjustments[x["dist_num"]][0],
                coords[1] + hand_adjustments[x["dist_num"]][1],
            )

            ax.annotate(
                text=f'Dist {x["dist_num"]}\n{x["district_ai_share"]:.0%} AI',
                xy=coords,
                ha="center",
                fontsize=10,
                weight="bold",
                bbox=bbox_props,
            )

    dist["dist_num"] = (
        dist["NAMELSAD"]
        .str.replace("State (Senate|House) District ", "", regex=True)
        .astype("int")
    )
    dist.apply(add_district_label, axis=1)

    gpd.GeoSeries([districts.geometry.union_all()]).boundary.plot(
        ax=ax, edgecolor="black", linewidth=2
    )

    # Add bold black line from district 2 centroid down 30,000 units
    dist2_centroid = dist[dist["dist_num"] == 2].geometry.centroid.iloc[0]
    x_start = dist2_centroid.x - 1_000
    y_start = dist2_centroid.y
    x_end = x_start + hand_adjustments[2][0]
    y_end = y_start + hand_adjustments[2][1] + 5_000

    ax.plot([x_start, x_end], [y_start, y_end], color="black", linewidth=2)

    ax.set_xlim([670_000, 950_000])
    ax.set_ylim([3_750_000, 4_105_000])

    # ax.set_xlim([670_000, 950_000])
    # ax.set_ylim([3_825_000, 4_105_000])
    ax.set_axis_off()

    ax.figure.savefig(
        f"../../30_paper/maps/"
        f"NM_NWregion_specific_map{map_year}_{state_abbrevs[state_fips]}_census{census_year}_{level}_{sample_pct * 100:.0f}pct.pdf"
    )

    print(ax)


plot_points_NM_nw(
    state_fips="35",
    level="lower",
    census_year=2010,
    color="PiYG",
    map_year=2019,
    sample_pct=samples["35"],
)
plot_points_NM_nw(
    state_fips="35",
    level="lower",
    census_year=2020,
    color="PiYG",
    map_year=2023,
    sample_pct=samples["35"],
    legend=True,
)
