"""
This application loads the full map information file from a world generated by 'https://azgaar.github.io/Fantasy-Map-Generator/' and extends it.

World data:
    - Metadata
    - Settings
    - Pack:
        * Cells
        * Vertices
        * Features (oceans, islands, etc)
        * Cultures
        * Burgs
        * States
        * Provinces
        * Religions
        * Rivers
        * Markers
    - Grid:
        * Cells
        * Vertices
        * ...
        * Features (oceans, islands, etc)
    - biomesData:
        * i, name, color, biomesMatrix, habitability, iconsDensity, icons, cost
    - notes:
        * [(id, name, legend)]
    - nameBases (names for each culture)
    - 

Manual data:
    - Economy parameters (farmland required to feed a person, urban area required to house a person, surplus people that a farmer/fisherman can feed, etc)
    - Quartier size (600-1000) and urban and farm area use
    - Citizen consumption & production
    - Citizen random generation based on Burg data (burg type, culture type, biome, features, religion) ----()----> citizens
    

Extended data:
    - Burg:
        * Old columns: cell 2517, x 1531.65, y 524.32, state 1, i 1, culture 4, name Parabriz, feature 2, capital 1, port 0, population 25.742, type Generic, coa {...}, citadel 1, plaza 1, walls 1, shanty 1, temple 1, lock false
        * New columns:
            > from cells: biome 0, pop 0, culture 0, road 0, crossroad 0, state 0, religion 0, province 0
            > from features: type (coast, lake...), group (ocean, island, freshwater...), land & border define type of geometric definition?
            > from rivers: river 0
            > from culture: type (coastal, nomadic, generic...)

    - Cell:
        * Old columns: i 0, v [...], c [...], p [...], g 626, h 18, area 968, f 1, t 0, haven 0, harbor 0, fl 0, r 0, conf 0, biome 0, s 0, pop 0, culture 0, burg 0, road 0, crossroad 0, state 0, religion 0, province 0
"""

import json
from typing import List, Tuple

import numpy as np
import pandas as pd


def generate_extended_world_data(
    world_data_filepath: str, manual_data_filepath: str
) -> List[pd.DataFrame]:
    world_data = load_world_data(world_data_filepath)
    manual_data = load_manual_data(manual_data_filepath)

    *extended_world_data, manual_data = extend_world_data(*world_data, manual_data)
    save_world_data(world_data_filepath, extended_world_data)

    return extended_world_data


def load_world_data(filepath: str) -> Tuple[pd.DataFrame]:
    """
    World data:
        - Metadata
        - Settings
        - Pack:
            * Cells
            * Vertices
            * Features (oceans, islands, etc)
            * Cultures
            * Burgs
            * States
            * Provinces
            * Religions
            * Rivers
            * Markers
        - Grid:
            * Cells
            * Vertices
            * ...
            * Features (oceans, islands, etc)
        - biomesData:
            * i, name, color, biomesMatrix, habitability, iconsDensity, icons, cost
        - notes:
            * [(id, name, legend)]
        - nameBases (names for each culture)
    """
    with open(filepath, "rb") as fp:
        wd = json.load(fp)
        return (
            burgs_from_world_data(wd),
            cells_from_world_data(wd),
            features_from_world_data(wd),
            rivers_from_world_data(wd),
            cultures_from_world_data(wd),
            religions_from_world_data(wd),
            states_from_world_data(wd),
            provinces_from_world_data(wd),
            biomes_from_world_data(wd),
        )


def burgs_from_world_data(d: dict) -> pd.DataFrame:
    return (
        pd.DataFrame.from_records(d["pack"]["burgs"]).dropna(how="all").set_index("i")
    )


def cells_from_world_data(d: dict) -> pd.DataFrame:
    return (
        pd.DataFrame.from_records(d["pack"]["cells"]).dropna(how="all").set_index("i")
    )


def features_from_world_data(d: dict) -> pd.DataFrame:
    return (
        pd.DataFrame.from_records(d["pack"]["features"][1:])
        .dropna(how="all")
        .set_index("i")
    )


def rivers_from_world_data(d: dict) -> pd.DataFrame:
    return (
        pd.DataFrame.from_records(d["pack"]["rivers"]).dropna(how="all").set_index("i")
    )


def cultures_from_world_data(d: dict) -> pd.DataFrame:
    return (
        pd.DataFrame.from_records(d["pack"]["cultures"])
        .dropna(how="all")
        .set_index("i")
    )


