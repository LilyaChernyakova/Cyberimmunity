# implements Kafka topic consumer functionality
from datetime import datetime
import threading
from confluent_kafka import Consumer, OFFSET_BEGINNING
import json
from producer import proceed_to_deliver

TOPIC_NAME = "hash"
AUTHORIZATION_FLAG = 0
AUTHORIZATION_TIME = 0


def log_deliver(id: str, top: str):
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    details = dict()
    details['destination'] = 'log'
    details['operation'] = 'logging'
    details['payload'] = [f"{TOPIC_NAME}:{timestamp}:{top} signal"]
    proceed_to_deliver(id, details)


def handle_event(id: str, details: dict):
    # print(f"[debug] handling event {id}, {details}")
    print(f"[info] handling event {id}, {details['source']}->{details['destination']}: {details['operation']}")
    try:
        log_deliver(id, details['source'])
        if details['source'] == 'input':
            details['destination'] = 'settings'
            details['operation'] = 'send_hash'
            data = hash(details['payload'])
            details['payload'] = data
            proceed_to_deliver(id, details)
        elif details['source'] == 'writer_set':
            details['destination'] = 'ADP'
            details['operation'] = 'apply_settings'
            data = details['payload']
            hash_value = hash(data)
            details['payload'] = [data, hash_value]
            proceed_to_deliver(id, details)
    except Exception as e:
        print(f"[error] failed to handle request: {e}")

def consumer_job(args, config):
    # Create Consumer instance
    settings_consumer = Consumer(config)

    # Set up a callback to handle the '--reset' flag.
    def reset_offset(settings_consumer, partitions):
        if args.reset:
            for p in partitions:
                p.offset = OFFSET_BEGINNING
            settings_consumer.assign(partitions)

    # Subscribe to topic
    topic = TOPIC_NAME
    settings_consumer.subscribe([topic], on_assign=reset_offset)
    print("hash exists")

    # Poll for new messages from Kafka and print them.
    try:
        while True:
            msg = settings_consumer.poll(1.0)
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
                except Exception as e:
                    print(
                        f"Malformed event received from topic {topic}: {msg.value()}. {e}")
    except KeyboardInterrupt:
        pass
    finally:
        # Leave group and commit final offsets
        settings_consumer.close()


def start_consumer(args, config):
    threading.Thread(target=lambda: consumer_job(args, config)).start()


if __name__ == '__main__':
    start_consumer(None)