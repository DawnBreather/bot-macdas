import math
import time
import currencyConnector
import ema
from datetime import datetime, timedelta

from models.configuration import Configuration
from models.state import State, DbMode

from models.bybit import ByBit, ByBitType


import telebot

_CONFIG = Configuration()


def send_new_posts(text):
    telegram_bot = telebot.TeleBot(_CONFIG.telegram_bot_api_key)
    telegram_channel = _CONFIG.telegram_bot_channel

    telegram_bot.send_message(telegram_channel, text)


def last_candle(local_period):
    seconds = math.floor(datetime.now().timestamp()) - math.floor(datetime.now().timestamp()) % (local_period * 60)
    return seconds


def update_order(long, last_state, pointer=2):
    client = None
    try:
        client = ByBit(ByBitType.Setter).client
    except Exception as e:
        send_new_posts("Failed to init position : \n" + str(e))
        time.sleep(30)
        if pointer != 0:
            update_order(long, last_state, pointer - 1)
        else:
            last_state.long1 = int(not last_state.long1)
            return 0

    if currencyConnector.bybit_position(client)['side'] != "None":
        currencyConnector.close_position(client)
    send_new_posts(f"я тут {long}")
    if not currencyConnector.set_position(long, client):
        last_state.long1 = int(not last_state.long1)
        send_new_posts("ошибка сделки")
    print("сделка")
    send_new_posts("новая сделка {0} детали: {1}".format(currencyConnector.bybit_position(client)['side'], currencyConnector.bybit_position_tg(client)))


def protocol_update(last_state):
    last = currencyConnector.get_by_bit_last_kline(last_state.main_period)
    # print(last)
    result = ema.macdas_update(last, last_state)
    prev_long = last_state.long1
    last_state.update_element(result, last_candle(last_state.main_period))
    long = int(last_state.macdas > last_state.signal1)
    send_new_posts(f"update new element: {last} %s %s" % (last_state.delta, last_state.macdas))
    if long != prev_long:
        update_order(long, last_state)
    last_state.set_data()


def protocol_update_after_wait(last_state):
    start = last_state.time + timedelta(minutes=last_state.main_period)
    end = last_candle(last_state.main_period)
    candles = math.trunc((end - start.timestamp()) / (60 * last_state.main_period))
    mas = currencyConnector.get_by_bit_kline(start, last_state.main_period, candles)
    send_new_posts("start {0}, end {1}".format(start, datetime.fromtimestamp(end)))
    prev_long = last_state.long1
    for i in mas:
        result = ema.macdas_update(i, last_state)
        last_state.update_element(result, last_candle(last_state.main_period))
    long = int(last_state.macdas > last_state.signal1)
    send_new_posts(f"update_after_wait new elements: {mas}%s %s" % (last_state.delta, last_state.macdas, ))
    if long != prev_long:
        update_order(long, last_state)
    last_state.set_data()


def protocol_new(last_state):
    delta_days = _CONFIG.trd_history_delta_days
    start = (datetime.now() - timedelta(days=delta_days))
    end = last_candle(last_state.main_period)
    candles = math.trunc((end - start.timestamp()) / (60 * last_state.main_period))
    # print(start, end, candles)
    mas = currencyConnector.get_by_bit_kline(start, last_state.main_period, candles)
    if not mas:
        send_new_posts("API error")
        return 0
    result = ema.macdas(mas, last_state.fast, last_state.slow, last_state.signal)
    last_state.update_element(result, last_candle(last_state.main_period))
    last_state.set_data()
    send_new_posts("new %s %s" % (last_state.delta, last_state.macdas))
    current_deal = currencyConnector.bybit_position(ByBit(ByBitType.Setter).client)['side']
    if current_deal != "None":
        if (current_deal == "Buy") and not last_state.long1:
            update_order(last_state.long1, last_state)
        elif (current_deal == "Sell") and last_state.long1:
            update_order(last_state.long1, last_state)


def entrypoint():
    last_state = State(db_mode=DbMode.DYNAMODB)
    if last_state.time:
        print(last_candle(last_state.main_period) - (last_state.main_period * 1 * 60))
        print(last_candle(last_state.main_period) - (last_state.main_period * 2 * 60))
        print(last_state.time.timestamp())
        if last_state.time.timestamp() == (last_candle(last_state.main_period) - (last_state.main_period * 2 * 60)):
            protocol_update(last_state)
            # print("up")
            return 0

    protocol_update_after_wait(last_state)
    # print("new")


def lambda_handler(event=None, context=None):
    entrypoint()


# last_state = State(db_mode=DbMode.DYNAMODB)
# protocol_update(last_state)
