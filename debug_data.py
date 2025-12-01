from src.data_loader import fetch_stock_data
import pandas as pd

print("Fetching data for 7203.T...")
data = fetch_stock_data(['7203.T'], period="2y")

if not data:
    print("No data returned.")
else:
    df = data.get('7203.T')
    if df is None or df.empty:
        print("Dataframe is empty.")
    else:
        print(f"Data fetched successfully. Rows: {len(df)}")
        print(df.head())
        print(df.tail())
