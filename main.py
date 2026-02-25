# Script to figure out GTP, GWP, AGTP, AGWP for a given gas

import matplotlib.pyplot as plt
from   climateScenario import climateScenario
pulseCO2 = climateScenario( 'pulseCO2' )
pulseCO2.integrate()