import math
import mysql.connector
import currencyConnector
import ema
from datetime import datetime, timedelta

import telebot

bot = telebot.TeleBot('1644677350:AAFphMLBPP4PLPeQULq7Y_Tndlt5x7ZtzZ4')
CHANNEL_NAME = '@macdastothemoon'


def send_new_posts(text):
    bot.send_message(CHANNEL_NAME, text)


main_period = 15
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="12345678",
    database="trade"
)

mycursor = mydb.cursor()

fast = 3
slow = 9
signal = 6


def last_candle(localperiod):
    milliseconds = math.floor(datetime.now().timestamp()) - math.floor(datetime.now().timestamp()) % (localperiod*60)
    return milliseconds


def get_data():
    mycursor.execute("SELECT * FROM trade.single")
    return mycursor.fetchall()


def set_data(result, last_timestamp):
    time = datetime.timestamp(datetime.fromtimestamp(last_timestamp) - timedelta(minutes=main_period))
    mycursor.execute("DELETE FROM trade.single")
    mydb.commit()
    sql = "INSERT INTO single (macdas, signal1, delta, long1, fastprev, slowprev, signalprev, time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    long = int(result['histogram'] > result['signal_as'])
    delta = round((result['histogram'] - result['signal_as']), 3)
    val = (result['histogram'], result['signal_as'], delta, long, result['fast'], result['slow'], result['signal'], time)
    mycursor.execute(sql, val)
    mydb.commit()


def update_order(long):
    if currencyConnector.bybit_position()['side'] != "None":
        currencyConnector.close_position()
    currencyConnector.set_position(long)
    send_new_posts(currencyConnector.bybit_position()['side'])


def protocol_update():
    last = currencyConnector.get_by_bit_last_kline(main_period)
    prev = get_data()[0]
    if prev[7] == datetime.timestamp(datetime.fromtimestamp(last_candle(main_period)) - timedelta(minutes=main_period)):
        return 0
    new = ema.macdas_update(last, prev[4], prev[5], prev[6], prev[1], fast, slow, signal)
    set_data(new, last_candle(main_period))
    long = int(new['histogram'] > new['signal_as'])
    if long != prev[3]:
        update_order(long)


def protocol_new():
    period = main_period
    start = (datetime.now() - timedelta(days=3) - timedelta(minutes=period*2))
    end = last_candle(period)
    candles = math.trunc((end - start.timestamp())/(period*60))
    mas = currencyConnector.get_by_bit_kline(start, period, candles)
    result = ema.macdas(mas, fast, slow, signal)
    set_data(result, end)
    currencyConnector.close_all_position()
    protocol_update()
