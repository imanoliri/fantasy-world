import pathlib
from typing import Callable, List, Tuple

import pandas as pd

from plot.plot_independent_params import plot_histograms
from plot.plot_related_params import plot_pairplot
from study.study_burgs import parameter_groups_burgs, summaries_burgs, summary_burgs
from study.study_cells import parameter_groups_cells, summaries_cells, summary_cells

def study_burgs(df: pd.DataFrame, plot_dir: str):

    study_general(
        df, plot_dir, "burgs", summary_burgs, summaries_burgs, parameter_groups_burgs
    )


def study_cells(df: pd.DataFrame, plot_dir: str):

    study_general(
        df,
        plot_dir,
        "cells",
        summary_cells,
        summaries_cells,
        parameter_groups_cells,
        plot_relationships=False,
    )


def study_general(
    df: pd.DataFrame,
    plot_dir: str,
    name: str,
    summary_function: Callable = None,
    summaries_function: Callable = None,
    parameter_groups: List[Tuple[str, List[Tuple[str]]]] = None,
    plot_parameters: bool = True,
    plot_relationships: bool = True,
    columns_not_to_plot: List[str] = None,
):

    # Independent parameters
    if summary_function is not None:
        df_summary = summary_function(df)
        fpath = f"{plot_dir}/{name}/{name}_summary.csv"
        pathlib.Path(fpath).parent.mkdir(parents=True, exist_ok=True)
        df_summary.to_csv(fpath)

    if summaries_function is not None:
        df_summaries = summaries_function(df)
        fpath = f"{plot_dir}/{name}/{name}_summaries.csv"
        pathlib.Path(fpath).parent.mkdir(parents=True, exist_ok=True)
        df_summaries.to_csv(fpath)
        plot_histograms(
            df_summaries, plot_dir=f"{plot_dir}/{name}/parameters_summaries"
        )
    df_plot = df
    if columns_not_to_plot is not None:
        df_plot = df.loc[:, [c for c in df.columns if c not in columns_not_to_plot]]

    if plot_parameters:
        plot_histograms(df_plot, plot_dir=f"{plot_dir}/{name}/parameters")

    # Related parameters
    if plot_relationships:
        if parameter_groups is not None:
            for group_1, params_1 in parameter_groups:
                for group_2, params_2 in parameter_groups:
                    pair_name = f"{group_1} vs {group_2}"
                    pair_name_str = pair_name.replace(" ", "_")
                    if columns_not_to_plot is not None:
                        params_1 = [p for p in params_1 if p not in columns_not_to_plot]
                        params_2 = [p for p in params_2 if p not in columns_not_to_plot]
                    plot_pairplot(
                        df_plot,
                        plot_dir=f"{plot_dir}/{name}/parameter_relations",
                        name=pair_name_str,
                        x_vars=params_1,
                        y_vars=params_2,
                    )

    # Repeat by kingdom, continent etc
