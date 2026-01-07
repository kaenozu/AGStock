import pandas as pd
import yfinance as yf

# 対象銘柄（ログから）
tickers = ["7203.T", "9984.T", "6758.T", "8035.T", "9983.T", "4063.T", "9432.T", "7974.T", "8306.T", "8316.T"]

prices = []
for ticker in tickers:
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d")
        if not hist.empty:
            price = hist["Close"].iloc[-1]
            prices.append({"ticker": ticker, "price": price, "min_investment": price * 100})
    except:
        pass

df = pd.DataFrame(prices)
df = df.sort_values("price")
print(df.to_string(index=False))
print(f'\n最安値: {df["price"].min():.0f}円')
print(f'最安銘柄の最小投資額（100株）: {df["min_investment"].min():.0f}円')
print(f'平均株価: {df["price"].mean():.0f}円')
print(f'平均最小投資額（100株）: {df["min_investment"].mean():.0f}円')
