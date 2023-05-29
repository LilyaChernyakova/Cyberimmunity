# implements Kafka topic consumer functionality

import threading
from confluent_kafka import Consumer, OFFSET_BEGINNING
import json
from producer import proceed_to_deliver
from datetime import datetime
from time import sleep

VERSION = 4


def handle_event(id: str, details: dict):
    # print(f"[debug] handling event {id}, {details}")
    print(f"[info] handling event {id}, {details['source']}->{details['destination']}: {details['operation']}")
    try:
        if details['source'] == 'auth_sec' and details['operation'] == 'apply_update':
            # waiting for other modules
            sleep(0.2)
            # logging
            timestamp =  datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            details['destination'] = 'log'
            details['operation'] = 'logging'
            details['payload'] = f"update:{timestamp}:request sent to writer_upd"
            proceed_to_deliver(id, details)
            # delivering query to writer_upd
            details_2 = dict(details)
            details_2['destination'] = 'writer_upd'
            details_2['operation'] = 'validate_update'
            proceed_to_deliver(id, details_2)
        elif details['source'] == 'validator_upd' and details['operation'] == 'apply_update':
            timestamp =  datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            global VERSION
            if details['payload'] is not None:
                VERSION = details['payload']
                msg = f'new version {VERSION} applied'
            else:
                msg = "update canceled: no update found or update is invalid"
            # logging
            print(msg)
            details['destination'] = 'log'
            details['operation'] = 'logging'
            details['payload'] = f"update:{timestamp}:{msg}"
            proceed_to_deliver(id, details)
            # deauth
            details_3 = dict(details)
            details_3['destination'] = 'log'
            details_3['operation'] = 'logging'
            details_3['payload'] = f"update:{timestamp}:deauthorization complete"
            proceed_to_deliver(id, details_3)
            
            details_4 = dict(details)
            details_4['operation'] = 'deauthorization'
            details_4['payload'] = f"deauthorization:{timestamp}"
            details_4['destination'] = 'auth_sec'
            proceed_to_deliver(id, details_4)
            details_5 = dict(details_4)
            details_5['destination'] = 'auth_tech'
            proceed_to_deliver(id, details_5)
    except Exception as e:
        print(f"[error] failed to handle request: {e}")


def consumer_job(args, config):
    # Create Consumer instance
    recorder_upd_consumer = Consumer(config)

    # Set up a callback to handle the '--reset' flag.
    def reset_offset(recorder_upd_consumer, partitions):
        if args.reset:
            for p in partitions:
                p.offset = OFFSET_BEGINNING
            recorder_upd_consumer.assign(partitions)

    # Subscribe to topic
    topic = "update"
    recorder_upd_consumer.subscribe([topic], on_assign=reset_offset)

    # Poll for new messages from Kafka and print them.
    try:
        while True:
            msg = recorder_upd_consumer.poll(1.0)
            if msg is None:
                # Initial message consumption may take up to
                # `session.timeout.ms` for the consumer group to
                # rebalance and start consuming
                # print("Waiting...")
                pass
            elif msg.error():
                print(f"[error] {msg.error()}")
            else:
                # Extract the (optional) key and value, and print.
                try:
                    id = msg.key().decode('utf-8')
                    details = json.loads(msg.value().decode('utf-8'))
                    # print(
                    #     f"[debug] consumed event from topic {topic}: key = {id} value = {details}")
                    handle_event(id, details)
                except Exception as e:
                    print(
                        f"Malformed event received from topic {topic}: {msg.value()}. {e}")
    except KeyboardInterrupt:
        pass
    finally:
        # Leave group and commit final offsets
        recorder_upd_consumer.close()


def start_consumer(args, config):
    threading.Thread(target=lambda: consumer_job(args, config)).start()


if __name__ == '__main__':
    start_consumer(None)
