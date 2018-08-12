#!/usr/bin/python
import time
import math
import os
import sys
import multiprocessing as mp
from random import randint
from binance.client import Client
from binance.enums import *

interval = 75

# first sort
price_change_min = -0.8
price_change_max = 100

# last sort
ob_strength_min = -1

rsi_max = 30

change1h_min = -3
change1h_max = 4
change24h_min = -20
change24h_max = 15

volume1h_min = 30
volume24h_min = 400
volume_ratio_min = 0.5

loop_buy_style = 'vol'

# buy fraction
ballpark_modifier = 1

# trailer
#change_since_high_outset = -1
#change_since_high_increment = -0.4

# take profit
#change_since_buy_outset = 1
#change_since_buy_increment = 0.4

client = Client(<API>, <API_SECRET>)

print ' _           _   _                '
print '| |         | | | |               '
print '| |__   ___ | |_| |_ __ _ ___     '
print '| \'_ \ / _ \\| __| __/ _` / __|  '
print '| |_) | (_) | |_| || (_| \\__ \\  '
print '|_.__/ \\___/ \\__|\\__\\__,_|___/'
print '             v0.3: Kobayashi'

def getBTCBalance():
    try:
        balance = client.get_asset_balance(asset='BTC')
        btc_balance = float(balance['free'])
        return btc_balance
    except:
        print 'BTC balance exception'
        time.sleep(5)
        getBTCBalance()

def logger(cat, payload):
    log_str = time.strftime("%H:%M:%S", time.localtime()) + '\t' + payload + '\n'
    f_str = 'logs/' + cat + '.txt'
    with open(f_str, 'a') as f:
        f.write(log_str)    

def getRSI(ticker_symbol):
    
    #prices = client.get_historical_klines(ticker_symbol, Client.KLINE_INTERVAL_1MINUTE, "16 minutes ago UTC")
    prices = client.get_historical_klines(ticker_symbol, Client.KLINE_INTERVAL_5MINUTE, "80 minutes ago UTC")
    
    rsi_var = 14
    upward = []
    downward = []
    first_close_price = float(prices[0][4])
    current_price = float(prices[-1][4])
    
    #print 'Current Price: %.8f' % current_price
    #print len(prices)
    
    #i = 14
    last_close = first_close_price
    
    for p in prices[1:-1]:
        
        close_price = float(p[4])
        
        if close_price > last_close:
            up_mov = close_price - last_close
            #adj_up = up_mov * (1 - ((i*i) / 100))
            #print '%.8f' % adj_up
            upward.append(up_mov)
            #print 'Up: ' + '%.8f' % up_mov
            
        if close_price < last_close:
            down_mov = last_close - close_price
            #adj_down = down_mov * (1 - ((i*i) / 100))
            #print '%.8f' % adj_down
            downward.append(down_mov)
            #print 'Down: ' + '%.8f' % down_mov
        
        last_close = close_price
        #i -= 1
    
    up_sum = 0.0
    for u in upward:
        up_sum += u
    
    up_avg = up_sum / rsi_var
    
    down_sum = 0.0
    for d in downward:
        down_sum += d
    
    down_avg = down_sum / rsi_var
    
    if current_price > last_close:
        now_up_avg = ((up_avg * (rsi_var - 1)) + (current_price - last_close)) / rsi_var
        now_down_avg = (down_avg * (rsi_var - 1)) / rsi_var
    
    if current_price < last_close:
        now_down_avg = ((down_avg * (rsi_var - 1)) + (last_close - current_price)) / rsi_var
        now_up_avg = (up_avg * (rsi_var - 1)) / rsi_var

    else:
        now_up_avg = (up_avg * (rsi_var - 1)) / rsi_var
        now_down_avg = (down_avg * (rsi_var - 1)) / rsi_var
    
    rs = now_up_avg / now_down_avg
    
    rsi = 100 - (100 / (rs + 1))

    #print 'Up: %.10f' % up_avg
    #print 'Down: %.10f' % down_avg
    #print 'Up: %.10f' % now_up_avg
    #print 'Down: %.10f' % now_down_avg
    #print 'RS: %.4f' % rs
    #print 'RSI: %.2f' % rsi
    
    return rsi


