import os
from pathlib import Path
from typing import Iterable, List, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt


def summary_burgs(df: pd.DataFrame) -> pd.DataFrame:
    return summaries_burgs(df).apply(get_summary_burgs_parameter)


def get_summary_burgs_parameter(s: pd.Series) -> pd.Series:
    stat_names = ["Median", "Mean", "Min", "Max"]
    try:
        return pd.Series([s.median(), s.mean(), s.min(), s.max()], stat_names).round(1)
    except:
        sc = s.value_counts()
        return pd.Series([np.NaN, np.NaN, sc.idxmin(), sc.idxmax()], stat_names)


def summaries_burgs(df: pd.DataFrame) -> pd.DataFrame:
    return df.apply(summary_burg, axis=1)


def summary_burg(sb: pd.Series) -> pd.Series:
    return pd.Series(
        [
            *sb.loc[
                [
                    ("Population", "Total", "Heads"),
                    ("Political", "Characteristics", "Type"),
                    ("Nature", "Characteristics", "Biome"),
                ]
            ].values,
            sb.loc[
                [
                    ("Infrastructure", "Buildings", "Capital"),
                    ("Infrastructure", "Buildings", "Port"),
                    ("Infrastructure", "Buildings", "Castle"),
                    ("Infrastructure", "Buildings", "Market"),
                    ("Infrastructure", "Buildings", "Church"),
                    ("Infrastructure", "Buildings", "Shanty Town"),
                ]
            ].sum(),
            *sb.loc[[("Infrastructure", "Network", "road")]].values,
            sb.loc[[("Net", "Total", "Food"), ("Net", "Total", "Gold")]].mean(),
            sb.loc[
                [("Urban", "Area", "Min (ha)"), ("Urban", "Area", "Max (ha)")]
            ].mean(),
        ],
        index=[
            "Total_Population",
            "Type",
            "Biome",
            "Buildings",
            "Roads",
            "Farmland Area",
            "Urban Area",
        ],
    )


def plot_histograms(
    df: pd.DataFrame,
    columns: List[Union[str, Tuple[str]]] = None,
    titles: List[str] = None,
    plot_dir: str = None,
    bins: int = 20,
    with_boxplot: bool = True,
    sharex: bool = False,
    ignore_outliers: bool = True,
    save_plot: bool = True,
    **kwargs,
):
    Path(plot_dir).mkdir(parents=True, exist_ok=True)

    if columns is None:
        columns = df.columns

    if titles is None:
        titles = [
            "_".join(str(v) for v in c if v != "") if isinstance(c, tuple) else c
            for c in columns
        ]
        titles = [c.lower() for c in titles]
    for col, title in zip(columns, titles):
        plot_hist(
            df,
            col,
            title,
            plot_dir,
            bins,
            with_boxplot,
            sharex,
            ignore_outliers,
            save_plot,
            **kwargs,
        )


def plot_hist(
    ds: pd.DataFrame,
    col: str,
    title: str,
    plot_dir: str = None,
    bins: int = 20,
    binrange: Tuple[float] = None,
    with_boxplot: bool = True,
    sharex: bool = False,
    ignore_outliers: bool = True,
    save_plot: bool = True,
    x_tick_rotation: float = None,
    kwargs_hist: dict = None,
    kwargs_boxplot: dict = None,
):

    if with_boxplot:
        f, (ax_hist, ax_box) = plt.subplots(
            2, sharex=sharex, gridspec_kw={"height_ratios": (0.85, 0.15)}
        )

        dsc = ds.loc[:, col]
        dscna = dsc.dropna()
        dsna = ds.loc[dscna.index]
        binrange = None
        dsh = dsna

        if binrange is not None and ignore_outliers is True:
            binrange = get_binrange_no_outlier(dscna)
            if binrange is not None:
                dsh = dsh.loc[
                    dscna.loc[
                        (binrange[0] < dscna.values) & (dscna.values < binrange[1])
                    ].index
                ].drop_duplicates()
        sns.histplot(data=dsh, x=col, ax=ax_hist, binrange=binrange, bins=bins)
        sns.boxplot(x=dscna, ax=ax_box)

        ax_hist.set_xlabel("")
        if x_tick_rotation is not None:
            ax_box.tick_params(axis="x", rotation=x_tick_rotation)
        ax_hist.set_title(title)
    else:
        ds.loc[:, col].dropna().hist(bins=bins)
        ax = plt.gca()
        if x_tick_rotation is not None:
            ax.tick_params(axis="x", rotation=x_tick_rotation)
        ax.set_title(title)

    if save_plot:
        file_str = title.lower().replace(" ", "_")
        os.makedirs(os.path.dirname(plot_dir), exist_ok=True)
        plt.savefig(f"{plot_dir}/{file_str}.jpg")
        plt.close("all")


