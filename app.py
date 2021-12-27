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


# 使用 POST 方法接收表單
@app.route("/result", methods=["GET", "POST"])
def calculate():
    total_start_value = int(request.form["start-value"])
    start_time = request.form["start-date"]
    end_time = request.form["end-date"]
    company1 = request.form["ticker1"]
    company1_portion = request.form["ticker1-portion"]
    company2 = request.form["ticker2"]
    company2_portion = request.form["ticker2-portion"]
    company3 = request.form["ticker3"]
    company3_portion = request.form["ticker3-portion"]
    
    # 建立公司與投資比例列表
    companies_input = [company1, company2, company3]
    portion_input = [company1_portion, company2_portion, company3_portion]
    companies = [i for i in companies_input if i!= ""]
    portion = [int(i)/100 for i in portion_input if i!= ""]
    invest_start_lst = [ i * total_start_value for i in portion] #個股投資金額，例：[20, 50, 30]
    # list = [i for i in AlphaVantage(companies[0])[0]]

    # 測試用靜態資料
    # companies = ["AAPL", "GOOG"]
    # start_time = "2021-01-01"
    # end_time = "2021-12-15"
    # total_start_value = 100
    # portion = [0.5, 0.5]

    companies_result = []
    total_end_value = 0
    for i in range(len(companies)):
        company_adj_close = getCompanyPrice(companies[i], start_time, end_time)  #呼叫函式，取得list形式的區間股價資料
        return_percentage = (company_adj_close[-1] - company_adj_close[0]) / company_adj_close[0]  #個股報酬率
        start_value = invest_start_lst[i]   #個股初值
        end_value = invest_start_lst[i] * (1 + return_percentage)   #個股終值
        IRR = ((end_value/start_value)**(365/daysCount(start_time, end_time))-1)*100  #計算IRR
        
        # 建立單家公司字典，儲存單家公司內的所有回傳前端的資料
        company = {
            "company_name": companies[i],
            "start_price": round(company_adj_close[0],2),  #起始股價
            "end_price": round(company_adj_close[-1],2),   #最終股價
            "change": round(return_percentage*100,2),      #乘上100轉成百分比
            "start_value": round(start_value,2),
            "end_value": round(end_value,2),
            "IRR": round(IRR,2)
        }
        companies_result.append(company) #將個別公司資料加回最終的list
        total_end_value += company["end_value"]
        total_IRR = ((total_end_value/total_start_value)**(365/daysCount(start_time, end_time))-1)*100

    # 回傳前端的資料
    kwargs = {
    "start_time": start_time,
    "end_time": end_time,
    "total_start_value": total_start_value,
    "companies": companies,
    "total_end_value": total_end_value,
    "portion": portion,
    "total_change": round((total_end_value - total_start_value)/total_start_value * 100, 2),
    "total_IRR": round(total_IRR, 2)
    }

    # 開啟計算結果畫面
    return render_template("result.html", companies_result=companies_result, **kwargs) 

if __name__ == "__main__": ###如果以主程式執行
    app.run()  ###立即啟動伺服器
