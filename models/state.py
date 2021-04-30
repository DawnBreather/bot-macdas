import copy
import json
from enum import Enum
from types import SimpleNamespace
import boto3
from datetime import datetime, timedelta
import time
from botocore.exceptions import ClientError
import mysql.connector

from models.configuration import Configuration

_CONFIG = Configuration()


class DbMode(Enum):
    MYSQL = 1
    DYNAMODB = 2


class DbDataTypes(Enum):
    STATE = 1


class State:
    main_period = _CONFIG.trd_indicator_main_period
    macdas = None
    signal1 = None
    delta = None
    long1 = None
    fast_prev = None
    slow_prev = None
    signal_prev = None
    time = None
    last_rsi_candle = None
    last_up_rma = None
    last_dn_rma = None
    rsi_time = None
    rsi = None
    in_deal = None
    fast = _CONFIG.trd_indicator_fast
    slow = _CONFIG.trd_indicator_slow
    signal = _CONFIG.trd_indicator_signal

    mysqlConnector = None
    mysqlCursor = None

    dynamodbConnector = None

    db_mode = None

    def __init__(self, db_mode=DbMode.MYSQL, auto_fetch_last_state=True):
        self.db_mode = db_mode

        if db_mode == DbMode.MYSQL:
            if auto_fetch_last_state:
                self.__get_data_from_mysql()

        if db_mode == DbMode.DYNAMODB:
            if auto_fetch_last_state:
                self.__get_data_from_dynamodb()

    def update_element(self, result, last_timestamp):
        self.macdas = result['histogram']
        self.signal1 = result['signal_as']
        self.delta = round((result['histogram'] - result['signal_as']), 3)
        self.long1 = int(result['histogram'] > result['signal_as'])
        self.fast_prev = result['fast']
        self.slow_prev = result['slow']
        self.signal_prev = result['signal']
        self.time = datetime.timestamp(datetime.fromtimestamp(last_timestamp) - timedelta(minutes=self.main_period))

    def update_rsi(self, result, last_time):
        self.rsi = result["rsi"]
        self.last_up_rma = result["last_up_rma"]
        self.last_dn_rma = result["last_dn_rma"]
        self.last_rsi_candle = result["last_rsi_candle"]
        self.rsi_time = last_time + timedelta(hours=4)

    def get_data(self):
        if self.db_mode == DbMode.MYSQL:
            self.__get_data_from_mysql()
        if self.db_mode == DbMode.DYNAMODB:
            self.__get_data_from_dynamodb()

    def set_data(self):
        if self.db_mode == DbMode.MYSQL:
            self.__set_data_in_mysql()
        if self.db_mode == DbMode.DYNAMODB:
            self.__set_data_in_dynamodb()

    def __init_mysql_connector(self):
        if not self.mysqlConnector:
            self.mysqlConnector = mysql.connector.connect(
                host=_CONFIG.mysql_host,
                user=_CONFIG.mysql_user,
                password=_CONFIG.mysql_password,
                database=_CONFIG.mysql_database,
            )
            self.mysqlCursor = self.mysqlConnector.cursor()

    def __get_data_from_mysql(self):
        self.__init_mysql_connector()
        self.mysqlCursor.execute("SELECT * FROM trade.single")
        data = self.mysqlCursor.fetchall()
        if data:
            data = data[0]
            self.macdas = float(data[0])
            self.signal1 = float(data[1])
            self.delta = float(data[2])
            self.long1 = int(data[3])
            self.fast_prev = float(data[4])
            self.slow_prev = float(data[5])
            self.signal_prev = float(data[6])
            self.time = int(data[7])

    def __set_data_in_mysql(self):
        self.__init_mysql_connector()
        self.mysqlCursor.execute("DELETE FROM trade.single")
        self.mysqlConnector.commit()
        sql = "INSERT INTO single (macdas, signal1, delta, long1, fastprev, slowprev, signalprev, time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        val = (
            self.macdas, self.signal1, self.delta, self.long1, self.fast_prev, self.slow_prev, self.signal_prev,
            self.time)
        self.mysqlCursor.execute(sql, val)
        self.mysqlConnector.commit()

    def to_json(self):
        tmp = copy.copy(self)
        if type(tmp.time).__name__ != "float":
            tmp.time = round(tmp.time.timestamp())
            print("Warning! tmp.time class is not float: " + type(tmp.time).__name__)

        tmp.dynamodbConnector = None
        tmp.mysqlConnector = None
        tmp.mysqlCursor = None
        tmp.db_mode = None
        return json.dumps(tmp, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def from_json(self, jsonString):
        x = json.loads(jsonString, object_hook=lambda d: SimpleNamespace(**d))
        self.macdas = x.macdas
        self.signal1 = x.signal1
        self.delta = x.delta
        self.long1 = x.long1
        self.fast_prev = x.fast_prev
        self.slow_prev = x.slow_prev
        self.signal_prev = x.signal_prev
        self.time = datetime.fromtimestamp(x.time)

    def __init_dynamodb_connector(self):
        if not self.dynamodbConnector:
            self.dynamodbConnector = boto3.resource('dynamodb', region_name=_CONFIG.region_containing_configurations)

    def __set_data_in_dynamodb(self):
        self.__init_dynamodb_connector()
        table = self.dynamodbConnector.Table(_CONFIG.dynamodb_table)

        response = table.put_item(
            Item={
                'data_type': DbDataTypes.STATE.name,
                'timestamp': round(time.time()),
                'value': self.to_json()
            }
        )

        return response

    def __get_data_from_dynamodb(self):
        self.__init_dynamodb_connector()
        table = self.dynamodbConnector.Table(_CONFIG.dynamodb_table)

        try:
            response = table.get_item(Key={'data_type': DbDataTypes.STATE.name})
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            try:
                json_string = response['Item']['value']
                self.from_json(json_string)
            finally:
                return
