import time
from enum import Enum
import bybit

import telebot

from models.configuration import Configuration

_CONFIG = Configuration()


class DbMode(Enum):
    MYSQL = 1
    DYNAMODB = 2


class DbDataTypes(Enum):
    STATE = 1


class ByBit:
    client = None
    retries = 0

    def __init__(self, retries=5, interval=30):
        while self.client is None and self.retries < retries:
            self.client = self.__try_init_client(interval=interval)

    def __try_init_client(self, interval=30):
        by_bit_client = None
        try:
            by_bit_client = bybit(False, api_key=_CONFIG.bybit_api_key, api_secret=_CONFIG.bybit_api_secret)
        except Exception as e:
            self.__send_message_to_telegram("Failed to initialize ByBit client: \n", e)
            time.sleep(interval)
            self.retries += 1

        return by_bit_client

    def __send_message_to_telegram(self, text="placeholder"):
        telegram_bot = telebot.TeleBot(_CONFIG.telegram_bot_api_key)
        telegram_channel = _CONFIG.telegram_bot_channel

        telegram_bot.send_message(telegram_channel, text)