# kranke - October 2026
# #Download and combine global temperature, CO2, CH4 for 1750–2025.

#Global temperature: HadCRUT5 analysis (1850 onward), annual; rebased to 1850–1900.
#CO2/CH4: Our World in Data compilations, based on ice cores and NOAA.
#Sparse early concentration estimates are linearly interpolated to annual resolution.
#Missing temperature before 1850 is deliberately retained as NaN.

from io import StringIO
from pathlib import Path
import pandas as pd
import requests

START, END = 1750, 2025
OUT = Path('observed_climate_1750_2025.csv')
CACHE = Path('data')

URLS = {
    'temperature': (
        'https://www.metoffice.gov.uk/hadobs/hadcrut5/data/'
        'HadCRUT.5.2.0.0/analysis/diagnostics/'
        'HadCRUT.5.2.0.0.analysis.summary_series.global.annual.csv'
    ),
    'co2': 'https://ourworldindata.org/grapher/co2-long-term-concentration.csv?v=1&csvType=full&useColumnShortNames=false',
    'ch4': 'https://ourworldindata.org/grapher/long-run-methane-concentration.csv?v=1&csvType=full&useColumnShortNames=false',
}


def read_cached_csv(key):
    CACHE.mkdir(parents=True, exist_ok=True)
    dest = CACHE / f'{key}_source.csv'
    if not dest.exists():
        print(f'Downloading {key}...')
        response = requests.get(URLS[key], timeout=90,
                                headers={'User-Agent': 'ClimateDataResearch/1.0 (pandas requests)'})
        response.raise_for_status()
        # Cache atomically; do not leave truncated source files behind.
        tmp = dest.with_suffix('.tmp')
        tmp.write_bytes(response.content)
        tmp.replace(dest)
    return pd.read_csv(dest)


def load_hadcrut():
    df = read_cached_csv('temperature')
    df.columns = df.columns.astype(str).str.strip()
    year_col = next((c for c in df if c.lower() in ('time', 'year')), None)
    if year_col is None:
        raise ValueError(f'Unexpected HadCRUT year column: {df.columns.tolist()}')
    # Prefer published ensemble mean, not uncertainty bounds.
    temp_col = next((c for c in df if c.lower() == 'anomaly (deg c)'), None)
    if temp_col is None:
        temp_col = next((c for c in df if 'anomaly' in c.lower()
                         and not any(s in c.lower() for s in ('lower', 'upper', 'uncertainty'))), None)
    if temp_col is None:
        raise ValueError(f'Unexpected HadCRUT temperature columns: {df.columns.tolist()}')
    years = pd.to_numeric(df[year_col], errors='coerce')
    vals = pd.to_numeric(df[temp_col], errors='coerce')
    annual = pd.Series(vals.to_numpy(), index=years, dtype=float).dropna()
    annual = annual.loc[~annual.index.isna()]
    annual.index = annual.index.astype(int)
    annual = annual[~annual.index.duplicated(keep='last')].sort_index()
    # HadCRUT5 reference is 1961–1990; change to 1850–1900.
    baseline = annual.loc[1850:1900].mean()
    if pd.isna(baseline):
        raise ValueError('HadCRUT temperature baseline 1850–1900 unavailable')
    return (annual - baseline).rename('GMST_obs_C')


def load_owid(key, output_name):
    df = read_cached_csv(key)
    df.columns = df.columns.astype(str).str.strip()
    if 'Year' not in df.columns:
        raise ValueError(f'Unexpected {key} columns: {df.columns.tolist()}')
    # These OWID grapher datasets generally have one global entity. If more,
    # prefer World to avoid inadvertently selecting a regional series.
    if 'Entity' in df.columns and df['Entity'].nunique() > 1:
        world = df['Entity'].astype(str).str.lower().eq('world')
        if not world.any():
            raise ValueError(f'{key} has multiple entities but none named World: '
                             f'{df.Entity.unique()[:12]}')
        df = df.loc[world]
    values = [c for c in df.columns if c not in ('Entity', 'Code', 'Year')]
    if len(values) != 1:
        raise ValueError(f'Cannot uniquely select {key} concentration: {values}')
    df = df[['Year', values[0]]].copy()
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    df[values[0]] = pd.to_numeric(df[values[0]], errors='coerce')
    df = df.dropna().query('@START <= Year <= @END')
    df['Year'] = df['Year'].astype(int)
    s = df.drop_duplicates('Year', keep='last').set_index('Year')[values[0]].sort_index()
    # Early ice-core data may be spaced apart; interpolate only between measured
    # or reconstructed points, never beyond the first/last actual source year.
    full = s.reindex(range(START, END + 1)).interpolate(method='index', limit_area='inside')
    print(f'{output_name}: original source points {len(s)}, '
          f'coverage {int(s.index.min())}–{int(s.index.max())}')
    return full.rename(output_name)


def main():
    df = pd.DataFrame(index=pd.Index(range(START, END + 1), name='year'))
    df = df.join(load_hadcrut())
    df = df.join(load_owid('co2', 'CO2_obs_ppm'))
    df = df.join(load_owid('ch4', 'CH4_obs_ppb'))
    df.to_csv(OUT, float_format='%.6f')
    print(f'\nSaved {OUT.resolve()}')
    print('Non-missing years:\n', df.notna().sum().to_string())
    print('\nSelected years:\n', df.reindex([1750, 1850, 1900, 1950, 2000, 2015, 2025]))
    print('\nNOTE: pre-1850 global temperature is unavailable, not zero.')
    print('NOTE: early CO2/CH4 gaps are linearly interpolated ice-core estimates.')


if __name__ == '__main__':
    main()
