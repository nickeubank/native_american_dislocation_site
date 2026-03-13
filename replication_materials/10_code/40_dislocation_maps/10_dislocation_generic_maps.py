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
        legend_kwds={"shrink": 0.8, "aspect": 20, "pad": 0.01},
        figsize=(9, 9),
        vmin=-extrem,
        vmax=extrem,
        markersize=0.3,
        alpha=0.5,
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

    def add_district_label(x):
        coords = x.geometry.centroid.coords[0]
        if x["district_ai_share"] > 0.05:
            ax.annotate(
                # text=f"District {x['short_name']}",
                text=f'{x["short_name"]}, {x["district_ai_share"]:.0%} AI',
                xy=coords,
                ha="center",
                fontsize=10,
            )

    dist["short_name"] = dist["NAMELSAD"].str.replace(
        "State (Senate|House) District", "Dist", regex=True
    )
    dist.apply(add_district_label, axis=1)

    ax.set_axis_off()

    # Adjust layout to add space at the bottom
    ax.figure.subplots_adjust(bottom=0.15)

    # Add note below the plot
    ax.figure.text(
        0.17,
        0.05,
        f"{map_year-1} {states[state_fips]} State {level.capitalize()} Legislative map. District American Indian (AI) share of Voting Age"
        "\nPopulation shown under district name. "
        f"Each point is a representative voter generated from a "
        f"\n5% sample of Voting Age Population in {census_year} census. "
        "Colored dots are individuals who "
        "\nidentify as any-part Native American. Grey dots are individuals who did not identify "
        "as any \npart Native American.",
        ha="left",
        va="bottom",
        fontsize=12,
    )

    districting_cycle = 2012 if map_year == 2019 else 2022

    ax.figure.savefig(
        f"../../30_paper/maps/general_maps/"
        f"{state_abbrevs[state_fips]}_{districting_cycle}districting_cycle_{census_year}censusdemographics_{level}chamber.png"
    )

    print(ax)


for state in states.keys():
    for level in ["upper", "lower"]:
        for census_year in [2010, 2020]:
            for map_year in [2019, 2023]:
                plot_points(
                    state_fips=state,
                    level=level,
                    census_year=census_year,
                    color="PiYG",
                    map_year=map_year,
                    sample_pct=samples[state],
                )
