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
from matplotlib.ticker import MaxNLocator

warnings.simplefilter(action="ignore", category=FutureWarning)
nick_theme = {**style.library["seaborn-v0_8-whitegrid"]}
nick_theme.update({"font.sans-serif": ["Fira Sans", "Arial", "sans-serif"]})

with open("../config.yaml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)
states = cfg["states"]

######
# District data
######

dists = pd.read_parquet(
    "../../20_intermediate_data/00_districts/all_study_districts_w_reps.parquet"
)
state_list = ", ".join((dists.district_state_abbr.unique()))

dists.district_state_abbr.value_counts()

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
    ]
]
dists["native_vap_2010"] = dists["vap_ai_2010"] / dists["vap_2010"]
dists["native_vap_2020"] = dists["vap_ai_2020"] / dists["vap_2020"]

#########
# All pooled
########

for census in [2010, 2020]:

    if census == 2010:
        dists_to_plot = dists[dists["district_year"] == "2018"]
        district_year = "2018"
    if census == 2020:
        dists_to_plot = dists[dists["district_year"] == "2022"]
        district_year = "2022"
    dists_to_plot[f"native_vap_binned_{census}"] = (
        ((dists_to_plot[f"native_vap_{census}"] * 100)) // 10
    ) * 10 + 5
    dists_binned = dists_to_plot.groupby(
        [f"native_vap_binned_{census}", "any_native"], as_index=False
    )["district_year"].count()
    dists_binned

    dists_binned = dists_binned.rename(
        columns={"district_year": "num_districts_by_native"}
    )
    dists_binned["num_districts"] = dists_binned.groupby(
        [f"native_vap_binned_{census}"], as_index=False
    )["num_districts_by_native"].transform(np.sum)

    dists_binned["any_native"] = dists_binned["any_native"].astype("bool")

    # Summary Stats
    stats = dict()
    stats["total_native_districts"] = (
        dists_binned.loc[dists_binned["any_native"], "num_districts_by_native"]
        .sum()
        .squeeze()
    )

    stats["num_districts_over50vap"] = (
        dists_binned.loc[
            (~dists_binned["any_native"])
            & (dists_binned[f"native_vap_binned_{census}"] > 45),
            "num_districts_by_native",
        ]
        .sum()
        .squeeze()
    )

    stats["num_native_districts_over50vap"] = (
        dists_binned.loc[
            dists_binned["any_native"]
            & (dists_binned[f"native_vap_binned_{census}"] > 45),
            "num_districts_by_native",
        ]
        .sum()
        .squeeze()
    )

    stats["share_native_districts_over50"] = (
        stats["num_native_districts_over50vap"] / stats["total_native_districts"]
    )

    stats["num_native_districts_over50vap"] = (
        dists_binned.loc[
            dists_binned["any_native"]
            & (dists_binned[f"native_vap_binned_{census}"] > 45),
            "num_districts_by_native",
        ]
        .sum()
        .squeeze()
    )

    stats["share_native_districts_over50"] = (
        stats["num_native_districts_over50vap"] / stats["total_native_districts"]
    )

    left_bar = dists_binned.loc[
        dists_binned["any_native"] & (dists_binned[f"native_vap_binned_{census}"] == 5),
        ["num_districts_by_native", "num_districts"],
    ]

    stats["share_leftbar_dists_native"] = (
        left_bar["num_districts_by_native"] / left_bar["num_districts"]
    ).squeeze()
    stats["num_leftbar_dists_native"] = (left_bar["num_districts_by_native"]).squeeze()
    stats["num_leftbar_dists_total"] = (left_bar["num_districts"]).squeeze()

    for k in stats.keys():
        with open(
            f"../../30_paper/" f"stats/{k}_{census}.tex",
            "w",
        ) as f:
            if k[0:3] == "num":
                f.write(f"{stats[k]:0.0f}")
            else:
                f.write(f"{stats[k]:0.1%}")

    ########
    # Plot
    ########
    fig, ax = plt.subplots()
    (
        so.Plot(
            dists_binned,
            x=f"native_vap_binned_{census}",
            y="num_districts_by_native",
            color="any_native",
        )
        .add(so.Bar(), so.Stack())
        .label(
            title="Native VAP % and History of Electing Native Rep"
            f"\nUpper and Lower Chambers of Study States \n"
            f"Districts from {district_year}, Demographics from {census} Census",
            y="Number of Districts",
            x="District Native Voting Age Population Percentage",
            color="District Has\nElected Native Rep",
        )
        .limit(y=(0, 100))
        .theme(nick_theme)
        .on(ax)
        .plot()
    )

    # Add light grey horizontal gridlines every 10 units
    ax.yaxis.grid(True, which="major", color="lightgrey", linewidth=0.5)
    ax.set_yticks(range(0, 101, 10))

    total_below_10 = dists_binned.loc[
        (dists_binned[f"native_vap_binned_{census}"] == 5)
        & (~dists_binned[f"any_native"]),
        "num_districts",
    ].squeeze()
    native_elected_below_10 = dists_binned.loc[
        (dists_binned[f"native_vap_binned_{census}"] == 5)
        & (dists_binned[f"any_native"]),
        "num_districts_by_native",
    ].squeeze()

    # Add text annotation in upper right
    truncation_note = (
        f"Y-axis truncated for readability. There are {total_below_10} "
        f"districts where the Voting Age Population is less than 10% Native."
        f" {native_elected_below_10} have elected Native representatives."
    )
    truncation_note = textwrap.fill(truncation_note, width=30)

    ax.text(
        0.98,
        0.98,
        truncation_note,
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=9,
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.9, edgecolor="black"),
    )

    # Save the figure
    fig.savefig(
        f"../../30_paper/figures/district_native_share_hist_{census}.png",
        dpi=300,
        bbox_inches="tight",
    )

