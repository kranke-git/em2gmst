# Script to figure out GTP, GWP, AGTP, AGWP for a given gas

import matplotlib.pyplot as plt
from   climateScenario import climateScenario
import pandas as pd

GWP100_CH4     = 28 # Global Warming Potential of CH4 over 100 years, relative to CO2
pulse_size_CO2 = 1000e3 # This is in grams (1000 kg = 1 tonne = 0.001 Gt)
pulse_size_CH4 = pulse_size_CO2 / GWP100_CH4 # This is in grams (1000 kg = 1 tonne = 0.001 Gt)


pulseCH4 = climateScenario( 'pulseCH4', pulse_size = pulse_size_CH4 ) # Convert from kg to g
pulseCH4.integrate()
figCH4 = pulseCH4.plotOutput( species = 'CH4', units = 'ppb', title = '1 credit of CH4 (~35 kgCH4)' )
figCH4.savefig( "CH4plot.png", dpi=300, bbox_inches="tight", pad_inches=0.05, facecolor="white" )

pulseCO2 = climateScenario( 'pulseCO2', pulse_size = pulse_size_CO2 )
pulseCO2.integrate()
figCO2 = pulseCO2.plotOutput( species = 'CO2', units = 'ppm', title = '1 credit of CO2 (1000 kgCO2)' )
figCO2.savefig( "CO2plot.png", dpi=300, bbox_inches="tight", pad_inches=0.05, facecolor="white" )

# Comparison of GTP
figComp = plt.plot( pulseCH4.outdf['GMST'], label = 'CH4 credit response', color = 'orange' )
plt.plot( pulseCO2.outdf['GMST'], label = 'CO2 credit response', color = 'green' )
plt.xlabel("Year")
plt.ylabel("GMST response (K)")
plt.title("GMST response to 1 credit of CH4 vs CO2")
plt.legend()
plt.grid(True, which='both', linestyle='--', alpha=0.6)
plt.savefig( "GTP_comparison.png", dpi=300, bbox_inches="tight", pad_inches=0.05, facecolor="white" )
plt.show()

# GTP and GWP calculations

pulseCH4_1kg = climateScenario( 'pulseCH4', pulse_size = 1e3 ) # 1 kg of CH4
pulseCH4_1kg.integrate()
horizons = [20, 50, 100, 250]
gtps_ch4 = []; gwps_ch4 = []
gtps_co2 = []; gwps_co2 = []
for horizon in horizons:
    gtps_co2.append( pulseCO2.outdf['GMST'].loc[1750 + horizon] / 1e3  ) # K/kg
    gtps_ch4.append( pulseCH4_1kg.outdf['GMST'].loc[1750 + horizon]  ) # K/kg

ratio = [ gtps_ch4[i] / gtps_co2[i] for i in range(len(horizons)) ]

ch4_historical = climateScenario( 'historical_ch4' )
ch4_historical.integrate()
figHistorical = ch4_historical.plotOutput( species = 'CH4', units = 'ppb', title = 'Historical CH4 emissions and GMST response' )