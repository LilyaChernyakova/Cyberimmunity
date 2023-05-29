# implements Kafka topic consumer functionality
import time
from datetime import datetime
import threading
from confluent_kafka import Consumer, OFFSET_BEGINNING
import json
from producer import proceed_to_deliver

TOPIC_NAME = "auth_sec"

def log_deliver(is_authorized: bool):
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    details = dict()

    if is_authorized:
        info = "Sec Authorization Success"
    else:
        info = "Sec Authorization Failure"

    details['destination'] = 'log'
    details['operation'] = 'logging'
    details['payload'] = f"{TOPIC_NAME}:{timestamp}:{info}"
    proceed_to_deliver("11", details)

def auth_sec_deliver():
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    details = dict()
    details['destination'] = 'auth_sec'
    details['operation'] = 'authorization'
    details['payload'] = f"authorization:{timestamp}"
    proceed_to_deliver("11", details)

def update_deliver(is_authorized: bool):
    if is_authorized:
        details = dict()
        details['destination'] = 'update'
        details['operation'] = 'apply_update'
        proceed_to_deliver("11", details)

def downloader_deliver(is_authorized: bool):
    if is_authorized:
        details = dict()
        details['destination'] = 'downloader'
        details['operation'] = 'download_update'
        proceed_to_deliver("11", details)

def handle_event(id: str, details: dict):
    # print(f"[debug] handling event {id}, {details}")
    print(f"[info] handling event {id}, {details['source']}->{details['destination']}: {details['operation']}")
    try:
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        info = "Waiting for authorization"
        details['destination'] = 'log'
        details['operation'] = 'logging'
        details['payload'] = [f"{TOPIC_NAME}:{timestamp}:{info}"]
        proceed_to_deliver(id, details)

    except Exception as e:
        print(f"[error] failed to handle request: {e}")

def consumer_job(args, config):
    # Create Consumer instance
    auth_sec_consumer = Consumer(config)

    # Set up a callback to handle the '--reset' flag.
    def reset_offset(auth_sec_consumer, partitions):
        if args.reset:
            for p in partitions:
                p.offset = OFFSET_BEGINNING
            auth_sec_consumer.assign(partitions)

    # Subscribe to topic
    topic = TOPIC_NAME
    auth_sec_consumer.subscribe([topic], on_assign=reset_offset)

    # Poll for new messages from Kafka and print them.
    try:
        while True:
            msg = auth_sec_consumer.poll(1.0)
            msg = auth_sec_consumer.poll(1.0)

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
                    details_str = msg.value().decode('utf-8')
                    # print("[debug] consumed event from topic {topic}: key = {key:12} value = {value:12}".format(
                    # topic=msg.topic(), key=id, value=details_str))
                    handle_event(id, json.loads(details_str))
                    continue
                except Exception as e:
                    print(
                        f"Malformed event received from topic {topic}: {msg.value()}. {e}")
    except KeyboardInterrupt:
        pass
    finally:
        # Leave group and commit final offsets
        auth_sec_consumer.close()


def start_consumer(args, config):
    threading.Thread(target=lambda: consumer_job(args, config)).start()


if __name__ == '__main__':
    start_consumer(None)