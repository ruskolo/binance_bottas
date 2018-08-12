#!/usr/bin/python
import time
import math
import os
import sys
from random import randint
from binance.client import Client
from binance.enums import *
import multiprocessing as mp


# first sort
price_change_min = -0.7

# last sort
ob_strength_min = 1

change1h_min = -3
change1h_max = 5
change24h_min = -3
change24h_max = 15

volume1h_min = 25
volume24h_min = 100
volume_ratio_min = 0.8

loop_buy_style = 'hi'


client = Client('r4wwOjKaAGLqP12ETukXGDl3197rgAAjTs2c8fMtsWNpH8pEgTeJLmqArlcdQYjc', '6rsJJ5KEPA8crdlgg0MMCZUcoRMOAE998rMuHcaof085bJuSUAoHBwbqTJcQ7LFf')

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



print ' _           _   _                '
print '| |         | | | |               '
print '| |__   ___ | |_| |_ __ _ ___     '
print '| \'_ \ / _ \\| __| __/ _` / __|  '
print '| |_) | (_) | |_| || (_| \\__ \\  '
print '|_.__/ \\___/ \\__|\\__\\__,_|___/'
print '                v0.22: P Pastor'

#bitcoins = getBTCBalance()
#btc_str = str(bitcoins)
#btc_determinator = int(btc_str.split('.')[1][0])
#buy_fraction = btc_determinator


#btc_str = 'BTC: ' + str(bitcoins)
#print btc_str
#logger('balance', btc_str)

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

def placeNewSellOrder(ticker_symbol, ticksize, precision, order_amount):
    low_ask = findLowestAsk(ticker_symbol)
    price_str = "{:0.0{}f}".format((low_ask - ticksize), precision)
    order = client.order_limit_sell(
        symbol=ticker_symbol,
        quantity=order_amount,
        price=price_str
    )
    order_str = ticker_symbol + ': Selling ' + str(order_amount) + ' @ ' + price_str + '...'
    print order_str
    return


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
                print ticker_symbol + ': ' + str(exec_qty) + ' filled'
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
    print ticker_symbol + ': ' + str(order_amount) + ' filled'
    return

def positionHandler(ticker_symbol, buy_price, order_amount):
    asset_symbol = ticker_symbol.split('BTC')[0]
    org_price = float(buy_price)
    chk_trail1 = False
    chk_trail2 = False
    chk_trail3 = False
    chk_profit1 = False
    chk_profit2 = False
    chk_profit3 = False
    high_close = 0
    steps, ticksize, precision = getSymbolInfo(ticker_symbol)
    while True:
        try:
            open_orders = client.get_open_orders(symbol=ticker_symbol)
            time.sleep(5)
            trades = client.get_recent_trades(symbol=ticker_symbol)
            buyer_maker = trades[-1]['isBuyerMaker']
            close_price = float(trades[-1]['price'])        
            if close_price > high_close:
                high_close = close_price
                print 'New high: ' + "{:0.0{}f}".format(high_close, precision)
            change_since_high = (close_price - high_close) / high_close * 100
            change_since_high_str = "{0:.2f}%".format(change_since_high)
            change_since_buy = (close_price - org_price) / org_price * 100
            change_since_buy_str = "{0:.2f}%".format(change_since_buy)
            close_price_str = "{:0.0{}f}".format(close_price, precision)
            print ticker_symbol + ' '*(25-len(ticker_symbol)) + close_price_str + ' '*(8-len(change_since_high_str)) + change_since_high_str + ' '*(8-len(change_since_buy_str)) + change_since_buy_str + '   Buyer maker?: ' + str(buyer_maker)
            
            # trailer            
            if change_since_high < -0.8 and chk_trail1 == False:
                chk_trail1 = True
                if chk_profit2 == True:
                    sellFraction(ticker_symbol, 1)
                    lastCheck(ticker_symbol)
                    #return
                if chk_profit1 == True:
                    sellFraction(ticker_symbol, 2)
                    continue
                sellFraction(ticker_symbol, 3)
                    
            if change_since_high < -1 and chk_trail2 == False:
                chk_trail2 = True
                if chk_profit1 == True:
                    sellFraction(ticker_symbol, 1)
                    lastCheck(ticker_symbol)
                    #return
                sellFraction(ticker_symbol, 2)
                
            if change_since_high < -1.3 and chk_trail3 == False:
                chk_trail3 = True
                sellFraction(ticker_symbol, 1)
                lastCheck(ticker_symbol)
                #return
            
            
            # take profit
            if change_since_buy > 0.7 and chk_profit1 == False:
                chk_profit1 = True
                if chk_trail2 == True:
                    sellFraction(ticker_symbol, 1)
                    lastCheck(ticker_symbol)
                    #return
                if chk_trail1 == True:
                    sellFraction(ticker_symbol, 2)
                else:
                    sellFraction(ticker_symbol, 3)
                    
            if change_since_buy > 0.8 and chk_profit2 == False:
                chk_profit2 = True
                if chk_trail1 == True:
                    sellFraction(ticker_symbol, 1)
                    lastCheck(ticker_symbol)
                    #return
                else:
                    sellFraction(ticker_symbol, 2)
            
            if change_since_buy > 1:
                chk_profit3 = True
                sellFraction(ticker_symbol, 1)
                lastCheck(ticker_symbol)
                #return
            
                
        #except KeyboardInterrupt:
            #print '\n'
            #if chk_trail1 == False and chk_profit1 == False:
                #sellFraction(ticker_symbol, 3)
                #chk_profit1 = True
                #chk_trail1 = True
                #continue
            #if (chk_trail1 == True or chk_profit1 == True) and chk_profit2 == False and chk_trail2 == False:
                #sellFraction(ticker_symbol, 2)
                #chk_profit2 = True
                #chk_trail2 = True
                #continue
            #sellFraction(ticker_symbol, 1)
            #lastCheck(ticker_symbol)
            #return
        
        except:
            print 'Binance exception...'
            time.sleep(10)
            continue
        

