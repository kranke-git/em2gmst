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

# emission conv is the factor to covert from kg of that species to ppm, ppb or whatever units is used in the RF calculations
SPECIES = {
    "CO2":      {'emissUnits': 'GtCO2',      'units':'ppm', "GWP100": 1,     "MOLAR_MASS": M_CO2,  "C_PI": CO2_PI, 'emission_conv': 1 / 1e12 / 7.8,},
    "CH4":      {'emissUnits': 'MtCH4',      'units':'ppb', "GWP100": 28,    "MOLAR_MASS": M_CH4,  "C_PI": CH4_PI, 'emission_conv': 1 / 1e9 / 2.8, "tau": CH4_TAU, "molecule":"CH4", 'f1': 0.000, 'f2': 0.000, 'f3': 0.036},
    "SF6":      {'emissUnits': 'ktSF6',      'units':'ppt', "GWP100": 23500, "MOLAR_MASS": 146.06, "C_PI": 0,      'emission_conv': 1 / 1e6 / 26, "tau": 3200, "molecule":"SF6",      'f1':0.0, 'f2': 0.57 / 1e3, 'f3': 0 }, 
    'HFC-134a': {'emissUnits': 'ktHFC-134a', 'units':'ppt', "GWP100": 1300,  "MOLAR_MASS": 102.03, "C_PI": 0,      'emission_conv': 1 / 1e6 / 18, "tau": 13.4, "molecule":"HFC-134a", 'f1':0.0, 'f2': 0.16 / 1e3, 'f3': 0 }, 
    'N2O':      {'emissUnits': 'MtN2O',      'units':'ppb', "GWP100": 265,   "MOLAR_MASS": 44.013, "C_PI": 270,    'emission_conv': 1 / 1e9 / 7.8, "tau": 121, "molecule":"N2O",      'f1':0.0, 'f2': 0.0, 'f3': 0.12}
}