### https://dbsk-web.herokuapp.com

from flask import Flask
import yfinance as yf
import pandas as pd

app = Flask(__name__) ###__name__ 代表目前執行的模組

@app.route("/") 
def index():
    return "<h1>Hello Flask</h1>"




@app.route("/info") 
###http://127.0.0.1:5000/test
def info():
    stkID = "PLTR"
    stk = yf.Ticker("PLTR")
    data = stk.info
    return data


@app.route("/pltr")
def yf_test():
    stkID = "PLTR"
    stk = yf.Ticker("PLTR")
    data = stk.history(period = "Max")

    return f'<h1>{stkID}<h1>\n{data.head().to_html()}'


if __name__ == "__main__": ###如果以主程式執行
    app.run()  ###立即啟動伺服器
