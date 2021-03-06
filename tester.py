from time import sleep
import main
from datetime import datetime


class Signal:
    long = 0
    next_time = 0

    def update_next_time(self):
        self.next_time = datetime.now().timestamp() - datetime.now().timestamp() % 900 + 905
        print("жду до ", datetime.fromtimestamp(self.next_time))


def wait_coup():
    signal = Signal()

    def new_candle():
        main.root()
        signal.update_next_time()

    while True:
        new_candle()
        sleep(signal.next_time - datetime.now().timestamp() + 1)


wait_coup()
