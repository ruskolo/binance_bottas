#!/usr/bin/python
import time
import math
import os
import sys
import multiprocessing as mp
from random import randint
from binance.client import Client
from binance.enums import *

interval = 300

client = Client(<API>, <API_SECRET>)

print ' _           _   _                '
print '| |         | | | |               '
print '| |__   ___ | |_| |_ __ _ ___     '
print '| \'_ \ / _ \\| __| __/ _` / __|  '
print '| |_) | (_) | |_| || (_| \\__ \\  '
print '|_.__/ \\___/ \\__|\\__\\__,_|___/'
print '                  SE2: Pricer'

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
        



if __name__ ==  '__main__':
    ticker_price = {}
    while True:
        try:
            if ticker_price:
                print ''
                
                #close_price, min10_in_percent, min30_in_percent, hour1_in_percent, hour4_in_percent = getBTCinfo()
                #btc_price_str = '${0:.2f}'.format(close_price)
                #min10_str = '{0:.2f}%'.format(min10_in_percent)
                #min30_str = '{0:.2f}%'.format(min30_in_percent)
                #hour1_str = '{0:.2f}%'.format(hour1_in_percent)
                #hour4_str = '{0:.2f}%'.format(hour4_in_percent)                
                
                #print time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + '   BTC @ ' + btc_price_str + '  (' + min10_str + ', ' + min30_str + ', ' + hour1_str + ')'
                #print '-'*19                
            
            prices = client.get_all_tickers()

            for p in prices:
                if p['symbol'].endswith('BTCUSDT'):
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
                    
                    if price_change > 0.8 or price_change < -0.8:
                        os.system('play --no-show-progress --null --channels 1 synth %s sine %f' % (2, 360))
                        price_change_string = "{0:.2f}%".format(price_change)
                        change24h, change1h, change30m, change10m, volume24h, volume1h, volume30m, volume10m, volume_ratio = getVolume(p_ticker)
                        change_str = '(' + "{0:.2f}%".format(change10m) + ', ' + "{0:.2f}%".format(change30m) + ', ' + "{0:.2f}%".format(change1h) + ', ' + "{0:.2f}%".format(change24h) + ')'
                        volume_str = '[' + "{0:.1f}".format(volume10m) + ', ' + "{0:.1f}".format(volume30m) + ', ' + "{0:.0f}".format(volume1h) + ', ' + "{0:.0f}".format(volume24h) + ']'
                        volume_ratio_str = "{0:.2f}".format(volume_ratio)
                        big_str = p_ticker + ' '*(10-len(p_ticker)) + "%.8f" % last_price + ' --> ' + "%.8f" % new_price + ' '*(10-len(price_change_string)) + price_change_string + ' '*(40-len(change_str)) + change_str + ' '*(28-len(volume_str)) + volume_str + ' '*(8-len(volume_ratio_str)) + volume_ratio_str
                        print big_str
                                            
            
            print ''
            print 'Waiting ' + str(interval) + ' seconds for prices...'
            
        except:
            continue
        
        time.sleep(interval)
