"""
----------------- FACADE SERVICE -----------------

Accepts POST/GET requests from the client.
"""
import sys
import signal
import time
import uuid
import random
import argparse
from flask import Flask, request, jsonify
import requests
import hazelcast

app = Flask(__name__)

CONFIG_SERVER_URL = "http://127.0.0.1:5006/config"
SERVICES_IPS = {}
CLIENT = None
MESSAGES_QUEUE = None
RETRIES = 3
DELAY = 2


def get_service_data(service_name: str, path: str):
    """
    Getting service data from config server.
    """
    service_ips = list(SERVICES_IPS.get(service_name))
    num_services = len(service_ips)
    service_ip = random.choice(service_ips)
    service_ips.remove(service_ip)
    url = f"http://{service_ip}/{path}"

    while num_services:
        for attempt in range(RETRIES):
            try:
                response = requests.get(url, timeout=10)

                if response.status_code == 200:
                    return response.json()

            except requests.exceptions.RequestException as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < RETRIES - 1:
                    time.sleep(DELAY)

        if num_services == 1:
            print(f"All {service_name} ports are unavailable after retries.")
            break

        print(f"Port {service_ip} is unavailable after retries. Selecting another port...")
        service_ip = random.choice(service_ips)
        service_ips.remove(service_ip)
        url = f"http://{service_ip}/{path}"
        num_services -= 1

    return None


def post_data_to_service(service_name: str, path: str, payload: dict):
    """
    Posting data to service.
    """
    service_ips = list(SERVICES_IPS.get(service_name))
    num_services = len(service_ips)
    service_ip = random.choice(service_ips)
    service_ips.remove(service_ip)
    url = f"http://{service_ip}/{path}"

    while num_services:
        for attempt in range(RETRIES):
            try:
                response = requests.post(url, json=payload, timeout=10)
                if response.status_code == 200:
                    print(f"Message: {payload['msg']} was posted to {url}.")
                    return "success"

            except requests.exceptions.RequestException as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < RETRIES - 1:
                    time.sleep(DELAY)

        if num_services == 1:
            print("All port are unavailable after retries.")
            break

        print(f"Port {service_ip} is unavailable after retries. Selecting another port...")
        service_ip = random.choice(service_ips)
        service_ips.remove(service_ip)
        url = f"http://{service_ip}/{path}"
        num_services -= 1

    return None


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


def get_hazelcast_service_ips(property_name: str):
    """
    Function to initialize the service IPs from command-line arguments
    """
    global CONFIG_SERVER_URL

    try:
        response = requests.get(f"{CONFIG_SERVER_URL}/{property_name}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get(f"{property_name}", "")

        print(f"Failed to get {property_name} IPs from config server. Status: {response.status_code}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error getting {property_name} IPs from config server: {e}")


def initialize_hazelcast():
    """
    Initializing hazelcast.
    """
    global CLIENT
    global MESSAGES_QUEUE

    hazelcast_cluster_name = ""
    cluster_members = []

    # Get hazelcast-cluster-name IPs from config server
    hazelcast_cluster_name = get_hazelcast_service_ips("hazelcast-cluster-name")
    if hazelcast_cluster_name is None:
        return "failure", "No Hazelcast cluster name"

    # Get hazelcast-clients IPs from config server
    cluster_members = get_hazelcast_service_ips("hazelcast-clients")
    if cluster_members is None:
        return "failure", "No Hazelcast cluster clients"

    CLIENT = hazelcast.HazelcastClient(
        cluster_name=hazelcast_cluster_name,
        cluster_members=cluster_members,
        lifecycle_listeners=[
            lambda state: print("Lifecycle event >>>", state),
        ]
    )

    MESSAGES_QUEUE = CLIENT.get_queue("messages-queue").blocking()

    return "success", "Hazelcast IPs loaded successfully"


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

    # Putting the message in the queue
    MESSAGES_QUEUE.offer(msg)

    # Generate a unique UUID for the message
    uuid_val = str(uuid.uuid4())
    payload = {"uuid": uuid_val, "msg": msg}

    # Selecting port for logging service
    status = post_data_to_service("logging-service", "log", payload)
    if status == "success":
        return jsonify({"status": "success", "uuid": uuid_val}), 200

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
    # Selecting port for logging service
    logs = get_service_data("logging-service", "log")

    # Selecting port for messaging service
    messages = get_service_data("messages-service", "messages")

    if logs is not None and messages is not None:
        return jsonify({"logs": logs, "message": messages}), 200

    return jsonify({"status": "failure", "message": "Service unavailable after retries"}), 500


def shutdown_handler(signum, frame):
    """
    Signal handler to gracefully shut down the Hazelcast client and exit the program.
    """
    global CLIENT

    print(f"Received signal {signum}. Shutting down Hazelcast client...")
    if CLIENT:
        CLIENT.shutdown()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, shutdown_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, shutdown_handler)  # kill command


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Facade service")
    parser.add_argument('--port', type=int, default=5000, help='Port to run the service on')
    args = parser.parse_args()

    STATUS = ""
    while STATUS != "success":
        print("Getting services IPs...")
        STATUS, _ = get_services_ips()

    STATUS = ""
    while STATUS != "success":
        print("Initializing Hazelcast...")
        STATUS, _ = initialize_hazelcast()

    app.run(port=args.port, debug=True)