def religions_from_world_data(d: dict) -> pd.DataFrame:
    return pd.DataFrame.from_records(d["pack"]["religions"])


def states_from_world_data(d: dict) -> pd.DataFrame:
    return pd.DataFrame.from_records(d["pack"]["states"])


def provinces_from_world_data(d: dict) -> pd.DataFrame:
    return pd.DataFrame.from_records(d["pack"]["provinces"][1:])


def biomes_from_world_data(d: dict) -> pd.DataFrame:
    return pd.DataFrame({k: v for k, v in list(d["biomesData"].items())[1:3]}).replace(
        {
            "Tropical seasonal forest": "Tropical forest",
            "Temperate deciduous forest": "Temperate forest",
        }
    )


def load_manual_data(filepath: str) -> Tuple[pd.DataFrame]:
    """
    Manual data:
        - Economy parameters (farmland required to feed a person, urban area required to house a person, surplus people that a farmer/fisherman can feed, etc)
        - Quartier size (600-1000) and urban and farm area use
        - Citizen consumption & production
        - Citizen random generation based on Burg data (burg type, culture type, biome, features, religion) ----()----> citizens
    """
    tabs = [
        "Economy",
        "Land Use",
        "Citizens",
        "Citizen Generator",
        "Citizen Burg Modifiers",
        "Citizen Biome Modifiers",
    ]
    two_col_kwargs = dict(index_col=0, header=[0, 1])
    one_col_kwargs = dict(index_col=0)
    read_kwargs = [
        two_col_kwargs,
        two_col_kwargs,
        two_col_kwargs,
        one_col_kwargs,
        one_col_kwargs,
        one_col_kwargs,
    ]
    with open(filepath, "rb") as fp:
        return tuple(
            pd.read_excel(filepath, tab, **read_kwargs)
            for tab, read_kwargs in zip(tabs, read_kwargs)
        )


def extend_world_data(
    burgs: pd.DataFrame,
    cells: pd.DataFrame,
    features: pd.DataFrame,
    rivers: pd.DataFrame,
    cultures: pd.DataFrame,
    religions: List[str],
    states: List[str],
    provinces: List[str],
    biomes: List[str],
    manual_data: Tuple[pd.DataFrame],
) -> pd.DataFrame:
    new_burgs = extend_burgs(
        burgs,
        cells,
        features,
        rivers,
        cultures,
        religions,
        states,
        provinces,
        biomes,
        manual_data,
    )

    return (
        new_burgs,
        cells,
        features,
        rivers,
        cultures,
        religions,
        states,
        provinces,
        biomes,
        manual_data,
    )


def extend_burgs(
    burgs: pd.DataFrame,
    cells: pd.DataFrame,
    features: pd.DataFrame,
    rivers: pd.DataFrame,
    cultures: pd.DataFrame,
    religions: List[str],
    states: List[str],
    provinces: List[str],
    biomes: List[str],
    manual_data: Tuple[pd.DataFrame],
    convert_categorical_ids_strings: bool = True,
) -> pd.DataFrame:
    new_burgs = burgs.reset_index().copy()
    columns_to_add = [
        (
            cells.reset_index("i"),
            ["biome", "pop", "road", "crossroad", "religion", "province"],
            {"pop": "land_population"},
            "cell",
            "i",
        ),
        (
            cultures.reset_index("i"),
            ["name", "shield"],
            {"name": "culture_name", "shield": "culture_shield"},
            "culture",
            "i",
        ),
    ]
    for data, cols, renamer, on_left, on_right in columns_to_add:
        new_burgs = add_columns(new_burgs, data, cols, renamer, on_left, on_right)

    if convert_categorical_ids_strings:

        def get_names(df_cat: pd.DataFrame) -> List[str]:
            return [cat.replace(" ", "\n") for cat in df_cat.name.values]

        categorical_idxs_to_str = [
            ("state", get_names(states)),
            ("province", get_names(provinces)),
            ("culture", get_names(cultures)),
            ("religion", get_names(religions)),
            ("biome", get_names(biomes)),
        ]
        for col, names in categorical_idxs_to_str:
            new_burgs.loc[:, col] = new_burgs.loc[:, col].replace(
                dict(zip(range(len(names)), names))
            )
    new_burgs = generate_new_burg_data(new_burgs, manual_data)
    return new_burgs


