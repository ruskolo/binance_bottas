#!/usr/bin/python
import time
import math
import os
from random import randint
from binance.client import Client
from binance.enums import *

client = Client(<API>, <API_SECRET>)


def findLowestAsk(ticker_symbol):
    depth = client.get_order_book(symbol=ticker_symbol)
    asks = depth['asks']
    lowest_ask = float(asks[0][0])
    return lowest_ask

def findHighestBid(ticker_symbol):
    depth = client.get_order_book(symbol=ticker_symbol)
    bids = depth['bids']
    highest_bid = float(bids[0][0])
    return highest_bid

def getSymbolInfo(ticker_symbol):
    info = client.get_symbol_info(ticker_symbol)
    steps = float(info['filters'][1]['stepSize'])
    ticksize = float(info['filters'][0]['tickSize'])
    precision = info['baseAssetPrecision']
    return steps, ticksize, precision

def getLastTrade(ticker_symbol):
    trades = client.get_my_trades(symbol=ticker_symbol, limit=1)
    avg_price = trades[0]['price']
    return avg_price

def getShitcoinBalance(ticker_symbol):
    asset_symbol = ticker_symbol.split('BTC')[0]
    balance = client.get_asset_balance(asset=asset_symbol)
    coin_balance = float(balance['free'])
    return coin_balance

def sellAllMarket(ticker_symbol):
    asset_symbol = ticker_symbol.split('BTC')[0]
    balance = client.get_asset_balance(asset=asset_symbol)
    coin_balance = float(balance['free'])
    if coin_balance != 0:
        steps, ticksize, precision = getSymbolInfo(ticker_symbol)
        order_amount = (coin_balance // steps) * steps
        try:
            order = client.order_market_sell(
            symbol=ticker_symbol,
            quantity=order_amount,
            )                
            print '\nSold to market.'
        except:
            print '\nSell to market failed.'
    return

def cancelLatestOrder(ticker_symbol, order_id):
    try:
        result = client.cancel_order(
                 symbol=ticker_symbol,
                 orderId=order_id
                 )
        return
    except:
        print 'Cancel failed.'
        return



def placeNewSellOrder(ticker_symbol, ticksize, precision, order_amount):
    low_ask = findLowestAsk(ticker_symbol)
    price_str = "{:0.0{}f}".format((low_ask - ticksize), precision)
    order = client.order_limit_sell(
        symbol=ticker_symbol,
        quantity=order_amount,
        price=price_str
    )
    print 'New sell order placed @ ' + price_str
    return


def sellFraction(ticker_symbol, sell_fraction):
    coin_balance = getShitcoinBalance(ticker_symbol)
    steps, ticksize, precision = getSymbolInfo(ticker_symbol)
    low_ask = findLowestAsk(ticker_symbol)
    order_amount = ((coin_balance / sell_fraction) // steps) * steps
    price_str = "{:0.0{}f}".format((low_ask - ticksize), precision)
    print ticker_symbol + ': Selling ' + str(order_amount) + ' of ' + str(coin_balance) + ' @ ' + price_str + '...'
    order = client.order_limit_sell(
        symbol=ticker_symbol,
        quantity=order_amount,
        price=price_str
        )    
    time.sleep(1)
    open_order = client.get_open_orders(symbol=ticker_symbol)
    while open_order != []:
        time.sleep(randint(20, 29))
        open_order = client.get_open_orders(symbol=ticker_symbol)
        try:
            order_id = open_order[0]['orderId']
            exec_qty = float(open_order[0]['executedQty'])
            time.sleep(5)
            if exec_qty == 0.0:
                cancelLatestOrder(ticker_symbol, order_id)
                time.sleep(randint(10, 17))
                placeNewSellOrder(ticker_symbol, ticksize, precision, order_amount)
            else:
                print str(exec_qty) + ' filled'
                cancelLatestOrder(ticker_symbol, order_id)
                coin_balance = getShitcoinBalance(ticker_symbol)
                order_amount = ((coin_balance / sell_fraction) // steps) * steps
                time.sleep(5)
                placeNewSellOrder(ticker_symbol, ticksize, precision, order_amount)                
        except:
            continue
    print 'Sold'
    return



def positionHandler(ticker_symbol, buy_price, order_amount):
    
    asset_symbol = ticker_symbol.split('BTC')[0]
    org_price = float(buy_price)
    check1 = False
    check2 = False
    check3 = False
    steps, ticksize, precision = getSymbolInfo(ticker_symbol)
    
    while True:
        
        open_orders = client.get_open_orders(symbol=ticker_symbol)
        
        try:
            time.sleep(8)
            trades = client.get_recent_trades(symbol=ticker_symbol)
            close_price = float(trades[-1]['price'])        
            change_since_buy = (close_price - org_price) / org_price * 100
            change_since_buy_str = "{0:.2f}%".format(change_since_buy)
            close_price_str = "{:0.0{}f}".format(close_price, precision)
            print ticker_symbol + ' '*(25-len(ticker_symbol)) + close_price_str + ' '*(8-len(change_since_buy_str)) + change_since_buy_str #+ '\t' + "{0:.3f}".format(ob_symbol)
            
            
            
            if not (-0.5 < change_since_buy < 0.7) and check1 == False:
                print 'check1 activated'
                sellFraction(ticker_symbol, 3)
                check1 = True
                    
            if not (-1 < change_since_buy < 1.3) and check2 == False:
                print 'check2 activated'
                sellFraction(ticker_symbol, 2)
                check2 = True
                    
            if not (-1.5 < change_since_buy < 2) and check3 == False:
                print 'check3 activated'
                sellFraction(ticker_symbol, 1)
                check3 = True
                return
                
        except KeyboardInterrupt:
            print '\n'
            sellFraction(ticker_symbol, 1)
            return
