from confluent_kafka import Consumer, OFFSET_BEGINNING
import time
import json
import threading

settings = {
    "bootstrap.servers": "su-broker:9192",
    "group.id": "monitor",
    "auto.offset.reset": "earliest",
}

SEC_AUTH = False
TECH_AUTH = False

def check_authorization():
    global SEC_AUTH, TECH_AUTH
    return TECH_AUTH and SEC_AUTH

def checker(args, config):
    # Create Consumer instance
    monitor_consumer = Consumer(config)

    # Set up a callback to handle the '--reset' flag.
    def reset_offset(monitor_consumer, partitions):
        if True:
            for p in partitions:
                p.offset = OFFSET_BEGINNING
            monitor_consumer.assign(partitions)

    # Subscribe to topic
    monitor_consumer.subscribe(["auth_sec", "auth_tech"], on_assign=reset_offset)

    # Poll for new messages from Kafka and print them.
    while True:
        try:
            msg = monitor_consumer.poll(1.0)
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
                    details_str = msg.value().decode('utf-8')
                    data = json.loads(details_str)
                    global SEC_AUTH, TECH_AUTH
                    if data['payload'].split(":")[0] == "authorization":
                        if data['source'] == "auth_tech":
                            TECH_AUTH = True
                        elif data['source'] == "auth_sec":
                            SEC_AUTH = True
                    else:
                        if data['source'] == "auth_tech":
                            TECH_AUTH = False
                        elif data['source'] == "auth_sec":
                            SEC_AUTH = False
                    
                    # print("[debug] consumed event from topic {topic}: key = {key:12} value = {value:12}".format(
                    # topic=msg.topic(), key=id, value=details_str))
                except Exception as e:
                    print(
                        f"Malformed event received from topic. {e}")
        except KeyboardInterrupt:
            pass


def check_operation(id, details):
    authorized = False
    # print(f"[debug] checking policies for event {id}, details: {details}")
    print(f"[info] checking policies for event {id},"\
          f" {details['source']}->{details['destination']}: {details['operation']}")
    src = details['source']
    dst = details['destination']
    operation = details['operation']
    if  src == 'downloader' and dst == 'log' \
        and operation == 'logging':
        authorized = True   
    if  src == 'downloader' and dst == 'writer_upd' \
        and operation == 'write_update':
        authorized = True    
    if  src == 'update' and dst == 'log' \
        and operation == 'logging':
        authorized = True
    if  src == 'update' and dst == 'writer_upd' \
        and operation == 'validate_update':
        authorized = True           
    if src == 'update' and dst == 'auth_sec' \
        and operation == 'deauthorization':
        authorized = True    
    if src == 'update' and dst == 'auth_tech' \
        and operation == 'deauthorization':
        authorized = True    
    if src == 'validator_upd' and dst == 'log' \
        and operation == 'logging':
        authorized = True    
    if src == 'validator_upd' and dst == 'update' \
        and operation == 'apply_update':
        authorized = True    
    if src == 'writer_upd' and dst == 'log' \
        and operation == 'logging':
        authorized = True    
    if src == 'writer_upd' and dst == 'validator_upd' \
        and operation == 'validate_update ':
        authorized = True    


    if  src == 'ADP' and dst == 'log' \
        and operation == 'logging':
        authorized = True   
    if  src == 'ADP' and dst == 'writer_set' \
        and operation == 'get_settings':
        authorized = True    
    if  src == 'ADP' and dst == 'auth_sec' \
        and operation == 'deauthorization':
        authorized = True
    if  src == 'ADP' and dst == 'auth_tech' \
        and operation == 'deauthorization':
        authorized = True     


    if src == 'auth_sec' and dst == 'log' \
        and operation == 'logging':
        authorized = True
    if src == 'auth_sec' and dst == 'update' \
        and operation == 'apply_update':
        authorized = True and check_authorization()   
    if src == 'auth_sec' and dst == 'downloader' \
        and operation == 'download_update':
        authorized = True and check_authorization()   
    if src == 'auth_sec' and dst == 'auth_sec' \
        and operation == 'authorization':
        authorized = True
    if src == 'auth_tech' and dst == 'log' \
        and operation == 'logging':
        authorized = True
    if src == 'auth_tech' and dst == 'settings' \
        and operation == 'change_settings':
        authorized = True and check_authorization()   
    if src == 'auth_tech' and dst == 'input' \
        and operation == 'input_update':
        authorized = True and check_authorization()  
    if src == 'auth_tech' and dst == 'auth_tech' \
        and operation == 'authorization':
        authorized = True   
    if src == 'hash' and dst == 'log' \
        and operation == 'logging':
        authorized = True    
    if src == 'hash' and dst == 'settings' \
        and operation == 'send_hash':
        authorized = True    
    if src == 'hash' and dst == 'ADP' \
        and operation == 'apply_settings':
        authorized = True    
    if src == 'input' and dst == 'log' \
        and operation == 'logging':
        authorized = True
    if src == 'input' and dst == 'writer_set' \
        and operation == 'send_value':
        authorized = True    
    if src == 'settings' and dst == 'log' \
        and operation == 'logging':
        authorized = True    
    if src == 'settings' and dst == 'ADP' \
        and operation == 'send_hash':
        authorized = True    
    if src == 'writer_set' and dst == 'hash' \
        and operation == 'calculate_hash':
        authorized = True    
    if  src == 'receiver' and dst == 'log' \
            and operation == 'logging':
            authorized = True
    if  src == 'receiver' and dst == 'validator_out ' \
            and operation == 'validate_command':
            authorized = True
    if  src == 'transmitter' and dst == 'log' \
            and operation == 'logging':
            authorized = True
    if  src == 'validator_out' and dst == 'log' \
            and operation == 'logging':
            authorized = True
    if  src == 'validator_out' and dst == 'transmitter1 ' \
            and operation == 'transmit_message':
            authorized = True
    if  src == 'validator_out' and dst == 'transmitter2 ' \
            and operation == 'transmit_message':
            authorized = True
    if  src == 'ADP' and dst == 'transmitter' \
            and operation == 'transmit_message':
            authorized = True     

    # kea - Kafka events analyzer - an extra service for internal monitoring,
    # can only communicate with itself
    if src == 'kea' and dst == 'kea' \
        and (operation == 'self_test' or operation == 'test_param'):
        authorized = True
    
    return authorized


def start_auth_check(args, config):
    threading.Thread(target=lambda: checker(args, settings)).start()

