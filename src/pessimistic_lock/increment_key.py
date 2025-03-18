"""
----------------- Pessimistic Lock -----------------

Incrementing the value of a key 0 in a distributed map with pessimistic locking.
"""
import hazelcast

def main():
    """
    Function that demonstrates the usage of the distributed map with pessimistic locking.
    """
    client = hazelcast.HazelcastClient(
        cluster_name="dev",
        cluster_members=[
            "127.0.0.1:5701",
            "127.0.0.1:5702",
            "127.0.0.1:5703",
        ],
        lifecycle_listeners=[
            lambda state: print("Lifecycle event >>>", state),
        ]
    )

    # Get or create the "distributed-map" on the cluster
    # blocking() - sync map, all operations are blocking
    distributed_map = client.get_map("distributed-map").blocking()
    iterations = 10000
    key = 0

    for _ in range(iterations):
        distributed_map.lock(key)
        try:
            current_value = distributed_map.get(key) or 0
            distributed_map.put(key, current_value + 1)
        finally:
            distributed_map.unlock(key)

    client.shutdown()


if __name__ == "__main__":
    main()
