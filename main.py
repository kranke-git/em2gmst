# Script to figure out GTP, GWP, AGTP, AGWP for a given gas

import matplotlib.pyplot as plt
from   climateScenario import climateScenario

pulseCH4 = climateScenario( 'pulseCH4' )
pulseCH4.integrate()
pulseCH4.plotOutput( species = 'CH4' )

pulseCO2 = climateScenario( 'pulseCO2' )
pulseCO2.integrate()
pulseCO2.plotOutput( species = 'CO2' )

horizons = [20, 50, 100, 250]
gtps_ch4 = []; gwps_ch4 = []
gtps_co2 = []; gwps_co2 = []
for horizon in horizons:
    gwps_ch4.append( pulseCH4.outdf['RF_CH4'].loc[1750 + horizon] / 1e12 ) # K*yr/kg
    gtps_co2.append( pulseCO2.outdf['GMST'].loc[1750 + horizon]   / 1e12 ) # K/kg
    gtps_ch4.append( pulseCH4.outdf['GMST'].loc[1750 + horizon]   / 1e12 ) # K/kg
