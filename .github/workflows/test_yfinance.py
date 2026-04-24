import yfinance as yf
tickers = ["ARADEL.LG", "ZENITHBANK.LG", "MTNN.LG", "ARADEL.NG", "MTNN"]
for t in tickers:
    df = yf.download(t, period="5d", progress=False)
    print(f"{t}: {'✅ Data' if not df.empty else '❌ Empty'}")
