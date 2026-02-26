# kranke - August 2025
# Script to define the climateScenario class for handling emissions scenarios

import pandas            as pd
import numpy             as np
import matplotlib.pyplot as plt
from   constants         import CO2_PI, CH4_PI, DEFAULT_PARAMS, CH4_TAU

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
        else:
            raise ValueError("emissions must be a string or a pandas Series.")

        
    def _load_preset( self, name ):
        """Load emissions data from a CSV file for known presets."""
        name = name.lower()

        if name == "historical":
            return self._load_historical()
        elif name.startswith("ssp"):
            return self._load_sspScenario()
        elif name == 'pulseco2':
            return self._load_pulseCO2()
        elif name == 'pulsech4':
            return self._load_pulseCH4()
        elif name == 'abrupt-4xco2':
            return self._load_abrupt4xCO2()
        elif name.startswith("cmip7_"):
            return self._load_cmip7scenario()
        else:
            raise ValueError(f"Unknown preset '{name}'")
    
    def _load_pulseCO2( self ):
        """Load pulse CO2 emissions data."""
        # Pulse CO2 scenario: 1 GtC pulse in 1750
        years = np.arange( 1750, 2001 )
        df = pd.DataFrame( index = years, data = 0.0, columns = ['ppmCO2'] )
        df.loc[ 1750, 'ppmCO2']  = 1.0 / 7.8  # This is 1 GtC, converted to ppm for the carbon cycle model
        self.flagEmissions       = True
        return df
    
    def _load_pulseCH4( self ):
        """Load pulse CH4 emissions data."""
        # Pulse CH4 scenario: 1 GtCH4 pulse in 1750
        years = np.arange( 1750, 2001 )
        df = pd.DataFrame( index = years, data = 0.0, columns = ['ppmCH4'] )
        df.loc[ 1750, 'ppmCH4']  = 1 / 2.8 * 1e3  # This is 1 GtCH4, converted to ppb for the methane cycle model
        self.flagEmissions       = True
        return df

    
    def _load_abrupt4xCO2( self ):
        """Load abrupt 4xCO2 concentration data."""
        # Abrupt 4xCO2 scenario: 4x pre-industrial CO2 concentration in 1750
        years = np.arange( 1750, 2001 )
        df    = pd.DataFrame( index = years, data = 0.0, columns = ['Catm'] )
        df[ 'Catm' ]       = 277.15 * 4.0
        self.flagEmissions = False
        return df

    
    def _load_historical( self ):
        """Load historical emissions data from a CSV file."""
        filename     = self.datadir + '/historicalEmissions.csv'
        df           = pd.read_csv( filename, index_col = 0 ) # This values are in GtCO2
        df['ppmCO2'] = ( df['FF'] + df['LU'] ) / 2.12         #  ppm/year; for the carbon cycle model
        self.flagEmissions = True
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
        species   = [ s.replace( 'ppm', '' ) for s in emissions.columns[ emissions.columns.str.startswith( 'ppm' ) ] ]
        NS        = len( species )
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
            elif s == 'CH4':
                Catm[ 0, species.index( s ) ] = CH4_PI # Pre-industrial CH4 concentration [ppm]
                RFs[ 0, species.index( s ) ]  = 0.0    # Initial Radiative Forcing [W/m^2]
            else:
                raise ValueError(f"Unknown species '{s}' in emissions data.")
        # Figure out emission vector to be used in the carbon cycle model (if needed)
        if self.flagEmissions == True:
            Et = np.zeros( ( NT, NS ) )
            for s in species:
                for i in range( NT ):
                    idx = np.searchsorted( tvecE, tvec[ i ], side = 'right' ) - 1
                    Et[ i, species.index( s ) ] = emissions.iloc[ idx ][ f'ppm{s}' ] if idx >= 0 else 0
        
        # Handle the pulse cases with a special initial condition
        if self.name ==  'pulseCO2':
            Et = np.zeros( ( NT, NS ) )
            cpool = self._carbonCycle( cpool, emissions['ppmCO2'].iloc[0], 1 ) # Run the carbon cycle for the first time step to get the initial carbon pool state
            Catm[ 0, species.index( 'CO2' ) ] = CO2_PI + np.sum( cpool )
            RFs[  0, species.index( 'CO2' ) ] = self._radiativeForcingCO2( Catm[ 0, species.index( 'CO2' ) ] )    # Initial Radiative Forcing [W/m^2]
        elif self.name == 'pulseCH4':
            Et = np.zeros( ( NT, NS ) )
            Catm[ 0, species.index( 'CH4' ) ] = CH4_PI + emissions.iloc[ 0 ].iloc[0] if 'CH4' in species else CH4_PI
            RFs[  0, species.index( 'CH4' ) ] = self._radiativeForcingCH4( Catm[ 0, species.index( 'CH4' ) ] + CH4_PI )    # Initial Radiative Forcing [W/m^2]

        # Main loop over time #
        idx = 0
        for currtime in tvec[:-1]:
            # Update the current time index
            idx += 1
            # Loop over species to update concentrations, RFs
            for s in species:
                if s == 'CH4':
                    Catm[ idx, species.index( s ) ] = CH4_PI + self._ch4Cycle( Catm[ idx - 1, species.index( s ) ] - CH4_PI, tau = CH4_TAU, Et = Et[ idx-1, species.index( s ) ], dt = dt ) # Update the CH4 cycle and get new concentration
                    RFs[ idx, species.index( s ) ]  = self._radiativeForcingCH4( Catm[ idx, species.index( s ) ] ) # Update the radiative forcing for CH4
                elif s == 'CO2':
                    # Carbon Cycle (skip it if we have concentrations, otherwise run it)
                    if self.flagEmissions == True:
                        cpool       = self._carbonCycle( cpool, Et[idx-1, species.index( s ) ], dt )
                        Catm[ idx, species.index( s ) ] = CO2_PI + np.sum( cpool )
                    else:
                        Catm[ idx, species.index( s ) ] = emissions.iloc[ int( np.searchsorted( emissions.index.values, currtime, side = 'right' ) - 1 ) ].iloc[0]
                    RFs[ idx, species.index( s ) ]  = self._radiativeForcingCO2( Catm[ idx, species.index( s ) ] )
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
                convfac = 7.8 if s == 'CO2' else 2.8 # Convert ppm to GtC for CO2, and ppm to GtCH4 for CH4
                self.outdf[ f'emissions_{s}' ] = emissions[ f'ppm{s}' ] * convfac  # Convert ppm to GtC for emissions
                self.outdf[f'cumulativeEmissions_{s}'] = self.outdf[ f'emissions_{s}' ].cumsum()  # Cumulative emissions in GtC
        
        # Output stuff (on the true grid)
        self.outdf_tgrid = pd.DataFrame( index = tvec, data = { 'GMST': gmst } )
        for s in species:
            self.outdf_tgrid[ f'Catm_{s}' ] = Catm[ :, species.index( s ) ]
            self.outdf_tgrid[ f'RF_{s}' ]   = RFs[ :, species.index( s ) ]
            if self.flagEmissions == True:
                self.outdf_tgrid[ f'emissions_{s}' ] = Et[ :, species.index( s ) ]
                self.outdf_tgrid[f'cumulativeEmissions_{s}'] = np.cumsum( self.outdf_tgrid[ f'emissions_{s}' ] ) * dt  # Cumulative emissions in GtC
        
    
    def _ch4Cycle( self, ch4, tau, Et, dt ):
        """
        This function simulates the methane (CH4) cycle by updating the atmospheric concentration based on emissions data and a specified time scale.
        :param self: The `self` parameter refers to the instance of the class in which this method is defined
        :param tau: The `tau` parameter represents the time scale for the methane cycle in years
        :param Et: The `Et` parameter represents the emissions at the current time step
        :param dt: The `dt` parameter represents the time step for the integration process in years
        """
        
        # Update concentration using a simple exponential decay model
        dCdt       = Et - ( ch4 / tau )
        return ch4 + dt * dCdt
    
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
    
    
    def _overlap(self, M, N):
        return 0.47 * np.log(
            1
            + 2.01e-5 * (M * N)**0.75
            + 5.31e-15 * M * (M * N)**1.52
        )

    def _radiativeForcingCH4(self, M, M0=722, N0=270):
        """
        Radiative forcing from methane (W/m^2)
        M  : CH4 concentration (ppb)
        M0 : reference CH4 (ppb), preindustrial ~722
        N0 : reference N2O (ppb), preindustrial ~270
        """
        return 0.036 * (np.sqrt(M) - np.sqrt(M0)) \
            - (self._overlap(M, N0) - self._overlap(M0, N0))
    

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
    
    def plotOutput( self, species = 'CO2' ):
        """
        This function plots the output of the climate scenario, including CO2 concentration, emissions, radiative forcing, and GMST.
        """
        df = self.outdf
        df["Catm"] = df[ f'Catm_{species}' ]
        df["RF"]   = df[ f'RF_{species}' ]
        
        if self.flagEmissions:
        
            fig, axes = plt.subplots( 1, 3, figsize = ( 15, 5 ), sharex = True )

            # --- Panel 1 ---
            ax1 = axes[ 0 ]
            ax2 = ax1.twinx()

            ax1.plot(df.index, df["Catm"], color="tab:blue"); ax1.set_ylabel(f"{species} Concentration (ppm)", color="tab:blue"); ax1.tick_params(axis="y", labelcolor="tab:blue")
            ax1.grid( True, which='both', linestyle='--', alpha=0.6)  # Grid on left axis
            ax2.plot(df.index, df[f'emissions_{species}'], color = "tab:red" ); ax2.set_ylabel(f"{species} Emissions", color="tab:red");ax2.tick_params(axis="y", labelcolor="tab:red")
            ax1.set_title(f"{species} Emissions vs Concentrations")

            # --- Panel 2 ---
            ax1 = axes[1]
            ax2 = ax1.twinx()

            ax1.plot(df.index, df["Catm"], color="tab:blue"); ax1.set_ylabel(f"{species} Concentration (ppm)", color="tab:blue"); ax1.tick_params(axis="y", labelcolor="tab:blue")
            ax1.grid( True, which='both', linestyle='--', alpha=0.6)  # Grid on left axis
            ax2.plot(df.index, df["RF"], color="tab:green"); ax2.set_ylabel("Effective Radiative Forcing (W m⁻²)", color="tab:green");  ax2.tick_params(axis="y", labelcolor="tab:green")
            ax1.set_title(f"{species} concentrations vs Radiative Forcing")

            # --- Panel 3 ---
            ax1 = axes[2]
            ax2 = ax1.twinx()
            ax1.plot( df.index, df[f'cumulativeEmissions_{species}'], color="tab:purple" ); ax1.set_ylabel(f"Cumulative {species} Emissions", color="tab:purple"); ax1.tick_params(axis="y", labelcolor="tab:purple")
            ax1.grid( True, which='both', linestyle='--', alpha=0.6)  # Grid on left axis
            ax2.plot( df.index, df["GMST"], color="tab:orange"); ax2.set_ylabel("Temp Anomaly (K)", color="tab:orange"); ax2.tick_params(axis="y", labelcolor="tab:orange")
            ax1.set_title(f"Cumulative {species} Emissions vs GMST response")

            # Shared X-axis label
            for ax in axes:
                ax.set_xlabel("Year")

            fig.suptitle( f"{self.name} scenario", fontsize=18, fontweight='bold', y = 1.01 )
            plt.tight_layout()
            
        else:
            fig, axes = plt.subplots(1, 2, figsize=( 10, 4), sharex=True)

            # --- Panel 1 (MATLAB figure 2) ---
            ax1 = axes[0]
            ax2 = ax1.twinx()

            ax1.plot(df.index, df["Catm"], color="tab:blue"); ax1.set_ylabel("CO₂ Concentration (ppm)", color="tab:blue"); ax1.tick_params(axis="y", labelcolor="tab:blue")
            ax2.plot(df.index, df["RF"], color="tab:green");  ax2.set_ylabel( "Effective Radiative Forcing (W m⁻²)", color="tab:green" ); ax2.tick_params(axis="y", labelcolor="tab:green")
            ax1.set_title("CO₂ concentrations vs Radiative Forcing")
            ax1.set_xlabel("Year")
            ax1.grid( True, which='both', linestyle='--', alpha=0.6)  # Grid on left axis

            # --- Panel 2 (MATLAB figure 3) ---
            axes[1].plot(df.index, df["GMST"], color="tab:orange"); axes[1].set_ylabel("Temperature Anomaly wrt PI (K)", color="tab:orange")
            axes[1].tick_params(axis="y", labelcolor="tab:orange")
            axes[1].set_title("GMST Anomaly")
            axes[1].set_xlabel("Year")
            axes[1].grid(True, which='both', linestyle='--', alpha=0.6)
            
            fig.suptitle( f"{self.name} scenario", fontsize=18, fontweight='bold', y = 1.01 )
            plt.tight_layout()
