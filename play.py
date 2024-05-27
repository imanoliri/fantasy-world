import os

from medieval_world import generate_extended_world_data
from study_world import study_burgs

cwd = os.getcwd()
wd_dir = f"{cwd}/Fantasy_Maps/Montreia__2024_05_23"
wd_path = f"{wd_dir}/Montreia Full 2024-05-23-10-01.json"
md_path = "Medieval Info.xlsx"
suffix = f".{wd_dir}/Montreia"
ewd_files = ["burgs", "cells", "features", "rivers", "cultures"]
ewd_paths = [f"{suffix}_{ef}" for ef in ewd_files]
world_data_extended = generate_extended_world_data(wd_path, md_path)
burgs, cells, features, rivers, cultures, religions, states, provinces, biomes = (
    world_data_extended
)
study_burgs(burgs, wd_dir)
