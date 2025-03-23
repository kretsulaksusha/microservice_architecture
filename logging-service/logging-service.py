"""
----------------- LOGGING SERVICE -----------------

Stores in memory all the messages it receives and can return them.
"""
import argparse
import requests
from flask import Flask, request, jsonify
import hazelcast

app = Flask(__name__)

CONFIG_SERVER_URL = "http://127.0.0.1:5005/config"
CLIENT = None
MESSAGES_MAP = None


def initialize_hazelcast_clients():
    """
    Initializing hazelcast clients.
    """
    global CLIENT
    global MESSAGES_MAP

    hazelcast_cluster_name = ""
    cluster_members = []

    try:
        response = requests.get(f"{CONFIG_SERVER_URL}/hazelcast-cluster-name", timeout=5)
        if response.status_code == 200:
            data = response.json()
            hazelcast_cluster_name = data.get("hazelcast-cluster-name", "")
        else:
            print(f"Failed to get hazelcast-cluster-name IPs from config server. Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error getting hazelcast-cluster-name IPs from config server: {e}")

    if not hazelcast_cluster_name:
        return "failure", "No Hazelcast cluster name"

    try:
        response = requests.get(f"{CONFIG_SERVER_URL}/hazelcast-clients", timeout=5)
        if response.status_code == 200:
            data = response.json()
            cluster_members = data.get("hazelcast-clients", [])
        else:
            print(f"Failed to get hazelcast-clients IPs from config server. Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error getting hazelcast-clients IPs from config server: {e}")

    if not cluster_members:
        return "failure", "No Hazelcast cluster members"

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
        print(f"Logged message: {msg}")
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
    parser.add_argument('--port', type=int, default=5002, help='Port to run the service on')
    args = parser.parse_args()

    status = ""
    while status != "success":
        print("Getting Hazelcast client IPs...")
        status, _ = initialize_hazelcast_clients()

    app.run(port=args.port, debug=True)
