import re
from ast import literal_eval

import numpy as np
import pandas as pd
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
# Summary Tables
#
###########

gathered = list()

for state_fips in states.keys():
    for level in ["upper", "lower"]:
        for census_year in [2010, 2020]:
            for map_year in [2019, 2023]:

                # Get points
                points = pd.read_csv(
                    f"../../20_intermediate_data/30_dislocation/"
                    f"dislocation_map{map_year}_{state_fips}_census{census_year}_{level}_{samples[state_fips] * 100:.0f}pct.csv"
                )
                points = points[points.ai == 1]
                points = points.drop(columns="Unnamed: 0")
                points["state_fips"] = state_fips
                points["level"] = level
                points["map_year"] = map_year
                points["census_year"] = census_year
                points["state"] = states[state_fips]
                points["sample"] = samples[state_fips]
                gathered.append(points)
                # except:
                #     print(
                #         f'skip: "state_fips": "{state_fips}", "level": "{level}", "census_year": {census_year}, "map_year": {map_year}'
                #     )


df = pd.concat(gathered)
df.to_parquet("../../20_intermediate_data/45_all_ai_points.parquet", index=False)
