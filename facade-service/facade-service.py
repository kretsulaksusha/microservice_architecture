"""
----------------- FACADE SERVICE -----------------

Accepts POST/GET requests from the client.
"""
import time
import uuid
import random
import argparse
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

CONFIG_SERVER_URL = "http://127.0.0.1:5005/config"
SERVICES_IPS = {}

def get_logging_service_ips():
    """
    Getting logging service ips from config server.
    """
    try:
        response = requests.get(f"{CONFIG_SERVER_URL}/logging-service", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("logging-service", [])

        print(f"Failed to get logging-service IPs from config server. Status: {response.status_code}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error getting logging-service IPs from config server: {e}")
        return []

def get_messages_service_ips():
    """
    Getting messages service ips from config server.
    """
    try:
        response = requests.get(f"{CONFIG_SERVER_URL}/messages-service", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("messages-service", [])

        print(f"Failed to get messages-service IPs from config server. Status: {response.status_code}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error getting messages-service IPs from config server: {e}")
        return []

def get_services_ips():
    """
    Getting services IPs from the config server and storing them globally.
    Returns a tuple (status, message).
    """
    global SERVICES_IPS

    logging_service_ips = get_logging_service_ips()
    if not logging_service_ips:
        return "failure", "No logging services available"

    messages_service_ips = get_messages_service_ips()
    if not messages_service_ips:
        return "failure", "No messaging services available"

    SERVICES_IPS['logging-service'] = logging_service_ips
    SERVICES_IPS['messages-service'] = messages_service_ips

    return "success", "Services IPs loaded successfully"


@app.route('/facade', methods=['POST'])
def facade_post():
    """
    Handles POST requests from the client, logs the message, and returns a response.

    Retry Mechanism:
    - Attempts to send the message to the logging service up to 3 times.
    - Waits 2 seconds between retries.
    - Returns a failure response if all retries are exhausted.

    Expects a JSON payload with the following structure:
    {
        "msg": "<message_text>"
    }

    Returns:
        A response indicating success or failure, along with the UUID of the logged message.
        If the request fails after retries, returns a failure response.
    """
    msg = request.json.get('msg')
    if not msg:
        return jsonify({"status": "failure", "message": "No message provided"}), 400

    uuid_val = str(uuid.uuid4())
    payload = {"uuid": uuid_val, "msg": msg}

    retries = 3
    delay = 2    # delay between retries in seconds

    # Selecting port
    logging_service_ips = list(SERVICES_IPS.get("logging-service"))
    num_logging_services = len(logging_service_ips)
    logging_service_ip = random.choice(logging_service_ips)
    logging_service_ips.remove(logging_service_ip)
    logging_url = f"http://{logging_service_ip}/log"

    while num_logging_services:
        for attempt in range(retries):
            try:
                response = requests.post(logging_url, json=payload, timeout=10)
                if response.status_code == 200:
                    print(f"Message: {msg} was posted to {logging_url}.")
                    return jsonify({"status": "success", "uuid": uuid_val}), 200

            except requests.exceptions.RequestException as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(delay)

        if num_logging_services == 1:
            print("All port are unavailable after retries.")
            break

        print(f"Port {logging_service_ip} is unavailable after retries. Selecting another port...")
        logging_service_ip = random.choice(logging_service_ips)
        logging_service_ips.remove(logging_service_ip)
        logging_url = f"http://{logging_service_ip}/log"
        num_logging_services -= 1

    return jsonify({"status": "failure", "message": "Failed to log message after retries"}), 500


@app.route('/facade', methods=['GET'])
def facade_get():
    """
    Handles GET requests from the client, retrieves logs and a static message,
    and returns a combined response.

    Retry Mechanism:
    - Attempts to connect to the logging and messages services up to 3 times.
    - Waits 2 seconds between retries.
    - Returns a failure response if all retries are exhausted.

    Returns:
        A response containing all logged messages and a static message from the messages service.
        If the request fails after retries, returns a failure response.
    """
    retries = 3
    delay = 2    # delay between retries in seconds

    # Selecting port
    logging_service_ips = list(SERVICES_IPS.get("logging-service"))
    num_logging_services = len(logging_service_ips)
    logging_service_ip = random.choice(logging_service_ips)
    logging_service_ips.remove(logging_service_ip)
    logging_url = f"http://{logging_service_ip}/log"

    messaging_service_ips = list(SERVICES_IPS.get("messages-service"))
    messaging_url = f"http://{messaging_service_ips[0]}/message"

    while num_logging_services:
        for attempt in range(retries):
            try:
                logging_response = requests.get(logging_url, timeout=10)
                message_response = requests.get(messaging_url, timeout=10)

                if logging_response.status_code == 200 and message_response.status_code == 200:
                    logs = logging_response.json()
                    message = message_response.text
                    return jsonify({"logs": logs, "message": message}), 200

            except requests.exceptions.RequestException as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(delay)

        if num_logging_services == 1:
            print("All port are unavailable after retries.")
            break

        print(f"Port {logging_service_ip} is unavailable after retries. Selecting another port...")
        logging_service_ip = random.choice(logging_service_ips)
        logging_service_ips.remove(logging_service_ip)
        logging_url = f"http://{logging_service_ip}/log"
        num_logging_services -= 1

    return jsonify({"status": "failure", "message": "Service unavailable after retries"}), 500


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Facade service")
    parser.add_argument('--port', type=int, default=5000, help='Port to run the service on')
    args = parser.parse_args()

    status = ""
    while status != "success":
        print("Getting services IPs...")
        status, _ = get_services_ips()

    app.run(port=args.port, debug=True)
