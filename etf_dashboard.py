import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# List of ETFs to backtest
etfs = ['SPY', 'QQQ', 'VTI', 'IWM', 'XLK', 'XLF', 'XLV', 'XLE']

# Settings
start_date = '2010-01-01'
end_date = datetime.today().strftime('%Y-%m-%d')
holding_period_months = 14
drop_threshold = 0.30
initial_capital = 50000

# RSI Calculation
def compute_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    data['RSI'] = rsi
    return data

# Backtest results storage
results = []

for symbol in etfs:
    df = yf.download(symbol, start=start_date, end=end_date)
    df = compute_rsi(df)
    df['52w_high'] = df['Close'].rolling(window=252).max()
    df['drop_from_high'] = (df['Close'] - df['52w_high']) / df['52w_high']

    for i in range(len(df)):
        row = df.iloc[i]
        if row['drop_from_high'] <= -drop_threshold and row['RSI'] < 30:
            entry_date = row.name
            exit_date = entry_date + pd.DateOffset(months=holding_period_months)
            
            if exit_date in df.index:
                entry_price = row['Close']
                exit_price = df.loc[exit_date]['Close']
                
                shares = initial_capital / entry_price
                final_value = shares * exit_price
                profit = final_value - initial_capital
                
                results.append({
                    'ETF': symbol,
                    'Buy Date': entry_date,
                    'Sell Date': exit_date,
                    'Buy Price': entry_price,
                    'Sell Price': exit_price,
                    'Profit': profit,
                    'ROI %': (profit / initial_capital) * 100
                })

# Convert results to DataFrame
results_df = pd.DataFrame(results)

# Show summary
print("\n--- Strategy Summary ---")
print(results_df.groupby('ETF')[['Profit', 'ROI %']].mean())
print("\nTotal Trades:", len(results_df))

# Plot ROI per trade
plt.figure(figsize=(10,6))
plt.hist(results_df['ROI %'], bins=20, edgecolor='black')
plt.title('Distribution of ROI per Trade')
plt.xlabel('ROI %')
plt.ylabel('Frequency')
plt.grid(True)
plt.show()
