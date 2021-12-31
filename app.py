### https://dbsk-web.herokuapp.com

from flask import Flask, app, request, render_template, session, url_for
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

#處理大小寫，把公司名稱統一轉成代號
def getCompanySymbol(user_input):   
    user_input = user_input.upper()
    if user_input in company_name_symbol.keys():
        return company_name_symbol[user_input]
    else:
        return user_input

################## 首頁 ##################

@app.route("/")
def index():
    return render_template("index.html")

################## 報酬率回測相關函式 ##################

# yfinance抓取單家公司指定日期股價
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

# 處理用戶輸入的表單資料
def companies_return(form):
    total_start_value = int(form["start-value"])
    start_time = form["start-date"]
    end_time = form["end-date"]
    company1 = form["ticker1"]
    company1_portion = form["ticker1-portion"]
    company2 = form["ticker2"]
    company2_portion = form["ticker2-portion"]
    company3 = form["ticker3"]
    company3_portion = form["ticker3-portion"]
    
    # 建立公司與投資比例列表
    companies_input = [company1, company2, company3]
    portion_input = [company1_portion, company2_portion, company3_portion]
    companies = [i for i in companies_input if i!= ""]    #去掉空白資料
    portion = [int(i)/100 for i in portion_input if i!= ""]   #去掉空白資料
    invest_start_lst = [ i * total_start_value for i in portion] #個股投資金額，例：[20, 50, 30]

    # 測試用靜態資料
    # companies = ["AAPL", "GOOG"]
    # start_time = "2021-01-01"
    # end_time = "2021-12-15"
    # invest_start_lst = [50, 50]
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
        
        # 建立單家公司字典，儲存單家公司內的所有資料
        company = {
            "company_name": company,
            "start_price": round(company_adj_close[0],2),  #起始股價
            "end_price": round(company_adj_close[-1],2),   #最終股價
            "change": round(return_percentage*100,2),      #乘上100轉成百分比
            "start_value": round(start_value,2),
            "end_value": round(end_value,2),
            "IRR": round(IRR,2)
        }
        companies_result.append(company) #將個別公司資料加回最終的list (函式回傳的資料一)
        total_end_value += company["end_value"]
        total_IRR = ((total_end_value/total_start_value)**(365/daysCount(start_time, end_time))-1)*100

    # 函式回傳的資料二
    result = {
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
    return companies_result, result


# 使用 GET 方法處理路徑 / 的對應函式
@app.route("/backtesting", methods=["GET", "POST"])
def backtesting():
    # companies_result, final_result = False, False
    if request.method=='POST':      #當使用者有輸入資料時，呼叫companies_return()函式並取得回測結果
        form = request.form
        data = companies_return(form)
        companies_result = data[0]  # 取得result的第一個值，格式為list，其中包含各公司的資料（字典格式）
        kwargs = data[1]  # 取得時間、報酬率、投資終值等資料（字典格式）
        return render_template("backtesting.html", companies_result=companies_result, **kwargs)
    else:
        return render_template("backtesting.html")


################## 財報評分 ##################

# 抓財報資料函式
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

# 處理大於100與小於0的分數
def score_transformation(x):   
    if x < 0 :
        return 0
    elif x > 100 :
        return 100
    else :
        return x

# 財務面分數計算
def finance_score(data): 
    cash_netincome_rate = score_transformation(   # 營業現金流與稅後淨利比值
        round((data["operating_Cash_flow"]/data["net_income_0"])*100,2))
    current_rate = score_transformation(          # 流動比率
        round((data["total_Current_Assets"]/data["total_Current_Liabilities"])*100,2))
    debt_to_asset_ratio = score_transformation(   # 資產負債比
        round((data["total_Liabilities"]/data["total_Assets"])*100,2))
    finance_score = round(((cash_netincome_rate + current_rate + debt_to_asset_ratio)/3),2)
    return finance_score

# 價值面分數計算
def value_score(data):
    value_score = score_transformation(    # 價值面總分 ROE
        round((data["net_income_0"]/data["total_Shareholder_Equity"])*100,2))
    return value_score

# 成長面分數計算
def growth_score(data):
    netincome_growth_rate = score_transformation(  # 稅後淨利成長率
        round(((data["net_income_0"]-data["net_income_1"])/abs(data["net_income_1"]))*100,2))
    growth_score = netincome_growth_rate
    return growth_score

# 最後推薦分數
def total_score(data):
    total_score = round((finance_score(data) + value_score(data) + growth_score(data))/3,2)
    return total_score


# 填寫股票代號頁面
@app.route("/stock")
def stock_valuation():
    user_input = request.args.get("symbol", "")    #判斷用戶是否有輸入/網址後面是否有字串
    if user_input == "":
        return render_template("stock.html", )     #如果沒有則開啟stock.html

    if user_input != "":   #當用戶有輸入，或網址後面有字串
        symbol = getCompanySymbol(user_input) #處理大小寫，把公司名稱統一轉成代號
        finance = finance_fun(symbol)  #呼叫finance_fun，跟yfinance拿資料

        # 回傳結果
        if finance != "empty":   #若成功從yfinance拿到資料，則回傳以下資料給前端
            kwargs = {
            "company_name": symbol,
            "total_score": total_score(finance),
            "growth_score": growth_score(finance),
            "value_score": value_score(finance),
            "finance_score": finance_score(finance),
            "finance": finance,
            }
            return render_template("stock.html", symbol_valid = True, user_input=user_input, **kwargs)

        elif finance == "empty":   #如果找不到資料，回傳symbol_valid = False
            return render_template("stock.html", symbol_valid = False, user_input=user_input) 
            

if __name__ == "__main__": ###如果以主程式執行
    app.run()  ###立即啟動伺服器