"""
----------------- LOGGING SERVICE -----------------

Stores in memory all the messages it receives and can return them.
"""
import argparse
import requests
from flask import Flask, request, jsonify
import hazelcast

app = Flask(__name__)

CONFIG_SERVER_URL = "http://127.0.0.1:5006/config"
CLIENT = None
MESSAGES_MAP = None
PORT = None


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
    global MESSAGES_MAP

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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Logging service")
    parser.add_argument('--port', type=int, default=5003, help='Port to run the service on')
    args = parser.parse_args()
    PORT = args.port

    STATUS = ""
    while STATUS != "success":
        print("Initializing Hazelcast...")
        STATUS, _ = initialize_hazelcast()

    app.run(port=args.port, debug=True)
