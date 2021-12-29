### https://dbsk-web.herokuapp.com

from flask import Flask, app, request, render_template, session
import yfinance as yf
import json   #載入json
import pandas as pd
import requests #如果最後沒有使用alpha vantage可刪除
from datetime import datetime

#建立Application物件，設定靜態檔案的路徑處理
app = Flask(__name__, static_folder="static", static_url_path="/")

# 讀取 json 檔案（公司股票代號與名稱對應）
with open('./static/cmp_data.json', 'r') as cmp_data:
    data = cmp_data.read()   
    company_name_symbol = json.loads(data)

def getCompanySymbol(user_input):   #處理大小寫，把公司名稱統一轉成代號
    user_input = user_input.upper()
    if user_input in company_name_symbol.keys():
        return company_name_symbol[user_input]
    else:
        return user_input

################## 報酬率回測 ##################

def getCompanyPrice(symbol, start_time, end_time):
    # 使用yfinance抓取公司股價。由於一家公司與多家公司回傳格式不同，為了後續處理方便，統一單次只抓取單家公司
    data = yf.download(symbol, start=start_time, end=end_time)
    if data.empty:
        return "empty"
    #原始資料有很多欄位，抓取Adj Close欄位，並從Pandas Series格式轉成list
    else:
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

# 使用 POST 方法接收報酬率回測表單
@app.route("/return", methods=["GET", "POST"])
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
    empty_symbol = []
    total_IRR = 0
    for i in range(len(companies)):
        company = getCompanySymbol(companies[i])
        company_adj_close = getCompanyPrice(company, start_time, end_time)  #呼叫函式，取得list形式的區間股價資料
        if company_adj_close == "empty":
            empty_symbol.append(company)
            continue
        return_percentage = (company_adj_close[-1] - company_adj_close[0]) / company_adj_close[0]  #個股報酬率
        start_value = invest_start_lst[i]   #個股初值
        end_value = invest_start_lst[i] * (1 + return_percentage)   #個股終值
        IRR = ((end_value/start_value)**(365/daysCount(start_time, end_time))-1)*100  #計算IRR
        
        # 建立單家公司字典，儲存單家公司內的所有回傳前端的資料
        company = {
            "company_name": company,
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
    "total_IRR": round(total_IRR, 2),
    "empty_symbol": empty_symbol,
    }

    # 開啟計算結果畫面
    return render_template("return.html", companies_result=companies_result, **kwargs) 


################## 財報評分 ##################

# 抓財報資料

empty_symbol = False
def finance_fun(symbol) :
    stock = yf.Ticker(str(symbol))
    #income_statement = stock.financials.T
    balance_sheet = stock.balance_sheet.T
    cash_flow = stock.cashflow.T
    if balance_sheet.empty:
        return "empty"
    # 存成字典格式
    else:
        finance = {"net_income_1": cash_flow["Net Income"][1],  # 2020.9.30 net income   
                    "net_income_0": cash_flow["Net Income"][0],  # 2021.9.30 net income    
                    "total_Current_Assets": balance_sheet["Total Current Assets"][0],  # 2020.12.31 total Current Assets
                    "total_Assets": balance_sheet["Total Assets"][0],  # 2020.12.31 total Assets
                    "total_Liabilities": balance_sheet["Total Liab"][0],  # 2020.12.31 total totalLiabilities
                    "total_Current_Liabilities": balance_sheet["Total Current Liabilities"][0],  # 2020.12.31 total Current Liabilities
                    "total_Shareholder_Equity": balance_sheet["Total Stockholder Equity"][0],  # 2020.12.31 total Shareholder Equity
                    "operating_Cash_flow": cash_flow["Total Cash From Operating Activities"][0],  # 2020.12.31 cash flow
                    }
        return finance

# 填寫股票代號頁面
@app.route("/stock")
def stock_input():
    return render_template("stock.html")

# 計算股票評分頁面

@app.route("/valuation")
def valuation():
    user_input = request.args.get("symbol", "")
    symbol = getCompanySymbol(user_input) #處理大小寫，把公司名稱統一轉成代號
    finance = finance_fun(symbol)

    # 分數轉換函式，將各面向數據之計算結果轉換成相應分數
    def score_transformation(x):
        if x < 0 :
            return 0
        elif x > 100 :
            return 100
        else :
            return x

    ##### 財務面分數計算
    def finance_score():    
        # 營業現金流與稅後淨利比值
        cash_netincome_rate = score_transformation(
            round((finance["operating_Cash_flow"]/finance["net_income_0"])*100,2))
        # 流動比率
        current_rate = score_transformation(
            round((finance["total_Current_Assets"]/finance["total_Current_Liabilities"])*100,2))
        # 資產負債比
        debt_to_asset_ratio = score_transformation(
            round((finance["total_Liabilities"]/finance["total_Assets"])*100,2))
        # 財務面總分
        finance_score = round(((cash_netincome_rate + current_rate + debt_to_asset_ratio)/3),2)
        return finance_score

    ##### 價值面分數計算
    def value_score():
        # 價值面總分 ROE
        value_score = score_transformation(round((finance["net_income_0"]/finance["total_Shareholder_Equity"])*100,2))
        return value_score

    ##### 成長面計算
    def growth_score():
        # 稅後淨利成長率
        netincome_growth_rate = score_transformation(
            round(((finance["net_income_0"]-finance["net_income_1"])/abs(finance["net_income_1"]))*100,2))
        # 成長面總分
        growth_score = netincome_growth_rate
        return growth_score

    ##### 最後推薦分數
    def total_score():
        total_score = round((finance_score() + value_score() + growth_score())/3,2)
        return total_score

    # 回傳前端的資料
    if finance == "empty":
        return render_template("valuation.html", empty_symbol = "True", symbol = user_input)
        # return render_template("error.html", user_input = user_input)
    else:
        kwargs = {
        "company_name": symbol,
        "total_score": total_score(),
        "growth_score": growth_score(),
        "value_score": value_score(),
        "finance_score": finance_score(),
        "finance": finance,
        }

        return render_template("valuation.html", empty_symbol = "False", **kwargs)


if __name__ == "__main__": ###如果以主程式執行
    app.run()  ###立即啟動伺服器
