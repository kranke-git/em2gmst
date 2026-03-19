# Script to figure out GTP, GWP, AGTP, AGWP for a given gas

import matplotlib.pyplot as plt
from   climateScenario import climateScenario
import pandas as pd
from   constants       import SPECIES

species = [ 'CO2', 'CH4', 'SF6', 'N2O', 'HFC-134a' ] # List of species to analyze, should match the keys in the SPECIES dictionary
pulse_size_CO2 = 1000 # This is in kg of CO2, which is equivalent to 1 credit of CO2 in the carbon market. We will use this as the reference pulse size for calculating GTP and GWP for CH4.

gmst_responses = {}
for spec in species:
    
    print( f"Processing species: {spec}" )
    pulse_size_spec = pulse_size_CO2 / SPECIES[spec]['GWP100'] # This is in kg, based on the GWP100 of the species
    pulse_instance = climateScenario( f'pulse{spec}', pulse_size = pulse_size_spec )
    pulse_instance.integrate()
    gmst_responses[spec] = pulse_instance.outdf['GMST'].values
    fig = pulse_instance.plotOutput( species = spec, title = f'1 credit of {spec} (~{pulse_size_spec:.2f} kg{spec})' )
    fig.savefig( f"plots/{spec}_pulse1credit.png", dpi=300, bbox_inches="tight", pad_inches=0.05, facecolor="white" )   


# Comparison of credit responses for CH4 vs CO2
figComp = plt.plot( gmst_responses['CH4'], label = 'CH4 credit response', color = 'orange' )
plt.plot( gmst_responses['CO2'], label = 'CO2 credit response', color = 'green' )
plt.xlabel("Year")
plt.ylabel("GMST response (K)")
plt.title("GMST response to 1 credit of CH4 vs CO2")
plt.legend()
plt.grid(True, which='both', linestyle='--', alpha=0.6)
plt.savefig( "plots/GTP_comparison.png", dpi=300, bbox_inches="tight", pad_inches=0.05, facecolor="white" )
plt.show()

# gtp calculations
horizons = [20, 50, 100, 200] 
pulseCO2 = climateScenario( f'pulseCO2', pulse_size = 1 )
pulseCO2.integrate()
gtp_df = pd.DataFrame( index = species, columns = [ f'Year {h}' for h in horizons ] )
for spec in species:
    pulse_spec = climateScenario( f'pulse{spec}', pulse_size = 1 )
    pulse_spec.integrate()
    for h in horizons:
        gtp_df.loc[ spec, f'Year {h}' ] = pulse_spec.outdf['GMST'].values[h] / pulseCO2.outdf['GMST'].values[h]
        print( f"GTP of {spec} relative to CO2 at year {h}: {gtp_df.loc[ spec, f'Year {h}']:.4f}" )