import os

from medieval_world import generate_extended_world_data, save_world_data
from study_world import study_burgs

cwd = os.getcwd()
wd_dir = f"{cwd}/Fantasy_Maps/Montreia__2024_05_23"
save_dir = f"{wd_dir}/study"
wd_path = f"{wd_dir}/Montreia Full 2024-05-23-10-01.json"
md_path = "Medieval Info.xlsx"
suffix = f".{wd_dir}/Montreia"
ewd_files = ["burgs", "cells", "features", "rivers", "cultures"]
ewd_paths = [f"{suffix}_{ef}" for ef in ewd_files]

world_data_extended, manual_data = generate_extended_world_data(wd_path, md_path)

save_world_data(save_dir, world_data_extended)
burgs, cells, features, rivers, cultures, religions, states, provinces, biomes = (
    world_data_extended
)
study_burgs(burgs, save_dir)
