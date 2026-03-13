import re
import textwrap
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn.objects as so
import seaborn_objects_recipes as sor
import yaml
from matplotlib import style

warnings.simplefilter(action="ignore", category=FutureWarning)
nick_theme = {**style.library["seaborn-v0_8-whitegrid"]}
nick_theme.update({"font.sans-serif": ["Fira Sans", "Arial", "sans-serif"]})


with open("../config.yaml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)
states = cfg["states"]

#########
# Load districts and native data
#########

dists = pd.read_parquet(
    "../../20_intermediate_data/00_districts/all_study_districts_w_reps.parquet"
)
state_list = ", ".join((dists.district_state_abbr.unique()))


dists["any_native"] = (dists["native_rep"] > 0).astype("int")
dists = dists[
    [
        "any_native",
        "district_year",
        "vap_ai_2010",
        "vap_2010",
        "vap_ai_2020",
        "vap_2020",
        "district_state_abbr",
        "district_chamber",
    ]
]
dists["district_chamber"] = dists["district_chamber"].replace(
    {"u": "Upper Chamber", "l": "Lower Chamber"}
)


# All pooled

for census in [2010, 2020]:
    if census == 2010:
        dists_to_plot = dists[dists.district_year == "2018"]
        maps = 2018
        year_range = (2012, 2020)
    if census == 2020:
        dists_to_plot = dists[dists.district_year == "2022"]
        maps = 2022
        year_range = (2022, 2023)
    dists_to_plot[f"native_vap_{census}"] = (
        dists_to_plot[f"vap_ai_{census}"] / dists_to_plot[f"vap_{census}"]
    )

    # Plot
    fig, ax = plt.subplots()

    (
        so.Plot(dists_to_plot, x=f"native_vap_{census}", y="any_native")
        .add(so.Dots())
        .add(
            so.Line(),
            lowess := sor.Lowess(frac=0.4, gridsize=100, num_bootstrap=200, alpha=0.05),
        )
        .add(so.Band(), lowess)
        .label(
            title=f"Native VAP % and Probability of Electing Native Rep\n{census} Demographic Data, {maps} District Maps",
            y="Prob Electing Native Rep",
            x="District % Native",
        )
        .limit(x=(0.9, 0))
        .theme(nick_theme)
        .on(ax)
        .plot()
    )

    # Add averages per bin
    dists_to_plot["dist_ai_bin"] = (
        (dists_to_plot[f"native_vap_{census}"] // 0.1) * 0.1
    ) + 0.05
    binned_averages = dists_to_plot.groupby(["dist_ai_bin"], as_index=False)[
        "any_native"
    ].mean()

    blue_dots = "firebrick"

    (
        so.Plot(binned_averages, x=f"dist_ai_bin", y="any_native")
        .add(so.Dot(pointsize=7, marker="D", color=blue_dots))
        .limit(x=(0.9, 0))
        .label(
            title=f"Native VAP % and Probability of Electing Native Rep\n{census} Demographic Data, {maps} District Maps",
            y="Prob Electing Native Rep",
            x="District % Native",
        )
        .theme(nick_theme)
        .on(ax)
        .plot()
    )

    # Add dashed horizontal line at 50%
    ax.axhline(y=0.5, color="lightgrey", linestyle="--", linewidth=1.5)

    plt.tight_layout()

    # Add note at the bottom of the figure

    bottom_note = (
        f"Shaded region denotes 95% confidence interval. "
        f"Upper and lower chambers, {state_list}. Estimate of probability"
        f" of electing at least one Native Representative between {year_range[0]}"
        f" and {year_range[1]} (inclusive) according to data from Blasingame et al. (2024)."
    )
    bottom_note = textwrap.fill(bottom_note, width=90)
    ax.text(
        0.01,
        -0.15,
        bottom_note,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8,
    )

    blue_diamond_note = (
        f"Raw share of districts with Native representatives in "
        f"each 10% band plotted as red diamonds."
    )
    wrapped_text = textwrap.fill(blue_diamond_note, width=26)

    ax.text(
        0.35,
        0.9,
        wrapped_text,
        ha="left",
        va="top",
        color=blue_dots,
        fontsize=10,
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8, edgecolor=blue_dots),
    )

    # Save the figure
    fig.savefig(
        f"../../30_paper/figures/native_reps_probability_plot_census{census}.png",
        dpi=300,
        bbox_inches="tight",
    )

    #########
    # Lower Chamber
    ########
    fig, ax = plt.subplots()
    (
        so.Plot(
            dists_to_plot[dists_to_plot.district_chamber == "Lower Chamber"],
            x=f"native_vap_{census}",
            y="any_native",
        )
        .add(so.Dots())
        .add(
            so.Line(),
            lowess := sor.Lowess(frac=0.4, gridsize=100, num_bootstrap=200, alpha=0.05),
        )
        .add(so.Band(), lowess)
        .label(
            title=f"Native VAP % and Probability of Electing Native Rep\n{census} Demographic Data, {maps} District Maps\nLower Legislative Chamber",
            y="Prob Electing Native Rep",
            x="District % Native",
        )
        .limit(x=(0.9, 0))
        .theme(nick_theme)
        .on(ax)
        .plot()
    )

    # Add note at the bottom of the figure
    ax.text(
        0.01,
        -0.15,
        f"Shaded region denotes 95% confidence interval. Lower chamber, {state_list}."
        f"\nEstimate of probability of electing at least one Native Representative between\n{year_range[0]} and {year_range[1]} (inclusive) according to data from Blasingame et al. (2024).",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8,
    )

    # Save the figure
    fig.savefig(
        f"../../30_paper/figures/native_reps_probability_plot_census{census}_lowerchamber.png",
        dpi=300,
        bbox_inches="tight",
    )

    #########
    # Upper Chamber
    ########

    fig, ax = plt.subplots()
    (
        so.Plot(
            dists_to_plot[dists_to_plot.district_chamber == "Upper Chamber"],
            x=f"native_vap_{census}",
            y="any_native",
        )
        .add(so.Dots())
        .add(
            so.Line(),
            lowess := sor.Lowess(frac=0.5, gridsize=100, num_bootstrap=200, alpha=0.05),
        )
        .add(so.Band(), lowess)
        .label(
            title=f"Native VAP % and Probability of Electing Native Rep"
            f"\n{census} Demographic Data, {maps} District Maps"
            "\nUpper Legislative Chamber",
            y="Prob Electing Native Rep",
            x="District % Native",
        )
        .limit(x=(0.9, 0))
        .theme(nick_theme)
        .on(ax)
        .plot()
    )

    ax.text(
        0.01,
        -0.15,
        f"Shaded region denotes 95% confidence interval. Upper chamber, {state_list}."
        f"\nEstimate of probability of electing at least one Native Representative between\n{year_range[0]} and {year_range[1]} (inclusive) according to data from Blasingame et al. (2024).",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8,
    )

    # Save the figure
    fig.savefig(
        f"../../30_paper/figures/native_reps_probability_plot_census{census}_upperchamber.png",
        dpi=300,
        bbox_inches="tight",
    )

    ##############
    # By state
    ##############
    dists_to_plot["temp"] = 1
    dists_to_plot["district_n"] = dists_to_plot.groupby(["district_state_abbr"])[
        "temp"
    ].transform("sum")

    fig, ax = plt.subplots()
    (
        so.Plot(
            dists_to_plot[dists_to_plot.district_n > 60],
            x=f"native_vap_{census}",
            y="any_native",
            color="district_state_abbr",
        )
        .add(so.Dots())
        .add(
            so.Line(),
            lowess := sor.Lowess(frac=0.4, gridsize=100, num_bootstrap=200, alpha=0.9),
        )
        .add(so.Band(), lowess)
        .label(
            title=f"Native VAP % and Probability of Electing Native Rep"
            f"\n{census} Demographic Data, {maps} District Maps"
            f"\nStates With More Than 60 Legislative Districts",
            y="Prob Electing Native Rep",
            x="District % Native",
            color="State",
        )
        .limit(x=(0.9, 0))
        .theme(nick_theme)
        .on(ax)
        .plot()
    )

    state_list_bystate = list(
        dists_to_plot.loc[dists_to_plot.district_n > 60, "district_state_abbr"].unique()
    )

    ax.text(
        0.01,
        -0.15,
        f"Shaded region denotes 90% confidence interval. Both Chambers, {state_list_bystate}."
        f"\nEstimate of probability of electing at least one Native Representative between\n{year_range[0]} and {year_range[1]} (inclusive) according to data from Blasingame et al. (2024).",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8,
    )

    # Save the figure
    fig.savefig(
        f"../../30_paper/figures/native_reps_probability_plot_census{census}_bystate.png",
        dpi=300,
        bbox_inches="tight",
    )
