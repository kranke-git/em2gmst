# kranke - February 2026
# This file contains constants used in the climate scenario model.

# Physical constants
spy     = 365.25 * 24 * 3600  # Number of seconds in a year
R       = 8.314  # Universal gas constant [J/(mol*K)]
M_CO2   = 44.01  # Molar mass of CO2 [g/mol]
M_CH4   = 16.04  # Molar mass of CH4 [g/mol
M_air   = 28.97  # Molar mass of dry air [g/mol]
CO2_PI  = 277.15  # Pre-industrial CO2 concentration [ppm]
CH4_PI  = 722     # Pre-industrial CH4 concentration [ppb]
CH4_TAU = 12.0    # Atmospheric lifetime of CH4 [years]

# Defautlt model parameters, can be overridden with **kwargs
DEFAULT_PARAMS = {
    "ecs": 3.0,                             # Equilibrium Climate Sensitivity [K]
    "ohtr": 1.23,                           # Ocean heat transport coefficient
    "a": [0.2173, 0.2240, 0.2824, 0.2763],  # Carbon cycle reservoir fractions [-]
    "tau": [1e6, 394.4, 36.54, 4.304],      # Reservoir time scales [years]
    "pulse_size": 1e15,                     # Size of the pulse emission [g]; default is 1 Gt =  1 Pg = 1e15 g = 1e12 kg
}
