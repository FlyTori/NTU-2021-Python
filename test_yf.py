import yfinance as yf
import pandas as pd

stkID = yf.Ticker("PLTR")
data = stkID.info

print(data)

