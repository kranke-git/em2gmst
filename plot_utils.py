import matplotlib.pyplot as plt
import numpy as np

def plot_gmst_stacked( df, species, scen_labels, colors = None ):
    """
    Plot stacked GMST contributions per scenario with total line.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing GMST contributions. Columns should be named as "scenario_species".
        Must include a 'Year' column.
    species : list of str
        List of species names (suffix in column names).
    scen_labels : list of str
        List of scenario names (prefix in column names).
    """
    years = df['Year']
    n_scen = len(scen_labels)

    # Determine subplot grid (max 2x2)
    nrows = 2
    ncols = 2
    fig, axes = plt.subplots(nrows, ncols, figsize=(14,8), sharex=True, sharey=True)
    axes = axes.flatten()

    # color palette for species (consistent across all scenarios)
    if colors is None:
        colors = plt.cm.tab20(np.linspace(0,1,len(species)))        

    for i, scen in enumerate(scen_labels):
        ax = axes[i]

        # select columns for this scenario
        cols = [f'{scen}_{sp}' for sp in species]
        data = df[cols]

        # stacked area plot per species
        ax.stackplot(years, data.T, labels=species, colors=colors, alpha=0.7)

        # total GMST per scenario as black line
        total = data.sum(axis=1)
        ax.plot(years, total, color='black', linewidth=2, label='Total')

        ax.set_title(f'{scen} GMST contributions')
        ax.set_xlabel('Year')
        ax.set_ylabel('ΔT (K)')
        ax.legend(loc='upper left', fontsize=8)

    # remove empty axes if fewer than 4 scenarios
    for j in range(n_scen, nrows*ncols):
        fig.delaxes(axes[j])

    plt.tight_layout()
    plt.show()
    
    return fig

def plot_gmst_totals(df, species, scen_labels, title = None):
    """
    Plot total GMST per scenario for comparison.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing GMST contributions. Columns should be named as "scenario_species".
        Must include a 'Year' column.
    species : list of str
        List of species names.
    scen_labels : list of str
        List of scenario names.
    """
    years = df['Year']
    
    # color palette for scenarios
    colors = plt.cm.tab10(np.linspace(0,1,len(scen_labels)))
    
    fig = plt.figure(figsize=(10,5))
    
    for i, scen in enumerate(scen_labels):
        cols = [f'{scen}_{sp}' for sp in species]
        total = df[cols].sum(axis=1)
        plt.plot(years, total, color=colors[i], linewidth=2, label=scen)
    
    if title is None:
        title = 'Total GMST Comparison'
    
    plt.xlabel('Year')
    plt.ylabel('Total ΔT (K)')
    plt.title( title )
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()
    
    return fig