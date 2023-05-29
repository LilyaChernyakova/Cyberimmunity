# implements Kafka topic consumer functionality

import threading
from confluent_kafka import Consumer, OFFSET_BEGINNING
import json
from producer import proceed_to_deliver
from datetime import datetime

CURR_VERSION = 4


def handle_event(id: str, details: dict):
    update_version = None
    # print(f"[debug] handling event {id}, {details}")
    print(f"[info] handling event {id}, {details['source']}->{details['destination']}: {details['operation']}")
    try:
        global CURR_VERSION
        if details['source'] == 'writer_upd' and details['operation'] == 'validate_update':
            version = details['payload']
            if version == CURR_VERSION + 1:
                CURR_VERSION = version
                update_version = version
                msg = 'update is valid'
            # Вопрос, что делать в случае равенства версий
            elif version == CURR_VERSION:
                msg = 'no changes found'
            else:
                msg = 'ALERT: update is invalid'

            # logging validation results
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            details['destination'] = 'log'
            details['operation'] = 'logging'
            details['payload'] = f"validator_upd:{timestamp}:{msg}"
            proceed_to_deliver(id, details)
            
            # delivering validation results to update
            details_2 = dict(details)
            details_2['destination'] = 'update'
            details_2['operation'] = 'apply_update'
            details_2['payload'] = update_version
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
    topic = "validator_upd"
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
