# kranke - March 2026
# Script to analyze GMST response to different carbon credits scenarios

from   climateScenario import climateScenario
from   constants       import SPECIES
from   matplotlib      import pyplot as plt
from   plot_utils      import plot_gmst_stacked, plot_gmst_totals, plot_gmst_totals
import pandas as pd
import numpy  as np

# Input begins
scen_file   = '/home/kranke/Documents/ResearchProjects/BC3/em2gmst/data/carbonCredits/vcm_credits_retired.csv' # This file should contain the credit scenarios data, with columns for 'Scenario', 'GHG', 'Metric', and yearly values from 2005 to 2100
scen_labels = [ 'BAU', '2xCH4', 'CH4_half_vcm', '0.5xCH4' ]
species     = [ 'CH4', 'CO2red', 'CO2rem', 'ICO2' ] # List of species to analyze, should match the keys in the SPECIES dictionary
# Input ends

# Initialize the output dataframes
credits_scen = pd.read_csv( scen_file )
outer_labels = [ f"{scen}_{spec}" for scen in scen_labels for spec in species ] # This will be used for labeling the output dataframe columns
out_gmst     = pd.DataFrame( columns = ['Year'] + outer_labels ) # This will store the GMST response for each scenario/species combination
out_gmst['Year'] = credits_scen[ credits_scen['Scenario'] == scen_labels[0] ].filter(regex='^\d{4}$').columns.astype(int) # Assuming all scenarios have the same year columns, we can take the years from the first scenario
out_rf           = out_gmst.copy() # This will store the RF for each scenario/species combination
out_conc         = out_gmst.copy() # This will store the concentration of the species for each scenario/species combination
out_emissions    = out_gmst.copy() # This will store the emissions for each scenario/species combination
out_cumulative   = out_gmst.copy() # This will store the cumulative emissions for each scenario/species combination
for scen_selection in scen_labels:
    scen_data      = credits_scen[ credits_scen['Scenario'] == scen_selection ]
    for spec in species:
        print( f"Processing scenario: {scen_selection}, species: {spec}" )
        gas_ts         = scen_data[ ( scen_data['GHG'] == spec  ) & ( scen_data['Metric'] == 'Annual') ]
        df = gas_ts.melt(
            value_vars=[str(y) for y in range(2005, 2101)],
            var_name="year",
            value_name="value"
        )
        df["year"]  = df["year"].astype(int)
        gaslabel = f"{SPECIES[spec]['units']}{SPECIES[spec]['molecule']}"
        df[ gaslabel ] = df["value"] * ( 1000/SPECIES[spec]["GWP100"] ) * SPECIES[spec]["emission_conv"] # covert from credits to kgCH4, then to units used in the RF calculations (ppm for CO2, ppb for CH4)
        df.drop(columns=['value'], inplace=True)
        cs_instance = climateScenario( emissions = df.set_index('year'), name = scen_selection )
        cs_instance.integrate()
        # Save the GMST, RF, concentration, emissions and cumulative emissions for this scenario/species combination in the output dataframes
        out_gmst[f"{scen_selection}_{spec}"]       = cs_instance.outdf['GMST'].values
        out_rf[f"{scen_selection}_{spec}"]         = cs_instance.outdf[f'RF_{SPECIES[spec]["molecule"]}'].values
        out_conc[f"{scen_selection}_{spec}"]       = cs_instance.outdf[f'Catm_{SPECIES[spec]["molecule"]}'].values - SPECIES[spec]["C_PI"] # Convert from concentration to emissions units (kg of that species emitted in that year)
        out_emissions[f"{scen_selection}_{spec}"]  = cs_instance.outdf[f'emissions_{SPECIES[spec]["molecule"]}'].values 
        out_cumulative[f"{scen_selection}_{spec}"] = cs_instance.outdf[f'cumulativeEmissions_{SPECIES[spec]["molecule"]}'].values
        # Plot the results for this scenario/species combination and save out the figure
        figScen = cs_instance.plotOutput( species = spec, units = SPECIES[spec]["units"], title = f'Scenario:{scen_selection}, Species:{spec}', Catm_anomaly_flag = True )
        figScen.savefig( f"plots/{scen_selection}_{spec}_plot.png", dpi=300, bbox_inches="tight", pad_inches=0.05, facecolor="white" )

out_gmst.to_csv( "allscenarios_gmst.csv", index=False )
out_rf.to_csv( "allscenarios_rf.csv", index=False )
out_conc.to_csv( "allscenarios_conc.csv", index=False )
out_emissions.to_csv( "allscenarios_emissions.csv", index=False )
out_cumulative.to_csv( "allscenarios_cumulative.csv", index=False )


# After processing all scenarios/species combinations, we can create a stacked area plot of the GMST contributions for each scenario
colors = plt.cm.tab20(np.linspace(0,1,len(species)))        
fig = plot_gmst_stacked( out_gmst, species, scen_labels, colors = colors )
fig.savefig( f"plots/GMST_stacked_contributions.png", dpi=300, bbox_inches="tight", pad_inches=0.05, facecolor="white" )
fig = plot_gmst_stacked( out_gmst, ['CH4', 'CO2red', 'CO2rem' ], scen_labels, colors = colors[0:3] )
fig.savefig( f"plots/GMST_stacked_contributions_noICO2.png", dpi=300, bbox_inches="tight", pad_inches=0.05, facecolor="white" )
    
fig = plot_gmst_totals(out_gmst, species, scen_labels, title = 'Total GMST with impermanent CO2')
fig.savefig( f"plots/Total_GMST_with_impermanent_CO2.png", dpi=300, bbox_inches="tight", pad_inches=0.05, facecolor="white" )
fig = plot_gmst_totals(out_gmst, ['CH4', 'CO2red', 'CO2rem' ], scen_labels, title = 'Total GMST without impermanent CO2')
fig.savefig( f"plots/Total_GMST_without_impermanent_CO2.png", dpi=300, bbox_inches="tight", pad_inches=0.05, facecolor="white" )