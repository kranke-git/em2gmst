# kranke - August 2025
# Script to define the climateScenario class for handling emissions scenarios

import pandas            as pd
import numpy             as np
import matplotlib.pyplot as plt
import matplotlib        as mpl
from   constants         import CO2_PI, DEFAULT_PARAMS, SPECIES


class climateScenario:
        
    def __init__( self, emissions, name = None, **kwargs ):
        """
        This Python function initializes an object with emissions data and an optional name attribute.
        
        :param emissions: The `emissions` parameter can be either a string (for presets) or a pandas DataFrame (for custom emissions data)
        :param name: The `name` parameter in the `__init__` method is an optional parameter for the custom emissions data
        kwargs : dict
            Override model parameters (e.g., ecs=4.5, ohtr=1.5).
        """
        # Merge defaults with overrides
        self.params = DEFAULT_PARAMS.copy()
        self.params.update( kwargs )
        
        if isinstance( emissions, str ):
            self.name        = name or emissions
            self.preset_name = emissions
            self.datadir = 'https://svante.mit.edu/~pgiani/emissionsdata'
            self.emissions   = self._load_preset( emissions )
        elif isinstance( emissions, pd.Series ):
            self.name        = name or "Custom"
            self.preset_name = None
            self.emissions   = pd.DataFrame( emissions.sort_index() )
            self.emissions['ppmCO2'] = self.emissions['CO2emissions_GtC'] / 2.12  # Convert GtC to ppm for the carbon cycle model
            self.flagEmissions = True
        elif isinstance( emissions, pd.DataFrame ):
            self.name        = name or "Custom"
            self.preset_name = None
            self.emissions   = emissions.sort_index()
            self.flagEmissions = True
        else:
            raise ValueError("emissions must be a string or a pandas Series.")

        
    def _load_preset( self, name ):
        """Load emissions data from a CSV file for known presets."""
        name = name.lower()

        if name == "historical":
            return self._load_historical()
        elif name == "historical_ch4":
            return self._load_historical_ch4()
        elif name == 'pulseco2':
            return self._load_pulseCO2()
        elif name == 'abrupt-4xco2':
            return self._load_abrupt4xCO2()
        elif name.startswith("cmip7_"):
            return self._load_cmip7scenario()
        elif name.startswith("pulse"):
            # we only get here if not pulseCO2, this is for other non-CO2 gases
            return self._load_pulseNonCO2()
        elif name.startswith("ssp"):
            return self._load_sspScenario()
        else:
            raise ValueError(f"Unknown preset '{name}'")
    
    def _load_pulseCO2( self ):
        """Load pulse CO2 emissions data."""
        # Pulse CO2 scenario: 1 GtC pulse in 1750
        years = np.arange( 1750, 2001 )
        df = pd.DataFrame( index = years, data = 0.0, columns = ['ppmCO2'] )
        df.loc[ 1750, 'ppmCO2']  = self.params['pulse_size']  * SPECIES[ "CO2" ]["emission_conv"]  # Assume pulse_size is in kgCO2
        self.flagEmissions       = True
        return df
    
    def _load_pulseNonCO2( self ):
        """Load pulse non-CO2 emissions data."""
        # Pulse non-CO2 scenario: pulse_size in kilograms of that species in 1750
        species = self.name.replace( "pulse", "" ) # Extract the species name from the preset name (e.g., 'CH4' from 'pulseCH4')
        years   = np.arange( 1750, 2001 )
        df      = pd.DataFrame( index = years, data = 0.0, columns = [f'{SPECIES[ species ]["units"]}{species}'] )
        df.loc[ 1750, f'{SPECIES[ species ]["units"]}{species}']  = self.params['pulse_size']  * SPECIES[ species]["emission_conv"]  # Assume pulse_size is in kg of the species
        self.flagEmissions       = True
        return df
    
    def _load_abrupt4xCO2( self ):
        """Load abrupt 4xCO2 concentration data."""
        # Abrupt 4xCO2 scenario: 4x pre-industrial CO2 concentration in 1750
        years = np.arange( 1750, 2001 )
        df    = pd.DataFrame( index = years, data = 0.0, columns = ['Catm_CO2'] )
        df[ 'Catm_CO2' ]       = 277.15 * 4.0
        self.flagEmissions = False
        return df

    
    def _load_historical( self ):
        """Load historical emissions data from a CSV file."""
        filename     = self.datadir + '/historicalEmissions.csv'
        df           = pd.read_csv( filename, index_col = 0 ) # This values are in GtCO2
        df['ppmCO2'] = ( df['FF'] + df['LU'] ) / 2.12         #  ppm/year; for the carbon cycle model
        self.flagEmissions = True
        return df 
    
    def _load_historical_ch4( self ):
        """Load historical CH4 emissions data from a CSV file."""
        fair_emissions_file = '/home/kranke/Documents/ResearchProjects/BC3/Data/emissionsdata/CEDS_CH4_global_emissions_by_CEDS_sector_v_2019_12_23.csv'
        df                  = pd.read_csv( fair_emissions_file, header = None, names = ['Year', 'Emissions'] )  
        df['ppbCH4']        = df['Emissions'] / 2.8
        self.flagEmissions = True
        df.set_index( 'Year', inplace=True )

        return df
    
    def _load_sspScenario( self ):
        """Load SSP Concentrations data from a CSV file."""
        histfile = self.datadir + '/CO2molefractions_hist_ssp/mole-fraction-of-carbon-dioxide-in-air_input4MIPs_GHGConcentrations_CMIP_UoM-CMIP-1-2-0_gr1-GMNHSH_0000-2014.csv'
        sspfiles = {'ssp119': 'mole-fraction-of-carbon-dioxide-in-air_input4MIPs_GHGConcentrations_ScenarioMIP_UoM-IMAGE-ssp119-1-2-1_gr1-GMNHSH_2015-2500.csv',
                    'ssp126': 'mole-fraction-of-carbon-dioxide-in-air_input4MIPs_GHGConcentrations_ScenarioMIP_UoM-IMAGE-ssp126-1-2-1_gr1-GMNHSH_2015-2500.csv',
                    'ssp245': 'mole-fraction-of-carbon-dioxide-in-air_input4MIPs_GHGConcentrations_ScenarioMIP_UoM-MESSAGE-GLOBIOM-ssp245-1-2-1_gr1-GMNHSH_2015-2500.csv',
                    'ssp370': 'mole-fraction-of-carbon-dioxide-in-air_input4MIPs_GHGConcentrations_ScenarioMIP_UoM-AIM-ssp370-1-2-1_gr1-GMNHSH_2015-2500.csv',
                    'ssp585': 'mole-fraction-of-carbon-dioxide-in-air_input4MIPs_GHGConcentrations_ScenarioMIP_UoM-REMIND-MAGPIE-ssp585-1-2-1_gr1-GMNHSH_2015-2500.csv' }
        if self.name in sspfiles.keys():
            sspfile  = f"{self.datadir}/CO2molefractions_hist_ssp/{sspfiles[ self.name ] }"
        else:
            raise ValueError(f"Unknown SSP scenario '{self.name}'. Valid options are: {', '.join(sspfiles.keys())}")    
        # Process historical and SSP concentration data
        histdf   = pd.read_csv( histfile )
        sspdf    = pd.read_csv( sspfile )
        merged   = pd.concat( [ histdf, sspdf ] ).sort_values(by='year').drop_duplicates( subset='year', keep='last').sort_values('year')
        merged.set_index( 'year', inplace = True )
        merged   = merged.rename( columns = { 'data_mean_global': 'Catm' } ) 
        syear    = 1750
        eyear    = 2100
        # Set emission flag to be false for SSP scenarios
        self.flagEmissions = False
        dfout = merged.loc[ syear:eyear ][['Catm']]
        dfout.rename( columns={ 'Catm': 'ppmCO2' }, inplace=True )
        return dfout
    
    def _load_cmip7scenario( self ):
        """Load CMIP7 Emissions data from the big CSV file."""
        filename = self.datadir + '/cmip7_extensions_1750-2500.csv'
        # Read in the data and subset for the correct scenario and CO2 only
        df             = pd.read_csv( filename, index_col = 0 )
        dfCO2          = df[ ( ( df['variable'] == 'CO2 AFOLU' ) | ( df['variable'] == 'CO2 FFI' ) ) ]
        scen_name_file = self.name.replace( 'cmip7_', '', 1 )
        if scen_name_file not in dfCO2.index:
            raise ValueError(f"Unknown CMIP7 scenario '{self.name}'. Valid options are: {', '.join( dfCO2.index.unique() ) }" )
        else:
            dfscen         = dfCO2[ dfCO2.index == scen_name_file ]
        # Convert to a DataFrame with 'year' as index
        numeric_data   = dfscen.drop( columns=['region', 'variable', 'ar6_gwp_mass_adjusted', 'unit'] )
        sum_by_year    = numeric_data.sum( axis=0 )
        df_sum           = sum_by_year.reset_index()
        df_sum.columns   = ['year', 'total_GtCO2']
        df_sum[ 'year' ] = ( df_sum[ 'year' ].astype( float ) - 0.5).astype( int )
        df_sum['ppmCO2'] = df_sum['total_GtCO2'] / 2.12 * 12/44  # Convert GtCO2 to ppm for the carbon cycle model
        df_sum.set_index( 'year', inplace=True )
        # These are emission driven scenarios, so we set the flag accordingly
        self.flagEmissions = True
        return df_sum

        
    def integrate( self, dt = 0.1 ):
        """
        This function integrates emissions data over time to simulate the carbon cycle and update atmospheric CO2 concentration and GMST.
        :param self: The `self` parameter refers to the instance of the class in which this method is defined
        :param dt: The `dt` parameter in the `integrate` method represents the time step for the integration process, which is set to 0.1 by default
        """
        # Unpack variables from self
        emissions = self.emissions
        species_units = {
            c[3:]: c[:3]
            for c in emissions.columns
            if c.startswith(('ppm', 'ppb', 'ppt'))
        }        
        species = list( species_units.keys() )
        units   = list( species_units.values() )
        NS      = len( species )
        # Assign time stuff and initialize variables to nan
        startTime          = emissions.index.min()
        endTime            = emissions.index.max()
        tvec               = np.arange( startTime, endTime + dt, dt )
        tvecE              = emissions.index.values
        NT                 = int( ( endTime - startTime ) / dt ) + 1
        Catm               = np.full( ( NT, NS ), np.nan )
        Et                 = np.full( ( NT, NS ), np.nan )
        RFs                = Catm.copy()
        gmst               = np.full( NT, np.nan )
        oceantemps         = np.full( ( NT, 4 ), np.nan )
        # Initial conditions for temperatures
        gmst[ 0 ]          = 0.0    # Initial GMST anomaly [K]
        oceantemps[ 0, : ] = 0.0    # Initial ocean temperature anomalies [K]
        
        # Initial condition for gas species
        for s in species:
            if s == 'CO2':
                Catm[ 0, species.index( s ) ] = CO2_PI # Pre-industrial CO2 concentration [ppm]
                RFs[ 0, species.index( s ) ]  = 0.0    # Initial Radiative Forcing [W/m^2]
                cpool                         = np.zeros( ( 1, 4 ) ) # Initial carbon pool for the carbon cycle model
            else:
                Catm[ 0, species.index( s ) ] = SPECIES[ s ][ 'C_PI' ] # Pre-industrial CH4 concentration [ppm]
                RFs[ 0, species.index( s ) ]  = 0.0    # Initial Radiative Forcing [W/m^2]
            
        # Figure out emission vector to be used in the carbon cycle model (if needed)
        if self.flagEmissions == True:
            Et = np.zeros( ( NT, NS ) )
            for s in species:
                for i in range( NT ):
                    idx = np.searchsorted( tvecE, tvec[ i ], side = 'right' ) - 1
                    Et[ i, species.index( s ) ] = emissions.iloc[ idx ][ f'{units[species.index(s)]}{s}' ] if idx >= 0 else 0
        
        # Handle the pulse cases with a special initial condition
        if self.name ==  'pulseCO2':
            Et = np.zeros( ( NT, 1 ) )
            cpool = self._carbonCycle( cpool, emissions[f'{units[species.index("CO2")]}CO2'].iloc[0], 1 ) # Run the carbon cycle for the first time step to get the initial carbon pool state
            Catm[ 0, species.index( 'CO2' ) ] = CO2_PI + np.sum( cpool )
            RFs[  0, species.index( 'CO2' ) ] = self._radiativeForcingCO2( Catm[ 0, species.index( 'CO2' ) ] )    # Initial Radiative Forcing [W/m^2]
        elif self.name.startswith( 'pulse' ):
            Et      = np.zeros( ( NT, 1 ) )
            Catm[ 0, species.index( species[ 0 ] ) ] = SPECIES[ species[ 0 ] ][ 'C_PI' ] + emissions.iloc[ 0 ][ f'{SPECIES[ species[ 0 ]]["units"]}{species[ 0 ]}' ] # Set the initial concentration based on the pulse size
            C0      = SPECIES[ species[ 0 ] ][ 'C_PI' ]
            f1      = SPECIES[ species[ 0 ] ][ 'f1' ]
            f2      = SPECIES[ species[ 0 ] ][ 'f2' ]
            f3      = SPECIES[ species[ 0 ] ][ 'f3' ]
            RFs[  0, species.index( species[ 0 ] ) ] = self._gasRadiativeForcing( f1, f2, f3, Catm[ 0, species.index( species[ 0 ] ) ], C0 ) # Update the radiative forcing for CH4 based on the initial concentration

        # Main loop over time #
        idx = 0
        for currtime in tvec[:-1]:
            # Update the current time index
            idx += 1
            # Loop over species to update concentrations, RFs
            for s in species:
                if s == 'CO2':
                    # Carbon Cycle (skip it if we have concentrations, otherwise run it)
                    if self.flagEmissions == True:
                        cpool       = self._carbonCycle( cpool, Et[idx-1, species.index( s ) ], dt )
                        Catm[ idx, species.index( s ) ] = CO2_PI + np.sum( cpool )
                    else:
                        Catm[ idx, species.index( s ) ] = emissions.iloc[ int( np.searchsorted( emissions.index.values, currtime, side = 'right' ) - 1 ) ][ f'{units[species.index(s)]}{s}' ]
                    RFs[ idx, species.index( s ) ]  = self._radiativeForcingCO2( Catm[ idx - 1, species.index( s ) ] )
                else:
                    # Not CO2 - use gas cycle and general radiative forcing function
                    C0      = SPECIES[ s ][ 'C_PI' ]
                    tau_gas = SPECIES[ s ][ 'tau' ]
                    f1      = SPECIES[ s ][ 'f1' ]
                    f2      = SPECIES[ s ][ 'f2' ]
                    f3      = SPECIES[ s ][ 'f3' ]
                    Catm[ idx, species.index( s ) ] = C0 + self._gasCycle( Catm[ idx - 1, species.index( s ) ] - C0, tau = tau_gas, Et = Et[ idx-1, species.index( s ) ], dt = dt ) # Update the CH4 cycle and get new concentration
                    RFs[ idx, species.index( s ) ]  = self._gasRadiativeForcing( f1, f2, f3, Catm[ idx - 1, species.index( s ) ], C0 ) # Update the radiative forcing
            # Climate Model
            totalRF = np.nansum( RFs[ idx - 1, : ] )
            gmst[ idx ], oceantemps[ idx, : ] = self._climateModel( totalRF, gmst[ idx - 1], oceantemps[ idx-1, : ], dt )
            
        # Output stuff (Interpolated)#
        indices     = np.searchsorted( tvec, emissions.index, side='right') - 1
        gmst_interp = gmst[ indices ]
        self.outdf  = pd.DataFrame({'GMST': gmst_interp, }, index = emissions.index )
        for s in species:
            self.outdf[ f'Catm_{s}' ] = Catm[ indices, species.index( s ) ]
            self.outdf[ f'RF_{s}' ]   = RFs[ indices, species.index( s ) ]
            if self.flagEmissions == True:
                convfac = 1 / SPECIES[ s ]['emission_conv']
                self.outdf[ f'emissions_{s}' ] = emissions[ f'{units[species.index(s)]}{s}' ] * convfac  # Convert ppm to GtC for emissions
                self.outdf[f'cumulativeEmissions_{s}'] = self.outdf[ f'emissions_{s}' ].cumsum()  # Cumulative emissions in GtC
        
        # Output stuff (on the true grid)
        self.outdf_tgrid = pd.DataFrame( index = tvec, data = { 'GMST': gmst } )
        for s in species:
            self.outdf_tgrid[ f'Catm_{s}' ] = Catm[ :, species.index( s ) ]
            self.outdf_tgrid[ f'RF_{s}' ]   = RFs[ :, species.index( s ) ]
            if self.flagEmissions == True:
                self.outdf_tgrid[ f'emissions_{s}' ] = Et[ :, species.index( s ) ]
                self.outdf_tgrid[f'cumulativeEmissions_{s}'] = np.cumsum( self.outdf_tgrid[ f'emissions_{s}' ] ) * dt  # Cumulative emissions in GtC
        
    
    def _gasCycle( self, gas, tau, Et, dt ):
        """
        This function simulates the gas cycle by updating the atmospheric concentration based on emissions data and a specified time scale.
        :param self: The `self` parameter refers to the instance of the class in which this method is defined
        :param tau: The `tau` parameter represents the time scale for the gas cycle in years
        :param Et: The `Et` parameter represents the emissions at the current time step
        :param dt: The `dt` parameter represents the time step for the integration process in years
        """
        
        # Update concentration using a simple exponential decay model
        dCdt       = Et - ( gas / tau )
        return gas + dt * dCdt
    
    def _carbonCycle( self, cpool, Et, dt ):
        """
        This function simulates the carbon cycle by updating the atmospheric CO2 concentration based on emissions data.
        :param self: The `self` parameter refers to the instance of the class in which this method is defined
        """
        
        # Carbon cycle parameters (from Joos et al., 2013)
        a   = np.array(self.params["a"])   # fractions in each reservoir
        tau = np.array(self.params["tau"]) # time scale in years for each reservoir

        # Vectorized update of all carbon reservoirs
        dydt  = a * Et - cpool / tau
        cpool = cpool + dt * dydt

        # Sum it up to get C concentrations and assign to outstruct
        return cpool
    
    def _radiativeForcingCO2( self, C ):
        """
        Compute Radiative Forcing (RF) from CO2 concentration C (ppm), based on AR6 Table 6.2 parameters (similar to EnROADS).
        Parameters:
        - C : scalar or numpy array of CO2 concentrations [ppm]
        Returns:
        - RF : Radiative Forcing [W/m^2], same shape as C
        """

        a1 = -2.4785e-7   # W m-2 ppm-2
        b1 = 7.5906e-4    # W m-2 ppm-1
        d1 = 5.2488       # W m-2
        C0 = 277.15       # Preindustrial Concentration [ppm]

        # Calculate Camax based on the formula provided
        Camax = C0 - b1 / (2 * a1)

        # Ensure C is a numpy array for vectorized logic
        C              = np.array( C, dtype = float )
        coefC          = np.full_like( C, d1 )
        mask1          = C >= Camax
        mask2          = (C < Camax) & (C > C0)
        mask3          = C <= C0 
        coefC[ mask1 ] = d1 - (b1 ** 2) / (d1 * a1)
        coefC[ mask2 ] = d1 + a1 * (C[mask2] - C0) ** 2 + b1 * (C[mask2] - C0)
        coefC[ mask3 ] = d1
        rf             = coefC * np.log( C / C0 )
        return( rf )
    
    def _gasRadiativeForcing( self, f1, f2, f3, C, C0 = 0.0 ):
        """
        General radiative forcing function (FaIR-style, no overlap terms).

        Parameters
        ----------
        C : float or array
            Current concentration
        C0 : float
            Reference (preindustrial) concentration
        f1 : float
            Logarithmic coefficient (CO2-like)
        f2 : float
            Square-root coefficient (CH4/N2O-like)
        f3 : float
            Linear coefficient (F-gases)

        Returns
        -------
        RF : float or array
            Radiative forcing (W/m^2)
        """

        C  = np.asarray(C, dtype=float)
        rf = np.zeros_like(C)

        # Log term (CO2-like)
        if f1 > 0:
            rf_log  = f1 * np.log(C / C0)
        else:
            rf_log = 0
        # Linear term (F-gases like)
        rf_lin  = f2 * (C - C0)
        # Square-root term (CH4/N2O-like)
        rf_sqrt = f3 * (np.sqrt(C) - np.sqrt(C0))
        # Combine terms
        rf = rf_log + rf_sqrt + rf_lin
        return rf

    def _climateModel( self, RF, tanm_ao, tanm_d, dt ):
        """_summary_

        Args:
            cpool (_type_): _description_
            emissions (_type_): _description_
            tvec (_type_): _description_
            currtime (_type_): _description_
            dt (_type_): _description_
        """
        # Define parameters
        eartharea = 5.1e14               # m2
        lfrac     = 0.292                # -
        lthk      = 8.4                  # m
        othk      = 100                  # m
        omhc      = 4186                 # J kg-1 K-1
        odens     = 1000                 # kg m-3
        dthk      = np.array([300, 300, 1300, 1800])  # m
        spy       = 3600 * 24 * 365.25   # s yr-1
        ecs       = self.params["ecs"]   # K
        ohtr      = self.params["ohtr"]  # W m-2 K-1

        # Initialization
        NLEV          = len( dthk )
        ao_vol        = eartharea * ( lfrac * lthk + (1 - lfrac) * othk )
        ao_vhc        = omhc * odens
        ao_hc         =  (ao_vol * ao_vhc ) / eartharea
        d_vol         = ( 1 - lfrac ) * eartharea * dthk
        d_vhc         = ao_vhc
        d_hc          = ( d_vol * d_vhc ) / eartharea
        layert        = np.concatenate( ( [ othk ], dthk ) )
        mlayert       = np.mean( np.vstack( ( layert[:-1], layert[1:] ) ), axis=0 )
        htc           = ohtr * mlayert[ 0 ]
        feedbackParam = self._radiativeForcingCO2( 277.15 * 2 ) / ecs

        # Initial condition for current step
        aoQ = tanm_ao * ao_hc
        dQ  = tanm_d  * d_hc

        # Terms and update
        feedcooling = tanm_ao * feedbackParam
        htr         = np.full( NLEV, np.nan )
        htr[0]      = ( tanm_ao - tanm_d[0] ) * htc / mlayert[ 0 ]
        htr[1:]     = ( ( dQ[:-1] / d_hc[:-1]) - ( dQ[1:] / d_hc[1:] ) ) * htc / mlayert[1:]
        aoQnew      = aoQ + dt * ( RF - feedcooling - htr[0] ) * spy # Update equation for gmst
        dQnew       = np.full( NLEV, np.nan )
        dQnew[:-1]  = dQ[:-1] + dt * ( htr[:-1] - htr[1:] ) * spy
        dQnew[-1]   = dQ[-1]  + dt * htr[-1] * spy

        # Post-processing
        return aoQnew / ao_hc, dQnew / d_hc
    
    def plotOutput( self, species = 'CO2', title = None, family = 'monospace', Catm_anomaly_flag = False, **kwargs ):
        """
        This function plots the output of the climate scenario, including CO2 concentration, emissions, radiative forcing, and GMST.
        """
        mpl.rcParams['font.family'] = family

        # Handle species name for labeling
        units  = SPECIES[species]['units']
        unitsE = f'kg{species}'
        if species == 'ICO2' or species == 'CO2rem' or species == 'CO2red':
            species = 'CO2'        
        df = self.outdf.copy()
        df["Catm"] = df[ f'Catm_{species}' ]
        df["RF"]   = df[ f'RF_{species}' ]
        if Catm_anomaly_flag == True:
            df["Catm"] = df["Catm"] - df["Catm"].iloc[0]  # Convert to anomaly by subtracting the initial value
            ylab_catm = f"{species} Concentration Anomaly ({units})"
        else:
            ylab_catm = f"{species} Concentration ({units})"

            
        if title is None:
            title = f"{self.name} scenario"
        
        if self.flagEmissions:
        
            fig, axes = plt.subplots( 1, 3, figsize = ( 15, 5 ), sharex = True )

            # --- Panel 1 ---
            ax1 = axes[ 0 ]
            ax2 = ax1.twinx()

            ax1.plot(df.index, df["Catm"], color="tab:blue"); ax1.set_ylabel(ylab_catm, color="tab:blue"); ax1.tick_params(axis="y", labelcolor="tab:blue")
            ax1.grid( True, which='both', linestyle='--', alpha=0.6)  # Grid on left axis
            ax2.plot(df.index, df[f'emissions_{species}'], color = "tab:red" ); ax2.set_ylabel(f"{species} Emissions ({unitsE})", color="tab:red");ax2.tick_params(axis="y", labelcolor="tab:red")
            ax1.set_title(f"{species} Emissions vs Concentrations")

            # --- Panel 2 ---
            ax1 = axes[1]
            ax2 = ax1.twinx()

            ax1.plot(df.index, df["Catm"], color="tab:blue"); ax1.set_ylabel(ylab_catm, color="tab:blue"); ax1.tick_params(axis="y", labelcolor="tab:blue")
            ax1.grid( True, which='both', linestyle='--', alpha=0.6)  # Grid on left axis
            ax2.plot(df.index, df["RF"], color="tab:green"); ax2.set_ylabel("Effective Radiative Forcing (W m⁻²)", color="tab:green");  ax2.tick_params(axis="y", labelcolor="tab:green")
            ax1.set_title(f"{species} concentrations vs Radiative Forcing")

            # --- Panel 3 ---
            ax1 = axes[2]
            ax2 = ax1.twinx()
            ax1.plot( df.index, df[f'cumulativeEmissions_{species}'], color="tab:purple" ); ax1.set_ylabel(f"Cumulative {species} Emissions ({unitsE})", color="tab:purple"); ax1.tick_params(axis="y", labelcolor="tab:purple")
            ax1.grid( True, which='both', linestyle='--', alpha=0.6)  # Grid on left axis
            ax2.plot( df.index, df["GMST"], color="tab:orange"); ax2.set_ylabel("Temp Anomaly (K)", color="tab:orange"); ax2.tick_params(axis="y", labelcolor="tab:orange")
            ax1.set_title(f"Cumulative {species} Emissions vs GMST response")

            # Shared X-axis label
            for ax in axes:
                ax.set_xlabel("Year")

            fig.suptitle( title, fontsize=18, fontweight='bold', y = 1.01 )
            plt.tight_layout()
            
        else:
            fig, axes = plt.subplots(1, 2, figsize=( 10, 4), sharex=True)

            # --- Panel 1 (MATLAB figure 2) ---
            ax1 = axes[0]
            ax2 = ax1.twinx()

            ax1.plot(df.index, df["Catm"], color="tab:blue"); ax1.set_ylabel(ylab_catm, color="tab:blue"); ax1.tick_params(axis="y", labelcolor="tab:blue")
            ax2.plot(df.index, df["RF"], color="tab:green");  ax2.set_ylabel( "Effective Radiative Forcing (W m⁻²)", color="tab:green" ); ax2.tick_params(axis="y", labelcolor="tab:green")
            ax1.set_title(f"{species} concentrations vs Radiative Forcing")
            ax1.set_xlabel("Year")
            ax1.grid( True, which='both', linestyle='--', alpha=0.6)  # Grid on left axis

            # --- Panel 2 (MATLAB figure 3) ---
            axes[1].plot(df.index, df["GMST"], color="tab:orange"); axes[1].set_ylabel("Temperature Anomaly (K)", color="tab:orange")
            axes[1].tick_params(axis="y", labelcolor="tab:orange")
            axes[1].set_title("GMST Anomaly")
            axes[1].set_xlabel("Year")
            axes[1].grid(True, which='both', linestyle='--', alpha=0.6)
            
            fig.suptitle( title, fontsize=18, fontweight='bold', y = 1.01 )
            plt.tight_layout()
            
        return fig