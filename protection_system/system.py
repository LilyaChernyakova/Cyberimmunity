from flask import Flask, request, jsonify
import random
import requests
import json

ALARM_FLAG = 0
STATUS = 0
KEY = 0

host_name = "0.0.0.0"
port = 6068

app = Flask(__name__)             # create an app instance

def check_func(content):
    global KEY
    if KEY == content['key']:
        print(f"[ALARM] срабатывание аварийной защиты: {content['status']}")

@app.route("/check", methods=['POST'])
def check():
    try:
        content = request.json
        print(f"[ALARM] Данные модулей не совпадают")
        check_func(content)
    except Exception as e:
        print(f'exception raised: {e}')
        return "MALFORMED REQUEST", 400
    return jsonify({"status": True})

def delivery_func(key, first, second): 
    url = 'http://device/receiver:6070/validate'
    json_data = json.dumps({"key" : key, "first" : first, "second" : second, "type" : "protection"})
    requests.post(url, data = json_data)


def alarm_func(content):
    # в будущем появится обработка времени
    global ALARM_FLAG, STATUS, KEY
    if ALARM_FLAG == 0:
        STATUS = content['status']
    elif ALARM_FLAG == 1:
        if STATUS == content['status']:
            print(f"[ALARM] срабатывание аварийной защиты: {content['status']}")
        else:
            key = random.randint(100000, 200000)
            KEY = key
            delivery_func(key, STATUS, content['status'])


@app.route("/alarm", methods=['POST'])
def alarm():
    try:
        content = request.json
        alarm_func(content)
    except Exception as e:
        print(f'exception raised: {e}')
        return "MALFORMED REQUEST", 400
    return jsonify({"status": True})


if __name__ == "__main__":        # on running python app.py    
    app.run(port = port, host=host_name)