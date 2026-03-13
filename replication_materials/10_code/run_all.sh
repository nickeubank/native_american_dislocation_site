#!/bin/bash
set -euo pipefail

# cd "$(dirname "$0")"

# Decompress source data archives if not already present
echo "=== Decompressing source data (if needed) ==="
for archive in ../00_source_data/*.tar.xz; do
    dir="${archive%.tar.xz}"
    if [ ! -d "$dir" ]; then
        echo "  Decompressing $(basename "$archive")..."
        tar -xJf "$archive" -C "../00_source_data"
    fi
done

echo "=== 00_data_prep ==="
cd 00_data_prep
# python 00_import_census_blocks.py
# python 10_districts_by_ni_share.py
# python 20_elected_reps.py

# echo "=== 10_districts_and_elected_reps ==="
# cd ../10_districts_and_elected_reps
# python 10_national_native_rep_districts.py
# python 25_native_reps_and_ai_pct_hists.py
# python 30_native_reps_and_ai_pct_plots.py

# echo "=== 20_make_dislocation ==="
# cd ../20_make_dislocation
# python 10_create_representative_points.py
# python 20_make_knns.py

# echo "=== 30_analyze_dislocation ==="
cd ../30_analyze_dislocation
python 10_collect_dislocation_by_district.py
python 20_dislocation_dists_by_district_box_plots.py

# echo "=== 40_dislocation_maps ==="
cd ../40_dislocation_maps
python 10_dislocation_generic_maps.py
python 10_dislocation_NM_2010.py
python 10_dislocation_NM_HD65_2010.py
python 15_dislocation_MT_Overview.py
python 15_dislocation_NM_2022.py
python 20_dislocation_MT_lower_31.py
python 20_dislocation_MT_upper_16.py
python 20_dislocation_SD26.py

echo "=== All scripts completed successfully ==="
