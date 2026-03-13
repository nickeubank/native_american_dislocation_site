import numpy as np
import pandas as pd
import us
import yaml

with open("../config.yaml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)
states = cfg["states"]

######
# District data
######

dists = pd.read_parquet(
    "../../20_intermediate_data/00_districts/all_districts_w_reps_2022.parquet"
)
dists

dists["share_native_vap"] = dists["vap_ai_2020"] / dists["vap_2020"]


# Just dists with native rep
native_dists = dists[dists["native_rep"] > 0]

native_dists["State"] = native_dists["district_state_abbr"].map(
    lambda x: us.states.lookup(x).name
)

means = native_dists.groupby("State", as_index=False)["share_native_vap"].mean()
medians = native_dists.groupby("State", as_index=False)["share_native_vap"].median()
table = pd.merge(means, medians, on="State", validate="1:1", indicator=True)
assert (table._merge == "both").all()
del table["_merge"]
table = table.rename(
    columns={
        "share_native_vap_x": "Mean Native VAP",
        "share_native_vap_y": "Median Native VAP",
    }
)

# State native share for sorting, leaning on equal population rules
lowers = dists.loc[
    dists["district_chamber"] == "l",
    ["district_state_abbr", "native_rep", "vap_2020", "vap_ai_2020"],
]
summed = lowers.groupby("district_state_abbr", as_index=False)[
    ["vap_2020", "vap_ai_2020", "native_rep"]
].sum()
summed["state_share_native"] = summed["vap_ai_2020"] / summed["vap_2020"]
summed[["state_share_native", "district_state_abbr"]]
summed["State"] = summed["district_state_abbr"].map(lambda x: us.states.lookup(x).name)

table = pd.merge(table, summed, how="outer", on="State", validate="1:1", indicator=True)
table["_merge"].value_counts()
assert (table["_merge"] != "left_only").all()
table = table[table["_merge"] == "both"]
del table["_merge"]

# Tabulate

from tabulate import tabulate

latex_table = tabulate(
    table.sort_values("state_share_native", ascending=True)[
        ["State", "Mean Native VAP"]
    ],
    headers="keys",
    tablefmt="latex",
    showindex=False,
    floatfmt="0.0%",
)

print(latex_table)
with open(
    f"../../30_paper/stats/state_district_mean_native_vap.tex",
    "w",
) as f:
    f.write(latex_table)

print(
    tabulate(
        table.sort_values("state_share_native", ascending=True)[
            ["State", "Mean Native VAP", "state_share_native", "native_rep"]
        ],
        headers="keys",
        tablefmt="latex",
        showindex=False,
        floatfmt="0.2%",
    )
)
