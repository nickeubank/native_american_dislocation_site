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
states.keys()

all_states = {s.fips: s.name for s in us.STATES}


PROJECTION = "ESRI:102010"

chamber_long = {"u": "upper", "l": "lower"}

# Get Leg districts
district_list = list()


for map_year in ["2019", "2023"]:
    for chamber in ["u", "l"]:
        for state_fips in all_states.keys():
            # Skip over all 2019 non-study states
            included_state_year = (map_year != "2019") or (state_fips in states.keys())
            not_nebraska_lower = (state_fips != "31") or (chamber == "u")
            if included_state_year and not_nebraska_lower:
                if map_year == "2019":
                    suffix = "shp"
                if map_year == "2023":
                    suffix = "zip"
                dists = gpd.read_file(
                    f"../../00_source_data/state_legislative_districts/{map_year}/"
                    f"{all_states[state_fips]}/{chamber_long[chamber]}/"
                    f"tl_{map_year}_{state_fips}_sld{chamber}.{suffix}"
                )
                dists = dists.to_crs(PROJECTION)
                dists = dists[
                    [
                        "STATEFP",
                        "NAMELSAD",
                        f"SLD{chamber.upper()}ST",
                        "LSY",
                        "geometry",
                    ]
                ]
                dists = dists.rename(
                    columns={
                        "STATEFP": "district_state_fips",
                        "NAMELSAD": "district_name",
                        f"SLD{chamber.upper()}ST": "district_code",
                        "LSY": "district_year",
                    }
                )

                state_blocks = gpd.read_file(
                    f"../../20_intermediate_data/10_blockgroups/"
                    f"blockgroups_{state_fips}.geojson"
                )
                state_blocks = state_blocks.to_crs(PROJECTION)
                state_blocks["centroid"] = state_blocks.centroid
                state_blocks = state_blocks.set_geometry("centroid")

                # Join up.
                blocks_w_dist = state_blocks.sjoin(dists, how="left")
                assert blocks_w_dist["district_name"].notnull().mean() > 0.99

                blocks_w_dist = blocks_w_dist.drop(
                    columns=["index_right", "centroid", "geometry"]
                )

                vap_cols = [c for c in state_blocks.columns if re.match("vap_.*", c)]
                district_cols = [c for c in dists.columns if re.match("district_.*", c)]

                district_level = blocks_w_dist.groupby(district_cols, as_index=False)[
                    vap_cols
                ].sum()
                district_level["district_chamber"] = chamber
                district_list.append(district_level)

all_dists = pd.concat(district_list)
all_dists["study_state"] = all_dists["district_state_fips"].isin(states.keys())

all_dists.to_parquet(
    "../../20_intermediate_data/00_districts/all_districts.parquet", index=False
)