def lastCheck(ticker_symbol):
    time.sleep(randint(3, 6))
    bal = getShitcoinBalance(ticker_symbol)
    if bal > 0:
        print ticker_symbol + ': Last check balance: ' + str(bal)
        try:
            sellAllMarket(ticker_symbol)
            print str(bal) + ' sold to market'
        except:
            print 'That dust...'
            
    return



def placeBuyOrder(ticker_symbol, order_amt, price):
    try:
        order = client.order_limit_buy(
            symbol=ticker_symbol,
            quantity=order_amt,
            price=price
        )
        print 'Order placed for ' + str(order_amt) + ' @ ' + str(price)
        return
    except:
        print 'Failed to place order'
        return


def prepareBuyOrder(ticker_symbol, price, buy_style, steps, ticksize, precision, fraction):
    asset_symbol = ticker_symbol.split('BTC')[0]
    btc_available = getBTCBalance()
    if buy_style == 'vol':
        rough_order_amt = btc_available / price
        high_bid_volume = findBigBuyVolume(ticker_symbol, rough_order_amt)
        bid_price = high_bid_volume + ticksize
    if buy_style == 'hi':
        high_bid = findHighestBid(ticker_symbol)
        bid_price = high_bid + ticksize

    order_amount_raw = (btc_available / bid_price) / fraction
    order_amount = (order_amount_raw // steps) * steps
    order_cutoff = order_amount / 3
    
    price_str = "{:0.0{}f}".format(bid_price, precision)
    #print 'Order size: ' + str(order_amount)
    #print 'Order cutoff: ' + str(order_cutoff)
    
    placeBuyOrder(ticker_symbol, order_amount, price_str)
    
    return bid_price, order_amount

def buyShitcoin(ticker_symbol, price, buy_style, fraction):
    steps, ticksize, precision = getSymbolInfo(ticker_symbol)
    
    
    i = 0
    imax = 5    
    active_order = False
    
    while i < imax:
        try:
            if not active_order:
                bid_price, order_amt = prepareBuyOrder(ticker_symbol, price, buy_style, steps, ticksize, precision, fraction)
                order_cutoff = order_amt / 3
                active_order = True
            time.sleep(randint(12, 18))
            orders = client.get_open_orders(symbol=ticker_symbol)
            if len(orders) != 0:
                order_id = orders[0]['orderId']
                order_orig_qty = float(orders[0]['origQty'])
                order_orig_qty_str = "{0:.2f}".format(order_orig_qty)
                order_exec_qty = float(orders[0]['executedQty'])
                order_exec_qty_str = "{0:.2f}".format(order_exec_qty)
                order_side = orders[0]['side']
                order_price = float(orders[0]['price'])
                #print ticker_symbol + ': ' + order_side + '-side order open: ' + order_exec_qty_str + ' of ' + order_orig_qty_str + ' filled @ ' + order_price
                
                if buy_style == 'vol':
                    new_high_bid = findBigBuyVolume(ticker_symbol, order_amt)
                if buy_style == 'hi':
                    new_high_bid = findHighestBid(ticker_symbol)
                
                if new_high_bid > order_price:
                    cancelOrder(ticker_symbol, order_id)
                    active_order = False
                    time.sleep(3)
                
                i += 1
                
                continue
            else:
                time.sleep(1)
                print ticker_symbol + ': Order filled' 
                bal = getShitcoinBalance(ticker_symbol)
                if bal > order_cutoff:
                    time.sleep(2)
                    return bid_price, bal, steps, ticksize, precision
                else:
                    print 'Selling right away...'
                    time.sleep(randint(8, 12))
                    sellFraction(ticker_symbol, 1)
                    main()                
            
        except KeyboardInterrupt:
            cancelOrder(ticker_symbol, orders[0]['orderId'])
            print '\n' + ticker_symbol + ': Order cancelled'
            lastCheck(ticker_symbol)
            main()
    

    cancelOrder(ticker_symbol, orders[0]['orderId'])        
    bal = getShitcoinBalance(ticker_symbol)
    print ticker_symbol + ': ' + str(bal) + ' filled'
    if bal > order_cutoff:
        return bid_price, bal, steps, ticksize, precision
    else:
        time.sleep(randint(3, 5))
        sellFraction(ticker_symbol, 1)
        main()
        

    print 'Exception! Restarting...'
    os.execl('/home/mik/py-scripts/trader/funpastor.py', '')
        
    
        
    
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
        if (b_vol / 2) > order_amt:
            return b_price

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
    os.execl('/home/mik/py-scripts/trader/funpastor.py', '')

# main starts here

#if __name__ ==  '__main__':

def main():
    print 'Entering main()...'
    
    bitcoins = getBTCBalance()
    btc_str = str(bitcoins)
    btc_determinator = int(btc_str.split('.')[1][0])
    buy_fraction = btc_determinator + 1
    
    
    btc_str = 'BTC: ' + str(bitcoins)
    print btc_str
    logger('balance', btc_str)
    
    
    
    interval = 180
    ticker_price = {}
    pool = mp.Pool(3)

    while True:
        try:
            if ticker_price:
                print ''
                print time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                print '-'*19    
                
            prices = client.get_all_tickers()
            for p in prices:
                if p['symbol'].endswith('BTC') and not p['symbol'].startswith('BNB') and not p['symbol'].startswith('DGD') and not p['symbol'].startswith('XMR') and not p['symbol'].startswith('ETH') and not p['symbol'].startswith('XRP'):
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
                    
                    if not (price_change_min < price_change):
                        
                        price_change_string = "{0:.2f}%".format(price_change)
                        ob_strength = orderBookHandler(p_ticker)
                        ob_strength_str = "{0:.3f}".format(ob_strength)
                        change24h, change1h, volume24h, volume1h, volume_ratio = getVolume(p_ticker)
                        change_str = '(' + "{0:.2f}%".format(change1h) + ', ' + "{0:.2f}%".format(change24h) + ')'
                        volume_str = '[' + "{0:.0f}".format(volume1h) + ', ' + "{0:.0f}".format(volume24h) + ']'
                        volume_ratio_str = "{0:.2f}".format(volume_ratio)
                        big_str = p_ticker + ' '*(10-len(p_ticker)) + "%.8f" % last_price + ' --> ' + "%.8f" % new_price + ' '*(8-len(price_change_string)) + price_change_string + ' '*(8-len(ob_strength_str)) + ob_strength_str + ' '*(20-len(change_str)) + change_str + ' '*(12-len(volume_str)) + volume_str + ' '*(6-len(volume_ratio_str)) + volume_ratio_str
                        print big_str
                                            
                        if (change1h_min < change1h < change1h_max) and (change24h_min < change24h < change24h_max) and ob_strength > ob_strength_min and volume_ratio > volume_ratio_min and volume1h > volume1h_min and volume24h > volume24h_min:
                            logger('targets', big_str)
                            print '\aBuying...'
                            bal_chk = getShitcoinBalance(p_ticker)
                            if bal_chk > 0.1:
                                main()
                            buy_price, order_amount, steps, ticksize, precision = buyShitcoin(p_ticker, new_price, loop_buy_style, buy_fraction)
                            
                            
                            pool.apply_async(positionHandler, args=(p_ticker, buy_price, order_amount))
                            pool.close()
                            pool.join()                        
                            
                            #positionHandler(p_ticker, buy_price, order_amount)
                            if buy_fraction == 1:
                                sys.exit()                            
                            main()
        
            time.sleep(interval)
    
        except KeyboardInterrupt:
            print ''
            print ''
            fomo_buy_input = raw_input('FOMO:>')
            fomo_buy = fomo_buy_input.upper() + 'BTC'
            buy_type = raw_input('Style? (hi, vol): ')
            fraction_choice = int(raw_input('How much?: '))
            print 'FOMOing into ' + fomo_buy + '...'
            trades = client.get_recent_trades(symbol=fomo_buy)
            price_check = float(trades[-1]['price'])        
            buy_price, order_amount, steps, ticksize, precision = buyShitcoin(fomo_buy, price_check, buy_type, fraction_choice)
            #handler = raw_input('Handler? (y, n): ')
            #if handler == 'y':
                #positionHandler(fomo_buy, buy_price, order_amount)
            pool.apply_async(positionHandler, args=(fomo_buy, buy_price, order_amount))
            pool.close()
            pool.join()               
            main()        
            
main()