"""
----------------- MESSAGES SERVICE -----------------

For now acting as a stub, when accessed, it returns a static message.
"""
from flask import Flask

app = Flask(__name__)

@app.route('/message', methods=['GET'])
def get_message():
    """
    Returns a static message.

    Returns:
        A static message "not implemented yet".
    """
    return "not implemented yet"

if __name__ == '__main__':
    app.run(port=5002, debug=True)
