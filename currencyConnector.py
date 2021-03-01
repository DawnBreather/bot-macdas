import math
from datetime import timedelta, datetime
from bybit import bybit

bybit_api_key = "Eh7cAqnyOf6JarnZl4"
bybit_secret = "AZGFkxVODn6vdmyEqZKNC7UsEszWZAD4UKbO"

client_by_bit = bybit(False, api_key=bybit_api_key, api_secret=bybit_secret)


def get_by_bit_kline(start_time, period, length):
    num_of_elements = math.floor(24 * 60 / period)
    massive = []
    start = start_time
    for i in range(math.floor(length / num_of_elements)):
        element = client_by_bit.Kline.Kline_get(symbol="BTCUSD", interval=str(period), limit=num_of_elements, **{'from': start.timestamp()}).result()
        for item in element[0]['result']:
            massive.append(float(item['close']))
        start += timedelta(days=1)

    return massive


def get_by_bit_last_kline(period):
    last = (datetime.now() - timedelta(minutes=period*2)).timestamp()
    element = client_by_bit.Kline.Kline_get(symbol="BTCUSD", interval=str(period), limit=2, **{'from': last}).result()
    return float(element[0]['result'][0]['close'])


def deal_qty():
    qty = client_by_bit.Wallet.Wallet_getBalance(coin="BTC").result()
    price = client_by_bit.Market.Market_tradingRecords(symbol="BTCUSD").result()[0]["result"][0]
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
    client_by_bit.Order.Order_new(side=position_dir, symbol="BTCUSD", order_type="Market", qty=current_position['size'], time_in_force="GoodTillCancel").result()


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
        client_by_bit.Positions.Positions_saveLeverage(symbol="BTCUSD", leverage="1").result()
    else:
        side = "Sell"
        client_by_bit.Positions.Positions_saveLeverage(symbol="BTCUSD", leverage="3").result()
        usd *= 3
    client_by_bit.Order.Order_new(side=side, symbol="BTCUSD", order_type="Market", qty=usd, time_in_force="GoodTillCancel").result()


# def close_deal():

# set_position()
# close_position()
