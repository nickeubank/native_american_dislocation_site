import re
import textwrap

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import partisan_dislocation as pdn
import us
import yaml
from matplotlib import style
from matplotlib_inline.backend_inline import set_matplotlib_formats

# set_matplotlib_formats("retina")
nick_theme = {**style.library["seaborn-v0_8-whitegrid"]}
nick_theme.update({"font.sans-serif": ["Fira Sans", "Arial", "sans-serif"]})
plt.rcParams.update(nick_theme)

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

    fig, ax = plt.subplots(figsize=(9, 6))

    non_ai.plot(color="grey", markersize=1, alpha=0.2, ax=ax)

    ai.plot(
        "partisan_dislocation",
        ax=ax,
        cmap=color,
        legend=legend,
        legend_kwds={"shrink": 0.8, "aspect": 20, "pad": 0.02},
        vmin=-extrem,
        vmax=extrem,
        markersize=7,
        alpha=1,
    )
    fig.suptitle(
        states[state_fips]
        + "\n"
        + level.capitalize()
        + f" Legislative Chamber Districts in {map_year-1}",
        fontsize=16,
    )

    # Add rotated text alongside the colorbar

    # text
    SPACES = 35
    ax.text(
        1.16,
        0.5,
        f'Native Racial Dislocation\nConcentrated{" "*SPACES}Diluted      \n("Packed"){" "*SPACES}("Cracked") ',
        transform=ax.transAxes,
        rotation=270,
        va="center",
        ha="center",
        fontsize=12,
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

    gpd.GeoSeries([dist.geometry.union_all()]).boundary.plot(
        ax=ax, edgecolor="black", linewidth=1
    )

    # Turn off grid lines
    ax.grid(False)

    ax.set_xlim([100_000, 1_100_000])
    ax.set_ylim([4_900_000, 5_500_000])
    ax.set_axis_off()

    # Adjust layout to add more space at the bottom
    ax.figure.subplots_adjust(bottom=0.25)

    # Add note below the plot
    bottom_note = (
        f"{map_year-1} Montana State Senate district map."
        f"Each point is a representative voter generated from a "
        f"5% sample of Voting Age Population in {census_year} census. "
        "Colored dots are individuals "
        "who identify as any-part Native American. Grey dots are individuals who did not identify "
        "as any part Native American."
    )

    bottom_note = textwrap.fill(bottom_note, width=90)

    ax.figure.text(
        0.13,
        0.05,
        bottom_note,
        ha="left",
        va="bottom",
        fontsize=12,
    )

    ax.figure.savefig(
        f"../../30_paper/maps/"
        f"MT_map{map_year}_level{level}_{state_abbrevs[state_fips]}_census{census_year}_{sample_pct * 100:.0f}pct.pdf"
    )

    print(ax)


plot_points(
    state_fips="30",
    level="upper",
    census_year=2020,
    color="PiYG",
    map_year=2023,
    sample_pct=samples["30"],
)
