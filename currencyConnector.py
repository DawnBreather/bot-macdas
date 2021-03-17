import math
from datetime import timedelta, datetime

from models.bybit import ByBit
from models.configuration import Configuration

_CONFIG = Configuration()

_BYBIT_CLIENT = ByBit().client


def get_by_bit_kline(start_time, period, length):
    symbol = _CONFIG.bybit_symbol

    num_of_elements = math.floor(24 * 60 / period)
    massive = []
    start = start_time
    for i in range(0, length, num_of_elements):
        try:
            element = _BYBIT_CLIENT.Kline.Kline_get(symbol=symbol, interval=str(period), limit=num_of_elements, **{'from': start.timestamp()}).result()
            for item in element[0]['result']:
                massive.append(float(item['close']))
        except:
            return None
        start += timedelta(hours=24)

    return massive[0: -1]


def get_by_bit_last_kline(period):
    symbol = _CONFIG.bybit_symbol

    last = (datetime.now() - timedelta(minutes=period*2)).timestamp()
    try:
        element = _BYBIT_CLIENT.Kline.Kline_get(symbol=symbol, interval=str(period), limit=2, **{'from': last}).result()
        return float(element[0]['result'][0]['close'])
    except:
        return None


def deal_qty():
    coin_name = _CONFIG.bybit_balance_coin
    symbol = _CONFIG.bybit_symbol
    deal_adjustment = _CONFIG.bybit_deal_qty_adjustment

    qty = _BYBIT_CLIENT.Wallet.Wallet_getBalance(coin=coin_name).result()
    price = _BYBIT_CLIENT.Market.Market_tradingRecords(symbol=symbol).result()[0]["result"][0]
    qty = qty[0]['result'][coin_name]['available_balance']
    price = price['price']
    usd = math.floor(qty * price)
    return usd + deal_adjustment


def close_position():

    symbol = _CONFIG.bybit_symbol
    order_type = _CONFIG.bybit_position_settings_order_type
    time_in_force = _CONFIG.bybit_position_settings_time_in_force

    current_position = bybit_position()
    if current_position['side'] == "Sell":
        position_dir = 'Buy'
    elif current_position['side'] == "Buy":
        position_dir = 'Sell'
    else:
        return 0
    _BYBIT_CLIENT.Order.Order_new(side=position_dir, symbol=symbol, order_type=order_type, qty=current_position['size'], time_in_force=time_in_force).result()


def bybit_position():
    position = _BYBIT_CLIENT.Positions.Positions_myPosition().result()[0]['result'][0]['data']
    return {"side": position['side'], "size": position['size']}


def close_all_position():
    if close_position():
        close_all_position()


def set_position(long):
    symbol = _CONFIG.bybit_symbol
    long_leverage = _CONFIG.bybit_position_settings_long_leverage
    short_leverage = _CONFIG.bybit_position_settings_short_leverage
    order_type = _CONFIG.bybit_position_settings_order_type
    time_in_force = _CONFIG.bybit_position_settings_time_in_force

    usd = deal_qty()

    if long:
        side = "Buy"
        _BYBIT_CLIENT.Positions.Positions_saveLeverage(symbol=symbol, leverage=long_leverage).result()
    else:
        side = "Sell"
        _BYBIT_CLIENT.Positions.Positions_saveLeverage(symbol=symbol, leverage=short_leverage).result()
        usd *= int(short_leverage)
    _BYBIT_CLIENT.Order.Order_new(side=side, symbol=symbol, order_type=order_type, qty=usd, time_in_force=time_in_force).result()
