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
    symbol = _CONFIG.bybit_symbol

    num_of_elements = math.floor(24 * 60 / period)
    massive = []
    start = start_time

    for i in range(0, length, num_of_elements):
        try:
            element = _BYBIT_CLIENT.Kline.Kline_get(symbol=symbol, interval=str(period), limit=num_of_elements, **{'from': start.timestamp()}).result()
            send_new_posts("elements {0}".format(element))
            for item in element[0]['result']:
                massive.append(float(item['close']))
        except:
            return None
        start += timedelta(hours=24)
    send_new_posts("num_of_elements: {0}, start {1}, ".format(num_of_elements, start, massive))
    return massive


def get_by_bit_last_kline(period):
    _BYBIT_CLIENT = ByBit().client
    symbol = _CONFIG.bybit_symbol

    last = (datetime.now() - timedelta(minutes=period*2)).timestamp()
    try:
        element = _BYBIT_CLIENT.Kline.Kline_get(symbol=symbol, interval=str(period), limit=2, **{'from': last}).result()
        return float(element[0]['result'][0]['close'])
    except:
        return None


def deal_qty(client):
    coin_name = _CONFIG.bybit_balance_coin
    symbol = _CONFIG.bybit_symbol
    deal_adjustment = _CONFIG.bybit_deal_qty_adjustment

    qty = client.Wallet.Wallet_getBalance(coin=coin_name).result()
    price = client.Market.Market_tradingRecords(symbol=symbol).result()[0]["result"][0]
    qty = qty[0]['result'][coin_name]['available_balance']
    price = price['price']
    usd = math.floor(qty * price)
    return usd - (usd/100)*deal_adjustment


def close_position(client):

    symbol = _CONFIG.bybit_symbol
    order_type = _CONFIG.bybit_position_settings_order_type
    time_in_force = _CONFIG.bybit_position_settings_time_in_force

    current_position = bybit_position(client)
    if current_position['side'] == "Sell":
        position_dir = 'Buy'
    elif current_position['side'] == "Buy":
        position_dir = 'Sell'
    else:
        return 0
    client.Order.Order_new(side=position_dir, symbol=symbol, order_type=order_type, qty=current_position['size'], time_in_force=time_in_force).result()


def bybit_position(client):
    position = client.Positions.Positions_myPosition().result()[0]['result'][0]['data']
    return {"side": position['side'], "size": position['size']}


def close_all_position(client):
    if close_position(client):
        close_all_position(client)


def set_position(long, client, pointer=10):
    symbol = _CONFIG.bybit_symbol
    long_leverage = _CONFIG.bybit_position_settings_long_leverage
    short_leverage = _CONFIG.bybit_position_settings_short_leverage
    order_type = _CONFIG.bybit_position_settings_order_type
    time_in_force = _CONFIG.bybit_position_settings_time_in_force
    try:
        usd = deal_qty(client)

        if long:
            side = "Buy"
            client.Positions.Positions_saveLeverage(symbol=symbol, leverage=long_leverage).result()
        else:
            side = "Sell"
            client.Positions.Positions_saveLeverage(symbol=symbol, leverage=short_leverage).result()
            usd *= int(short_leverage)
        client.Order.Order_new(side=side, symbol=symbol, order_type=order_type, qty=usd, time_in_force=time_in_force).result()
    except Exception as e:
        send_new_posts("Failed to open position: \n" + str(e))
        time.sleep(30)
        if pointer != 0:
            set_position(long, ByBit(ByBitType.Setter).client, pointer - 1)
        else:
            return False
    return True
