# kranke - August 2025
# Script to define the climateScenario class for handling emissions scenarios

import pandas            as pd
import numpy             as np
import matplotlib.pyplot as plt
import matplotlib        as mpl
import xarray            as xr
from   constants         import CO2_PI, DEFAULT_PARAMS, SPECIES
from   pathlib           import Path
from   urllib.request    import urlretrieve


class climateScenario:
        
    def __init__( self, emissions, name = None, datadir = './data', **kwargs ):
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
        
        self.datadir        = Path( datadir )
        self.remote_datadir = 'https://svante.mit.edu/~pgiani/emissionsdata'
        
        if isinstance( emissions, str ):
            self.name        = name or emissions
            self.preset_name = emissions
            # Handle end_year for historical (set to 2025 by default in case not passed and user selected historical)
            if emissions == 'historical':
                if 'end_year' not in kwargs:
                    self.params['end_year'] = 2025

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
        
        
    def _get_datafile(self, filename):

        local_path = self.datadir / filename

        if local_path.is_file():
            return local_path

        local_path.parent.mkdir(parents=True, exist_ok=True)

        remote_url = f"{self.remote_datadir}/{filename}"
        tmp_path = local_path.with_suffix(local_path.suffix + '.tmp')

        try:
            urlretrieve(remote_url, tmp_path)
            tmp_path.replace(local_path)
        finally:
            tmp_path.unlink(missing_ok=True)

        return local_path
        
    def _load_preset( self, name ):
        """Load emissions data from a CSV file for known presets."""
        name = name.lower()

        if name == "historical_co2":
            return self._load_historical_co2()
        elif name == 'historical':
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
        years = np.arange( 1750, self.params['end_year'] + 1 )
        df    = pd.DataFrame( index = years, data = 0.0, columns = ['ppmCO2'] )
        df.loc[ 1750, 'ppmCO2']  = self.params['pulse_size']  * SPECIES[ "CO2" ]["emission_conv"]  # Assume pulse_size is in kgCO2
        self.flagEmissions       = True
        return df
    
    def _load_pulseNonCO2( self ):
        """Load pulse non-CO2 emissions data."""
        # Pulse non-CO2 scenario: pulse_size in kilograms of that species in 1750
        species = self.name.replace( "pulse", "" ) # Extract the species name from the preset name (e.g., 'CH4' from 'pulseCH4')
        years   = np.arange( 1750, self.params['end_year'] + 1 )
        df      = pd.DataFrame( index = years, data = 0.0, columns = [f'{SPECIES[ species ]["units"]}{species}'] )
        df.loc[ 1750, f'{SPECIES[ species ]["units"]}{species}']  = self.params['pulse_size']  * SPECIES[ species]["emission_conv"]  # Assume pulse_size is in kg of the species
        self.flagEmissions       = True
        return df
    
    def _load_abrupt4xCO2( self ):
        """Load abrupt 4xCO2 concentration data."""
        # Abrupt 4xCO2 scenario: 4x pre-industrial CO2 concentration in 1750
        years = np.arange( 1750, self.params['end_year'] + 1 )
        df    = pd.DataFrame( index = years, data = 0.0, columns = ['Catm_CO2'] )
        df[ 'Catm_CO2' ]       = 277.15 * 4.0
        self.flagEmissions = False
        return df

    
    def _load_historical_co2( self ):
        """Load historical emissions data from a CSV file."""
        filename     = self._get_datafile('historicalEmissions.csv')
        df           = pd.read_csv( filename, index_col = 0 ) # This values are in GtCO2
        df['ppmCO2'] = ( df['FF'] + df['LU'] ) / 2.12         #  ppm/year; for the carbon cycle model
        self.flagEmissions = True
        return df 
    
    def _load_historical_ch4( self ):
        """Load historical CH4 emissions data from a CSV file."""
        fair_emissions_file = self._get_datafile('CEDS_CH4_global_emissions_by_CEDS_sector_v_2019_12_23.csv')
        df                  = pd.read_csv( fair_emissions_file, header = None, names = ['Year', 'Emissions'] )  
        df['ppbCH4']        = df['Emissions'] / 2.8
        self.flagEmissions = True
        df.set_index( 'Year', inplace=True )
        return df
    
    def _load_historical(self):
        """
        Load historical emissions for multiple greenhouse gases.
        Input CSV units:
            CO2_total : Mt CO2/yr
            CH4       : Mt CH4/yr
            N2O       : kt N2O/yr
            SF6       : kt SF6/yr
            HFC134a   : kt HFC134a/yr

        Output:
            DataFrame with columns ppmCO2, ppbCH4, ppbN2O,
            pptSF6, pptHFC134a.
        """

        filename = self._get_datafile('global_emissions_1750_2025_by_species.csv')
        df       = pd.read_csv(filename, index_col=0)

        # Species and input mass units (kg per unit of CSV emissions)
        species = {
            'CO2':      ('CO2_total', 1e9),
            'CH4':      ('CH4',       1e9),
            'N2O':      ('N2O',       1e6),
            'SF6':      ('SF6',       1e6),
            'HFC-134a': ('HFC134a',   1e6),
        }

        dfout = pd.DataFrame(index=df.index)

        for s, (column, factor) in species.items():

            # Conversion from kg emissions to atmospheric concentration change
            conv = SPECIES[s]['emission_conv']
            units = SPECIES[s]['units']
            dfout[f'{units}{s}'] = df[column] * factor * conv
            # subtract preindustrial baseline that maintains PI concentrations
            dfout[f'{units}{s}'] -= dfout[f'{units}{s}'].iloc[0]

        external_filename = self._get_datafile('external_forcing_ssp245_1750_2100.csv')
        external          = pd.read_csv( external_filename, index_col=0 )       
        # Select only forcing columns meant to drive the climate model
        external = external[[   'RF_aerosol', 'RF_ozone', 'RF_stratospheric_H2O', 'RF_contrails', 'RF_bc_snow',
                                'RF_land_use', 'RF_volcanic', 'RF_solar' ]]
        dfout             = dfout.join( external , how='left')
        self.flagEmissions = True
        
        # Cut dataframe up to desired end_year
        dfout = dfout.loc[:self.params['end_year']]
        
        return dfout
    
    def _load_sspScenario( self ):
        """Load SSP Concentrations data from a CSV file."""
        histfile = self._get_datafile('CO2molefractions_hist_ssp/mole-fraction-of-carbon-dioxide-in-air_input4MIPs_GHGConcentrations_CMIP_UoM-CMIP-1-2-0_gr1-GMNHSH_0000-2014.csv')
        sspfiles = {'ssp119': 'mole-fraction-of-carbon-dioxide-in-air_input4MIPs_GHGConcentrations_ScenarioMIP_UoM-IMAGE-ssp119-1-2-1_gr1-GMNHSH_2015-2500.csv',
                    'ssp126': 'mole-fraction-of-carbon-dioxide-in-air_input4MIPs_GHGConcentrations_ScenarioMIP_UoM-IMAGE-ssp126-1-2-1_gr1-GMNHSH_2015-2500.csv',
                    'ssp245': 'mole-fraction-of-carbon-dioxide-in-air_input4MIPs_GHGConcentrations_ScenarioMIP_UoM-MESSAGE-GLOBIOM-ssp245-1-2-1_gr1-GMNHSH_2015-2500.csv',
                    'ssp370': 'mole-fraction-of-carbon-dioxide-in-air_input4MIPs_GHGConcentrations_ScenarioMIP_UoM-AIM-ssp370-1-2-1_gr1-GMNHSH_2015-2500.csv',
                    'ssp585': 'mole-fraction-of-carbon-dioxide-in-air_input4MIPs_GHGConcentrations_ScenarioMIP_UoM-REMIND-MAGPIE-ssp585-1-2-1_gr1-GMNHSH_2015-2500.csv' }
        if self.name in sspfiles.keys():
            sspfile  = self._get_datafile(f"CO2molefractions_hist_ssp/{sspfiles[ self.name ] }")
        else:
            raise ValueError(f"Unknown SSP scenario '{self.name}'. Valid options are: {', '.join(sspfiles.keys())}")    
        # Process historical and SSP concentration data
        histdf   = pd.read_csv( histfile )
        sspdf    = pd.read_csv( sspfile )
        merged   = pd.concat( [ histdf, sspdf ] ).sort_values(by='year').drop_duplicates( subset='year', keep='last').sort_values('year')
        merged.set_index( 'year', inplace = True )
        merged   = merged.rename( columns = { 'data_mean_global': 'Catm' } ) 
        syear    = 1750
        eyear    = self.params['end_year']
        # Set emission flag to be false for SSP scenarios
        self.flagEmissions = False
        dfout = merged.loc[ syear:eyear ][['Catm']]
        dfout.rename( columns={ 'Catm': 'ppmCO2' }, inplace=True )
        return dfout
    
    def _load_cmip7scenario( self ):
        """Load CMIP7 Emissions data from the big CSV file."""
        filename = self._get_datafile('cmip7_extensions_1750-2500.csv')
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
        """Integrate gases and any externally prescribed RF_* forcing components.

        Input gas columns: ppmCO2, ppbCH4, etc. (emissions if
        self.flagEmissions, concentrations otherwise).
        Input external forcing columns: RF_aerosol, RF_volcanic, ... [W/m2].

        The linear climate model is run separately for each forcing component;
        summing these responses gives the total temperature and ocean state.
        """
        emissions = self.emissions
        species_units = {
            c[3:]: c[:3]
            for c in emissions.columns
            if c.startswith(('ppm', 'ppb', 'ppt'))
        }
        species = list(species_units.keys())
        units = list(species_units.values())
        NS = len(species)

        # Other forcings can be supplied simply by adding RF_* columns.
        external_cols = [c for c in emissions.columns if c.startswith('RF_')]
        external_names = [c[3:] for c in external_cols]
        overlap = set(species) & set(external_names)
        if overlap:
            raise ValueError(f'External RF names collide with gas species: {sorted(overlap)}')
        component_names = species + external_names
        NC = len(component_names)
        if NC == 0:
            raise ValueError('No gas or externally prescribed forcing columns found.')

        startTime = emissions.index.min()
        endTime = emissions.index.max()
        tvec = np.arange(startTime, endTime + dt / 2, dt)
        NT = len(tvec)
        tvecE = emissions.index.values

        Catm = np.full((NT, NS), np.nan)
        Et = np.full((NT, NS), np.nan)
        RFs = np.full((NT, NS), np.nan)

        # Build common time-by-component forcing array.
        forcing_components = np.zeros((NT, NC))
        for k, col in enumerate(external_cols):
            values = emissions[col].to_numpy(dtype=float)
            if not np.isfinite(values).all():
                raise ValueError(f'External forcing column {col!r} contains NaNs or infs.')
            forcing_components[:, NS + k] = np.interp(tvec, tvecE, values)

        # Separate temperature and four-layer ocean response for each agent.
        gmst_components = np.zeros((NT, NC))
        oceantemps_components = np.zeros((NT, NC, 4))
        gmst = np.zeros(NT)
        oceantemps = np.zeros((NT, 4))

        # Initial concentrations and forcing for emitted gases.
        for j, s in enumerate(species):
            if s == 'CO2':
                Catm[0, j] = CO2_PI
                RFs[0, j] = 0.0
                cpool = np.zeros((1, 4))
            else:
                Catm[0, j] = SPECIES[s]['C_PI']
                RFs[0, j] = 0.0

        if self.flagEmissions:
            Et = np.zeros((NT, NS))
            # Emission rates are held piecewise constant between years.
            interval_indices = np.searchsorted(tvecE, tvec, side='right') - 1
            for j, s in enumerate(species):
                col = f'{units[j]}{s}'
                values = emissions[col].to_numpy(dtype=float)
                if not np.isfinite(values).all():
                    raise ValueError(f'Gas emissions column {col!r} contains NaNs or infs.')
                Et[:, j] = np.where(interval_indices >= 0,
                                    values[np.maximum(interval_indices, 0)], 0.0)

        # Preserve the existing special handling of emission pulses.
        if self.name == 'pulseCO2':
            Et = np.zeros((NT, 1))
            j = species.index('CO2')
            cpool = self._carbonCycle(cpool, emissions[f'{units[j]}CO2'].iloc[0], 1)
            Catm[0, j] = CO2_PI + np.sum(cpool)
            RFs[0, j] = self._radiativeForcingCO2(Catm[0, j])
        elif self.name.startswith('pulse'):
            Et = np.zeros((NT, 1))
            s = species[0]
            Catm[0, 0] = SPECIES[s]['C_PI'] + emissions.iloc[0][f'{SPECIES[s]["units"]}{s}']
            C0 = SPECIES[s]['C_PI']
            RFs[0, 0] = self._gasRadiativeForcing(
                SPECIES[s]['f1'], SPECIES[s]['f2'], SPECIES[s]['f3'], Catm[0, 0], C0
            )

        # Initial gas forcing (external forcing is already populated).
        forcing_components[0, :NS] = RFs[0, :]

        for idx in range(1, NT):
            currtime = tvec[idx - 1]
            for j, s in enumerate(species):
                if s == 'CO2':
                    if self.flagEmissions:
                        cpool = self._carbonCycle(cpool, Et[idx - 1, j], dt)
                        Catm[idx, j] = CO2_PI + np.sum(cpool)
                    else:
                        source_idx = np.searchsorted(tvecE, currtime, side='right') - 1
                        Catm[idx, j] = emissions.iloc[source_idx][f'{units[j]}{s}']
                    # Retain existing one-step lag in the forcing calculation.
                    RFs[idx, j] = self._radiativeForcingCO2(Catm[idx - 1, j])
                else:
                    C0 = SPECIES[s]['C_PI']
                    if self.flagEmissions:
                        Catm[idx, j] = C0 + self._gasCycle(
                            Catm[idx - 1, j] - C0,
                            tau=SPECIES[s]['tau'], Et=Et[idx - 1, j], dt=dt
                        )
                    else:
                        source_idx = np.searchsorted(tvecE, currtime, side='right') - 1
                        Catm[idx, j] = emissions.iloc[source_idx][f'{units[j]}{s}']
                    RFs[idx, j] = self._gasRadiativeForcing(
                        SPECIES[s]['f1'], SPECIES[s]['f2'], SPECIES[s]['f3'],
                        Catm[idx - 1, j], C0
                    )

            forcing_components[idx, :NS] = RFs[idx, :]

            # Integrate each forcing response separately, then sum.
            for j in range(NC):
                gmst_components[idx, j], oceantemps_components[idx, j, :] = (
                    self._climateModel(
                        forcing_components[idx - 1, j],
                        gmst_components[idx - 1, j],
                        oceantemps_components[idx - 1, j, :],
                        dt
                    )
                )
            gmst[idx] = gmst_components[idx, :].sum()
            oceantemps[idx, :] = oceantemps_components[idx, :, :].sum(axis=0)

        # Annual-index output and the native integration grid.
        indices = np.searchsorted(tvec, tvecE, side='right') - 1
        indices = np.clip(indices, 0, NT - 1)
        self.outdf = pd.DataFrame({'GMST': gmst[indices]}, index=emissions.index)
        self.outdf_tgrid = pd.DataFrame({'GMST': gmst}, index=tvec)

        for j, s in enumerate(species):
            self.outdf[f'Catm_{s}'] = Catm[indices, j]
            self.outdf[f'RF_{s}'] = RFs[indices, j]
            self.outdf_tgrid[f'Catm_{s}'] = Catm[:, j]
            self.outdf_tgrid[f'RF_{s}'] = RFs[:, j]
            if self.flagEmissions:
                convfac = 1 / SPECIES[s]['emission_conv']
                self.outdf[f'emissions_{s}'] = emissions[f'{units[j]}{s}'] * convfac
                self.outdf[f'cumulativeEmissions_{s}'] = self.outdf[f'emissions_{s}'].cumsum()
                self.outdf_tgrid[f'emissions_{s}'] = Et[:, j]
                self.outdf_tgrid[f'cumulativeEmissions_{s}'] = np.cumsum(Et[:, j]) * dt

        for j, component in enumerate(component_names):
            # Gas RF_* output was already saved above; external RF_* output is new.
            if j >= NS:
                self.outdf[f'RF_{component}'] = forcing_components[indices, j]
                self.outdf_tgrid[f'RF_{component}'] = forcing_components[:, j]
            self.outdf[f'GMST_{component}'] = gmst_components[indices, j]
            self.outdf_tgrid[f'GMST_{component}'] = gmst_components[:, j]

        self.outdf['RF_total'] = forcing_components[indices, :].sum(axis=1)
        self.outdf_tgrid['RF_total'] = forcing_components.sum(axis=1)

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
    
    def patternScalingSpatial( self, year, variable, exp='ssp126-ssp245-ssp370-ssp585', member='MAVG', model='MPI-ESM1-2-LR', grid='r180x90', monthlab='AnnualAverages' ):
        """Estimate spatial climate anomalies using linear pattern scaling."""

        filename = self._get_datafile(
            f'patternScaling/{model}/'
            f'PatternScalingCoefficients_{variable}_{exp}_{member}_{grid}_{monthlab}.nc'
        )

        with xr.open_dataset(filename) as ds:
            pscoef = ds['slope'].load()

        global_tas = self.outdf['GMST'].loc[year]
        return pscoef * global_tas        
        
    def patternScalingTemporal( self, location, variable, exp='ssp126-ssp245-ssp370-ssp585', member='MAVG', model='MPI-ESM1-2-LR', grid='r180x90', monthlab='AnnualAverages' ):
        """
        Calculate a time series of local climate anomalies using pattern scaling.

        Parameters
        ----------
        location : tuple
            (latitude, longitude) in degrees.
        variable : str
            Climate variable (e.g., 'tas', 'pr').

        Returns
        -------
        pd.Series
            Local climate anomaly indexed by year.
        """

        lat, lon = location

        # Load pattern-scaling coefficients
        coeff_file = self._get_datafile(
            f'patternScaling/{model}/'
            f'PatternScalingCoefficients_{variable}_{exp}_{member}_{grid}_{monthlab}.nc'
        )

        with xr.open_dataset(coeff_file) as ds:

            pscoef = ds['slope']

            # Adjust longitude to match the dataset convention
            if ds['lon'].min().item() >= 0:
                lon = lon % 360
            else:
                lon = (lon + 180) % 360 - 180

            # Select nearest grid cell
            slope = pscoef.sel(
                lat=lat,
                lon=lon,
                method='nearest'
            ).item()

        # Apply pattern scaling to entire GMST time series
        local_ts = self.outdf['GMST'] * slope

        local_ts.name = f'{variable}_local'

        return local_ts        

    
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