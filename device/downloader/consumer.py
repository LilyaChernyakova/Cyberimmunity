# implements Kafka topic consumer functionality

import threading
from confluent_kafka import Consumer, OFFSET_BEGINNING
import json
from producer import proceed_to_deliver
from datetime import datetime

NEW_FW_PATHNAME = "file_server/data/new.txt"
f = open("file_server/data/log.txt", "w")


def handle_event(id: str, details: dict):    
    # print(f"[debug] handling event {id}, {details}")
    print(f"[info] handling event {id}, {details['source']}->{details['destination']}: {details['operation']}")
    try:
        if details['source'] == 'auth_sec' and details['operation'] == 'download_update':
            # Read new.txt from update
            with open(NEW_FW_PATHNAME,"r") as f:
                payload = f.read()
            
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            details['destintation'] = 'log'
            details['operation'] = 'logging'
            details['payload'] = f"downloader:{timestamp}:download complete"
            proceed_to_deliver(id, details)

            # Deliver update data to writer
            details['destination'] = 'writer_upd'
            details['operation'] = 'write_update'
            details['payload'] = payload
            proceed_to_deliver(id, details)
    except Exception as e:
        print(f"[error] failed to handle request: {e}")

def consumer_job(args, config):
    f.write("Downloader: do consumer_job\n")
    # Create Consumer instance
    downloader_consumer = Consumer(config)

    # Set up a callback to handle the '--reset' flag.
    def reset_offset(downloader_consumer, partitions):
        if args.reset:
            for p in partitions:
                p.offset = OFFSET_BEGINNING
            downloader_consumer.assign(partitions)

    # Subscribe to topic
    topic = "downloader"
    downloader_consumer.subscribe([topic], on_assign=reset_offset)
    f.write("Downloader: subscribed\n")

    # Poll for new messages from Kafka and print them.
    try:
        while True:
            msg = downloader_consumer.poll(1.0)
            f.write("Downloader: got a message\n")
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
        downloader_consumer.close()


def start_consumer(args, config):
    f.write("Downloader: initialize\n")
    threading.Thread(target=lambda: consumer_job(args, config)).start()


if __name__ == '__main__':
    start_consumer(None)