def add_columns(
    df: pd.DataFrame,
    data: pd.DataFrame,
    columns: List[str],
    renamer: dict,
    left_on: str,
    right_on: str,
) -> pd.DataFrame:
    df_to_add = data.set_index(right_on).loc[:, columns]
    if renamer is not None:
        if renamer != {}:
            df_to_add = df_to_add.rename(columns=renamer)
    df = pd.merge(df, df_to_add, how="left", left_on=left_on, right_on=right_on)
    return df


def add_features_to_burgs():
    pass


def add_cultures_to_burgs():
    pass


def generate_new_burg_data(
    burgs: pd.DataFrame, manual_data: List[pd.DataFrame]
) -> pd.DataFrame:
    """
    Manual data:
        - Citizen Quartiers
        - Citizen consumption & production
        - Citizen random generation based on Burg data (burg type, culture type, biome, features, religion) ----()----> citizens
        - Citizen urban and farm area use

    Extended data:
        - Burg:
            * Old columns: cell 2517, x 1531.65, y 524.32, state 1, i 1, culture 4, name Parabriz, feature 2, capital 1, port 0, population 25.742, type Generic, coa {...}, citadel 1, plaza 1, walls 1, shanty 1, temple 1, lock false
            * New columns:
                > from cells: biome 0, pop 0, culture 0, road 0, crossroad 0, state 0, religion 0, province 0
                > from features: type (coast, lake...), group (ocean, island, freshwater...), land & border define type of geometric definition?
                > from rivers: river 0
                > from culture: type (coastal, nomadic, generic...)

    """
    (
        *_,
        economy,
        land_use,
        citizen_consumption_and_productions,
        base_citizen_generator,
        citizen_burg_modifiers,
        citizen_biome_modifiers,
    ) = manual_data

    # OLD to NEW columns
    old_identifier_columns = ["state", "province", "name", "i"]
    old_columns = (
        ["culture", "religion", "type"]
        + ["road", "crossroad"]
        + ["capital", "port", "citadel", "plaza", "temple", "shanty"]
        + ["biome"]
    )
    old_to_new_columns = [
        [["Political"], ["Characteristics"], ["Culture", "Religion", "Type"]],
        [["Infrastructure"], ["Network"], ["road", "crossroad"]],
        [
            ["Infrastructure"],
            ["Buildings"],
            ["Capital", "Port", "Castle", "Market", "Church", "Shanty Town"],
        ],
        [["Nature"], ["Characteristics"], ["Biome"]],
    ]
    old_to_new_idx = pd.MultiIndex.from_product([[], [], []])
    for cg in old_to_new_columns:
        old_to_new_idx = old_to_new_idx.append(pd.MultiIndex.from_product(cg))

    new_columns = old_to_new_idx

    # NEW columns
    population_idx = [
        ["Population"],
        ["Total"],
        ["Heads", "Quartier min", "Quartier max", "Used Quartiers", "Free Quartiers"],
    ]
    citizen_idx = [
        ["Citizens"],
        ["Nr"],
        [
            "Farmer",
            "Fisherman",
            "Hunter",
            "Craftsman",
            "Tradesman",
            "Churchman",
            "Clerk",
            "Soldier",
        ],
    ]
    consumption_idx = [["Consumption"], ["Total"], ["Food", "Gold"]]
    production_idx = [["Production"], ["Total"], ["Food", "Gold"]]
    net_idx = [["Net"], ["Total"], ["Food", "Gold"]]
    buildings_idx = [
        ["Buildings"],
        ["Available"],
        ["Port", "Fort", "Church", "Capital", "Market"],
    ]
    urban_land_idx = [
        ["Urban"],
        ["Area", "Side"],
        ["Min (ha)", "Max (ha)"],
    ]
    farm_land_idx = [
        ["Farmland"],
        ["Area", "Side"],
        ["Min (ha)", "Max (ha)"],
    ]
    new_column_groups = [
        population_idx,
        citizen_idx,
        consumption_idx,
        production_idx,
        net_idx,
        buildings_idx,
        urban_land_idx,
        farm_land_idx,
    ]

    new_column_idx = pd.MultiIndex.from_product([[], [], []])
    for cg in new_column_groups:
        new_column_idx = new_column_idx.append(pd.MultiIndex.from_product(cg))

    new_columns = new_columns.append(new_column_idx)

    df_idx = pd.MultiIndex.from_arrays(
        burgs.loc[:, old_identifier_columns].T.values, names=old_identifier_columns
    )
    df = pd.DataFrame(index=df_idx, columns=new_columns)
    df.loc[:, old_to_new_idx] = burgs.loc[:, old_columns].values

    # Generate population & citizen data
    df.loc[:, ("Population", "Total", "Heads")] = (
        burgs.loc[:, "population"].values * 1000
    )
    df = update_max_min_quartiers(df, land_use)
    df = generate_random_citizens(
        df, base_citizen_generator, citizen_burg_modifiers, citizen_biome_modifiers
    )
    df = update_used_and_free_quartiers(df)
    df = update_consumption_and_production(df, citizen_consumption_and_productions)
    # df = update_buildings_available(df, citizen_burg_modifiers)
    df = update_urban_area(df, land_use)
    df = update_farmland_area(df, land_use)

    return df


