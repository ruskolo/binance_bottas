#!/usr/bin/python
import time
import math
import os
from binance.client import Client
from binance.enums import *

client = Client(<API>, <API_SECRET>)

print ' _           _   _                '
print '| |         | | | |               '
print '| |__   ___ | |_| |_ __ _ ___     '
print '| \'_ \ / _ \\| __| __/ _` / __|  '
print '| |_) | (_) | |_| || (_| \\__ \\  '
print '|_.__/ \\___/ \\__|\\__\\__,_|___/'
print '                   v0.1: Joleon'

def orderBookHandler(ticker_symbol):
    
    depth = client.get_order_book(symbol=ticker_symbol)
    
    bids = depth['bids']
    asks = depth['asks']
    
    spread_average = (float(bids[0][0]) + float(asks[0][0])) / 2
        
    bid_volume = 0
    bid_weighted_volume = 0
    
    for b in bids:
        b_price = float(b[0])
        b_vol = float(b[1])
        b_weighted_price = ((b_price - spread_average) / spread_average) * -1
        b_weighted_vol = b_vol * (1 - math.sqrt(b_weighted_price))
        bid_volume += b_vol
        bid_weighted_volume += b_weighted_vol
        
    ask_volume = 0
    ask_weighted_volume = 0
    
    for a in asks:
        a_price = float(a[0])
        a_vol = float(a[1])
        a_weighted_price = ((a_price - spread_average) / spread_average)
        a_weighted_vol = a_vol * (1 - math.sqrt(a_weighted_price))
        ask_volume += a_vol
        ask_weighted_volume += a_weighted_vol
    
    ba_weighted_vol = bid_weighted_volume/ask_weighted_volume
    
    return ba_weighted_vol



def getVolume(ticker_symbol):
    
    klines = client.get_historical_klines(ticker_symbol, Client.KLINE_INTERVAL_15MINUTE, "1 day ago UTC")
    
    price_24h_ago = float(klines[0][1])
    close_price = float(klines[-1][4])
    price_1h_ago = float(klines[-4][4])
    day_in_percent = (close_price - price_24h_ago) / price_24h_ago * 100
    hour_in_percent = (close_price - price_1h_ago) / price_1h_ago * 100
    
    volume_1h = 0
    price_acc_1h = 0
    for k in klines[-4:]:
        price_close = float(k[4])
        volume = float(k[5])
        price_acc_1h += price_close
        volume_1h += volume
        
    price_avg_1h = price_acc_1h / 4
    volume_in_btc_1h = price_avg_1h * volume_1h
        
    volume_24h = 0
    price_acc_24h = 0    
    for k in klines:
        time_open = k[0]
        time_close = k[6]
        price_open = k[1]
        price_high = k[2]
        price_low = k[3]
        price_close = float(k[4])
        volume = float(k[5])
        trades_no = k[8]
        qoute_asset_vol = k[7]      # Quote asset volume
        taker_buy_base = k[9]       # Taker buy base asset volume
        taker_buy_qoute = k[10]     # Taker buy quote asset volume
        
        volume_24h += volume
        price_acc_24h += price_close
        
    price_avg_24h = price_acc_24h / len(klines)
    volume_in_btc_24h = price_avg_24h * volume_24h
    volume_ratio = (volume_in_btc_1h / volume_in_btc_24h) * 24
    
    return day_in_percent, hour_in_percent, volume_in_btc_24h, volume_in_btc_1h, volume_ratio    


