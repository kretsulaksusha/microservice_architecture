"""
----------------- Optimistic Lock -----------------

Incrementing the value of a key 0 in a distributed map with optimistic locking.
"""
import hazelcast

def main():
    """
    Function that demonstrates the usage of the distributed map with optimistic locking.
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

    iterations, retries = 10000, 50
    key = 0

    for _ in range(iterations):
        for _ in range(retries):
            current_value = distributed_map.get(key)
            new_value = current_value + 1

            if distributed_map.replace_if_same(key, current_value, new_value):
                break

    client.shutdown()


if __name__ == "__main__":
    main()
