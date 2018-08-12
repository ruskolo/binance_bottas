import time
import urllib2
import re
from binance.client import Client
from bs4 import BeautifulSoup

client = Client("", "")

web_page = 'https://coinmarketcap.com/'
page = urllib2.urlopen(web_page)
soup = BeautifulSoup(page, 'html.parser')

coin_boxes = []

for item in soup.findAll('tr', {"id": re.compile('^id-')}):
    coin_boxes.append(item)
    
for coin in coin_boxes:
    c_name_box = coin.find('td', {'class': 'no-wrap currency-name'})
    c_name = c_name_box.get('data-sort')
    c_symbol = c_name_box.span.text
    c_url = c_name_box.span.a.get('href')
    
    c_price_btc = coin.find('a', {'class': 'price'}).get('data-btc')
    c_price_usd = coin.find('a', {'class': 'price'}).get('data-usd')
    c_volume_btc = coin.find('a', {'class': 'volume'}).get('data-btc')
    
    name_string = c_name + ' (' + c_symbol + ')'
    
    print name_string + ' '*(32-len(name_string)) + c_price_btc + '\t' + c_volume_btc


#players_box = soup.find('tbody')    
#players = players_box.find_all('tr')
