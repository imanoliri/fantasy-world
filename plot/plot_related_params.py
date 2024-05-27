
import pathlib
from typing import List

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def plot_pairplot(df: pd. DataFrame, name: str, plot_dir:str='.', sub: str = '', x_vars: List[str]=None, y_vars: List[str]=None, join_multilevel: bool = True):
    if sub != '':
        sub = f'_{sub.strip(' _')}'
    df_plot = df
    if join_multilevel:
        if isinstance(df.columns, pd.MultiIndex):
            df_plot = df.copy()
            df_plot.columns = ['_'.join(c) for c in df_plot.columns]
            x_vars = ['_'.join(c) for c in x_vars]
            y_vars = ['_'.join(c) for c in y_vars]
    pair_grid = sns.pairplot(df_plot, x_vars=x_vars, y_vars=y_vars)
    ax = plt.gca()
    title_str = f'pairplot_{name}{sub}'
    ax.set_title(title_str)
    fpath = f'{plot_dir}/{title_str}.jpg'
    pathlib.Path(fpath).parent.mkdir(parents=True,exist_ok=True)
    plt.savefig(fpath)
    plt.close()

