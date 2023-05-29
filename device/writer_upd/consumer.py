# implements Kafka topic consumer functionality

import threading
from confluent_kafka import Consumer, OFFSET_BEGINNING
import json
from producer import proceed_to_deliver
from datetime import datetime

VERSION = 4


def handle_event(id: str, details: dict):
    # print(f"[debug] handling event {id}, {details}")
    print(f"[info] handling event {id}, {details['source']}->{details['destination']}: {details['operation']}")
    try:
        global VERSION
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        if details['source'] == 'downloader' and details['operation'] == 'write_update':
            VERSION = int(details['payload'].split()[1])
            # logging
            details['destination'] = 'log'
            details['operation'] = 'logging'
            details['payload'] = f"writer_upd:{timestamp}:written update"
            proceed_to_deliver(id, details)
        elif details['source'] == 'update' and details['operation'] == 'validate_update':
            # logging
            details['destination'] = 'log'
            details['operation'] = 'logging'
            details['payload'] = f"writer_upd:{timestamp}:sending update to validator"
            proceed_to_deliver(id, details)
            # delivering to validator
            details_2 = dict(details)
            details_2['destination'] = 'validator_upd'
            details_2['operation'] = 'validate_update'
            details_2['payload'] = VERSION
            proceed_to_deliver(id, details_2)
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
    topic = "writer_upd"
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