def orderBookHandler(ticker_symbol):
    
    try:
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
    except:
        return 0.0



def getVolume(ticker_symbol):
    klines = client.get_historical_klines(ticker_symbol, Client.KLINE_INTERVAL_5MINUTE, "1 day ago UTC")
    
    close_price = float(klines[-1][4])
    price_10m_ago = float(klines[-2][4])
    price_30m_ago = float(klines[-6][4])
    price_1h_ago = float(klines[-12][4])
    price_24h_ago = float(klines[0][1])
    
    day_in_percent = (close_price - price_24h_ago) / price_24h_ago * 100
    hour_in_percent = (close_price - price_1h_ago) / price_1h_ago * 100
    min30_in_percent = (close_price - price_30m_ago) / price_30m_ago * 100
    min10_in_percent = (close_price - price_10m_ago) / price_10m_ago * 100

    volume_10m = 0
    price_acc_10m = 0
    for k in klines[-2:]:
        price_close = float(k[4])
        volume = float(k[5])
        price_acc_10m += price_close
        volume_10m += volume
        
    price_avg_10m = price_acc_10m / 2
    volume_in_btc_10m = price_avg_10m * volume_10m

    volume_30m = 0
    price_acc_30m = 0
    for k in klines[-6:]:
        price_close = float(k[4])
        volume = float(k[5])
        price_acc_30m += price_close
        volume_30m += volume
        
    price_avg_30m = price_acc_30m / 6
    volume_in_btc_30m = price_avg_30m * volume_30m

    volume_1h = 0
    price_acc_1h = 0
    for k in klines[-12:]:
        price_close = float(k[4])
        volume = float(k[5])
        price_acc_1h += price_close
        volume_1h += volume
        
    price_avg_1h = price_acc_1h / 12
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
    
    return day_in_percent, hour_in_percent, min30_in_percent, min10_in_percent, volume_in_btc_24h, volume_in_btc_1h, volume_in_btc_30m, volume_in_btc_10m, volume_ratio    
    

def placeNewSellOrder(ticker_symbol, ticksize, precision, order_amount):
    low_ask = findLowestAsk(ticker_symbol)
    price_str = "{:0.0{}f}".format((low_ask - ticksize), precision)
    
    try:
        order = client.order_limit_sell(
        symbol=ticker_symbol,
        quantity=order_amount,
        price=price_str
        )
        order_str = ticker_symbol + ': Selling ' + str(order_amount) + ' @ ' + price_str + '...'
        print order_str
        return
    except:
        print 'Sell order fail'


