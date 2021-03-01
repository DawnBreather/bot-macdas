from time import sleep
import main
from datetime import datetime



class Signal:
    long = 0
    next_time = 0

    def update_next_time(self):
        self.next_time = datetime.now().timestamp() - datetime.now().timestamp() % 60 + 60
        print("жду до ", datetime.fromtimestamp(self.next_time))


def wait_coup():
    main.protocol_new()
    signal = Signal()

    def new_candle():
        main.protocol_update()
        signal.update_next_time()

    while True:
        new_candle()
        print("я тут")
        sleep(signal.next_time - datetime.now().timestamp() + 1)


wait_coup()
