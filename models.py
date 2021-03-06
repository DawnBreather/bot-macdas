import json
from types import SimpleNamespace
import boto3
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

_DYNAMODB_TABLE_NAME = 'macdas'

class state:
    macdas = None
    signal1 = None
    delta = None
    long1 = None
    fastprev = None
    slowprev = None
    signalprev = None
    time = None

    def __init__(self, macdas, signal1, delta, long1, fastprev, slowprev, signalprev, time):
        self.macdas = macdas
        self.signal1 = signal1
        self.delta = delta
        self.long1 = long1
        self.fastprev = fastprev
        self.slowprev = slowprev
        self.signalprev = signalprev
        self.time = time

    def __init__(self, result, last_timestamp):
        self.macdas = result['histogram']
        self.signal1 = result['signal_as']
        self.delta = round((result['histogram'] - result['signal_as']), 3)
        self.long1 = int(result['histogram'] > result['signal_as'])
        self.fastprev = result['fast']
        self.slowprev = result['slow']
        self.signalprev = result['signal']
        self.time = datetime.timestamp(datetime.fromtimestamp(last_timestamp) - timedelta(minutes=main_period))

    def set_data_in_mysql(self, mycursor, mydb):
        mycursor.execute("DELETE FROM trade.single")
        mydb.commit()
        sql = "INSERT INTO single (macdas, signal1, delta, long1, fastprev, slowprev, signalprev, time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        val = (self.macdas, self.signal1, self.delta, self.long1, self.fastprev, self.slowprev, self.signalprev, self.time)
        mycursor.execute(sql, val)
        mydb.commit()

    def toJson(self):
        return json.dumps(self, default = lambda o: o.__dict__, sort_keys = True, indent = 4)
    
    def fromJson(self, jsonString):
        x = json.loads(jsonString, object_hook = lambda d: SimpleNamespace(**d))
        self.macdas = x.macdas
        self.signal1 = x.signal1
        self.delta = x.delta
        self.long1 = x.long1
        self.fastprev = x.fastprev
        self.slowprev = x.slowprev
        self.signalprev = x.signalprev
        self.time = x.time

    def set_data_in_dynamodb(self, dynamodb = None):
        if not dynamodb:
            dynamodb = boto3.resource('dynamodb', endpoint_url = "http://localhost:8000")

        table = dynamodb.Table(_DYNAMODB_TABLE_NAME)
        response = table.put_item(
            Item = {
                'data_type': 'state',
                'value': self.toJson
            }
        )

        return response

    def get_data_from_dynamodb(self, dynamodb = None):
        if not dynamodb:
            dynamodb = boto3.resource('dynamodb', endpoint_url = "http://localhost:8000")

        table = dynamodb.Table(_DYNAMODB_TABLE_NAME)
        try:
            response = table.get_item(Key={'data_type': 'state'})
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            return response['Item']