def sellFraction(ticker_symbol, sell_fraction):
    coin_balance = getShitcoinBalance(ticker_symbol)
    steps, ticksize, precision = getSymbolInfo(ticker_symbol)
    order_amount = ((coin_balance / sell_fraction) // steps) * steps
    if order_amount == 0:
        print 'Nothing to sell...'
        return
    placeNewSellOrder(ticker_symbol, ticksize, precision, order_amount)
    time.sleep(4)
    open_order = client.get_open_orders(symbol=ticker_symbol)
    exec_qty = 0
    while open_order != []:
        
        time.sleep(randint(20, 30)) # seconds order stays in book
        open_order = client.get_open_orders(symbol=ticker_symbol)
        try:
            order_id = open_order[0]['orderId']
            exec_qty = float(open_order[0]['executedQty'])
            if exec_qty == 0.0:
                cancelOrder(ticker_symbol, order_id)
                time.sleep(randint(12, 20)) # seconds between cancel and place new order
                placeNewSellOrder(ticker_symbol, ticksize, precision, order_amount)
            else:
                fin_price, fin_qty = getLastTrade(ticker_symbol)
                print ticker_symbol + ': Sold ' + str(fin_qty) + ' @ ' + '%.8f' % fin_price
                cancelOrder(ticker_symbol, order_id)
                new_order_amt = order_amount - exec_qty
                time.sleep(randint(10, 17)) # seconds between cancel and place new order
                placeNewSellOrder(ticker_symbol, ticksize, precision, new_order_amt)
                order_amount = new_order_amt
        except KeyboardInterrupt:
            coin_balance = getShitcoinBalance(ticker_symbol)
            order_amount = (coin_balance // steps) * steps
            order = client.order_market_sell(
                symbol=ticker_symbol,
                quantity=order_amount,
                )    
                        
        except:
            continue
    fin_price, fin_qty = getLastTrade(ticker_symbol)
    print ticker_symbol + ': Sold ' + str(fin_qty) + ' @ ' + '%.8f' % fin_price
    return

def lastCheck(ticker_symbol):
    time.sleep(randint(3, 6))
    bal = getShitcoinBalance(ticker_symbol)
    if bal > 0:
        print ticker_symbol + ': Last check balance: ' + str(bal)
        try:
            sellFraction(ticker_symbol, 1)
            #print ticker_symbol + ': ' + str(bal) + ' sold'
        except KeyboardInterrupt:
            sellAllMarket(ticker_symbol)
            print '%s: Sold to market' % ticker_symbol
        except:
            print ticker_symbol + ': Limit order failed. Amount likely too low.'
            sellAllMarket(ticker_symbol)
    return



def placeBuyOrder(ticker_symbol, order_amt, price):
    try:
        order = client.order_limit_buy(
            symbol=ticker_symbol,
            quantity=order_amt,
            price=price
        )
        print ticker_symbol + ': Order placed for ' + str(order_amt) + ' @ ' + str(price)
        
    except:
        print ticker_symbol + ': Failed to place order'
    
    return

def prepareBuyOrder(ticker_symbol, price, buy_style, steps, ticksize, precision, fraction):
    asset_symbol = ticker_symbol.split('BTC')[0]
    btc_available = getBTCBalance()
    if buy_style == 'vol':
        try:
            rough_order_amt = (btc_available / fraction) / price
            high_bid_volume = findBigBuyVolume(ticker_symbol, rough_order_amt)
            bid_price = high_bid_volume + ticksize
        except:
            print 'No volume bid found. Restarting...'
            restartBottas()
    if buy_style == 'hi':
        high_bid = findHighestBid(ticker_symbol)
        bid_price = high_bid + ticksize

    order_amount_raw = (btc_available / bid_price) / fraction
    order_amount = (order_amount_raw // steps) * steps
    order_cutoff = order_amount / 3
    
    price_str = "{:0.0{}f}".format(bid_price, precision)
    
    placeBuyOrder(ticker_symbol, order_amount, price_str)
    
    return bid_price, order_amount

def buyShitcoin(ticker_symbol, price, buy_style, fraction):
    steps, ticksize, precision = getSymbolInfo(ticker_symbol)
    
    i = 0
    imax = 8
    active_order = False
    
    while i < imax:
        try:
            if not active_order:
                bid_price, order_amt = prepareBuyOrder(ticker_symbol, price, buy_style, steps, ticksize, precision, fraction)
                time.sleep(3)
                order_cutoff = order_amt / 3
                active_order = True
            
            orders = client.get_open_orders(symbol=ticker_symbol)
            
            if len(orders) != 0:
                order_id = orders[0]['orderId']
                order_orig_qty = float(orders[0]['origQty'])
                order_orig_qty_str = "{0:.2f}".format(order_orig_qty)
                order_exec_qty = float(orders[0]['executedQty'])
                order_exec_qty_str = "{0:.2f}".format(order_exec_qty)
                order_side = orders[0]['side']
                order_price = float(orders[0]['price'])
                
                print ticker_symbol + ': ' + order_side + '-side order open, ' + order_exec_qty_str + ' of ' + order_orig_qty_str + ' filled @ ' + "%.8f" % order_price + '  (' + str(i + 1) + '/' + str(imax) + ')'
            
                i += 1
                time.sleep(randint(4, 6))
                continue
   
            else:
                time.sleep(1)
                bal = getShitcoinBalance(ticker_symbol)
                print ticker_symbol + ': Bought ' + str(bal)
                if bal > order_cutoff:
                    time.sleep(2)
                    return bid_price, bal, steps, ticksize, precision
                else:
                    print ticker_symbol + ': Selling right away...'
                    time.sleep(randint(6, 9))
                    try:
                        sellFraction(ticker_symbol, 1)
                    except:
                        print ticker_symbol + ': Selling failed'
                    restartBottas()                
            
        except KeyboardInterrupt:
            cancelOrder(ticker_symbol, orders[0]['orderId'])
            print '\n' + ticker_symbol + ': Order cancelled'
            lastCheck(ticker_symbol)
            restartBottas()
    

    cancelOrder(ticker_symbol, orders[0]['orderId'])        
    bal = getShitcoinBalance(ticker_symbol)
    print ticker_symbol + ': Bought ' + str(bal) #+ ' @ ' + str(order_price)
    if bal > order_cutoff:
        return bid_price, bal, steps, ticksize, precision
    else:
        time.sleep(randint(3, 5))
        lastCheck(ticker_symbol)
        time.sleep(12)
        restartBottas()
        

    print ticker_symbol + ': Exception! Restarting...'
    restartBottas()
        
    
        
def spinOffHandler(ticker_symbol):
    handler_str = 'x-terminal-emulator -e python pos_handler.py ' + ticker_symbol
    os.system(handler_str)

def setStopLoss(ticker_symbol, current_price, ticksize, precision, order_amount, ticks_percent):
        
    ticks_1pct = (float(current_price) / 100) // ticksize
    ticks_0_7pct = (ticks_1pct * 0.7) // 1
    ticks_1_5pct = (ticks_1pct * 1.5) // 1
    ticks_10pct = (ticks_1pct * 10) // 1
    ticks = (ticks_1pct * ticks_percent) // 1
    
    stop_price = float(current_price) - (ticksize * ticks)
    stop_price_str = "{:0.0{}f}".format(stop_price, precision)
    stop_limit_price = float(current_price) - (ticksize * ticks_10pct)
    stop_limit_price_str = "{:0.0{}f}".format(stop_limit_price, precision)
    
    order = client.create_order(
        symbol=ticker_symbol,
        side=SIDE_SELL,
        type=ORDER_TYPE_STOP_LOSS_LIMIT,
        timeInForce=TIME_IN_FORCE_GTC,
        quantity=order_amount,
        price=stop_limit_price_str,
        stopPrice=stop_price_str
        )
    
    print 'Stop set @ ' + "%.8f" % stop_price
    
    return
    

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

def findBigSellVolume(ticker_symbol, order_amt):
    depth = client.get_order_book(symbol=ticker_symbol)
    asks = depth['asks']
    for ask in asks:
        a_price = float(ask[0])
        a_vol = float(ask[1])
        if (a_vol / 2) > order_amt:
            return a_price

def findBigBuyVolume(ticker_symbol, order_amt):
    depth = client.get_order_book(symbol=ticker_symbol)
    bids = depth['bids']
    for bid in bids:
        b_price = float(bid[0])
        b_vol = float(bid[1])
        if b_vol > order_amt:
            return b_price

def getSymbolInfo(ticker_symbol):
    info = client.get_symbol_info(ticker_symbol)
    steps = float(info['filters'][1]['stepSize'])
    ticksize = float(info['filters'][0]['tickSize'])
    precision = info['baseAssetPrecision']
    return steps, ticksize, precision

def getLastTrade(ticker_symbol):
    trades = client.get_my_trades(symbol=ticker_symbol, limit=1)
    price = float(trades[0]['price'])
    qty = float(trades[0]['qty'])
    return price, qty

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
        except:
            print 'Sell to market failed.'
    return

def cancelOrder(ticker_symbol, order_id):
    try:
        result = client.cancel_order(
                 symbol=ticker_symbol,
                 orderId=order_id
                 )
        #print ticker_symbol + ': Order cancelled'
        return
    except:
        return

def sellShitcoin(ticker_symbol, ticker_price):
    asset_symbol = ticker_symbol.split('BTC')[0]
    balance = client.get_asset_balance(asset=asset_symbol)
    coin_balance = float(balance['free'])
    print ''
    print asset_symbol + ' in account: ' + str(coin_balance)
    
    steps, ticksize, precision = getSymbolInfo(ticker_symbol)
    
    lowest_ask_price = findLowestAsk(ticker_symbol)
    order_amount = (coin_balance // steps) * steps
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
            coin_balance = float(balance['free'])            
            info = client.get_symbol_info(ticker_symbol)
            steps = float(info['filters'][1]['stepSize'])
            order_amount = (coin_balance // steps) * steps
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
    coin_balance = float(balance['free'])            
    info = client.get_symbol_info(ticker_symbol)
    steps = float(info['filters'][1]['stepSize'])
    order_amount = (coin_balance // steps) * steps
    
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
    


def restartBottas():
    os.execl(sys.argv[0], '')

def getBTCinfo():
    klines = client.get_historical_klines('BTCUSDT', Client.KLINE_INTERVAL_5MINUTE, "4 hours ago UTC")
    
    close_price = float(klines[-1][4])
    price_10m_ago = float(klines[-2][4])
    price_30m_ago = float(klines[-6][4])
    price_1h_ago = float(klines[-12][4])
    price_4h_ago = float(klines[0][1])
    
    min10_in_percent = (close_price - price_10m_ago) / price_10m_ago * 100
    min30_in_percent = (close_price - price_30m_ago) / price_30m_ago * 100
    hour1_in_percent = (close_price - price_1h_ago) / price_1h_ago * 100
    hour4_in_percent = (close_price - price_4h_ago) / price_4h_ago * 100

    volume_10m = 0
    price_acc_10m = 0
    for k in klines[-2:]:
        price_close = float(k[4])
        volume = float(k[5])
        price_acc_10m += price_close
        volume_10m += volume
        
    price_avg_10m = price_acc_10m / 2
    
    volume_30m = 0
    price_acc_30m = 0
    for k in klines[-6:]:
        price_close = float(k[4])
        volume = float(k[5])
        price_acc_30m += price_close
        volume_30m += volume
        
    price_avg_30m = price_acc_30m / 6
    
    volume_1h = 0
    price_acc_1h = 0
    for k in klines[-12:]:
        price_close = float(k[4])
        volume = float(k[5])
        price_acc_1h += price_close
        volume_1h += volume
        
    price_avg_1h = price_acc_1h / 12
            
    volume_4h = 0
    price_acc_4h = 0    
    for k in klines:
        price_close = float(k[4])
        volume = float(k[5])
        price_acc_4h += price_close
        volume_4h += volume
        
    price_avg_4h = price_acc_4h / len(klines)
    volume_ratio = (volume_10m / volume_4h) * 24
    
    return close_price, min10_in_percent, min30_in_percent, hour1_in_percent, hour4_in_percent
        

# main starts here

if __name__ ==  '__main__':
    ticker_price = {}
    while True:
        try:
            if ticker_price:
                print ''
                bitcoins = getBTCBalance()
                if bitcoins < 0.05:
                    print 'BTC check failed'
                    sys.exit()         
                btc_ballpark = int(str(bitcoins).split('.')[1][0])
                buy_fraction = btc_ballpark + ballpark_modifier
                #if btc_ballpark > 1:
                    #buy_fraction = 2
                #else:
                    #buy_fraction = 1
                btc_str = 'BTC: ' + str(bitcoins)
                print btc_str
                logger('balance', btc_str)
                
                close_price, min10_in_percent, min30_in_percent, hour1_in_percent, hour4_in_percent = getBTCinfo()
                
                btc_price_str = '${0:.2f}'.format(close_price)
                min10_str = '{0:.2f}%'.format(min10_in_percent)
                min30_str = '{0:.2f}%'.format(min30_in_percent)
                hour1_str = '{0:.2f}%'.format(hour1_in_percent)
                hour4_str = '{0:.2f}%'.format(hour4_in_percent)                
                
                print time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + '   BTC @ ' + btc_price_str + '  (' + min10_str + ', ' + min30_str + ', ' + hour1_str + ')'
                print '-'*19                
            
                if (min10_in_percent > 0.8 or min10_in_percent < -0.8) or (min30_in_percent > 1.2 or min30_in_percent < -1.2):
                    print 'BTC volatility spike detected!'
                    print 'Sleeping for 5 mins...'
                    try:
                        time.sleep(300)
                        restartBottas()
                    except KeyboardInterrupt:
                        pass
                    
            prices = client.get_all_tickers()
            for p in prices:
                if p['symbol'].endswith('BTC') and not p['symbol'].startswith('BNB')  and not p['symbol'].startswith('BCN') and not p['symbol'].startswith('DGD'):
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
                    
                    if not (price_change_min < price_change < price_change_max):
                        price_change_string = "{0:.2f}%".format(price_change)
                        #ob_strength = orderBookHandler(p_ticker)
                        #ob_strength_str = "{0:.3f}".format(ob_strength)
                        rsi = getRSI(p_ticker)
                        rsi_str = '%.0f' % rsi
                        change24h, change1h, change30m, change10m, volume24h, volume1h, volume30m, volume10m, volume_ratio = getVolume(p_ticker)
                        change_str = '(' + "{0:.2f}%".format(change10m) + ', ' + "{0:.2f}%".format(change30m) + ', ' + "{0:.2f}%".format(change1h) + ', ' + "{0:.2f}%".format(change24h) + ')'
                        volume_str = '[' + "{0:.1f}".format(volume10m) + ', ' + "{0:.1f}".format(volume30m) + ', ' + "{0:.0f}".format(volume1h) + ', ' + "{0:.0f}".format(volume24h) + ']'
                        volume_ratio_str = "{0:.2f}".format(volume_ratio)
                        big_str = p_ticker + ' '*(10-len(p_ticker)) + "%.8f" % last_price + ' --> ' + "%.8f" % new_price + ' '*(10-len(price_change_string)) + price_change_string + ' '*(10-len(rsi_str)) + rsi_str + ' '*(40-len(change_str)) + change_str + ' '*(28-len(volume_str)) + volume_str + ' '*(8-len(volume_ratio_str)) + volume_ratio_str
                        print big_str
                                            
                        if (change1h_min < change1h < change1h_max) and (change24h_min < change24h < change24h_max) and rsi < rsi_max and volume_ratio > volume_ratio_min and volume1h > volume1h_min and volume24h > volume24h_min:
                            #orders = client.get_open_orders(symbol=p_ticker)
                            #if orders:
                                #restartBottas()
                            #logger('targets', big_str)
                            os.system('play --no-show-progress --null --channels 1 synth %s sine %f' % (0.5, 440))
                            print p_ticker + ': Buying...'
                            
                            #bal_chk = getShitcoinBalance(p_ticker)
                            
                            #if bal_chk > 1:
                                #restartBottas()
                            
                            print 'Buying with fraction ' + str(buy_fraction)
                            
                            buy_price, order_amount, steps, ticksize, precision = buyShitcoin(p_ticker, new_price, loop_buy_style, buy_fraction)
                            #positionHandler(p_ticker, buy_price, order_amount)
                            spinOffHandler(p_ticker)
                            
                            btcs_remain = getBTCBalance()
                            
                            if btcs_remain > 0.1:
                                restartBottas()
                            else:
                                print 'Out of funds'
                                sys.exit()
            
            print ''
            print 'Waiting ' + str(interval) + ' seconds for prices...'
            time.sleep(interval)
    
        except KeyboardInterrupt:
            print ''
            print ''
            fomo_buy_input = raw_input('FOMO:>')
            fomo_buy = fomo_buy_input.upper() + 'BTC'
            buy_type = raw_input('Style? (hi, vol): ')
            fraction_choice = int(raw_input('How much? (1/x): '))
            print 'FOMOing into ' + fomo_buy + '...'
            trades = client.get_recent_trades(symbol=fomo_buy)
            price_check = float(trades[-1]['price'])        
            buy_price, order_amount, steps, ticksize, precision = buyShitcoin(fomo_buy, price_check, buy_type, fraction_choice)
            spinOffHandler(fomo_buy)
            #handler = raw_input('Handler? (y, n): ')
            #if handler == 'y':
                #positionHandler(fomo_buy, buy_price, order_amount)
            restartBottas()
