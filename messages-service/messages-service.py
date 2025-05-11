"""
----------------- MESSAGES SERVICE -----------------

For now acting as a stub, when accessed, it returns a static message.
"""
import os
import sys
import json
import signal
import time
import argparse
import threading
import hazelcast
from flask import Flask, jsonify
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from consul_service.consul_service import register_service, get_key_value


CLIENT = None
MESSAGES_QUEUE = None
PORT = None

app = Flask(__name__)
consumer_thread = None

messages = []
stop_event = threading.Event()

def initialize_hazelcast():
    """
    Initializing hazelcast.
    """
    global CLIENT
    global MESSAGES_QUEUE

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

    register_service("messages-service", port=PORT)

    while True:
        print("Initializing Hazelcast...")
        status, _ = initialize_hazelcast()
        if status == "success":
            break
        time.sleep(2)

    consumer_thread = threading.Thread(target=consume_messages, daemon=True, args=(stop_event,))
    consumer_thread.start()

    # use_reloader=False -> disable reloader to prevent multiple processes
    app.run(port=args.port, debug=True, use_reloader=False)
