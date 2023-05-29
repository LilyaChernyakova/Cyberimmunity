# implements Kafka topic consumer functionality
from datetime import datetime
import threading
from confluent_kafka import Consumer, OFFSET_BEGINNING
import json
from producer import proceed_to_deliver
import pycurl

TOPIC_NAME = "transmitter"

def log_deliver(id: str, top: str):
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    details = dict()
    details['destination'] = 'log'
    details['operation'] = 'logging'
    details['payload'] = f"{TOPIC_NAME}:{timestamp}:{top} signal"
    proceed_to_deliver(id, details)

def handle_event(id: str, details: dict):
    # print(f"[debug] handling event {id}, {details}")
    print(f"[info] handling event {id}, {details['source']}->{details['destination']}: {details['operation']}")
    try:
        # https://scrapeops.io/python-web-scraping-playbook/python-curl-pycurl/#making-post-requests-with-pycurl
        # https://stackabuse.com/using-curl-in-python-with-pycurl/
        log_deliver(id, details['source'])
        if details['source'] == 'ADP':
            value = details['payload'].split(":")[-1]
            status = details['payload'].split(":")[0]
            crl = pycurl.Curl()
            crl.setopt(crl.URL, 'http://scada:6069/data')         
            crl.setopt(crl.HTTPHEADER, ['Accept: application/json', 'Content-Type: application/json'])
            payload = {"status": status, "value": value}
            encoded_data = json.dumps(payload).encode('utf-8')
            crl.setopt(crl.POSTFIELDS, encoded_data)
            crl.perform()
            crl.close()
            if status == "warning" or status == "fatal":
                crl = pycurl.Curl()
                crl.setopt(crl.URL, 'http://protection:6068/alarm')         
                crl.setopt(crl.HTTPHEADER, ['Accept: application/json', 'Content-Type: application/json'])
                payload = {"status": status}
                encoded_data = json.dumps(payload).encode('utf-8')
                crl.setopt(crl.POSTFIELDS, encoded_data)
                crl.perform()
                crl.close()              
        elif details['source'] == 'validator':
            value = details['key']
            status = details['status']
            t = details['type']
            current_value = details['value']
            if (t == "protection"):
                crl = pycurl.Curl()
                crl.setopt(crl.URL, 'http://protection:6068/check')         
                crl.setopt(crl.HTTPHEADER, ['Accept: application/json', 'Content-Type: application/json'])
                payload = {"status": status, "key": value}
                encoded_data = json.dumps(payload).encode('utf-8')
                crl.setopt(crl.POSTFIELDS, encoded_data)
                crl.perform()
                crl.close()            
            else:
                crl = pycurl.Curl()
                crl.setopt(crl.URL, 'http://scada:6069/check')         
                crl.setopt(crl.HTTPHEADER, ['Accept: application/json', 'Content-Type: application/json'])
                payload = {"value": current_value, "key": value}
                encoded_data = json.dumps(payload).encode('utf-8')
                crl.setopt(crl.POSTFIELDS, encoded_data)
                crl.perform()
                crl.close()                
    except Exception as e:
        print(f"[error] failed to handle request: {e}")

def consumer_job(args, config):
    # Create Consumer instance
    transmitter_consumer = Consumer(config)

    # Set up a callback to handle the '--reset' flag.
    def reset_offset(transmitter_consumer, partitions):
        if args.reset:
            for p in partitions:
                p.offset = OFFSET_BEGINNING
            transmitter_consumer.assign(partitions)

    # Subscribe to topic
    topic = TOPIC_NAME
    transmitter_consumer.subscribe([topic, 'transmitter2'], on_assign=reset_offset)

    # Poll for new messages from Kafka and print them.
    try:
        while True:
            msg = transmitter_consumer.poll(1.0)
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
        transmitter_consumer.close()


def start_consumer(args, config):
    threading.Thread(target=lambda: consumer_job(args, config)).start()


if __name__ == '__main__':
    start_consumer(None)