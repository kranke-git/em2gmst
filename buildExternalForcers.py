# kranke - October 2026

#Download IPCC AR6/FaIR SSP2-4.5 forcing and extract annual net aerosol ERF, 1750–2100.
#Requires pandas. Output: aerosol_erf_ssp245_1750_2100.csv

from pathlib import Path
import pandas as pd

from pathlib import Path
import pandas as pd

SRC = 'ERF_ssp245_1750-2500.csv'
URL = ('https://raw.githubusercontent.com/chrisroadmap/ar6/main/'
       'data_output/SSPs/ERF_ssp245_1750-2500.csv')
OUTPUT = 'external_forcing_ssp245_1750_2100.csv'


def main():
    if Path(SRC).is_file():
        df = pd.read_csv(SRC)
        print(f'Reading local {SRC}')
    else:
        print('Downloading AR6/FaIR SSP2-4.5 ERF series...')
        df = pd.read_csv(URL)
        df.to_csv(SRC, index=False)  # cache original data

    df = df.set_index('year').sort_index()
    df.index = df.index.astype(int)
    df = df.loc[1750:2100]
    expected = pd.Index(range(1750, 2101), name='year')
    if not df.index.equals(expected):
        raise ValueError('Expected every year from 1750 through 2100 in original data')

    mapping = {
        'o3': 'RF_ozone',
        'h2o_stratospheric': 'RF_stratospheric_H2O',
        'contrails': 'RF_contrails',
        'bc_on_snow': 'RF_bc_snow',
        'land_use': 'RF_land_use',
        'volcanic': 'RF_volcanic',
        'solar': 'RF_solar',
    }
    required = [*mapping, 'aerosol-radiation_interactions',
                'aerosol-cloud_interactions']
    missing = sorted(set(required) - set(df.columns))
    if missing:
        raise ValueError(f'Missing columns from AR6 data: {missing}')

    out = df[list(mapping)].rename(columns=mapping).copy()
    out.insert(0, 'RF_aerosol',
               df['aerosol-radiation_interactions']
               + df['aerosol-cloud_interactions'])
    # Sum of only the columns meant to be ingested by climateScenario.
    external = list(out.columns)
    out['diagnostic_external_total'] = out[external].sum(axis=1)
    # Optional aerosol diagnostics; NOT additional independent forcings.
    out['diagnostic_RF_aerosol_ari'] = df['aerosol-radiation_interactions']
    out['diagnostic_RF_aerosol_aci'] = df['aerosol-cloud_interactions']
    if out.isna().any().any():
        raise ValueError('NaNs in extracted forcing data')
    out.to_csv(OUTPUT, float_format='%.10g')
    print(f'Saved {OUTPUT}: {len(out)} years, {len(out.columns)} columns')
    print(out.loc[[1750, 2019, 2050, 2100]].round(3))
    print('\nIntegration columns:', external)
    print('Do not add diagnostic_* to an input frame as forcings.')


if __name__ == '__main__':
    main()
