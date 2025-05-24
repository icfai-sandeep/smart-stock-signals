from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yfinance as yf
import pandas as pd
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StockRequest(BaseModel):
    symbol: str

@app.get("/recommendations")
def get_recommendations():
    stocks = ["INFY", "TCS", "RELIANCE", "HDFCBANK", "ICICIBANK"]
    results = []

    for symbol in stocks:
        try:
            df = yf.download(symbol + ".NS", period="6mo", interval="1d")
            df.dropna(inplace=True)
            if len(df) < 50:
                continue

            df["EMA20"] = EMAIndicator(df["Close"], window=20).ema_indicator()
            df["EMA50"] = EMAIndicator(df["Close"], window=50).ema_indicator()
            df["MACD"] = MACD(df["Close"]).macd_diff()
            df["RSI"] = RSIIndicator(df["Close"]).rsi()

            latest = df.iloc[-1]
            trend = ""
            if latest["EMA20"] > latest["EMA50"] and latest["MACD"] > 0 and latest["RSI"] > 55:
                trend = "📈 Uptrend (Swing)"
            elif latest["EMA20"] < latest["EMA50"] and latest["MACD"] < 0 and latest["RSI"] < 45:
                trend = "📉 Downtrend (Avoid)"
            else:
                trend = "⚖️ Sideways/Wait"

            results.append(f"{symbol}: {trend} | CMP ₹{latest['Close']:.2f} | RSI {latest['RSI']:.1f}")
        except Exception as e:
            results.append(f"{symbol}: Error - {str(e)}")

    return {"recommendations": results}
