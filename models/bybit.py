import os
import time
from enum import Enum

import boto3
from botocore.config import Config

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
        # self.__send_message_to_telegram(f"inicialisation {client_type}")
        if client_type == ByBitType.Setter:
            self.client = self.__try_init_client(_CONFIG.bybit_api_key, _CONFIG.bybit_api_secret)
        else:
            while (self.client is None) and (self.retries < 1):
                self.client = self.__try_init_client(_CONFIG.bybit_taker_api_key_mas[self.retries % 2],
                                                     _CONFIG.bybit_taker_api_secret_mas[self.retries % 2])

    def __try_init_client(self, api_key, api_secret):
        by_bit_client = None
        try:
            by_bit_client = bybit(False, api_key=api_key, api_secret=api_secret)

        except Exception as e:
            region = os.getenv("AWS_REGION")
            self.__send_message_to_telegram("Failed to initialize ByBit client: \n" + str(e) + "\n api_key: " + str(
                api_key) + "\n retry number: " + str(self.retries) + "\n region: " + region)
            self.__delegate_call_to_next_lambda()
            exit(0)
            # time.sleep(30)
            # self.retries += 1

        return by_bit_client

    def __delegate_call_to_next_lambda(self):
        next_lambda_region = _CONFIG.next_lambda_region
        next_lambda_name = _CONFIG.next_lambda_name
        if not next_lambda_region:
            lambda_client = boto3.client('lambda', region_name=next_lambda_region)
            lambda_client.invoke(FunctionName=next_lambda_name, InvocationType='RequestResponse')

    def __send_message_to_telegram(self, text="placeholder"):
        telegram_bot = telebot.TeleBot(_CONFIG.telegram_bot_api_key)
        telegram_channel = _CONFIG.telegram_bot_channel

        telegram_bot.send_message(telegram_channel, text)