def positionHandler(ticker_symbol, buy_price, ticksize, precision, order_amount):
    org_price = buy_price
    
    while True:
        
        open_orders = client.get_open_orders(symbol=ticker_symbol)
        
        try:
            time.sleep(10)
            
            
            
            if open_orders != []:
                
                
                trades = client.get_recent_trades(symbol=ticker_symbol)
                close_price = float(trades[-1]['price'])        
                change_since_stop = (close_price - buy_price) / buy_price * 100
                change_since_buy = (close_price - org_price) / buy_price * 100
                change_since_buy_str = "{0:.2f}%".format(change_since_buy)
                print ticker_symbol + ' '*(25-len(ticker_symbol)) + "%.8f" % close_price + ' '*(8-len(change_since_buy_str)) + change_since_buy_str #+ '\t' + "{0:.3f}".format(ob_symbol)
            
                if change_since_stop > 0.5:
                    result = client.cancel_order(
                             symbol=ticker_symbol,
                             orderId=(open_orders[0]['orderId']))
                
                    new_stop = setStopLoss(ticker_symbol, close_price, ticksize, precision, order_amount)
                    print 'Stop set @ ' + "%.8f" % new_stop
                    buy_price = close_price
                    
                
                
            else:
                sell_price = getLastTrade(ticker_symbol)
                print 'Sold @ ' + sell_price
                return
            #if not (-1.5 < change_since_buy < 1.5):
                #output_str = ticker_symbol + ' '*(14-len(ticker_symbol)) + 'Selling @' + '  ' + "%.8f" % close_price + ' '*(8-len(change_since_buy_str)) + change_since_buy_str
                #with open('1.5 | -1_1.txt', 'a') as f:
                    #f.write(output_str + '\n')
            
                #return close_price
                
        except KeyboardInterrupt:
            order_id = open_orders[0]['orderId']
            cancelLatestOrder(ticker_symbol, order_id)
            sellAllMarket(ticker_symbol)
            return
        
        except:
            print 'Something went wrong... Sleeping...'
            time.sleep(30)
            continue

