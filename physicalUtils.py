# kranke - March 2026
# Script to define some physical utility functions for the climate scenario model, such as GWP and GTP calculations, and to analyze the GMST response to different carbon credit scenarios. This script will use the climateScenario class to run simulations for different scenarios and plot the results.

import numpy as np

def ch4_n20_overlap(M, N):
    """Calculate the overlap between CH4 and N2O for radiative forcing calculations.
        M is the CH4 concentration in ppb, 
        N is the N2O concentration in ppb.
    """
    return 0.47 * np.log(
        1
        + 2.01e-5 * (M * N)**0.75
        + 5.31e-15 * M * (M * N)**1.52
    )