#######
# By state
########
for census in [2010, 2020]:
    if census == 2010:
        dists_to_plot = dists[dists["district_year"] == "2018"]
        district_year = "2018"
    if census == 2020:
        dists_to_plot = dists[dists["district_year"] == "2022"]
        district_year = "2022"

    dists_to_plot[f"native_vap_binned_{census}"] = (
        ((dists_to_plot[f"native_vap_{census}"] * 100)) // 10
    ) * 10 + 5

    dists_binned_state = dists_to_plot.groupby(
        [f"native_vap_binned_{census}", "any_native", "district_state_abbr"],
        as_index=False,
    )["district_year"].count()
    dists_binned_state

    dists_binned_state = dists_binned_state.rename(
        columns={"district_year": "num_districts_by_native"}
    )
    dists_binned_state["num_districts"] = dists_binned_state.groupby(
        [f"native_vap_binned_{census}", "district_state_abbr"], as_index=False
    )["num_districts_by_native"].transform(np.sum)

    dists_binned_state["any_native"] = dists_binned_state["any_native"].astype("bool")

    # Montana stats
    stats = dict()

    # MT
    stats["num_native_districts_over40vap_MT"] = (
        dists_binned_state.loc[
            (dists_binned_state["any_native"])
            & (dists_binned_state[f"native_vap_binned_{census}"] > 35)
            & (dists_binned_state[f"district_state_abbr"] == "MT"),
            "num_districts_by_native",
        ]
        .sum()
        .squeeze()
    )

    stats["total_native_districts_MT"] = (
        dists_binned_state.loc[
            dists_binned_state["any_native"]
            & (dists_binned_state[f"district_state_abbr"] == "MT"),
            "num_districts_by_native",
        ]
        .sum()
        .squeeze()
    )

    stats["share_native_districts_over40_MT"] = (
        stats["num_native_districts_over40vap_MT"] / stats["total_native_districts_MT"]
    )

    for k in stats.keys():
        with open(
            f"../../30_paper/" f"stats/{k}_{census}.tex",
            "w",
        ) as f:
            if k[0:3] == "num":
                f.write(f"{stats[k]:0.0f}")
            else:
                f.write(f"{stats[k]:0.1%}")

    ######
    # Plots
    ######
    fig, axs = plt.subplots(nrows=4, ncols=2, sharex="all", figsize=(12, 16))
    fig.subplots_adjust(hspace=0.4)  # Add vertical space between subplots
    for idx, state in enumerate(dists_binned_state.district_state_abbr.unique()):

        # Pull out first column info for note
        state_dists = dists_binned_state[
            dists_binned_state["district_state_abbr"] == state
        ]

        first_col = state_dists.loc[
            state_dists[f"native_vap_binned_{census}"] == 5, "num_districts"
        ].max()
        second_col = state_dists.loc[
            state_dists[f"native_vap_binned_{census}"] != 5, "num_districts"
        ].max()

        upper_bound = ((first_col - second_col) / 5) + second_col
        if upper_bound < second_col:
            upper_bound = second_col + 2

        state_total_below_10 = state_dists.loc[
            (state_dists[f"native_vap_binned_{census}"] == 5)
            & (~state_dists[f"any_native"]),
            "num_districts",
        ].squeeze()
        state_native_elected_below_10 = state_dists.loc[
            (state_dists[f"native_vap_binned_{census}"] == 5)
            & (state_dists[f"any_native"]),
            "num_districts_by_native",
        ].squeeze()

        if isinstance(state_native_elected_below_10, pd.Series):
            state_native_elected_below_10 = 0

        width = 0.8
        if state == "AZ":
            width = 0.2

        (
            so.Plot(
                dists_binned_state[dists_binned_state["district_state_abbr"] == state],
                x=f"native_vap_binned_{census}",
                y="num_districts_by_native",
                color="any_native",
            )
            .add(so.Bar(width=width), so.Stack())
            .label(
                title=f"{state}",
                y="Number of Districts",
                x="District Native Voting Age Population Percentage",
                color="District Has\nElected Native Rep",
            )
            .limit(x=(0, 95), y=(0, upper_bound))
            .theme(nick_theme)
            .on(axs.flatten()[idx])
            .plot()
        )

        axs.flatten()[idx].yaxis.set_major_locator(MaxNLocator(integer=True))
        # Add text annotation in upper right
        truncation_note = (
            f"{state_total_below_10} districts < 10% Native VAP\n"
            f"{state_native_elected_below_10} have elected Native reps."
        )
        axs.flatten()[idx].text(
            0.25,
            0.95,
            truncation_note,
            transform=axs.flatten()[idx].transAxes,
            ha="left",
            va="top",
            fontsize=14,
            bbox=dict(
                boxstyle="round", facecolor="white", alpha=0.9, edgecolor="black"
            ),
        )

    for i in fig.legends:
        i.set_bbox_to_anchor((0.55, 0.2))

    fig.suptitle(
        "District Native VAP\n"
        "by State and Whether Has Elected Native Rep\n"
        f"Districts from {district_year}, Demographics from {census} Census",
        fontsize=16,
    )
    # fig.tight_layout(rect=[0, 0, 0.85, 1])
    fig.text(
        0.5,
        0.02,
        "First column truncated for readability in all plots but AK.",
        ha="center",
        va="top",
        fontsize=12,
    )

    # Get rid of last one
    axs[3, 1].axis("off")
    # Save the figure
    fig.savefig(
        f"../../30_paper/figures/district_native_share_hist_{census}_bystate.png",
        dpi=300,
        bbox_inches="tight",
    )
