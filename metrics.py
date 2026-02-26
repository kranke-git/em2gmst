
# kranke - February 2025
# Script to compute metrics from different experiments, such as AGWP and AGTP.

import numpy as np

import numpy as np

def compute_agwp(
    df,
    rf_col="RF_CH4",
    emis_col="emissions_CH4",
    horizon=None,
):
    """
    Compute AGWP up to a specified time horizon.

    Parameters
    ----------
    df : pandas.DataFrame
        Time-indexed DataFrame (years).
    rf_col : str
        Radiative forcing column (W m-2).
    emis_col : str
        Emissions column (Gt).
    horizon : int or float, optional
        Time horizon in years since emission (e.g. 20, 50, 100).
        If None, integrates over full time span.

    Returns
    -------
    agwp : float
        AGWP_H in units of W m-2 yr per Gt emitted.
    """

    years = df.index.values
    t0 = years[0]

    # Apply time horizon
    if horizon is not None:
        df = df.loc[years <= t0 + horizon]

    # Time step (assumes regular spacing)
    years = df.index.values
    dt = np.mean(np.diff(years))

    # Integrate RF
    integrated_rf = np.trapezoid(df[rf_col].values, dx=dt)

    # Total emissions (Gt)
    total_emissions = df[emis_col].sum()

    return integrated_rf / total_emissions