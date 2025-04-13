"""
----------------- MESSAGES SERVICE -----------------

For now acting as a stub, when accessed, it returns a static message.
"""
import signal
import sys
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
consumer_thread = None

messages = []
stop_event = threading.Event()


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


def consume_messages(stop_event):
    """
    Consumes messages from the Hazelcast queue and stores them in memory.
    """
    global messages

    while not stop_event.is_set():
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


def shutdown_handler(signum, frame):
    """
    Signal handler to gracefully shut down the Hazelcast client and exit the program.
    """
    global CLIENT
    global consumer_thread

    print(f"Received signal {signum}. Shutting down Hazelcast client...")
    stop_event.set()  # signal the thread to stop
    consumer_thread.join()  # wait for thread to finish
    if CLIENT:
        CLIENT.shutdown()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, shutdown_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, shutdown_handler)  # kill command


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Messages service")
    parser.add_argument('--port', type=int, default=5001, help='Port to run the service on')
    args = parser.parse_args()
    PORT = args.port

    STATUS = ""
    while STATUS != "success":
        print("Initializing Hazelcast...")
        STATUS, _ = initialize_hazelcast()

    consumer_thread = threading.Thread(target=consume_messages, daemon=True, args=(stop_event,))
    consumer_thread.start()

    # use_reloader=False -> disable reloader to prevent multiple processes
    app.run(port=args.port, debug=True, use_reloader=False)
