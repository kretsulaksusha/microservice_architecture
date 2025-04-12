"""
----------------- MESSAGES SERVICE -----------------

For now acting as a stub, when accessed, it returns a static message.
"""
import time
import argparse
import threading
import hazelcast
from flask import Flask, jsonify
import requests

CONFIG_SERVER_URL = "http://127.0.0.1:5006/config"
CLIENT = None
MESSAGES_QUEUE = None
PORT = None

app = Flask(__name__)

messages = []


def get_hazelcast_service_ips(property_name: str):
    """
    Function to initialize the service IPs from command-line arguments
    """
    global CONFIG_SERVER_URL

    try:
        response = requests.get(f"{CONFIG_SERVER_URL}/{property_name}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("{property_name}", "")

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
        return "failure", "No Hazelcast cluster name"

    CLIENT = hazelcast.HazelcastClient(
        cluster_name=hazelcast_cluster_name,
        cluster_members=cluster_members,
        lifecycle_listeners=[
            lambda state: print("Lifecycle event >>>", state),
        ]
    )

    MESSAGES_QUEUE = CLIENT.get_queue("messages-queue").blocking()

    return "success", "Hazelcast IPs loaded successfully"

def consume_messages():
    """
    Consumes messages from the Hazelcast queue and stores them in memory.
    """
    global messages

    while True:
        try:
            message = MESSAGES_QUEUE.take()
            if message:
                print(f"Messages-service received message on port {PORT}: {message}")
                messages.append(message)
        except Exception as e:
            print(f"Error consuming message: {e}")
            time.sleep(0.5)


@app.route('/messages', methods=['GET'])
def get_message():
    """
    Returns a static message.

    Returns:
        A static message "not implemented yet".
    """
    return jsonify(messages)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Messages service")
    parser.add_argument('--port', type=int, default=5001, help='Port to run the service on')
    args = parser.parse_args()
    PORT = args.port

    STATUS = ""
    while STATUS != "success":
        print("Initializing Hazelcast...")
        STATUS, _ = initialize_hazelcast()

    threading.Thread(target=consume_messages, daemon=True).start()

    # use_reloader=False -> disable reloader to prevent multiple processes
    app.run(port=args.port, debug=True, use_reloader=False)
