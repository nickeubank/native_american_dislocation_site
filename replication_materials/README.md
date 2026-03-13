# Replication Materials: Native American Representation and Partisan Dislocation in State Legislatures

This repository contains replication code and data for an analysis of Native American (American Indian and Alaska Native) descriptive representation in state legislatures and the partisan dislocation of Native voters across state legislative districts.

The analysis focuses on six study states — Arizona, Montana, New Mexico, North Dakota, South Dakota, and Wyoming — and examines the relationship between district-level Native voting-age population (VAP) share, the election of Native representatives, and the geographic dislocation of Native voters under different redistricting plans.

To replicate, simply use `conda` and the `environment.yml` file to install the relevant software and run `10_code/run_all.sh`. The script will automatically decompress the source data archives on first run.

When complete, you should be able to just compile the `native_representation.tex` file in `30_paper` and have the paper pull all the results in and give you a new paper.

NOTE: You should be able to delete all the files (but not folders) in 30_paper/figures, 30_paper/maps, 30_paper/stats, and in 20_intermediate_data before replication. You should only need the content of `10_code` and `00_source_data`, along with the existing directory structure to generate all results and be able to recompile the paper. But I've left the intermediate files and results in the version being published for people who don't want to replicate from source data.

NOTE 2: Because there is a randomness to point creation, most results will NOT replicate exactly, just be the same in substance. Adding a seed for some of the calls gets weirdly complicated.

### A note on map_year variable

We make regular use of the map_year variable to distinguish between maps from the 2012-2020 districting cycle and the 2022-today districting cycle. In the paper we refer to these as the 2012 and 2022 maps, but often in code the reference is to 2019 and 2023. We refer to 2019 because we pull maps from the end of the districting period so we only have maps that have passed legal scrutiny. And we refer to 2023 because they are the census bureau's 2023 district maps, but those refer to the maps used in 2022 elections. We probably could have been a little better in making all the code refer to 2022 and just renamed the files, but 🤷‍♂️.

## Requirements

### Software

