import re

import geopandas as gpd
import numpy as np
import pandas as pd
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


###########
#
# Load block groups,
# merge with tabular data
#
###########

# Tables with 1990, 2000, 2010, and 2020 VAP
# harmonized to 2010 block groups.
tables = pd.read_csv(
    "../../00_source_data/2010_census_blockgroups/voting_age_population/"
    "voting_age_pop_1990_2000_2010_2020/"
    "voting_age_pop_1990_2000_2010_2020_geog2010_blck_grp.csv"
)

# 2010 block groups to merge with tables
shp_2010 = gpd.read_file(
    "../../00_source_data/2010_census_blockgroups/voting_age_population/"
    "us_2010_blockgroup_shapefile.zip"
)
# drop Puerto Rico
shp_2010 = shp_2010[shp_2010.STATEFP10 != "72"].copy()

###
# Merge up and validate
###
blocks = shp_2010.merge(
    tables, how="left", on="GISJOIN", validate="1:1", indicator=True
)
blocks.crs
# Anything with a geography should have tabular data
assert (blocks._merge != "left_only").all()

# Also checked that right_only merges all had population zero,
# but an outer join doesn't get us back a geodataframe, so
# moved merge to left and commented out code below.
# assert (blocks[blocks._merge == "right_only"].D06AB2010 == 0).all()
# blocks = blocks[blocks._merge != "right_only"].copy()

blocks = blocks.drop(["_merge"], axis="columns")

##########
#
# Load block groups,
# merge with tabular data
#
###########

# American Indians and others
for year in [2000, 2010, 2020]:
    blocks[f"vap_{year}"] = blocks[f"D06AB{year}"].copy()
    native_american_fields = [
        "AD",  # Time series AD: Persons: 18 years and over ~ Of one race--American Indian and Alaska Native alone
        "AK",  # Time series AK: Persons: 18 years and over ~ Of two races--White; American Indian and Alaska Native
        "AO",  # Time series AO: Persons: 18 years and over ~ Of two races--Black or African American; American Indian and Alaska Native
        "AS",  # Time series AS: Persons: 18 years and over ~ Of two races--American Indian and Alaska Native; Asian
        "AT",  # Time series AT: Persons: 18 years and over ~ Of two races--American Indian and Alaska Native; Native Hawaiian and Other Pacific Islander
        "AU",  # Time series AU: Persons: 18 years and over ~ Of two races--American Indian and Alaska Native; Some Other Race
        "AZ",  # Time series AZ: Persons: 18 years and over ~ Of three races--White; Black or African American; American Indian and Alaska Native
        "BD",  # Time series BD: Persons: 18 years and over ~ Of three races--White; American Indian and Alaska Native; Asian
        "BE",  # Time series BE: Persons: 18 years and over ~ Of three races--White; American Indian and Alaska Native; Native Hawaiian and Other Pacific Islander
        "BF",  # Time series BF: Persons: 18 years and over ~ Of three races--White; American Indian and Alaska Native; Some Other Race
        "BJ",  # Time series BJ: Persons: 18 years and over ~ Of three races--Black or African American; American Indian and Alaska Native; Asian
        "BK",  # Time series BK: Persons: 18 years and over ~ Of three races--Black or African American; American Indian and Alaska Native; Native Hawaiian and Other Pacific Islander
        "BL",  # Time series BL: Persons: 18 years and over ~ Of three races--Black or African American; American Indian and Alaska Native; Some Other Race
        "BP",  # Time series BP: Persons: 18 years and over ~ Of three races--American Indian and Alaska Native; Asian; Native Hawaiian and Other Pacific Islander
        "BQ",  # Time series BQ: Persons: 18 years and over ~ Of three races--American Indian and Alaska Native; Asian; Some Other Race
        "BR",  # Time series BR: Persons: 18 years and over ~ Of three races--American Indian and Alaska Native; Native Hawaiian and Other Pacific Islander; Some Other Race
        "BU",  # Time series BU: Persons: 18 years and over ~ Of four races--White; Black or African American; American Indian and Alaska Native; Asian
        "BV",  # Time series BV: Persons: 18 years and over ~ Of four races--White; Black or African American; American Indian and Alaska Native; Native Hawaiian and Other Pacific Islander
        "BW",  # Time series BW: Persons: 18 years and over ~ Of four races--White; Black or African American; American Indian and Alaska Native; Some Other Race
        "CA",  # Time series CA: Persons: 18 years and over ~ Of four races--White; American Indian and Alaska Native; Asian; Native Hawaiian and Other Pacific Islander
        "CB",  # Time series CB: Persons: 18 years and over ~ Of four races--White; American Indian and Alaska Native; Asian; Some Other Race
        "CC",  # Time series CC: Persons: 18 years and over ~ Of four races--White; American Indian and Alaska Native; Native Hawaiian and Other Pacific Islander; Some Other Race
        "CE",  # Time series CE: Persons: 18 years and over ~ Of four races--Black or African American; American Indian and Alaska Native; Asian; Native Hawaiian and Other Pacific Islander
        "CF",  # Time series CF: Persons: 18 years and over ~ Of four races--Black or African American; American Indian and Alaska Native; Asian; Some Other Race
        "CG",  # Time series CG: Persons: 18 years and over ~ Of four races--Black or African American; American Indian and Alaska Native; Native Hawaiian and Other Pacific Islander; Some Other Race
        "CI",  # Time series CI: Persons: 18 years and over ~ Of four races--American Indian and Alaska Native; Asian; Native Hawaiian and Other Pacific Islander; Some Other Race
        "CK",  # Time series CK: Persons: 18 years and over ~ Of five races--White; Black or African American; American Indian and Alaska Native; Asian; Native Hawaiian and Other Pacific Islander
        "CL",  # Time series CL: Persons: 18 years and over ~ Of five races--White; Black or African American; American Indian and Alaska Native; Asian; Some Other Race
        "CM",  # Time series CM: Persons: 18 years and over ~ Of five races--White; Black or African American; American Indian and Alaska Native; Native Hawaiian and Other Pacific Islander; Some Other Race
        "CO",  # Time series CO: Persons: 18 years and over ~ Of five races--White; American Indian and Alaska Native; Asian; Native Hawaiian and Other Pacific Islander; Some Other Race
        "CP",  # Time series CP: Persons: 18 years and over ~ Of five races--Black or African American; American Indian and Alaska Native; Asian; Native Hawaiian and Other Pacific Islander; Some Other Race
        "CR",  # Time series CR: Persons: 18 years and over ~ Of six races--White; Black or African American; American Indian and Alaska Native; Asian; Native Hawaiian and Other Pacific Islander; Some Other Race
    ]

    # Sum all AI counts
    blocks[f"vap_ai_{year}"] = 0
    for field in native_american_fields:
        blocks[f"vap_ai_{year}"] += blocks[f"CW2{field}{year}"]

    blocks[f"vap_nonai_{year}"] = blocks[f"vap_{year}"] - blocks[f"vap_ai_{year}"]

# Filter down to VAPs
keepers = [c for c in blocks.columns if re.match(".*(FP10|vap_|geometry)", c)]
vap = blocks[keepers].copy()

vap = vap.to_crs("epsg:4326")
all_states = [s.fips for s in us.STATES]

for s in all_states:
    state = vap[vap.STATEFP10 == s]
    state.to_file(f"../../20_intermediate_data/10_blockgroups/blockgroups_{s}.geojson")
