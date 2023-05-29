# implements Kafka topic producer functionality

import threading
from producer import proceed_to_deliver
from time import sleep
from random import randrange
from consumer import FATAL_THRESHOLD, WARNING_THRESHOLD
from datetime import datetime

DELIVERY_INTERVAL_SEC = 5
SIGNAL_RANGE = 20


def sensor_job():
    global DELIVERY_INTERVAL_SEC, SIGNAL_RANGE
    while True:
        sleep(DELIVERY_INTERVAL_SEC)
        value = randrange(SIGNAL_RANGE)
        if value > FATAL_THRESHOLD:
            msg_type = 'fatal'
        elif value > WARNING_THRESHOLD:
            msg_type = 'warning'
        else:
            msg_type = 'info'
        
        details = dict()
        # send message to transmitter
        details['destination'] = 'transmitter'
        details['operation'] = 'transmit_message'
        details['payload'] = f"{msg_type}:{value}"
        proceed_to_deliver('27', details)
        #logging
        details_2 = dict()
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        details_2['destination'] = 'log'
        details_2['operation'] = 'logging'
        details_2['payload'] = f"ADP:{timestamp}:value={value}"
        proceed_to_deliver('27', details_2)

def start_sensor():
    threading.Thread(target=lambda: sensor_job()).start()