# -*- coding: utf-8 -*-
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go

# Title
st.title("📉 AI-Powered ETF Dip Buying Dashboard")

# Sidebar
st.sidebar.header("Settings")
etfs = st.sidebar.multiselect(
    "Select ETFs",
    ['SPY', 'QQQ', 'VTI', 'IWM', 'XLK', 'XLF', 'XLV', 'XLE'],
    default=['SPY', 'QQQ']
)
drop_threshold = st.sidebar.slider("Drop from 52-Week High (%)", 10, 70, 30)
rsi_threshold = st.sidebar.slider("RSI Threshold (Buy < X)", 10, 50, 30)
holding_months = st.sidebar.slider("Holding Period (Months)", 6, 24, 14)
initial_capital = st.sidebar.number_input("Starting Capital ($)", value=50000)

# Function to calculate RSI
def compute_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Main
st.markdown("### 🧠 Smart ETF Picks Based on Your Strategy")

results = []

for symbol in etfs:
    df = yf.download(symbol, start='2010-01-01')

    # ✅ Skip if df is empty or missing critical columns
    if df.empty or 'Close' not in df.columns or len(df) < 252:
        st.warning(f"Skipping {symbol}: Not enough data or missing 'Close' prices.")
        continue

    # ✅ Copy to avoid warnings
    df = df.copy()
    df['52w_high'] = df['Close'].rolling(window=252).max()

    # ✅ Clean bad values
    df = df[df['52w_high'] != 0]
    df.dropna(subset=['Close', '52w_high'], inplace=True)

    df['drop_from_high'] = (df['Close'] - df['52w_high']) / df['52w_high']
    df['RSI'] = compute_rsi(df)
    df.dropna(inplace=True)

    for i in range(len(df)):
        row = df.iloc[i]
        if row['drop_from_high'] <= -drop_threshold / 100 and row['RSI'] < rsi_threshold:
            entry_date = row.name
            exit_date = entry_date + pd.DateOffset(months=holding_months)
            if exit_date in df.index:
                entry_price = row['Close']
                exit_price = df.loc[exit_date]['Close']
                shares = initial_capital / entry_price
                final_value = shares * exit_price
                profit = final_value - initial_capital

                results.append({
                    'ETF': symbol,
                    'Buy Date': entry_date.date(),
                    'Sell Date': exit_date.date(),
                    'Buy Price': round(entry_price, 2),
                    'Sell Price': round(exit_price, 2),
                    'Profit ($)': round(profit, 2),
                    'ROI (%)': round((profit / initial_capital) * 100, 2)
                })

if results:
    results_df = pd.DataFrame(results)
    st.success(f"Found {len(results_df)} qualifying trades.")
    st.dataframe(results_df)

    avg_roi = results_df['ROI (%)'].mean()
    total_profit = results_df['Profit ($)'].sum()
    st.metric("Average ROI per Trade (%)", f"{avg_roi:.2f}%")
    st.metric("Total Profit ($)", f"${total_profit:,.2f}")

    # Plot ROI distribution
    fig = go.Figure(data=[go.Histogram(x=results_df['ROI (%)'], nbinsx=20)])
    fig.update_layout(title='ROI % Distribution', xaxis_title='ROI %', yaxis_title='Frequency')
    st.plotly_chart(fig)
else:
    st.warning("No qualifying trades found for the selected criteria.")
