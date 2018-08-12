import time
from binance.client import Client

client = Client("", "")

trades = client.get_recent_trades(symbol='POEBTC')

for trade in trades:
    srv_time = client.get_server_time()
    now_time = srv_time['serverTime']
    min_ago = now_time - 60000    
    
    if trade['time'] < min_ago:
        quan = trade['qty']
        print(quan)        
    time.sleep(1)
    

"""srv_time = client.get_server_time()
    now_time = srv_time['serverTime']
    min_ago = now_time - 60000"""