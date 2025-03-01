"""
----------------- LOGGING SERVICE -----------------

Stores in memory all the messages it receives and can return them.
"""
from flask import Flask, request, jsonify

app = Flask(__name__)

messages = {}

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
        messages[uuid] = msg
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
    return jsonify(list(messages.values()))

if __name__ == '__main__':
    app.run(port=5001, debug=True)
