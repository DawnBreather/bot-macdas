import math
import currencyConnector
import ema
from datetime import datetime, timedelta
import models

import telebot

bot = telebot.TeleBot('1644677350:AAFphMLBPP4PLPeQULq7Y_Tndlt5x7ZtzZ4')
CHANNEL_NAME = '@macdastothemoon'


def send_new_posts(text):
    bot.send_message(CHANNEL_NAME, text)


def last_candle(localperiod):
    seconds = math.floor(datetime.now().timestamp()) - math.floor(datetime.now().timestamp()) % (localperiod*60)
    return seconds


# def get_data():
#     mycursor.execute("SELECT * FROM trade.single")
#     return mycursor.fetchall()
#
#
# def set_data(result, last_timestamp):
#     time = datetime.timestamp(datetime.fromtimestamp(last_timestamp) - timedelta(minutes=main_period))
#     mycursor.execute("DELETE FROM trade.single")
#     mydb.commit()
#     sql = "INSERT INTO single (macdas, signal1, delta, long1, fastprev, slowprev, signalprev, time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
#     long = int(result['histogram'] > result['signal_as'])
#     delta = round((result['histogram'] - result['signal_as']), 3)
#     val = (result['histogram'], result['signal_as'], delta, long, result['fast'], result['slow'], result['signal'], time)
#     mycursor.execute(sql, val)
#     mydb.commit()


def update_order(long):
    if currencyConnector.bybit_position()['side'] != "None":
        currencyConnector.close_position()
    currencyConnector.set_position(long)
    print("сделка")
    send_new_posts("я работаю {}".format(currencyConnector.bybit_position()['side']))


def protocol_update(last_condition):
    last = currencyConnector.get_by_bit_last_kline(last_condition.main_period)
    print(last)
    result = ema.macdas_update(last, last_condition)
    prev_long = last_condition.long1
    last_condition.update_element(result, last_candle(last_condition.main_period))
    long = int(last_condition.macdas > last_condition.signal1)
    if long != prev_long:
        update_order(long)
    last_condition.set_data_in_mysql()


def protocol_new(last_condition):
    start = (datetime.now() - timedelta(days=15))
    end = last_candle(last_condition.main_period)
    candles = math.trunc((end - start.timestamp())/(60 * last_condition.main_period))
    mas = currencyConnector.get_by_bit_kline(start, last_condition.main_period, candles)
    result = ema.macdas(mas, last_condition.fast, last_condition.slow, last_condition.signal, start)
    last_condition.update_element(result, last_candle(last_condition.main_period))
    last_condition.set_data_in_mysql()
    currencyConnector.close_all_position()


def root():
    last_condition = models.state()
    # print(last_condition.delta)
    if last_condition.time == (last_candle(last_condition.main_period) - (last_condition.main_period * 2 * 60)):
        protocol_update(last_condition)
        # print("up")
    else:
        protocol_new(last_condition)
        # print("new")


# protocol_new(models.state())
