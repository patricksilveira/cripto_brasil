import pandas as pd
import requests
from pathlib import Path
from datetime import datetime
import streamlit as st
import sys

def fetch_usd_rates():
    """
    Fetches the Daily USD/BRL exchange rate (Series 1) from Bacen 
    and resamples it to Monthly Average.
    """
    url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.1/dados?formato=json&dataInicial=01/01/2018"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        df = pd.DataFrame(data)
        
        if df.empty:
            print("Warning: Bacen returned empty data", file=sys.stderr)
            return pd.DataFrame(columns=['data', 'rate'])

        # Bacen API returns dates as DD/MM/YYYY
        df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')
        df['valor'] = pd.to_numeric(df['valor'])
        
        # Resample to Monthly Average
        # Index by date
        df.set_index('data', inplace=True)
        # Resample to Month Start (MS) and take mean
        monthly_avg = df.resample('MS')['valor'].mean().reset_index()
        monthly_avg.rename(columns={'valor': 'rate'}, inplace=True)
        
        return monthly_avg
        
    except Exception as e:
        msg = f"Error fetching USD rates from Bacen: {e}"
        print(msg, file=sys.stderr)
        try:
            st.error(msg)
        except:
            pass
        return pd.DataFrame(columns=['data', 'rate'])

def get_usd_rates(base_path: Path):
    """
    Gets USD rates, either from cached CSV or fetching new if needed.
    """
    rates_file = base_path / "usd_brl_monthly.csv"
    
    if rates_file.exists():
        try:
            df = pd.read_csv(rates_file)
            df['data'] = pd.to_datetime(df['data'])
            return df
        except Exception as e:
            print(f"Error reading cached rates: {e}", file=sys.stderr)
            
    # Fetch
    df = fetch_usd_rates()
    if not df.empty:
        # Save locally
        df.to_csv(rates_file, index=False)
    return df

def normalize_dataframe(df, value_columns, rates_df):
    """
    Normalizes value columns in df using the rates_df.
    df must have 'data' column (datetime).
    rates_df must have 'data' column (datetime) and 'rate'.
    
    Adds 'col_usd' for each col in value_columns.
    """
    # Create copies to avoid SettingWithCopy warnings on input dfs if they are slices
    df = df.copy()
    rates_df = rates_df.copy()
    
    df['ym'] = df['data'].dt.to_period('M')
    rates_df['ym'] = rates_df['data'].dt.to_period('M')
    
    # Merge
    merged = pd.merge(df, rates_df[['ym', 'rate']], on='ym', how='left')
    
    for col in value_columns:
        if col in df.columns:
            # col_usd = col_brl / rate
            merged[f"{col}_usd"] = merged[col] / merged['rate']
            
    # Clean up
    merged = merged.drop(columns=['ym', 'rate'])
    return merged