def get_binrange_no_outlier(data: pd.DataFrame, range: float = 1.5) -> Tuple[float]:
    outlier_extremes = get_outlier_extreme_values(
        data.loc[~data.loc[:].isnull()].values, range
    )
    if outlier_extremes is None:
        return None
    bin_range = outlier_extremes[2:]
    if any(e is None for e in bin_range):
        return None
    return bin_range


def get_outlier_extreme_values(data: np.array, erange: float = 1.5) -> Tuple[float]:
    if data.size == 0:
        return None
    Q1, median, Q3 = np.percentile(data, [25, 50, 75])
    IQR = Q3 - Q1

    loval = Q1 - erange * IQR
    hival = Q3 + erange * IQR

    actual_hival = np.max(np.compress(data <= hival, data))
    actual_loval = np.min(np.compress(data >= loval, data))

    return loval, hival, actual_loval, actual_hival


def multiplot(
    df: pd.DataFrame,
    series_to_plot: List[Tuple[str, str, str, dict]],
    hlines: List[Tuple[float, str, str]] = None,
    vlines: List[Tuple[float, str, str]] = None,
    plot_dir: str = None,
    title: str = None,
    dropna: bool = True,
    **kwargs,
):
    columns, kinds, colors, plot_kwargs = zip(*series_to_plot)

    if title is None:
        titles = [
            (
                "_".join(str(v) for v in c if v != "")
                if isinstance(c, Iterable) and not isinstance(c, str)
                else str(c)
            )
            for c in columns
        ]
        titles = [c.lower() for c in titles]
        title = "__".join(titles)

    df_plot = df.loc[:, list(columns)]
    if dropna:
        df_plot = df_plot.dropna()

    ax1 = None
    ax2 = None
    for plot_col, plot_kind, plot_color, plot_kwargs in series_to_plot:
        if ax1 is None:
            ax1 = df_plot.plot(
                y=plot_col, kind=plot_kind, color=plot_color, **plot_kwargs, **kwargs
            )
            plot_one = True
            continue

        if ax2 is None:
            ax2 = ax1.twinx()
        df_plot.plot(
            ax=ax2,
            y=plot_col,
            kind=plot_kind,
            color=plot_color,
            **plot_kwargs,
            **kwargs,
        )

    if hlines is not None:
        for hval, hcol, hstyle in hlines:
            if hcol is None:
                hcol = "r"
            if hstyle is None:
                hstyle = "-"
            plt.axhline(y=hval, color=hcol, linestyle=hstyle)

    if vlines is not None:
        for vval, vcol, vstyle in vlines:
            if vcol is None:
                vcol = "r"
            if vstyle is None:
                vstyle = "-"
            plt.axvline(x=vval, color=vcol, linestyle=vstyle)

    ax1.set_xticklabels(ax1.get_xticklabels(), rotation=90)

    file_str = title.lower().replace(" ", "_")
    os.makedirs(Path(plot_dir), exist_ok=True)
    plt.savefig(f"{plot_dir}/{file_str}.jpg")
    plt.close("all")
