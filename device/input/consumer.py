# implements Kafka topic consumer functionality
from datetime import datetime
import threading
from confluent_kafka import Consumer, OFFSET_BEGINNING
import json
from producer import proceed_to_deliver

TOPIC_NAME = "input"

def log_deliver(id: str):
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    details = dict()
    info = "Taken value"
    details['destination'] = 'log'
    details['operation'] = 'logging'
    details['payload'] = f"{TOPIC_NAME}:{timestamp}:{info}"
    proceed_to_deliver(id, details)

def writer_set_deliver(id : str, value: str):
    details = dict()
    details['destination'] = 'writer_set'
    details['operation'] = 'send_value'
    details['payload'] = value
    proceed_to_deliver(id, details)

def hash_deliver(id : str, value: str):
    details = dict()
    details['destination'] = 'hash'
    details['operation'] = 'send_value'
    details['payload'] = value
    proceed_to_deliver(id, details)

def handle_event(id: str, details: dict):
    # print(f"[debug] handling event {id}, {details}")
    print(f"[info] handling event {id}, {details['source']}->{details['destination']}: {details['operation']}")
    try:
        if details['source'] == 'auth_tech':
            f = open("file_server/data/input_file.txt", 'r')
            inp_str = f.read()
            f.close()
            log_deliver(id)
            writer_set_deliver(id, inp_str)
            hash_deliver(id, inp_str)
        else:
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            details['destination'] = 'log'
            details['operation'] = 'logging'
            details['payload'] = f"{TOPIC_NAME}:{timestamp}:signal from {details['source']}"
            proceed_to_deliver(id, details)
    except Exception as e:
        print(f"[error] failed to handle request: {e}")

def consumer_job(args, config):
    # Create Consumer instance
    input_consumer = Consumer(config)

    # Set up a callback to handle the '--reset' flag.
    def reset_offset(input_consumer, partitions):
        if args.reset:
            for p in partitions:
                p.offset = OFFSET_BEGINNING
            input_consumer.assign(partitions)

    # Subscribe to topic
    topic = TOPIC_NAME
    input_consumer.subscribe([topic], on_assign=reset_offset)

    # Poll for new messages from Kafka and print them.
    try:
        while True:
            msg = input_consumer.poll(1.0)
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
        input_consumer.close()


def start_consumer(args, config):
    threading.Thread(target=lambda: consumer_job(args, config)).start()


if __name__ == '__main__':
    start_consumer(None)