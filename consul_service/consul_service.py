"""
Consul Service Registration and Discovery
"""
import socket
import json
import consul


def get_consul_client(host="localhost", port=8500):
    """
    Create a Consul client instance.
    """
    return consul.Consul(host=host, port=port)


def register_service(
    name: str,
    port: int,
    service_id: str = None,
    address: str = None,
    consul_host: str = "localhost",
    consul_port: int = 8500,
):
    """
    Register the service with Consul.
    """
    if not address:
        address = socket.gethostbyname(socket.gethostname())  # Get the local IP address (127.0.0.1)

    if not service_id:
        service_id = f"{name}-{address}-{port}"

    client = get_consul_client(consul_host, consul_port)
    client.agent.service.register(
        name=name,
        service_id=service_id,
        address=address,
        port=port,
    )
    print(f"[✔] Registered service: {name} ({address}:{port})")


def set_key_value(key: str, value: str, consul_host="localhost", consul_port=8500):
    """
    Set a key-value pair in the Consul KV store.
    """
    client = get_consul_client(consul_host, consul_port)
    if not isinstance(value, str):
        value = json.dumps(value)
    client.kv.put(key, value)
    print(f"[✔] Set KV: {key} = {value}")


def get_key_value(key: str, consul_host="localhost", consul_port=8500):
    """
    Get all config values for a service from Consul KV.
    """
    client = get_consul_client(consul_host, consul_port)
    _, data = client.kv.get(key)
    value = None

    if data:
        value = data["Value"]
        print(f"[✔] Retrieved KV: {key} = {value}")
    else:
        print(f"[✘] No data found for key: {key}")

    return value


def discover_service(service_name: str, consul_host="localhost", consul_port=8500):
    """
    Discover registered instances of a service.
    """
    client = get_consul_client(consul_host, consul_port)
    _, nodes = client.catalog.service(service_name)
    # print(nodes[0].keys())
    # The output looks like this:
    # dict_keys(['ID', 'Node', 'Address', 'Datacenter', 'TaggedAddresses', 'NodeMeta',
    # 'ServiceKind', 'ServiceID', 'ServiceName', 'ServiceTags', 'ServiceAddress',
    # 'ServiceTaggedAddresses', 'ServiceWeights', 'ServiceMeta', 'ServicePort',
    # 'ServiceSocketPath', 'ServiceEnableTagOverride', 'ServiceProxy', 'ServiceConnect',
    # 'ServiceLocality', 'CreateIndex', 'ModifyIndex'])
    services = [
        {
            "ServiceID": node["ServiceID"],
            "Address": node["ServiceAddress"],
            "Port": node["ServicePort"],
        }
        for node in nodes
    ]

    for service in services:
        print(f"[✔] Discovered service: {service['ServiceID']}\n"
              f"    - Port: {service['Port']}\n"
              f"    - Service Address: {service['Address']}\n")

    return services


def deregister_service(service_id: str, consul_host="localhost", consul_port=8500):
    """
    Deregister a service from Consul.
    """
    client = get_consul_client(consul_host, consul_port)
    client.agent.service.deregister(service_id)
    print(f"[✔] Deregistered service: {service_id}")


def main():
    """
    Example usage of the Consul service registration and discovery.
    """
    set_key_value("hazelcast/hazelcast-cluster-name", "microservice")
    set_key_value("hazelcast/hazelcast-clients",
                  ["127.0.0.1:5701", "127.0.0.1:5702", "127.0.0.1:5703"])


if __name__ == "__main__":
    main()
