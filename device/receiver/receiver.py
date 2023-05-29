#!/usr/bin/env python

from flask import Flask, request, jsonify
from producer import proceed_to_deliver
from datetime import datetime

host_name = "0.0.0.0"
port = 6070

app = Flask(__name__)             # create an app instance


@app.route("/validate", methods=['POST'])
def alarm():
    try:
        content = request.json
        details = dict()
        # logging
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        details['destination'] = 'log'
        details['operation'] = 'logging'
        details['payload']=f"receiver:{timestamp}:received data from {content['type']}"
        proceed_to_deliver('49', details)
        # deliver to validator_out
        details_2 = dict(details)
        details_2['destination'] = 'validator_out'
        details_2['operation'] = 'validate_command'
        details_2['type'] = content['type']
        details_2['first'] = content['first']
        details_2['second'] = content['second']
        details_2['key'] = content['key']
        proceed_to_deliver('49', details_2)
    except Exception as e:
        print(f'exception raised: {e}')
        return "MALFORMED REQUEST", 400
    return jsonify({"status": True})

from argparse import ArgumentParser, FileType
from configparser import ConfigParser
from multiprocessing import Queue
from producer import start_producer

if __name__ == '__main__':
    # Parse the command line.
    parser = ArgumentParser()
    parser.add_argument('config_file', type=FileType('r'))
    parser.add_argument('--reset', action='store_true')
    args = parser.parse_args()

    # Parse the configuration.
    # See https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
    config_parser = ConfigParser()
    config_parser.read_file(args.config_file)
    config = dict(config_parser['default'])
    config.update(config_parser['receiver'])

    requests_queue = Queue()
    start_producer(args, config, requests_queue)
    app.run(port = port, host=host_name)