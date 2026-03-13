import re

import geopandas as gpd
import numpy as np
import pandas as pd
import partisan_dislocation as pdn
import yaml

# Load states we want.
# This imports the yaml file in the code folder.
# We use the list of states and their fips codes a lot, so
# just saving in one place.
# This loads

with open("../config.yaml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)
states = cfg["states"]

###########
#
# Create Representative Points
#
###########

sample_pct = 0.05


def rep_points_in_state(s):
    state_blocks = gpd.read_file(
        f"../../20_intermediate_data/10_blockgroups/blockgroups_{s}.geojson"
    )
    state_blocks = state_blocks.to_crs("ESRI:102010")

    for year in [2010, 2020]:
        points = pdn.random_points_in_polygon(
            state_blocks,
            p=sample_pct,
            dem_vote_count=f"vap_ai_{year}",
            repub_vote_count=f"vap_nonai_{year}",
        )

        points = points.rename({"dem": "ai"}, axis="columns")
        print(f"done with AI points for {states[s]} in year {year}")

        points = points.to_crs(epsg=4326)

        points.to_file(
            f"../../20_intermediate_data/20_points/points_{s}_census{year}_{sample_pct * 100:.0f}pct.geojson"
        )

    print(f"done with points for {states[s]}")
    return s


# Run the func above in parallel across states.
from joblib import Parallel, delayed

points = Parallel(n_jobs=7)(delayed(rep_points_in_state)(s) for s in states.keys())
