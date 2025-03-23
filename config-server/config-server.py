"""
----------------- CONFIG SERVER -----------------
"""
import argparse
from flask import Flask, jsonify
import toml

app = Flask(__name__)

config = toml.load("config.toml")
service_ips = config.get("service_ips", {})
hazelcast_data = config.get("hazelcast", {})


def initialize_service_ips(user_service_ips):
    """
    Function to initialize the service IPs from command-line arguments
    """
    global service_ips

    if user_service_ips:
        service_ips.clear()
        for service_ip in user_service_ips.split(','):
            service, ip = service_ip.split()
            if service in service_ips:
                service_ips[service].append(ip)
            else:
                service_ips[service] = [ip]


@app.route('/config/<service_name>', methods=['GET'])
def get_service_ips(service_name):
    """
    Returns the list of IPs for a service.
    """
    if "hazelcast" in service_name:
        data = hazelcast_data.get(service_name)
    else:
        data = service_ips.get(service_name)

    if data:
        return jsonify({f"{service_name}": data})

    return jsonify({"status": "failure", "message": f"Service {service_name} not found"}), 404


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Config service")
    parser.add_argument('--port', type=int, default=5005, help='Port to run the service on')
    parser.add_argument('--service-ips', type=str,
                        help='Comma separated list of service names and their IPs\n'
                        'separated by a space (<service IP>).'
                        'Ex.: logging-service 127.0.0.1:5001,messages-service 127.0.0.1:5005')
    args = parser.parse_args()

    initialize_service_ips(args.service_ips)

    app.run(port=args.port, debug=True)
