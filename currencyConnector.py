import math
from datetime import timedelta, datetime
import time

from models.bybit import ByBit, ByBitType
from models.configuration import Configuration
import telebot

_CONFIG = Configuration()


def send_new_posts(text):
    telegram_bot = telebot.TeleBot(_CONFIG.telegram_bot_api_key)
    telegram_channel = _CONFIG.telegram_bot_channel

    telegram_bot.send_message(telegram_channel, text)


def get_by_bit_kline(start_time, period, length):
    _BYBIT_CLIENT = ByBit().client
    symbol = _CONFIG.bybit_symbol_leverage
    if length == 0:
        exit(0)
    num_of_elements = math.floor(24 * 60 / period)
    if num_of_elements > length:
        num_of_elements = length
    massive = []
    start = start_time
    for i in range(0, length, num_of_elements):
        try:
            # print(symbol, period, num_of_elements, start, length, i)
            send_new_posts("get_b_b_kline")
            element = _BYBIT_CLIENT.LinearKline.LinearKline_get(symbol=symbol, interval=str(period), limit=num_of_elements, **{'from': start.timestamp()}).result()
            # element = _BYBIT_CLIENT.Kline.Kline_get(symbol=symbol, interval=str(period), limit=num_of_elements, **{'from': start.timestamp()}).result()
            # print(element[0])
            # send_new_posts("elements {0}".format(element))
            for item in element[0]['result']:
                massive.append(float(item['close']))
        except Exception as e:
            print('error: ', e)
            send_new_posts("не получил данные, останавливаю выполнение, function name: get_by_bit_kline")
            exit(0)
        start += timedelta(hours=24)
    send_new_posts("num_of_elements: {0}, start {1}, ".format(num_of_elements, start, massive))
    if not massive:
        exit(0)
    return massive


def get_by_bit_last_kline(period):
    _BYBIT_CLIENT = ByBit().client
    symbol = _CONFIG.bybit_symbol_leverage

    last = (datetime.now() - timedelta(minutes=period*2)).timestamp()
    try:
        send_new_posts("get_b_b_last_kline")
        element = _BYBIT_CLIENT.LinearKline.LinearKline_get(symbol=symbol, interval=str(period), limit=2, **{'from': last}).result()
        # element = _BYBIT_CLIENT.Kline.Kline_get(symbol=symbol, interval=str(period), limit=2, **{'from': last}).result()
        return float(element[0]['result'][0]['close'])
    except Exception as e:
        print('error: ', e)
        send_new_posts("не получил данные, останавливаю выполнение, function name: get_by_bit_last_kline")
        exit(0)


def get_by_bit_last_kline_time(period):
    _BYBIT_CLIENT = ByBit().client
    symbol = _CONFIG.bybit_symbol_leverage

    last = (datetime.now() - timedelta(minutes=period*2)).timestamp()
    try:
        send_new_posts("get_b_b_last_kline")
        element = _BYBIT_CLIENT.LinearKline.LinearKline_get(symbol=symbol, interval=str(period), limit=2, **{'from': last}).result()
        # element = _BYBIT_CLIENT.Kline.Kline_get(symbol=symbol, interval=str(period), limit=2, **{'from': last}).result()
        return datetime.fromtimestamp(element[0]['result'][0]['open_time'])
    except Exception as e:
        print('error: ', e)
        send_new_posts("не получил данные, останавливаю выполнение, function name: get_by_bit_last_kline")
        exit(0)


def deal_qty(client):
    coin_name = _CONFIG.bybit_balance_coin_usdt
    symbol = _CONFIG.bybit_symbol
    send_new_posts("deal_qty")
    qty = client.Wallet.Wallet_getBalance(coin=coin_name).result()
    price = client.Market.Market_tradingRecords(symbol=symbol).result()[0]["result"][0]
    qty = qty[0]['result'][coin_name]['available_balance']
    price = price['price']
    usd = qty / price
    send_new_posts(f"deal_qty: {usd - usd % 0.001}")
    return usd - usd % 0.001


def close_position(client):

    symbol = _CONFIG.bybit_symbol_leverage
    order_type = _CONFIG.bybit_position_settings_order_type
    time_in_force = _CONFIG.bybit_position_settings_time_in_force

    current_position = bybit_position(client)
    if current_position['side'] == "Sell":
        position_dir = 'Buy'
    elif current_position['side'] == "Buy":
        position_dir = 'Sell'
    else:
        return 0
    send_new_posts("close_position")
    usd = current_position["size"]
    client.LinearOrder.LinearOrder_new(side=position_dir, symbol=symbol, order_type=order_type, qty=usd, time_in_force=time_in_force, reduce_only=True, close_on_trigger=False).result()


def bybit_position(client):
    send_new_posts("bybit_position")
    position = client.LinearPositions.LinearPositions_myPosition(symbol="BTCUSDT").result()[0]['result']
    for i in position:
        if str(i["size"]) == "0":
            continue
        else:
            return {"side": i['side'], "size": i['size']}


def bybit_position_tg(client):
    send_new_posts("bybit_position_tg")
    position = client.LinearPositions.LinearPositions_myPosition(symbol="BTCUSDT").result()[0]['result']
    for i in position:
        if str(i["size"]) == "0":
            continue
        else:
            return i


def close_all_position(client):
    if close_position(client):
        close_all_position(client)


def set_position(long, client, pointer=2):
    send_new_posts("set_position")
    symbol_leverage = _CONFIG.bybit_symbol_leverage
    long_leverage = _CONFIG.bybit_position_settings_long_leverage
    short_leverage = _CONFIG.bybit_position_settings_short_leverage
    order_type = _CONFIG.bybit_position_settings_order_type
    time_in_force = _CONFIG.bybit_position_settings_time_in_force
    try:
        usd = deal_qty(client)

        if long:
            client.LinearPositions.LinearPositions_saveLeverage(symbol=symbol_leverage, buy_leverage=long_leverage, sell_leverage=short_leverage).result()
            side = "Buy"
        else:
            client.LinearPositions.LinearPositions_saveLeverage(symbol=symbol_leverage, buy_leverage=long_leverage, sell_leverage=short_leverage).result()
            side = "Sell"
        usd *= int(short_leverage)
        send_new_posts(f"set_position\nqty :{usd}\nsymbol: {symbol_leverage}\n side: {side}\n order_type: {order_type}\n time_in_force: {time_in_force}")
        client.LinearOrder.LinearOrder_new(side=side, symbol=symbol_leverage, order_type=order_type, qty=usd, time_in_force=time_in_force, reduce_only=False, close_on_trigger=False).result()
    except Exception as e:
        send_new_posts("Failed to open position: \n" + str(e))
        time.sleep(30)
        if pointer != 0:
            return set_position(long, ByBit(ByBitType.Setter).client, pointer - 1)
        else:
            return False
    return True