- Python 3.11
- [Git LFS](https://git-lfs.github.com/) (large data files are tracked with LFS)

### Python Environment

Create the conda environment from the provided environment file:

```bash
conda env create -f environment.yml
conda activate native_rep
```

Key dependencies include `geopandas`, `pandas`, `matplotlib`, `seaborn`, `partisan-dislocation`, `seaborn_objects_recipes`, and `joblib`.

## Analysis Pipeline

All scripts are in `10_code/` and should be run from their respective subdirectories. The master script `run_all.sh` documents the intended execution order.

Note the first step in this process is decompressing the source data archives. `run_all.sh` handles this automatically — each subdirectory of `00_source_data/` is stored as a separate `.tar.xz` archive alongside the directory structure.

## Repository Structure

```
├── environment.yml                # Conda environment specification
├── 00_source_data/                # Input data (see Data Sources below)
├── 10_code/                       # All analysis code
│   ├── config.yaml                # Study states and sampling parameters
│   ├── run_all.sh                 # Master script to run all analyses
│   ├── 00_data_prep/              # Data import and preparation
│   ├── 10_districts_and_elected_reps/  # Descriptive analysis of districts and representatives
│   ├── 20_make_dislocation/       # Dislocation computation
│   ├── 30_analyze_dislocation/    # Dislocation summary statistics and plots
│   └── 40_dislocation_maps/       # Dislocation map visualizations
├── 20_intermediate_data/          # Generated intermediate datasets
└── 30_paper/                      # Output figures, maps, and stats for the paper
```

## Data Sources

All source data are in `00_source_data/`. Each subdirectory is stored as a separate `.tar.xz` archive (e.g. `2010_census_blockgroups.tar.xz`). These will be decompressed automatically by `run_all.sh` on first run. Note that decompression may take some time — the total uncompressed size is about 8GB, and the archives use maximum compression (optimized for size, not speed, since you'll only decompress once).

| Folder | Description |
|--------|-------------|
| `2010_census_blockgroups/` | Census block group shapefiles and tabular voting-age population data (1990–2020), harmonized to 2010 block group geographies (from IPUMS NHGIS). |
| `state_legislative_districts/` | TIGER/Line state legislative district shapefiles for 2019 and 2023 vintages (from the U.S. Census Bureau). |
| `Blasingame_Replication/` | Data and code from Blasingame, Hansen, and Witmer, "Are Descriptive Representatives More Successful Passing Group-Relevant Legislation? The Case of Native American State Legislators," *Political Research Quarterly*. Includes the roster of Native state legislators (1993–2023). |
| `vote_data/` | Block-level 2020 general election results by state (from the Voting and Election Science Team / VEST). |

### Step 0: Data Preparation (`00_data_prep/`)

| Script | Description |
|--------|-------------|
| `00_import_census_blocks.py` | Imports 2010 Census block group shapefiles, merges with harmonized VAP tabular data (total and Native American populations for 2000, 2010, and 2020), and writes per-state GeoJSON files. |
| `10_districts_by_ni_share.py` | Spatially joins block groups to state legislative districts (2019 and 2023 TIGER/Line maps) and aggregates Native and total VAP to the district level for all 50 states. |
| `20_elected_reps.py` | Merges the Native state legislator roster with district-level demographic data to create a combined dataset of districts and their representation status. |

### Step 1: Descriptive Analysis (`10_districts_and_elected_reps/`)

| Script | Description |
|--------|-------------|
| `10_national_native_rep_districts.py` | Tabulates mean and median Native VAP share for districts that elected Native representatives, by state. |
| `25_native_reps_and_ai_pct_hists.py` | Histograms of district-level Native VAP share, overall and by state. |
| `30_native_reps_and_ai_pct_plots.py` | LOWESS plots of the probability of electing a Native representative as a function of district Native VAP share. |

### Step 2: Compute Dislocation (`20_make_dislocation/`)

| Script | Description |
|--------|-------------|
| `10_create_representative_points.py` | Generates random representative points within block groups, proportional to population, for use in dislocation calculations (5% sample). Runs in parallel across states using `joblib`. |
| `20_make_knns.py` | Computes k-nearest-neighbor (KNN) local Native population shares and partisan dislocation scores for each representative point, using the `partisan-dislocation` package. Outputs per-state, per-chamber, per-census-year GeoJSON and CSV files. |

### Step 3: Analyze Dislocation (`30_analyze_dislocation/`)

| Script | Description |
|--------|-------------|
| `10_collect_dislocation_by_district.py` | Collects all per-point dislocation results into a single dataset of Native (AI) representative points with dislocation scores. |
| `20_dislocation_dists_by_district_box_plots.py` | Box plots of dislocation and proportional dislocation distributions by district, binned by Native VAP share. |

### Step 4: Dislocation Maps (`40_dislocation_maps/`)

| Script | Description |
|--------|-------------|
| `10_dislocation_generic_maps.py` | State-level dislocation maps for all study states, chambers, census years, and map vintages. |
| `10_dislocation_NM_2010.py` | Focused dislocation map of northwest New Mexico under the 2010-cycle maps. |
| `10_dislocation_NM_HD65_2010.py` | Detailed map of New Mexico House District 65 under the 2010-cycle maps. |
| `15_dislocation_NM_2022.py` | Focused dislocation map of northwest New Mexico under the 2020-cycle maps. |
| `15_dislocation_MT_Overview.py` | Overview dislocation map of Montana. |
| `20_dislocation_MT_lower_31.py` | Detailed map of Montana House District 31. |
| `20_dislocation_MT_upper_16.py` | Detailed map of Montana Senate District 16. |
| `20_dislocation_SD26.py` | Detailed map of South Dakota Senate District 26. |

## Outputs

Results are written to `30_paper/`:

- `figures/` — Dislocation box plots, district Native VAP share histograms, and LOWESS probability plots.
- `maps/` — State-level and district-specific dislocation maps (PDF).
- `stats/` — LaTeX fragments with summary statistics for inclusion in the paper.

## Configuration

`10_code/config.yaml` defines the six study states (by FIPS code) and the representative-point sampling rate (5%) used throughout the analysis. (this did more before we settled on 5% for all states... :))

## Notes

- Large binary files (shapefiles, parquet, CSV, GeoJSON, Excel, Stata `.dta`) are stored with [Git LFS](https://git-lfs.github.com/). Run `git lfs pull` after cloning to retrieve them.
- The projection used for spatial operations is ESRI:102010 (North America Equidistant Conic).
- All scripts assume they are run from their own subdirectory (paths are relative).
