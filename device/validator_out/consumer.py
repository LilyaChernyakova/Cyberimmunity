# implements Kafka topic consumer functionality

import threading
from confluent_kafka import Consumer, OFFSET_BEGINNING
import json
from producer import proceed_to_deliver
from datetime import datetime


def handle_event(id_receiver: str, id_transmitter: str, details_receiver:dict, details_transmitter: dict):
    # print(f"[debug] handling event {id}, {details}")
    print(f"[info] handling event {id}, {details['source']}->{details['destination']}: {details['operation']}")
    try:
        if details_receiver['source'] == 'receiver' and details_receiver['operation'] == 'validate_command':
            # настоящий статус
            original_status = details_transmitter['payload'].split(':')[0]
            # настоящее значение
            original_value = details_transmitter['payload'].split(':')[1]
            
            details = dict()
            details['operation'] = 'transmit_message'
            details['type'] = details_receiver['type']
            # Как отправить нужному передатчику? И какие из значений класть - оригинальные или поступившие из приёмника?
            # Верный статус у первого
            if details_receiver['first'] == original_status:
                valid_transmitter = 'first'
                details['destination'] = 'transmitter1'
                if details['type'] == 'protection':
                    details['status'] = details_receiver[valid_transmitter]
                elif details['type'] == 'data':
                    details['value'] = original_value
                details['key'] = details_receiver['key']
            # Верный статус у второго
            elif details_receiver['second'] == original_status:
                valid_transmitter = 'second'
                details['destination'] = 'transmitter2'
                if details['type'] == 'protection':
                    details['status'] = details_receiver[valid_transmitter]
                elif details['type'] == 'data':
                    details['value'] = original_value
                details['key'] = details_receiver['key']
            # По какой-то причине нет верного статуса
            else:
                valid_transmitter = 'none'
            if valid_transmitter != 'none':
                proceed_to_deliver(id, details)
            
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            details_2 = dict(details)
            details_2['destination'] = 'log'
            details_2['operation'] = 'logging'
            if valid_transmitter != 'none':
                details_2['payload'] = f"validator_out:{timestamp}:transmitter {valid_transmitter} is valid, using it"
            else:
                details_2['payload'] = f"validator_out:{timestamp}:both transmitters are invalid"
            proceed_to_deliver(id, details_2)
    except Exception as e:
        print(f"[error] failed to handle request: {e}")



def consumer_job(args, config):
    # Create Consumer instance
    receiver_consumer = Consumer(config)
    transmitter_consumer = Consumer(config)

    # Set up a callback to handle the '--reset' flag.
    def reset_offset(consumer, partitions):
        if args.reset:
            for p in partitions:
                p.offset = OFFSET_BEGINNING
            consumer.assign(partitions)

    # Subscribe to topic
    topic1 = "validator_out"
    topic2 = "transmitter"
    receiver_consumer.subscribe([topic1], on_assign=reset_offset)
    transmitter_consumer.subscribe([topic2], on_assign=reset_offset)

    # Poll for new messages from Kafka and print them.
    try:
        while True:
            msg_receiver = receiver_consumer.poll(1.0)
            msg_transmitter = transmitter_consumer.poll(1.0)
            if msg_receiver is None or msg_transmitter is None:
                # Initial message consumption may take up to
                # `session.timeout.ms` for the consumer group to
                # rebalance and start consuming
                # print("Waiting...")
                pass
            elif msg_receiver.error():
                print(f"[error] {msg_receiver.error()}")
            elif msg_transmitter.error():
                print(f"[error] {msg_transmitter.error()}")
            else:
                # Extract the (optional) key and value, and print.
                try:
                    id_receiver = msg_receiver.key().decode('utf-8')
                    details_receiver = json.loads(msg_receiver.value().decode('utf-8'))
                    id_transmitter = msg_transmitter.key().decode('utf-8')
                    details_transmitter = json.loads(msg_transmitter.value().decode('utf-8'))
                    # print(
                    #     f"[debug] consumed event from topic {topic}: key = {id} value = {details}")
                    handle_event(id_receiver, id_transmitter, details_receiver, details_transmitter)
                except Exception as e:
                    print(
                        f"Malformed event received from topic {topic1} or {topic2}: {msg_receiver.value()}. {msg_transmitter.value()} {e}")
    except KeyboardInterrupt:
        pass
    finally:
        # Leave group and commit final offsets
        receiver_consumer.close()
        transmitter_consumer.close()


def start_consumer(args, config):
    threading.Thread(target=lambda: consumer_job(args, config)).start()


if __name__ == '__main__':
    start_consumer(None)
