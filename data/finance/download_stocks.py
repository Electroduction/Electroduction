
import yfinance as yf
import pandas as pd

# Download S&P 500 tickers
sp500_url = 'https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv'
tickers_df = pd.read_csv(sp500_url)

# Download sample data (top 50 to save time/space)
for ticker in tickers_df['Symbol'][:50]:
    try:
        data = yf.download(ticker, start='2020-01-01', end='2024-01-01')
        data.to_csv('data/finance/stocks/{ticker}.csv')
        print(f'Downloaded {ticker}')
    except Exception as e:
        print(f'Failed {ticker}: {e}')
