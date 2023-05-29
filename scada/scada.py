from flask import Flask, request, jsonify
import random
import requests
import json

host_name = "0.0.0.0"
port = 6069

app = Flask(__name__)             # create an app instance

DATA_FLAG = 0
VALUE = 0
KEY = 0


def check_func(content):
    global KEY, VALUE
    if KEY == content['key']:
        print(f"Значение датчика: {VALUE}")

@app.route("/check", methods=['POST'])
def check():
    try:
        content = request.json
        print(f"[DATA] получено цифровое значение: {content['value']}")
    except Exception as e:
        print(f"exception raised: {e}")
        return "BAD REQUEST", 400
    return jsonify({"operation": "check", "status": True})

def delivery_func(key, first, second): 
    url = 'http://device/receiver:6070/validate'
    json_data = json.dumps({"key" : key, "first" : first, "second": second, "type" : "data"})
    requests.post(url, data = json_data)

def data_func(content):
    # в будущем появится обработка времени
    global DATA_FLAG, VALUE, KEY
    if DATA_FLAG == 0:
        VALUE = content['value']
    elif DATA_FLAG == 1:
        if VALUE == content['value']:
            print(f"[DATA] получено цифровое значение: {VALUE}")
        else:
            key = random.randint(100000, 200000)
            KEY = key
            delivery_func(key, VALUE, content['value'])

@app.route("/data", methods=['POST'])
def alarm():
    try:
        content = request.json
        data_func(content)
    except Exception as e:
        print(f'exception raised: {e}')
        return "MALFORMED REQUEST", 400
    return jsonify({"status": True})

@app.route("/diagnostic", methods=['POST'])
def diagnostic_msg_receive():
    try:
        content = request.json
        print(f"[DIAGNOSTIC] проверка завершена со статусом: {content['status']}")
    except Exception as e:
        print(f"exception raised: {e}")
        return "BAD REQUEST", 400
    return jsonify({"operation": "diagnostic", "status": True})

@app.route("/key", methods=['POST'])
def key_msg_receive():
    try:
        content = request.json
        print(f"[KEY] изменен ключ: {content['key']}")
    except Exception as e:
        print(f"exception raised: {e}")
        return "BAD REQUEST", 400
    return jsonify({"operation": "key", "status": True})

@app.route("/error", methods=['POST'])
def err_msg_receive():
    try:
        content = request.json
        print(f"[ERROR] произошла ошибка: {content['error']}")
    except Exception as e:
        print(f"exception raised: {e}")
        return "BAD REQUEST", 400
    return jsonify({"operation": "error", "status": True})

if __name__ == "__main__":        
    app.run(port = port, host=host_name)