#!/usr/bin/env python
import urllib.request
import json
import pandas as pd
import argparse

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('stock', type=str,help='NASDAQ Stock you want to extract')

args = parser.parse_args()
print(args.stock)

stock_input = args.stock
nasdaq_load = urllib.request.urlopen("https://api.nasdaq.com/api/quote/{}/chart?assetclass=stocks".format(stock_input))
data = json.load(nasdaq_load)

# High level look (without chart)
data = data['data']

summary_info = pd.DataFrame.from_dict(data)
summary_info = summary_info.drop('chart',axis=1)

stock_timestamp = pd.DataFrame.from_dict(data['chart'])
stock_timestamp['ds'] = pd.to_datetime(stock_timestamp['x'],unit='ms')
stock_timestamp = stock_timestamp[['ds','y']]


# INSERT INTO stockdump(datetime,price,stock_name) VALUES ('2020-04-21 16:59:40',53.20,'AMD')

def data2sql(data,stock):
    for i in range(len(data)):
        print('INSERT INTO stockdump(datetime,price,stock_name) VALUES (\'',data['ds'][i],'\',',data['y'][i],',\'',stock,'\');',sep='')
data2sql(stock_timestamp,stock_input)
# Data structure as follows
# {'symbol': 'AMD',
#  'company': 'Advanced Micro Devices, Inc. Common Stock',
#  'timeAsOf': 'Apr 21, 2020 4:18 PM ET',
#  'isNasdaq100': True,
#  'lastSalePrice': '$53.35',
#  'netChange': '+0.3831',
#  'percentageChange': '0.72%',ß
#  'deltaIndicator': 'up',
#  'previousClose': '$56.97',
#  'chart': [{'z': {'dateTime': '04:18:54 PM', 'value': '53.35'},
#  'x': 1587485934000,
#  'y': 53.35},...]
#  }
