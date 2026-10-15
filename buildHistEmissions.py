# kranke - October 2026

# Export global multi-gas RCMIP emissions (1750–2025) to a single CSV.

# Data: RCMIP Phase 1/2 v5.1.0 (https://www.rcmip.org/home).
# 1750–2014: RCMIP historical; 2015–2025: SSP2-4.5 extension, NOT observed history.
# Emissions are physical mass per year, not CO2-equivalent.

from   io import BytesIO
from   pathlib import Path
import pandas as pd
import requests

URL = ('https://rcmip-protocols-au.s3-ap-southeast-2.amazonaws.com/'
       'v5.1.0/rcmip-emissions-annual-means-v5-1-0.csv')
RAW = Path('rcmip-emissions-annual-means-v5-1-0.csv')
OUT = Path('global_emissions_1750_2025_by_species.csv')
SSP = 'ssp245'  # clearly labeled scenario extension, not historical observations
YEARS = range(1750, 2101)
VARIABLES = {
    'CO2_FFI': 'Emissions|CO2|MAGICC Fossil and Industrial',
    'CO2_AFOLU': 'Emissions|CO2|MAGICC AFOLU',
    'CH4': 'Emissions|CH4',
    'N2O': 'Emissions|N2O',
    'SF6': 'Emissions|F-Gases|SF6',
    'HFC134a': 'Emissions|F-Gases|HFC|HFC134a',
}
# Require explicit units; prevents accidental mixing of mass and CO2-equivalent.
TARGET_UNITS = {
    'CO2_FFI': 'Mt CO2/yr',
    'CO2_AFOLU': 'Mt CO2/yr',
    'CH4': 'Mt CH4/yr',
    'N2O': 'kt N2O/yr',
    'SF6': 'kt SF6/yr',
    'HFC134a': 'kt HFC134a/yr',
}

def get_source():
    if not RAW.exists():
        print('Downloading RCMIP emissions (~48 MB)...')
        with requests.get(URL, stream=True, timeout=180) as r:
            r.raise_for_status()
            with RAW.open('wb') as f:
                for block in r.iter_content(1024 * 1024):
                    if block:
                        f.write(block)
    return pd.read_csv(RAW, low_memory=False)

def extract(df, variable, scenario, years, target_unit):
    mask = ((df['Region'].astype(str).str.casefold() == 'world') &
            (df['Scenario'].astype(str).str.casefold() == scenario.casefold()) &
            (df['Variable'].astype(str) == variable))
    selection = df.loc[mask]
    if selection.empty:
        raise ValueError(f'Missing: scenario={scenario}, variable={variable}. '
                         f'Available variables mentioning this gas: '
                         f'{df.loc[df.Variable.str.contains(variable.split("|")[-1], case=False, regex=False, na=False), "Variable"].unique().tolist()[:15]}')
    units = selection['Unit'].dropna().unique().tolist()
    if len(units) != 1:
        raise ValueError(f'Unexpected units for {variable} {scenario}: {units}')
    # RCMIP uses carbon-mass and nitrogen-mass units for some species.
    # Convert the chemical mass basis as well as mass prefix.
    def parse_unit(value):
        import re
        norm = re.sub(r"\s+", "", value).replace("a-1", "/yr").replace("yr-1", "/yr").replace("/a", "/yr")
        match = re.fullmatch(r"(Gt|Mt|kt|t)(CO2|C|CH4|N2O|N2ON|SF6|HFC134a)/yr", norm, flags=re.IGNORECASE)
        if not match:
            raise ValueError(f"Unsupported emissions unit {value!r}; please inspect source")
        return match.group(1).lower(), match.group(2).upper()

    src_prefix, src_species = parse_unit(units[0])
    dst_prefix, dst_species = parse_unit(target_unit)
    prefix_tonnes = {'gt': 1e9, 'mt': 1e6, 'kt': 1e3, 't': 1}
    conversion = {
        ('C', 'CO2'): 44 / 12,
        ('N2ON', 'N2O'): 44 / 28,
    }
    if src_species == dst_species:
        basis_factor = 1.0
    elif (src_species, dst_species) in conversion:
        basis_factor = conversion[(src_species, dst_species)]
    else:
        raise ValueError(f"Incompatible species basis: {units[0]!r} -> {target_unit!r}")
    scale = prefix_tonnes[src_prefix] / prefix_tonnes[dst_prefix] * basis_factor
    # Rows may differ by model/version; only aggregate if source has exactly one row.
    if len(selection) != 1:
        raise ValueError(f'Expected one World/{scenario}/{variable} row, found {len(selection)}; '
                         f'Models: {selection.Model.tolist()}')
    row = selection.iloc[0]
    missing_years = [str(y) for y in years if str(y) not in df.columns]
    if missing_years:
        raise ValueError(f'Year columns missing from source: {missing_years[:10]}')
    vals = pd.to_numeric(row[[str(y) for y in years]], errors='coerce') * scale
    vals.index = [int(y) for y in vals.index]
    return vals.astype(float)

def main():
    df = get_source()
    df.columns = df.columns.str.strip()
    print('Input fields:', list(df.columns[:12]))
    out = pd.DataFrame(index=pd.Index(YEARS, name='year'))
    for name, variable in VARIABLES.items():
        out[name] = pd.concat([
            extract(df, variable, 'historical', range(1750, 2015), TARGET_UNITS[name]),
            extract(df, variable, SSP, range(2015, 2101), TARGET_UNITS[name]),
        ]).reindex(out.index)
    out.insert(2, 'CO2_total', out['CO2_FFI'] + out['CO2_AFOLU'])
    out['data_period'] = ['RCMIP_historical' if y <= 2014 else 'SSP2-4.5_scenario' for y in out.index]
    if out[list(VARIABLES)].isna().any().any():
        gaps = out[list(VARIABLES)].isna().sum()
        print('WARNING: missing values (left blank, not zero-filled):', gaps[gaps > 0].to_dict())
        
        
    # Interpolate missing annual emissions
    cols = list(VARIABLES.keys())

    out[cols] = out[cols].interpolate(
        method='index',
        limit_area='inside'
    )

    # Recompute total CO2
    out['CO2_total'] = out['CO2_FFI'] + out['CO2_AFOLU']
    
    out.to_csv(OUT, float_format='%.10g')
    print(f'Saved {OUT.resolve()}')
    print('Units:', TARGET_UNITS, '; CO2_total: Mt CO2/yr')
    print(out.loc[[1750, 2014, 2015, 2025]].to_string())

if __name__ == '__main__':
    main()
