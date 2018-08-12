from binance.client import Client

print ''
ticker_symbol = raw_input('Ticker?:>')
print ''

client = Client("", "")

klines = client.get_historical_klines(ticker_symbol, Client.KLINE_INTERVAL_4HOUR, "1 day ago UTC")

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
volume_in_btc = price_avg_24h * volume_24h

print volume_24h
print price_avg_24h
print volume_in_btc