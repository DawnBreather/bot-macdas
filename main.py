import math
import os

import currencyConnector
import ema
from datetime import datetime, timedelta
from models.state import State, DbMode


import telebot

_TELEGRAM_BOT = telebot.TeleBot('1644677350:AAFphMLBPP4PLPeQULq7Y_Tndlt5x7ZtzZ4')
_TELEGRAM_CHANNEL_NAME = '@macdastothemoon'


def send_new_posts(text):
    _TELEGRAM_BOT.send_message(_TELEGRAM_CHANNEL_NAME, text)


def last_candle(local_period):
    seconds = math.floor(datetime.now().timestamp()) - math.floor(datetime.now().timestamp()) % (local_period * 60)
    return seconds


def update_order(long):
    if currencyConnector.bybit_position()['side'] != "None":
        currencyConnector.close_position()
    currencyConnector.set_position(long)
    print("сделка")
    send_new_posts("я работаю {}".format(currencyConnector.bybit_position()['side']))


def protocol_update(last_state):
    last = currencyConnector.get_by_bit_last_kline(last_state.main_period)
    print(last)
    result = ema.macdas_update(last, last_state)
    prev_long = last_state.long1
    last_state.update_element(result, last_candle(last_state.main_period))
    long = int(last_state.macdas > last_state.signal1)
    if long != prev_long:
        update_order(long)
    last_state.set_data()


def protocol_new(last_state):
    start = (datetime.now() - timedelta(days=15))
    end = last_candle(last_state.main_period)
    candles = math.trunc((end - start.timestamp()) / (60 * last_state.main_period))
    mas = currencyConnector.get_by_bit_kline(start, last_state.main_period, candles)
    result = ema.macdas(mas, last_state.fast, last_state.slow, last_state.signal, start)
    last_state.update_element(result, last_candle(last_state.main_period))
    last_state.set_data()
    currencyConnector.close_all_position()


def entrypoint():
    last_state = State(db_mode=DbMode.DYNAMODB)
    # print(last_state.delta)
    if last_state.time == (last_candle(last_state.main_period) - (last_state.main_period * 2 * 60)):
        protocol_update(last_state)
        # print("up")
    else:
        protocol_new(last_state)
        # print("new")


def lambda_handler(event, context):
    entrypoint()

