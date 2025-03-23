"""
----------------- MESSAGES SERVICE -----------------

For now acting as a stub, when accessed, it returns a static message.
"""
import argparse
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
    parser = argparse.ArgumentParser(description="Messages service")
    parser.add_argument('--port', type=int, default=5001, help='Port to run the service on')
    args = parser.parse_args()

    app.run(port=args.port, debug=True)
