import math
import os
from datetime import timedelta, datetime
from bybit import bybit

from models.ssm_parameter_store import SSMParameterStore

_BYBIT_API_KEY = "Eh7cAqnyOf6JarnZl4"
_BYBIT_SECRET = "AZGFkxVODn6vdmyEqZKNC7UsEszWZAD4UKbO"

_SYMBOL = 'BTCUSD'


client_by_bit = bybit(False, api_key=_BYBIT_API_KEY, api_secret=_BYBIT_SECRET)


def get_by_bit_kline(start_time, period, length):
    num_of_elements = math.floor(24 * 60 / period)
    massive = []
    start = start_time
    for i in range(0, length, num_of_elements):
        element = client_by_bit.Kline.Kline_get(symbol=_SYMBOL, interval=str(period), limit=num_of_elements, **{'from': start.timestamp()}).result()
        for item in element[0]['result']:
            massive.append(float(item['close']))
        start += timedelta(hours=24)

    return massive


def get_by_bit_last_kline(period):
    last = (datetime.now() - timedelta(minutes=period*2)).timestamp()
    element = client_by_bit.Kline.Kline_get(symbol=_SYMBOL, interval=str(period), limit=2, **{'from': last}).result()
    return float(element[0]['result'][0]['close'])


def deal_qty():
    qty = client_by_bit.Wallet.Wallet_getBalance(coin="BTC").result()
    price = client_by_bit.Market.Market_tradingRecords(symbol=_SYMBOL).result()[0]["result"][0]
    qty = qty[0]['result']['BTC']['available_balance']
    price = price['price']
    usd = math.floor(qty * price)
    return usd - 5


def close_position():
    current_position = bybit_position()
    if current_position['side'] == "Sell":
        position_dir = 'Buy'
    elif current_position['side'] == "Buy":
        position_dir = 'Sell'
    else:
        return 0
    client_by_bit.Order.Order_new(side=position_dir, symbol=_SYMBOL, order_type="Market", qty=current_position['size'], time_in_force="GoodTillCancel").result()


def bybit_position():
    position = client_by_bit.Positions.Positions_myPosition().result()[0]['result'][0]['data']
    return {"side": position['side'], "size": position['size']}


def close_all_position():
    if close_position():
        close_all_position()


def set_position(long):
    usd = deal_qty()
    if long:
        side = "Buy"
        client_by_bit.Positions.Positions_saveLeverage(symbol=_SYMBOL, leverage="1").result()
    else:
        side = "Sell"
        client_by_bit.Positions.Positions_saveLeverage(symbol=_SYMBOL, leverage="3").result()
        usd *= 3
    client_by_bit.Order.Order_new(side=side, symbol=_SYMBOL, order_type="Market", qty=usd, time_in_force="GoodTillCancel").result()