def update_max_min_quartiers(df: pd.DataFrame, land_use: pd.DataFrame) -> pd.DataFrame:
    quartier_sizes = land_use.Quartier.Inhabitants
    df.loc[:, ("Population", "Total", "Quartier min")] = np.floor(
        df.Population.Total.Heads / quartier_sizes.min()
    )
    df.loc[:, ("Population", "Total", "Quartier max")] = np.floor(
        df.Population.Total.Heads / quartier_sizes.max()
    )
    return df


def generate_random_citizens(
    df: pd.DataFrame,
    base_citizen_generator: pd.DataFrame,
    citizen_burg_modifiers: pd.DataFrame,
    citizen_biome_modifiers: pd.DataFrame,
) -> pd.DataFrame:

    for r, row in df.iterrows():
        df.loc[r] = generate_burg_random_citizens(
            row,
            base_citizen_generator=base_citizen_generator,
            citizen_burg_modifiers=citizen_burg_modifiers,
            citizen_biome_modifiers=citizen_biome_modifiers,
        )

    return df


def generate_burg_random_citizens(
    sb: pd.Series,
    base_citizen_generator: pd.DataFrame,
    citizen_burg_modifiers: pd.DataFrame,
    citizen_biome_modifiers: pd.DataFrame,
) -> pd.DataFrame:
    target_population = sb.loc[
        [
            ("Population", "Total", "Quartier min"),
            ("Population", "Total", "Quartier max"),
        ]
    ].mean()

    base_citizen_generator = base_citizen_generator.fillna(0)
    citizen_burg_modifiers = citizen_burg_modifiers.fillna(0)
    citizen_biome_modifiers = citizen_biome_modifiers.fillna(0)

    citizen_profile = base_citizen_generator.iloc[:, 0]

    # Modify citizen distribution by burg type
    burg_types = ["River", "Lake", "Naval", "Nomadic", "Hunting", "Highland"]

    if sb.loc[("Political", "Characteristics", "Type")] in burg_types:
        citizen_profile = (
            citizen_profile
            + citizen_burg_modifiers.loc[
                :, sb.loc[("Political", "Characteristics", "Type")]
            ]
        )

    # Modify citizen distribution by boolean characteristics
    burg_characteristic_modifier_columns = [
        "Capital",
        "Port",
        "Castle",
        "Market",
        "Church",
        "Shanty Town",
    ]
    burg_characteristics = pd.MultiIndex.from_product(
        [
            ["Infrastructure"],
            ["Buildings"],
            ["Capital", "Port", "Castle", "Market", "Church", "Shanty Town"],
        ]
    )
    for mod, char in zip(burg_characteristic_modifier_columns, burg_characteristics):
        if sb.loc[char] is False:
            continue
        citizen_profile = citizen_profile + citizen_burg_modifiers.loc[:, mod]

    # Generate final population based on distribution and target population
    final_population = (
        target_population * citizen_profile / citizen_profile.sum()
    ).round()

    # If burg characteristic buffs a certain citizen, at least one citizen of that type should exist
    for char in burg_characteristics:
        if sb.loc[char] is False:
            continue
        final_population = [
            max(f, m)
            for f, m in zip(
                final_population, (citizen_burg_modifiers.loc[:, mod] > 0).astype("int")
            )
        ]

    # Apply final citizens & return
    sb.loc[pd.IndexSlice["Citizens", :, :]] = final_population
    return sb


def update_used_and_free_quartiers(df: pd.DataFrame) -> pd.DataFrame:
    df.loc[:, ("Population", "Total", "Used Quartiers")] = df.Citizens.sum(
        axis=1
    ).values
    df.loc[:, ("Population", "Total", "Free Quartiers")] = (
        df.loc[
            :,
            [
                ("Population", "Total", "Quartier min"),
                ("Population", "Total", "Quartier max"),
            ],
        ].mean(axis=1)
        - df.loc[:, ("Population", "Total", "Used Quartiers")]
    )
    return df


