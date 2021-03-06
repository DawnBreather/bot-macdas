from datetime import datetime
from models.state import State, DbMode


def test_saving_data_to_dynamodb():
    print("TESTING")
    last_state = State(db_mode=DbMode.DYNAMODB)
    last_state.main_period = 1
    last_state.signal1 = 2
    last_state.long1 = 3
    last_state.time = datetime.now()
    last_state.signal = 4
    last_state.delta = 5
    last_state.fast = 6
    last_state.fast_prev = 7
    last_state.macdas = 8
    last_state.signal_prev = 9
    last_state.slow = 10
    last_state.slow_prev = 11

    last_state.set_data()


def test_getting_data_from_dynamodb():
    print("Test getting from dynamodb")
    last_state = State(db_mode=DbMode.DYNAMODB)
    last_state.get_data()
    print(last_state.to_json())


test_saving_data_to_dynamodb()

# testGettingFromDynamodb()