def buyShitcoin(ticker_symbol, ticker_price):
    asset_symbol = ticker_symbol.split('BTC')[0]
    balance = client.get_asset_balance(asset='BTC')
    btc_available = float(balance['free'])
    steps, ticksize, precision = getSymbolInfo(ticker_symbol)
    highest_bid = findHighestBid(ticker_symbol)
    bid_price = highest_bid + ticksize
    
    order_amount_raw = btc_available / bid_price    
    order_amount = (order_amount_raw // steps) * steps
    price_str = "{:0.0{}f}".format(bid_price, precision)
    print ''
    print 'Order size: ' + str(order_amount)
    
    order = client.order_limit_buy(
        symbol=ticker_symbol,
        quantity=order_amount,
        price=price_str
    )
    
    i = 0    
    while i < 18:
        try:
            orders = client.get_open_orders(symbol=ticker_symbol)
        
            if len(orders) != 0:
                time.sleep(5)
                order_id = orders[0]['orderId']
                order_orig_qty = orders[0]['origQty']
                order_exec_qty = orders[0]['executedQty']
                order_side = orders[0]['side']
                order_price = orders[0]['price']
                print order_side + '-side order open: ' + order_exec_qty + ' of ' + order_orig_qty + ' filled @ ' + order_price
                            
                i += 1
                continue
            else:
                trades = client.get_my_trades(symbol=ticker_symbol, limit=1)
                avg_price = trades[0]['price']
                
                print 'Order filled @ ' + avg_price
                print ''

                return float(avg_price), order_amount, ticksize, precision
            
        except KeyboardInterrupt:
            result = client.cancel_order(
                symbol=ticker_symbol,
                orderId=(orders[0]['orderId']))
            print '\nOrder cancelled.'
            
            sellAllMarket(ticker_symbol)
            os.execl('/home/mik/py-scripts/trader/bottas.py', '')
    
    try:
        result = client.cancel_order(
                 symbol=ticker_symbol,
                 orderId=(orders[0]['orderId']))
        print '\nOrder cancelled.'
        balance = client.get_asset_balance(asset=asset_symbol)
        shitcoin_available = float(balance['free'])
        steps, ticksize, precision = getSymbolInfo(ticker_symbol)
        order_amount = (shitcoin_available // steps) * steps        
        if order_amount != 0:
            return bid_price, order_amount, ticksize, precision
        else:
            os.execl('/home/mik/py-scripts/trader/bottas.py', '')
            
    except:
        return
    
        
    #balance = client.get_asset_balance(asset=asset_symbol)
    #shitcoin_available = float(balance['free'])
    #if shitcoin_available != 0:
        #steps, ticksize, precision = getSymbolInfo(ticker_symbol)
        #order_amount = (shitcoin_available // steps) * steps
        #try:
            #order = client.order_market_sell(
            #symbol=ticker_symbol,
            #quantity=order_amount,
            #)                
            #print 'Partial fill sold @ market.'
        #except:
            #print 'Stuck with fragments of shit...'
            
    #os.execl('/home/mik/py-scripts/trader/bottas.py', '')
        
    
def setStopLoss(ticker_symbol, current_price, ticksize, precision, order_amount):
        
    ticks_1pct = (current_price / 100) // ticksize
    ticks_0_7pct = (ticks_1pct * 0.7) // 1
    ticks_1_5pct = (ticks_1pct * 1.5) // 1
    ticks_10pct = (ticks_1pct * 10) // 1
    stop_price = current_price - (ticksize * ticks_0_7pct)
    stop_price_str = "{:0.0{}f}".format(stop_price, precision)
    stop_limit_price = current_price - (ticksize * ticks_10pct)
    stop_limit_price_str = "{:0.0{}f}".format(stop_limit_price, precision)
    try:
        order = client.create_order(
            symbol=ticker_symbol,
            side=SIDE_SELL,
            type=ORDER_TYPE_STOP_LOSS_LIMIT,
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=order_amount,
            price=stop_limit_price_str,
            stopPrice=stop_price_str
            )
    except:
        os.execl('/home/mik/py-scripts/trader/bottas.py', '')
    
    return float(stop_price_str)
    

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

def sellAllMarket(ticker_symbol):
    asset_symbol = ticker_symbol.split('BTC')[0]
    balance = client.get_asset_balance(asset=asset_symbol)
    shitcoin_available = float(balance['free'])
    if shitcoin_available != 0:
        steps, ticksize, precision = getSymbolInfo(ticker_symbol)
        order_amount = (shitcoin_available // steps) * steps
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

def sellShitcoin(ticker_symbol, ticker_price):
    asset_symbol = ticker_symbol.split('BTC')[0]
    balance = client.get_asset_balance(asset=asset_symbol)
    shitcoin_available = float(balance['free'])
    print ''
    print asset_symbol + ' in account: ' + str(shitcoin_available)
    
    steps, ticksize, precision = getSymbolInfo(ticker_symbol)
    
    lowest_ask_price = findLowestAsk(ticker_symbol)
    order_amount = (shitcoin_available // steps) * steps
    price_str = "{:0.0{}f}".format((lowest_ask_price - ticksize), precision)
    print 'Order size: ' + str(order_amount)
        
    order = client.order_limit_sell(
        symbol=ticker_symbol,
        quantity=order_amount,
        price=price_str
    )
    
    
    i = 0
    while i < 180:
        
        try:
            orders = client.get_open_orders(symbol=ticker_symbol)
        
            if len(orders) != 0:
                order_id = orders[0]['orderId']
                order_orig_qty = orders[0]['origQty']
                order_exec_qty = orders[0]['executedQty']
                order_side = orders[0]['side']
                order_price = orders[0]['price']
                print order_side + '-side order open: ' + order_exec_qty + ' of ' + order_orig_qty + ' filled @ ' + order_price
                time.sleep(2)
                i += 1
                continue
            else:
                trades = client.get_my_trades(symbol=ticker_symbol, limit=1)
                avg_price = trades[0]['price']
                
                print 'Order filled @ ' + avg_price
                print ''
                return
            
        except KeyboardInterrupt:
            result = client.cancel_order(
                symbol=ticker_symbol,
                orderId=(orders[0]['orderId']))
            print '\nLimit order cancelled.'

            balance = client.get_asset_balance(asset=asset_symbol)
            shitcoin_available = float(balance['free'])            
            info = client.get_symbol_info(ticker_symbol)
            steps = float(info['filters'][1]['stepSize'])
            order_amount = (shitcoin_available // steps) * steps
            try:
                order = client.order_market_sell(
                symbol=ticker_symbol,
                quantity=order_amount,
                )
                trades = client.get_my_trades(symbol=ticker_symbol, limit=1)
                avg_price = trades[0]['price']        
                print 'Sold to market @ ' + avg_price                
            except:
                print 'Something went wrong...'            
            
            return
        

    result = client.cancel_order(
        symbol=ticker_symbol,
        orderId=(orders[0]['orderId']))
    print '\nLimit order cancelled.'

    balance = client.get_asset_balance(asset=asset_symbol)
    shitcoin_available = float(balance['free'])            
    info = client.get_symbol_info(ticker_symbol)
    steps = float(info['filters'][1]['stepSize'])
    order_amount = (shitcoin_available // steps) * steps
    
    try:
        order = client.order_market_sell(
        symbol=ticker_symbol,
        quantity=order_amount,
        )
        trades = client.get_my_trades(symbol=ticker_symbol, limit=1)
        avg_price = trades[0]['price']        
        print 'Sold to market @ ' + avg_price
    except:
        print 'Something went wrong...'            
        
    return
    


# main starts here
interval = 180
ticker_price = {}

while True:    
    if ticker_price:
        print ''
        print time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print '-'*19    
        
    prices = client.get_all_tickers()
    
    for p in prices:
        
        if p['symbol'].endswith('BTC') and not p['symbol'].startswith('BNB') and not p['symbol'].startswith('XMR'):
            p_ticker = p['symbol']
            p_price = [p['price']]
        
            if p_ticker in ticker_price:
                ticker_price[p_ticker].append(p_price[0])
            else:
                ticker_price[p_ticker] = p_price
            
            new_price = float(ticker_price[p_ticker][-1])
            
            try:
                last_price = float(ticker_price[p_ticker][-2])
            except:
                last_price = new_price
            
            price_change = (new_price - last_price) / last_price * 100
            
            if not (-0.5 < price_change):
                price_change_string = "{0:.2f}%".format(price_change)
                ob_strength = orderBookHandler(p_ticker)
                ob_strength_str = "{0:.3f}".format(ob_strength)
                change24h, change1h, volume24h, volume1h, volume_ratio = getVolume(p_ticker)
                change_str = '(' + "{0:.2f}%".format(change1h) + ', ' + "{0:.2f}%".format(change24h) + ')'
                volume_str = '[' + "{0:.0f}".format(volume1h) + ', ' + "{0:.0f}".format(volume24h) + ']'
                volume_ratio_str = "{0:.2f}".format(volume_ratio)
                print p_ticker + ' '*(10-len(p_ticker)) + "%.8f" % last_price + ' --> ' + "%.8f" % new_price + ' '*(8-len(price_change_string)) + price_change_string + ' '*(8-len(ob_strength_str)) + ob_strength_str + ' '*(20-len(change_str)) + change_str + ' '*(12-len(volume_str)) + volume_str + ' '*(6-len(volume_ratio_str)) + volume_ratio_str
                
                if volume24h > 200 and change24h < 20 and ob_strength > 1.0 and (volume_ratio > 1 or volume1h > 50):
                    print 'Buying...'
                    buy_price, order_amount, ticksize, precision = buyShitcoin(p_ticker, new_price)
                    stop_loss = setStopLoss(p_ticker, buy_price, ticksize, precision, order_amount)
                    print 'Stop set @ ' + "%.8f" % stop_loss
                    positionHandler(p_ticker, buy_price, ticksize, precision, order_amount)
                    
                    
                    #sell_price = positionHandler(p_ticker, buy_price)
                    #sellShitcoin(p_ticker, sell_price)
                    os.execl('/home/mik/py-scripts/trader/bottas.py', '')
                  
    time.sleep(interval)
