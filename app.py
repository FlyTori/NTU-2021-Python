### https://dbsk-web.herokuapp.com

from flask import Flask, app, request, render_template, session
import yfinance as yf
import json   #載入json
import pandas as pd
import requests #如果最後沒有使用alpha vantage可刪除
from datetime import datetime

#建立Application物件，設定靜態檔案的路徑處理
app = Flask(__name__, static_folder="static", static_url_path="/")


def getCompanyPrice(company, start_time, end_time):
    # 使用yfinance抓取公司股價。由於一家公司與多家公司回傳格式不同，為了後續處理方便，統一單次只抓取單家公司
    data = yf.download(company, start=start_time, end=end_time)

    #原始資料有很多欄位，抓取Adj Close欄位，並從Pandas Series格式轉成list
    company_adj_close = data["Adj Close"].tolist() 
    return company_adj_close

# 利用datetime套件計算相差天數，計算IRR用
def daysCount(start_time, end_time):
    start = datetime.strptime(start_time, "%Y-%m-%d")
    end = datetime.strptime(end_time, "%Y-%m-%d")
    diff = end.date() - start.date()
    return(diff.days)

# 使用 GET 方法處理路徑 / 的對應函式
@app.route("/")  #路徑為/
def index():
    return render_template("index.html")  #連到index.html








# @app.route("/") 
# def index():
#     return "<h1>Hello Flask</h1>"


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
