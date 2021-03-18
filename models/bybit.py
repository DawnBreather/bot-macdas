import time
from enum import Enum
from bybit import bybit


import telebot

from models.configuration import Configuration

_CONFIG = Configuration()


class ByBitType(Enum):
    Taker = 1
    Setter = 2


class DbMode(Enum):
    MYSQL = 1
    DYNAMODB = 2


class DbDataTypes(Enum):
    STATE = 1


class ByBit:
    client = None
    retries = 0

    def __init__(self, client_type=ByBitType.Taker):
        if client_type == ByBitType.Setter:
            self.client = self.__try_init_client(_CONFIG.bybit_api_key, _CONFIG.bybit_api_secret)
        else:
            while self.client is None and self.retries < 2:
                self.client = self.__try_init_client(_CONFIG.bybit_taker_api_key_mas[self.retries], _CONFIG.bybit_taker_api_key_mas[self.retries])

    def __try_init_client(self, api_key, api_secret):
        by_bit_client = None
        try:
            by_bit_client = bybit(False, api_key=api_key, api_secret=api_secret)
        except Exception as e:
            self.__send_message_to_telegram("Failed to initialize ByBit client: \n" + str(e))

        return by_bit_client

    def __send_message_to_telegram(self, text="placeholder"):
        telegram_bot = telebot.TeleBot(_CONFIG.telegram_bot_api_key)
        telegram_channel = _CONFIG.telegram_bot_channel

        telegram_bot.send_message(telegram_channel, text)
