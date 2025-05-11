"""
----------------- LOGGING SERVICE -----------------

Stores in memory all the messages it receives and can return them.
"""
import sys
import os
import time
import json
import signal
import argparse
from flask import Flask, request, jsonify
import hazelcast
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from consul_service.consul_service import get_key_value, register_service


app = Flask(__name__)

# CONFIG_SERVER_URL = "http://127.0.0.1:5006/config"
CLIENT = None
MESSAGES_MAP = None
PORT = None


def get_hazelcast_config(key: str):
    """
    Get Hazelcast config values from Consul KV store.
    """
    value = get_key_value(f"hazelcast/{key}")
    if value:
        return json.loads(value)
    return None


def initialize_hazelcast():
    """
    Initializing hazelcast.
    """
    global CLIENT
    global MESSAGES_MAP

    cluster_name_encoded = get_key_value("hazelcast/hazelcast-cluster-name")
    clients_encoded = get_key_value("hazelcast/hazelcast-clients")

    if not cluster_name_encoded or not clients_encoded:
        return "failure", "Missing Hazelcast config in Consul"

    cluster_name = cluster_name_encoded.decode()
    members = json.loads(clients_encoded.decode())

    CLIENT = hazelcast.HazelcastClient(
        cluster_name=cluster_name,
        cluster_members=members,
        lifecycle_listeners=[
            lambda state: print("Lifecycle event >>>", state),
        ],
    )

    MESSAGES_MAP = CLIENT.get_map("messages-map").blocking()

    return "success", "Hazelcast IPs loaded successfully"


@app.route('/log', methods=['POST'])
def post_message():
    """
    Saves a message with a unique UUID into the in-memory storage.

    Expects a JSON payload with the following structure:
    {
        "uuid": "<unique_id>",
        "msg": "<message_text>"
    }

    Returns:
        A response indicating success or failure.
    """
    data = request.json
    uuid = data.get('uuid')
    msg = data.get('msg')
    if uuid and msg:
        MESSAGES_MAP.put(uuid, msg)
        print(f"Logging-service logged message on port {PORT}: {msg}")
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "failure"}), 400

@app.route('/log', methods=['GET'])
def get_messages():
    """
    Retrieves all logged messages from the in-memory storage.

    Returns:
        A list of all saved messages.
    """
    return jsonify(list(MESSAGES_MAP.values()))


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
    parser = argparse.ArgumentParser(description="Logging service")
    parser.add_argument('--port', type=int, default=5003, help='Port to run the service on')
    args = parser.parse_args()
    PORT = args.port

    register_service(name="logging-service", port=PORT)

    while True:
        print("Initializing Hazelcast...")
        status, _ = initialize_hazelcast()
        if status == "success":
            break
        time.sleep(2)

    app.run(port=args.port, debug=True)
