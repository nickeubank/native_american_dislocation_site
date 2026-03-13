##########
# Imports
##########

import re
import warnings
from itertools import product

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import seaborn.objects as so
import seaborn_objects_recipes as sor
import us
import yaml
from matplotlib import style

nick_theme = {**style.library["seaborn-v0_8-whitegrid"]}
nick_theme.update({"font.sans-serif": ["Fira Sans", "Arial", "sans-serif"]})
plt.rcParams.update(nick_theme)


###
# Load set of states to use
###

with open("../config.yaml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)
states = cfg["states"]
samples = cfg["samples"]
state_abbrevs = {fips: "_" + us.states.lookup(fips).abbr for fips in states.keys()}

###
# All points
###
points = pd.read_parquet("../../20_intermediate_data/45_all_ai_points.parquet")

points["ai_share_bins"] = (((points["district_ai_share"] * 100) // 5) * 5).astype("int")
points["ai_share_bins"] = points["ai_share_bins"].astype("category")
points["proportional_partisan_dislocation"] = (
    points["partisan_dislocation"] / points["knn_shr_ai"]
) * 100
points = points.reset_index(drop=True)


def native_box_plots(period, level, kind, state):

    # Subset data where required
    if period == 2018:
        plot_points = points[
            (points["map_year"] == 2019) & (points["census_year"] == 2010)
        ]
        map_year = 2018
        census_year = 2010
    if period == 2023:
        plot_points = points[
            (points["map_year"] == 2023) & (points["census_year"] == 2020)
        ]
        map_year = 2023
        census_year = 2020

    if level != "all":
        plot_points = plot_points[(plot_points["level"] == level)]
        chamber = f"{level} legislative chamber"
    if level == "all":
        chamber = f"both legislative chambers"

    if kind == "abs":
        y = "partisan_dislocation"
        yrange = (-0.5, 0.5)
        title_prefix = ""
        file_prefix = ""
    if kind == "proportional":
        y = "proportional_partisan_dislocation"
        yrange = (-100, 200)
        title_prefix = "Proportional "
        file_prefix = "proportinal_"

    if state != "all":
        plot_points = plot_points[plot_points["state_fips"] == state]
        state_list = f"{states[state]}."
        file_suffix = state_abbrevs[state]
    if state == "all":
        state_list = f"\n{', '.join(states.values())}."
        file_suffix = ""

    #################
    # Plot partisan dislocation dists
    #################

    fig, ax = plt.subplots()

    sns.boxplot(
        plot_points,
        y=y,
        x="ai_share_bins",
        showfliers=False,
        whis=[10, 90],
        width=0.6,
        color="white",
        linecolor="black",
        legend=False,
        ax=ax,
    )

    ax.xaxis.grid(False)
    ax.set(
        ylabel=f'{title_prefix}Racial Dislocation for Native VAP Constituents\n      Diluted{" "*30}Concentrated \n("Cracked"){" "*30}("Packed")',
        xlabel="Native VAP as % of District VAP",
    )
    ax.set_ylim(yrange)

    chamber_note = ""
    if chamber != "all":
        if state == "all":
            chamber_note = f"\n{level.capitalize()} Legislative Chambers"
        if state != "all":
            chamber_note = f"{level.capitalize()} Legislative Chamber"

    if state != "all":
        chamber_note = f"\n{states[state]} " + chamber_note

    ax.set_title(
        f"{title_prefix}Native Racial Dislocation by District Native Pct" + chamber_note
    )
    ax.axhline(y=0, color="darkred", linestyle="--", linewidth=1)
    sns.despine(trim=True, left=True)

    note = f"{title_prefix}Native Racial Dislocation distributions for {chamber} of {state_list}\nBased on {census_year} census data and {map_year-1} district maps.\nWhiskers cover 10th to 90th percentile of Native voter dislocation values."

    # Add note as text below the plot
    fig.text(
        0.1,
        -0.05,
        note,
        ha="left",
        va="top",
        fontsize=8,
        transform=fig.transFigure,
    )

    # Save the figure
    fig.savefig(
        f"../../30_paper/figures/{file_prefix}dislocation_by_district_AI_map{map_year}_census{census_year}_chamber{level}{file_suffix}.png",
        dpi=300,
        bbox_inches="tight",
    )


for period in [2018, 2023]:
    for level in ["all", "upper", "lower"]:
        for kind in ["abs", "proportional"]:
            for state in ["all"] + list(states.keys()):
                native_box_plots(period, level, kind, state)
