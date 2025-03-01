"""
----------------- FACADE SERVICE -----------------

Accepts POST/GET requests from the client.
"""
import time
import uuid
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

LOGGING_SERVICE_URL = "http://localhost:5001/log"
MESSAGES_SERVICE_URL = "http://localhost:5002/message"


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

    for attempt in range(retries):
        try:
            response = requests.post(LOGGING_SERVICE_URL, json=payload, timeout=10)
            if response.status_code == 200:
                return jsonify({"status": "success", "uuid": uuid_val}), 200

        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)

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

    for attempt in range(retries):
        try:
            logging_response = requests.get(LOGGING_SERVICE_URL, timeout=10)
            message_response = requests.get(MESSAGES_SERVICE_URL, timeout=10)

            if logging_response.status_code == 200 and message_response.status_code == 200:
                logs = logging_response.json()
                message = message_response.text
                return jsonify({"logs": logs, "message": message}), 200

        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)

    return jsonify({"status": "failure", "message": "Service unavailable after retries"}), 500


if __name__ == '__main__':
    app.run(port=5000, debug=True)
