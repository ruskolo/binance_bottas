import time
import urllib2
import re
from binance.client import Client
from binance.enums import *
from bs4 import BeautifulSoup

client = Client('r4wwOjKaAGLqP12ETukXGDl3197rgAAjTs2c8fMtsWNpH8pEgTeJLmqArlcdQYjc', '6rsJJ5KEPA8crdlgg0MMCZUcoRMOAE998rMuHcaof085bJuSUAoHBwbqTJcQ7LFf')

asset_symbol = 'EVXBTC'
asset_price = 0.00011901

balance = client.get_asset_balance(asset='BTC')
btc_available = float(balance['free'])

order_amount_raw = btc_available / asset_price

info = client.get_symbol_info(asset_symbol)
steps = float(info['filters'][1]['stepSize'])

order_amount = (order_amount_raw // steps) * steps

print order_amount_raw
print steps
print order_amount

order = client.order_limit_buy(
    symbol=asset_symbol,
    quantity=order_amount,
    price=asset_price
)



while True:
    
    orders = client.get_open_orders(symbol=asset_symbol)
    
    if len(orders) != 0:
        
        order_id = orders[0]['orderId']
        order_orig_qty = orders[0]['origQty']
        order_exec_qty = orders[0]['executedQty']
        order_side = orders[0]['side']
        order_price = orders[0]['price']
        
        print order_side + ' side order open: ' + order_exec_qty + ' of ' + order_orig_qty + ' filled @ ' + order_price
        
        time.sleep(10)
        continue
    
    else:
        print 'order closed'
        break

#0.0017679



#api
#r4wwOjKaAGLqP12ETukXGDl3197rgAAjTs2c8fMtsWNpH8pEgTeJLmqArlcdQYjc
#secret
#6rsJJ5KEPA8crdlgg0MMCZUcoRMOAE998rMuHcaof085bJuSUAoHBwbqTJcQ7LFf