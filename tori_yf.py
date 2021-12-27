import pandas as pd
import yfinance
import datetime

appStrt = datetime.datetime.now()

start_time = "2021-10-01"
end_time = "2021-12-15"
invest_start = 100
companies = ["TSLA", "NVDA", "GOOG"]
percentage = [0.2, 0.5, 0.3]
invest_start_lst = [ i * invest_start for i in percentage] #個股投資金額，例：[20, 50, 30]

data = yfinance.download(companies, start=start_time, end=end_time)
adj_close = data["Adj Close"]

print(adj_close)

companies_dic = {}

for company in companies:
  price_lst = adj_close[company].values.tolist()
  daily_change, end_to_start = [], []  #儲存每日股價變動與歷史投報率

  for i in range(len(price_lst)):
    if i == 0:
      daily_change.append(0)
      end_to_start.append(0)
    else:
      change = (price_lst[i] - price_lst[i-1]) / price_lst[i-1] *100
      daily_change.append(change)

      total_change = (price_lst[i] - price_lst[0]) / price_lst[0] * 100
      end_to_start.append(total_change)

  # 建立完整字典，包含個別股票的歷史價格，每日變動，以及歷史投報率
  companies_dic[company] = {"price_history": price_lst, "daily_change": daily_change, "end_to_start": end_to_start}

# for key, value in companies_dic.items():
#   print(key)
#   for i, j in value.items():
#     print(i, j)

for i in range(len(companies)):
  price_history = companies_dic[companies[i]]["price_history"]
  company_return = (price_history[-1] - price_history[0]) / price_history[0] * 100
  final_amount = invest_start_lst[i] * (100 + company_return) / 100
  print(companies[i])
  print("期初投資金額:", invest_start_lst[i])
  print("期末金額:", final_amount)
  print("投報率:", company_return)

appEnd = datetime.datetime.now()

print(f'time spending is {appEnd - appStrt}')
