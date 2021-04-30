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


def setter_client(last_state, pointer=2):
    client = None
    try:
        client = ByBit(ByBitType.Setter).client
    except Exception as e:
        send_new_posts("Failed to init position : \n" + str(e))
        time.sleep(30)
        if pointer != 0:
            setter_client(last_state, pointer - 1)
        else:
            last_state.long1 = int(not last_state.long1)
            exit(0)
    return client


def deal_processing(last_state, prev_position):
    if not last_state.in_deal:
        client = setter_client(last_state)
        close_deal(client)
        open_new(last_state, client)
        last_state.in_deal = True
    else:
        if last_state.long1 == prev_position:
            return 0
        else:
            client = setter_client(last_state)
            close_deal(client)
            open_new(last_state, client)
            last_state.in_deal = True


def update_order(last_state, prev_position):
    if last_state.long1 and (last_state.rsi >= _CONFIG.rsi_middle_level):
        deal_processing(last_state, prev_position)

    elif (not last_state.long1) and (last_state.rsi < _CONFIG.rsi_middle_level):
        deal_processing(last_state, prev_position)

    else:
        client = setter_client(last_state)
        close_deal(client)
        last_state.in_deal = False


def close_deal(client):
    if currencyConnector.bybit_position(client)['side'] != "None":
        currencyConnector.close_position(client)
    # send_new_posts("сделка закрыта")


def open_new(last_state, client):
    if not currencyConnector.set_position(last_state.long1, client):
        last_state.long1 = int(not last_state.long1)
        send_new_posts("ошибка сделки")
    side = currencyConnector.bybit_position(client)['side']
    info = currencyConnector.bybit_position_tg(client)
    send_new_posts(f"новая сделка:\n"
                   f"Symbol: {info['symbol']}\n"
                   f"Side: {side}\n"
                   f"value: {info['position_value']}\n"
                   f"entry_price: {info['entry_price']}")


def protocol_update(last_state):
    last = currencyConnector.get_by_bit_last_kline(last_state.main_period)
    # print(last)
    result = ema.macdas_update(last, last_state)
    prev_position = last_state.long1
    last_state.update_element(result, last_candle(last_state.main_period))
    # long = int(last_state.macdas > last_state.signal1)
    if (datetime.fromtimestamp(last_state.rsi_time) + timedelta(hours=8)) <= datetime.now():
        element = currencyConnector.get_by_bit_last_kline(_CONFIG.rsi_time_frame)
        rsi_result = ema.RSI_update(last_state, element)
        last_state.update_rsi(rsi_result)
    send_new_posts(f"update new element: {last} %s %s, rsi: {last_state.rsi}" % (last_state.delta, last_state.macdas))
    update_order(last_state, prev_position)
    last_state.set_data()


def protocol_update_after_wait(last_state):
    start = last_state.time + timedelta(minutes=last_state.main_period)
    end = last_candle(last_state.main_period)
    candles = math.trunc((end - start.timestamp()) / (60 * last_state.main_period))
    mas = currencyConnector.get_by_bit_kline(start, last_state.main_period, candles)
    print(len(mas))
    prev_position = last_state.long1
    for i in mas:
        result = ema.macdas_update(i, last_state)
        last_state.update_element(result, last_candle(last_state.main_period))

    last_4_hour_candle = currencyConnector.get_by_bit_last_kline_time(_CONFIG.rsi_period)
    delta_seconds = (datetime.timestamp(last_4_hour_candle) - last_state.rsi_time)
    if delta_seconds/(60*240) >= 1:
        candles_for_rsi = math.trunc(delta_seconds/(60*240))
        mas = currencyConnector.get_by_bit_kline(datetime.fromtimestamp(last_state.rsi_time) + timedelta(hours=4), _CONFIG.rsi_period, candles_for_rsi)
        for item in mas:
            rsi_result = ema.RSI_update(last_state, item)
            last_state.update_rsi(rsi_result)

    send_new_posts(f"update_after_wait new elements: {mas}%s %s, rsi: {last_state.rsi}" % (last_state.delta, last_state.macdas))
    update_order(last_state, prev_position)
    last_state.set_data()


def protocol_new(last_state):
    delta_days = _CONFIG.trd_history_delta_days
    send_new_posts("protocol_new_init")
    start = (datetime.now() - timedelta(days=delta_days))
    end = last_candle(last_state.main_period)
    candles = math.trunc((end - start.timestamp()) / (60 * last_state.main_period))
    mas = currencyConnector.get_by_bit_kline(start, last_state.main_period, candles)
    if not mas:
        send_new_posts("API error")
        return 0

    result = ema.macdas(mas, last_state.fast, last_state.slow, last_state.signal)
    last_state.update_element(result, last_candle(last_state.main_period))

    result_rsi = ema.RSI_new()
    last_time = currencyConnector.get_by_bit_last_kline_time(_CONFIG.rsi_period)
    last_state.update_rsi(result_rsi, last_time)

    send_new_posts("new %s %s %s" % (last_state.delta, last_state.macdas, last_state.rsi))
    current_deal = currencyConnector.bybit_position(setter_client(last_state))['side']
    prev_position = False
    if current_deal != "None":
        last_state.in_deal = True
        if current_deal == "Sell":
            prev_position = False
        else:
            prev_position = True
    else:
        last_state.in_deal = False

    update_order(last_state, prev_position)
    last_state.set_data()


def entrypoint():
    last_state = State(db_mode=DbMode.DYNAMODB)
    if not last_state.rsi:
        protocol_new(last_state)
        return 0
    elif last_state.time:
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


last_state = State(db_mode=DbMode.DYNAMODB)
protocol_new(last_state)
