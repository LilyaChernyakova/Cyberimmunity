#!/usr/bin/env python

from argparse import ArgumentParser, FileType
from configparser import ConfigParser
from multiprocessing import Queue
from consumer import start_consumer
from producer import start_producer
from consumer import auth_tech_deliver, log_deliver, settings_deliver, input_deliver
from flask import Flask, jsonify, request

app = Flask(__name__)  

host_name = "0.0.0.0"
port = 6071

@app.route("/key", methods=['POST'])
def update():
    try:
        content = request.json
        is_authorized = False
        if content['key'] == "123":
            auth_tech_deliver()
            is_authorized = True         
        log_deliver(is_authorized)
        settings_deliver(is_authorized)
        input_deliver(is_authorized)
    except:
        print(f"malformed request {request.data}")
    return jsonify({"operation": "password requested"})

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
    config.update(config_parser['auth_tech'])

    requests_queue = Queue()
    start_consumer(args, config)
    start_producer(args, config, requests_queue)
    app.run(host=host_name, port=port, debug=True, use_reloader=False)