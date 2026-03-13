import re

import numpy as np
import pandas as pd
import us
import yaml

with open("../config.yaml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)
states = cfg["states"]


# Dists
dists = pd.read_parquet("../../20_intermediate_data/00_districts/all_districts.parquet")

# Add abbreviation
dists["district_state_abbr"] = dists["district_state_fips"].map(
    lambda x: us.states.lookup(x).abbr
)
dists.loc[dists["district_code"].str.isnumeric(), "district_code"] = (
    dists.loc[dists["district_code"].str.isnumeric(), "district_code"]
    .astype("int")
    .astype("str")
)

dists.loc[~dists["district_code"].str.isnumeric(), "district_code"] = dists.loc[
    ~dists["district_code"].str.isnumeric(), "district_code"
].str.replace("^0+", "", regex=True)

#########
# Native reps
#########

reps = pd.read_stata(
    "../../00_source_data/Blasingame_Replication/"
    "native_state_legislators_1993_2023.dta"
)

reps = reps[reps["Year"].notnull()]
reps = reps[reps.columns[0:6]]
reps.columns = [c.lower() for c in reps.columns]
# Keep states we study
state_names = list(states.values())

# Table 1
# reps[reps.year == 2023].groupby("state")[["district"]].count().sort_values("district")


state_abbrevs = []
for state_name in state_names:
    state = us.states.lookup(state_name)
    state_abbrevs.append(state.abbr)
assert len(state_abbrevs) == len(state_names)
reps = reps[reps["state"].isin(state_abbrevs) | (reps["year"] >= 2022)]
assert set(reps.loc[reps["year"] < 2022, "state"]) == set(state_abbrevs)

reps.loc[reps["chamber"] == "senate", "chamber"] = "u"
reps.loc[reps["chamber"] == "senator", "chamber"] = "u"
reps.loc[reps["chamber"] == "house", "chamber"] = "l"
reps["decade"] = (
    (reps.year - 2) // 10
) * 10  # two year shift for redistricting cycles.

reps["native_rep"] = 1
reps[(reps.state == "NM") & (reps.chamber == "u")]

has_rep = reps.groupby(["state", "chamber", "district", "decade"], as_index=False)[
    "native_rep"
].sum()
has_rep["map_year"] = ""
has_rep.loc[has_rep["decade"] == 2010, "map_year"] = "2018"
has_rep.loc[has_rep["decade"] == 2020, "map_year"] = "2022"
has_rep = has_rep[has_rep["decade"].isin([2010, 2020])]
has_rep["district"] = has_rep["district"].astype("str")

# Drop non-voting
has_rep = has_rep[has_rep["district"] != "131 (Non - Voting Tribal Member)"]

# NH has some weird naming conventions. Map onto what census has.
has_rep.loc[
    (has_rep["state"] == "NH") & (has_rep["district"] == "Merrimack 8"), "district"
] = "608"

# MN has an 08B, want to be 8B
has_rep.loc[(has_rep["state"] == "MN") & (has_rep["district"] == "08B"), "district"] = (
    "8B"
)

dist_and_reps = pd.merge(
    has_rep,
    dists,
    left_on=["state", "chamber", "district", "map_year"],
    right_on=[
        "district_state_abbr",
        "district_chamber",
        "district_code",
        "district_year",
    ],
    how="outer",
    indicator=True,
    validate="1:1",
)
dist_and_reps[dist_and_reps._merge == "left_only"]
dist_and_reps._merge.value_counts()
assert (dist_and_reps._merge != "left_only").all()
del dist_and_reps["_merge"]

dist_and_reps["native_rep"] = dist_and_reps["native_rep"].fillna(0)


dist_and_reps = dist_and_reps.drop(
    columns=["chamber", "district", "decade", "map_year", "state"]
)

# Just study sample
study_sample = dist_and_reps[dist_and_reps.district_state_fips.isin(states.keys())]
assert len(study_sample["district_state_fips"].unique()) == len(states)

for y in ["2018", "2022"]:
    assert len(
        study_sample.loc[
            (study_sample.district_year == y), "district_state_fips"
        ].unique()
    ) == len(states)

study_sample.to_parquet(
    "../../20_intermediate_data/00_districts/all_study_districts_w_reps.parquet",
    index=False,
)

# All 2022
dist_and_reps[dist_and_reps.district_year == "2022"].to_parquet(
    "../../20_intermediate_data/00_districts/all_districts_w_reps_2022.parquet",
    index=False,
)
