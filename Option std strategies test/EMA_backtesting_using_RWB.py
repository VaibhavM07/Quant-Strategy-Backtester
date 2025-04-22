import pandas as pd
import yfinance as yf
import numpy as np
import datetime as dt
import pandas_ta as ta
import matplotlib.pyplot as plt

from pandas_datareader import data as pdr

yf.pdr_override() #workaround to access yahoo data

stock = input("Enter stock:")
print(stock)

syear=2019
smonth=1
sday=1

start = dt.datetime(syear,smonth,sday)
now = dt.datetime.now()

df=pdr.get_data_yahoo(stock,start,now) #Got our dataframe

ewma = [3,5,8,10,12,15,30,35,40,45,50,60] #all the ewma lines
for x in ewma:
    ema = x
    df['ema_'+str(ema)] = round(df.iloc[:,4].ewm(span=ema, adjust=False).mean(),2)

#df.drop("ema_[3, 5, 8, 10, 12, 15, 30, 35, 40, 45, 50, 60]",axis=1,inplace=True)

itr = 0
is_pos_open = 0
buy_price = 0
sell_price = 0
percentchange = []
profit = 0

for i in df.index:
    cmin = min(df['ema_3'][i], df['ema_5'][i], df['ema_8'][i], df['ema_10'][i], df['ema_12'][i], df['ema_15'][i])
    cmax = min(df['ema_30'][i], df['ema_35'][i], df['ema_40'][i], df['ema_45'][i], df['ema_50'][i], df['ema_60'][i])
    
    diff = 0
    close = df['Adj Close'][i]
    
    if (cmin) > (cmax): # buying condition (R W B Stratergy)
        if (is_pos_open == 0): # checking if there is no open position
            is_pos_open = 1
            buy_price = close
            print("Buying at "+str(buy_price)+" on "+str(i))
            
    elif (cmin) < (cmax): #selling condition (B W R Stratergy)
        if (is_pos_open == 1): #checking if there is a position open to sell
            sell_price = close
            profit+=(sell_price - buy_price)
            diff = ((sell_price/buy_price)-1)*100
            percentchange.append(round(diff,2))
            is_pos_open = 0
            print("Selling at "+str(sell_price)+" on "+str(i))
            
    if (itr == df['Open'].count()-1 and is_pos_open == 1): #checking if there is a position open to sell at end of df
        sell_price = close
        profit+=(sell_price - buy_price)
        diff = ((sell_price/buy_price)-1)*100
        percentchange.append(round(diff,2))
        is_pos_open = 0
        print("Selling at "+str(sell_price)+" on "+str(i))
        
    itr+=1

    
#print("Profits: "+str(profit))
gaindays = 0
lossdays = 0
profitpercent = 1

for i in percentchange:
    if (i > 0):
        gaindays+=1
    elif (i < 0):
        lossdays+=1
    profitpercent = (profitpercent*(i/100)+1)
    
profitpercent = round(((profitpercent-1)*100),2)

print("Backtesting for "+stock)
print("EMA used: "+str(ewma))
print("Days with gains: "+str(gaindays))
print("Days with losses: "+str(lossdays))
print("Batting average: "+str(round((gaindays)/(gaindays+lossdays),2)))
print("Biggest gain: "+str(max(percentchange)))
print("Biggest loss: "+str(min(percentchange)))

print("Total return: "+str(profitpercent)+"%")