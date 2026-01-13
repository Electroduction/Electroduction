
import pandas as pd

# Download list of FRED series
indicators = {
    'GDP': 'Gross Domestic Product',
    'UNRATE': 'Unemployment Rate',
    'CPIAUCSL': 'Consumer Price Index',
    'FEDFUNDS': 'Federal Funds Rate'
}

# Save indicator list
pd.DataFrame(list(indicators.items()), columns=['Code', 'Description']).to_csv('data/finance/fred_indicators.csv', index=False)
print('FRED indicator list created')