def update_consumption_and_production(
    df: pd.DataFrame, citizen_consumption_and_productions: pd.DataFrame
) -> pd.DataFrame:

    for r, row in df.iterrows():
        df.loc[r] = update_burg_consumption_and_production(
            row, citizen_consumption_and_productions=citizen_consumption_and_productions
        )

    return df


def update_burg_consumption_and_production(
    sb: pd.Series, citizen_consumption_and_productions: pd.DataFrame
) -> pd.DataFrame:
    citizen_consumption_and_productions = citizen_consumption_and_productions.fillna(0)
    sb.loc[pd.IndexSlice["Consumption", "Total", :]] = np.sum(
        [
            [c * f, c * g]
            for c, (f, g) in zip(
                sb.Citizens.values,
                citizen_consumption_and_productions.Consumption.values,
            )
        ],
        axis=0,
    ).T
    sb.loc[pd.IndexSlice["Production", "Total", :]] = np.sum(
        [
            [c * f, c * g]
            for c, (f, g) in zip(
                sb.Citizens.values,
                citizen_consumption_and_productions.Production.values,
            )
        ],
        axis=0,
    ).T
    sb.loc[pd.IndexSlice["Net", "Total", :]] = (
        sb.loc[pd.IndexSlice["Production", "Total", :]].values
        - sb.loc[pd.IndexSlice["Consumption", "Total", :]].values
    )
    return sb


def update_buildings_available(
    df: pd.DataFrame, citizen_burg_modifiers: pd.DataFrame
) -> pd.DataFrame:

    for r, row in df.iterrows():
        df.loc[r] = update_burg_buildings_available(row, citizen_burg_modifiers)

    return df


def update_burg_buildings_available(
    sb: pd.Series, citizen_burg_modifiers: pd.DataFrame
) -> pd.DataFrame:
    for char in sb.Infrastructure.Buildings.index:
        if sb.loc[("Infrastructure", "Buildings", char)] is False:
            continue
        final_population = np.min(
            final_population, (citizen_burg_modifiers.loc[:, char] > 0)
        )


def update_urban_area(df: pd.DataFrame, land_use: pd.DataFrame) -> pd.DataFrame:

    for r, row in df.iterrows():
        df.loc[r] = update_burg_urban_area(row, land_use=land_use)

    return df


def update_burg_urban_area(sb: pd.Series, land_use: pd.DataFrame) -> pd.DataFrame:

    population = sb.loc[("Population", "Total", "Heads")]

    sb.loc[pd.IndexSlice["Urban", "Area", :]] = np.ceil(
        population
        / land_use.unstack().loc[pd.IndexSlice["Quartier", "Inhabitants", :]]
        * land_use.unstack().loc[pd.IndexSlice["Requirements", "Urban area", :]]
    ).values
    sb.loc[pd.IndexSlice["Urban", "Side", :]] = np.ceil(
        [np.sqrt(v) for v in sb.loc[pd.IndexSlice["Urban", "Area", :]]]
    )

    return sb


def update_farmland_area(df: pd.DataFrame, land_use: pd.DataFrame) -> pd.DataFrame:

    for r, row in df.iterrows():
        df.loc[r] = update_burg_farmland_area(row, land_use=land_use)

    return df


def update_burg_farmland_area(sb: pd.Series, land_use: pd.DataFrame) -> pd.DataFrame:

    population = sb.loc[("Population", "Total", "Heads")]

    sb.loc[pd.IndexSlice["Farmland", "Area", :]] = np.ceil(
        population
        / land_use.unstack().loc[pd.IndexSlice["Quartier", "Inhabitants", :]]
        * land_use.unstack().loc[pd.IndexSlice["Requirements", "Farmland", :]]
    ).values
    sb.loc[pd.IndexSlice["Farmland", "Side", :]] = np.ceil(
        [np.sqrt(v) for v in sb.loc[pd.IndexSlice["Farmland", "Area", :]]]
    )

    return sb


def save_world_data(world_data_filepath: str, world_data):
    suffix = world_data_filepath.split(" Full ")[0]
    ewd_files = [
        "burgs",
        "cells",
        "features",
        "rivers",
        "cultures",
        "religions",
        "states",
        "provinces",
        "biomes",
    ]
    ewd_paths = [f"{suffix}_{ef}.csv" for ef in ewd_files]

    for data, fpath in zip(world_data, ewd_paths):
        data.to_csv(fpath)
