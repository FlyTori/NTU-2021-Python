def input_stockID_list(): ###Collect StockID List

    stockIDs = []

    while True:

        stockID = input("\nPlease enter <stockID> \nEx: AAPL/ 0050.TW/ BTC-USD/ USDTWD=X/ TWDJPY=X or\n \"end\" to close stockID collecting\n") 

        try:
            
            if stockID != "end":

                stockIDs.append(stockID.upper())

            else:

                break

        except:

            break
    
    return stockIDs


def get_data_yf(stockID:str, period:str, start=None, end=None): ###Collect historical data

    import yfinance as yf
    
    stkID = yf.Ticker(stockID)

    try:
        
        if command == "P":

            start = input("起始日期：yyyy-mm-dd") 
            end = input("結束日期：yyyy-mm-dd") 

            yf.download(stkID, start, end) 

        elif command =="M":

            return stkID.history(period="max") 

    except:
        return "Please correct input stock ID"


def integrating2dict(stockIDs:list, command:str):

    if command == "P":
        start = input("起始日期：yyyy-mm-dd") 
        end = input("結束日期：yyyy-mm-dd") 
        return {stockID:get_data_yf(stockID, command, start, end) for stockID in stockIDs} 

    elif command == "M":

        return {stockID:get_data_yf(stockID, command) for stockID in stockIDs}


def check_dir(path:str):
    ###沒有目錄就建立目錄

    import os

    if path[-1] != "/":

        path += "/"

    try:

        if not os.path.isdir(path):
            os.makedirs(path)
            ###No existed directory, creat directory

        return path

    except:
        
        return False


def check_file(path:str):

    try:
        file = open(Path,'a+')
        ###No existed file, creat file

        return True

    except:
        
        return False


def export2csv(stkHistDF:dict,path:str):

    import pandas as pd

    stkLst = list(stkHistDF.keys())
    path = check_dir(path)
    
    if path != False:

        for stk in stkLst:

            #dt = pd.dataframe(stkHistDF[stk])

            npath = path + str(stk) +".csv"
            stkHistDF[stk].to_csv(npath)
        
        return "Export completed"

    else:

        return "Wrong directory.\nPlease re-check filename or directory\n"


#Quick Start

stockIDs = input_stockID_list()
#print(stockIDs)

command = input("P:Download @start/end \nM:Max\n") 

stkHistDF = integrating2dict(stockIDs, command)
print(stkHistDF)

#path = input()
path = '~/DBSK-Web/test_output/'
###絕對路徑的最後面記得加上 "/"

export2csv(stkHistDF,path)
