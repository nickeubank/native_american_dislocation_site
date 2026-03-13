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


def plot_points(
    state_fips, level, census_year, sample_pct, map_year, color="PiYG", legend=True
):

    # Projection
    if state_fips != "02":
        projection = "EPSG:32614"
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

    ax = non_ai.plot(color="grey", markersize=4, alpha=0.5, figsize=(12, 12))

    ai.plot(
        "partisan_dislocation",
        ax=ax,
        cmap=color,
        legend=legend,
        legend_kwds={"shrink": 0.8, "aspect": 20, "pad": 0.05},
        figsize=(9, 9),
        vmin=-extrem,
        vmax=extrem,
        markersize=4,
        alpha=0.8,
    )
    ax.set_title(
        states[state_fips] + "\n" + level.capitalize() + " Legislative"
        "\n " + f"{census_year} Census Data, Districts from {map_year-1}"
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
        17: (0, 50_000),
    }

    def add_district_label(x):

        coords = x.geometry.centroid.coords[0]

        if x["dist_num"] in hand_adjustments.keys():
            coords = (
                coords[0] + hand_adjustments[x["dist_num"]][0],
                coords[1] + hand_adjustments[x["dist_num"]][1],
            )

        ax.annotate(
            text=f'Dist {x["dist_num"]}\n{x["district_ai_share"]:.0%} AI',
            xy=coords,
            ha="center",
            fontsize=7,
            weight="bold",
        )

    dist["dist_num"] = dist["NAMELSAD"].str.replace(
        "State (Senate|House) District ", "", regex=True
    )
    dist.apply(add_district_label, axis=1)

    ax.set_xlim([150_000, 500_000])
    ax.set_ylim([4_700_000, 5_100_000])
    # ax.set_axis_off()

    ax.figure.savefig(
        f"../../30_paper/maps/"
        f"SD_specific_map{map_year}_{state_abbrevs[state_fips]}_census{census_year}_{level}_{sample_pct * 100:.0f}pct.pdf"
    )

    print(ax)


plot_points(
    state_fips="46",
    level="upper",
    census_year=2010,
    color="PiYG",
    map_year=2019,
    sample_pct=samples["46"],
)
