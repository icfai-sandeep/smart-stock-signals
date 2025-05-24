from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import yfinance as yf
import pandas as pd
from ta.trend import macd
from ta.momentum import rsi
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# NSE sample symbols for demo
NSE_STOCKS = ["INFY.NS", "TCS.NS", "RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "LT.NS", "SBIN.NS", "HCLTECH.NS"]

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/stock/{symbol}", response_class=HTMLResponse)
async def stock_details(request: Request, symbol: str):
    stock = yf.Ticker(symbol)
    hist = stock.history(period="6mo")
    
    if hist.empty:
        return templates.TemplateResponse("result.html", {"request": request, "symbol": symbol, "message": "Stock data not found", "signal": "N/A", "price": "-", "target": "-", "stop_loss": "-"})
    
    hist['RSI'] = rsi(hist['Close'], window=14)
    macd_val = macd(hist['Close'])

    # Signal logic
    rsi_now = hist['RSI'].iloc[-1]
    macd_diff = macd_val.macd_diff().iloc[-1]
    price = hist['Close'].iloc[-1]

    if rsi_now < 30 and macd_diff > 0:
        signal = "BUY"
        target = price * 1.08
        stop_loss = price * 0.95
    elif rsi_now > 70 and macd_diff < 0:
        signal = "SELL"
        target = price * 0.92
        stop_loss = price * 1.05
    else:
        signal = "HOLD"
        target = "-"
        stop_loss = "-"

    return templates.TemplateResponse("result.html", {
        "request": request,
        "symbol": symbol,
        "message": "Analysis complete",
        "signal": signal,
        "price": f"{price:.2f}",
        "target": f"{target:.2f}" if target != "-" else "-",
        "stop_loss": f"{stop_loss:.2f}" if stop_loss != "-" else "-"
    })


def scan_swing_picks():
    picks = []
    for symbol in NSE_STOCKS:
        stock = yf.Ticker(symbol)
        hist = stock.history(period="6mo")
        if hist.empty:
            continue

        hist['RSI'] = rsi(hist['Close'], window=14)
        macd_val = macd(hist['Close'])
        macd_diff = macd_val.macd_diff().iloc[-1]
        rsi_now = hist['RSI'].iloc[-1]
        price = hist['Close'].iloc[-1]

        if rsi_now < 35 and macd_diff > 0:
            picks.append({
                "symbol": symbol,
                "type": "Swing",
                "price": f"{price:.2f}",
                "signal": "BUY"
            })
    return picks


def scan_longterm_picks():
    picks = []
    for symbol in NSE_STOCKS:
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            roe = info.get("returnOnEquity", 0)
            pe = info.get("trailingPE", 0)
            debt = info.get("debtToEquity", 0)
            price = info.get("currentPrice", 0)

            if roe and pe and debt:
                if roe > 0.15 and pe < 25 and debt < 100:
                    picks.append({
                        "symbol": symbol,
                        "type": "Long-Term",
                        "price": f"{price:.2f}",
                        "signal": "BUY"
                    })
        except:
            continue
    return picks

@app.get("/swing-picks", response_class=HTMLResponse)
async def swing(request: Request):
    picks = scan_swing_picks()
    return templates.TemplateResponse("result.html", {"request": request, "symbol": "Swing Picks", "message": "Swing Trade Stocks", "stock_list": picks})

@app.get("/longterm-picks", response_class=HTMLResponse)
async def longterm(request: Request):
    picks = scan_longterm_picks()
    return templates.TemplateResponse("result.html", {"request": request, "symbol": "Long Term Picks", "message": "Best Long Term Stocks", "stock_list": picks})
