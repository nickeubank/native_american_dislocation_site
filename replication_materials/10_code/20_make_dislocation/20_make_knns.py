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
samples = cfg["samples"]

###########
#
# Calculate Knns
#
###########

sample_pct = 0.05
short_level = {"upper": "u", "lower": "l"}
projection = "ESRI:102010"


def get_knns(state_fips, level, census_year, map_year):

    if state_fips == "04" and sample_pct == 0.1:
        print("skipping az")
        return "az done"

    if state_fips == "40" and sample_pct == 0.1:
        print("skipping OK")
        return "OK done"

    # # Debug
    # state_fips = "04"
    # level = "upper"
    # year = 2010

    # Get points
    state_points = gpd.read_file(
        f"../../20_intermediate_data/20_points/"
        f"points_{state_fips}_census{census_year}_{sample_pct * 100:.0f}pct.geojson"
    )
    state_points = state_points.to_crs(projection)

    # Get districts
    dists = gpd.read_file(
        f"../../00_source_data/state_legislative_districts/{map_year}/"
        f"{states[state_fips]}/{level}/"
        f"tl_{map_year}_{state_fips}_sld{short_level[level]}.shp"
    )
    dists = dists.to_crs(projection)

    # Get num districts
    num_dists = dists.NAMELSAD.nunique()
    assert len(dists) == num_dists

    target_k = len(state_points) / num_dists

    # Calculate knn
    knns = pdn.calculate_voter_knn(state_points, k=target_k, target_column="ai")
    knns = knns.rename({"knn_share_dem": "knn_share_ai"}, axis="columns")

    # Get dislocation scores
    dislocation = pdn.calculate_dislocation(
        knns,
        districts=dists,
        knn_column="knn_shr_ai",
        dem_column="ai",
        district_id_col="NAMELSAD",
    )

    dislocation = dislocation.to_crs(epsg=4326)
    dislocation.to_file(
        f"../../20_intermediate_data/30_dislocation/"
        f"dislocation_map{map_year}_{state_fips}_census{census_year}_{level}_{sample_pct * 100:.0f}pct.geojson"
    )
    dislocation = dislocation.drop("geometry", axis="columns")
    dislocation = pd.DataFrame(dislocation)
    dislocation.to_csv(
        f"../../20_intermediate_data/30_dislocation/"
        f"dislocation_map{map_year}_{state_fips}_census{census_year}_{level}_{sample_pct * 100:.0f}pct.csv"
    )

    print(f"done with points for {states[state_fips]}, {level}")
    return state_fips


# Run the func above in parallel across states.
from joblib import Parallel, delayed

loops = [
    {"state_fips": s, "level": level, "census_year": census_year, "map_year": map_year}
    for level in ["upper", "lower"]
    for s in states.keys()
    for census_year in [2010, 2020]
    for map_year in [2019, 2023]
]

successful_states = Parallel(n_jobs=1, timeout=999_999)(
    delayed(get_knns)(**l) for l in loops
)
