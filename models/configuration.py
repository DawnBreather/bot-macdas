import os
from pydoc import locate

import boto3


class Configuration:

    # ENV
    ssm_prefix = '/macdas'

    # SSM
    mysql_host = 'localhost'
    mysql_user = 'root'
    mysql_password = '12345678'
    mysql_database = 'trade'

    dynamodb_table = 'macdas'

    #telegram_bot_api_key = '1644677350:AAFphMLBPP4PLPeQULq7Y_Tndlt5x7ZtzZ4'
    telegram_bot_api_key = 'placeholder'
    telegram_bot_channel = '@macdastothemoon'

    # bybit_api_key = 'Eh7cAqnyOf6JarnZl4'
    # bybit_api_secret = 'AZGFkxVODn6vdmyEqZKNC7UsEszWZAD4UKbO'
    bybit_api_key = 'placeholder'
    bybit_api_secret = 'placeholder'

    bybit_symbol = 'BTCUSD'

    bybit_balance_coin = 'BTC'
    bybit_deal_qty_adjustment = -5

    bybit_position_settings_order_type = 'Market'
    bybit_position_settings_time_in_force = 'GoodTillCancel'
    bybit_position_settings_long_leverage = '1'
    bybit_position_settings_short_leverage = '3'

    trd_indicator_main_period = 15
    trd_indicator_fast = 61
    trd_indicator_slow = 81
    trd_indicator_signal = 368

    trd_history_delta_days = 15

    def __init__(self, ssm_enabled=True):

        ssm_connector = None

        if ssm_enabled:
            ssm_connector = boto3.client('ssm')

        self.__init_parameters(ssm_connector)

        return

    def __init_parameters(self, ssm_connector):
        parameter_names = [a for a in dir(self) if not a.startswith('__') and not callable(getattr(self, a))]
        self.__get_parameter('ssm_prefix', ssm_connector=ssm_connector)
        for pn in parameter_names:
            if pn != 'ssm_prefix':
                self.__get_parameter(pn, ssm_connector=ssm_connector)

    def print(self):
        parameter_names = [a for a in dir(self) if not a.startswith('__') and not callable(getattr(self, a))]
        for pn in parameter_names:
            print(pn + " <" + type(getattr(self, pn)).__name__ + ">" + " : " + str(getattr(self, pn)))

    def __get_parameter(self, parameter_name, ssm_connector):

        # STATIC
        initial_value = getattr(self, parameter_name)
        value = None

        # SSM
        if ssm_connector:
            with_decryption = parameter_name.endswith('_key') or parameter_name.endswith('_secret')
            tmp = self.__get_parameter_from_ssm(parameter_name, ssm_connector, with_decryption=with_decryption)
            if tmp:
                value = tmp

        # ENV
        tmp = self.__get_parameter_from_env(parameter_name)
        if tmp:
            value = tmp

        # ERROR
        if not value and not initial_value:
            print("Value for " + parameter_name + " not identified nor at SSM neither at ENV")
            exit(1)

        setattr(self, parameter_name, cast_to(initial_value, value))

        return

    def __get_parameter_from_ssm(self, parameter_name, ssm_connector, with_decryption=False):
        name = self.ssm_prefix + "/" + parameter_name.replace('_', "/")
        try:
            parameter = ssm_connector.get_parameter(Name=name, WithDecryption=with_decryption)
        except:
            return None
        res = parameter['Parameter']['Value']
        if res == "" or not parameter or not res:
            return None
        return res

    def __get_parameter_from_env(self, parameter_name):
        res = os.getenv(parameter_name.upper())
        if res == "":
            return None
        return res


def cast_to(initial_value, value):
    if not value:
        return initial_value
    initial_type = type(initial_value).__name__
    # print("Initial value type: " + type(initial_value).__name__ + '\n' + 'New value type: ' + type(value).__name__)
    if initial_type != "NoneType" and initial_type != "str":
        t = locate(initial_type)
        return t(value)
    return value
